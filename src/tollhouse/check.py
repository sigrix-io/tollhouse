"""Reading an MCP server's ``tools/list`` answer, and checking every string in it."""

from __future__ import annotations

import codecs
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tollhouse.rules.injection_scan import scan_text
from tollhouse.rules.tool_text import scan_tool_text, tool_text_strings

#: A ``tools/list`` answer runs to a few hundred kilobytes at the most. Past this,
#: the file is something else, and it is not read into memory.
MAX_FILE_BYTES = 8 * 1024 * 1024


class ToolsFileError(ValueError):
    """The file is not a ``tools/list`` answer this can read. The message says what to do."""


@dataclass(frozen=True)
class Finding:
    """One rule's match in one string a model is handed."""

    place: str  # where the string sits, e.g. tools[search].inputSchema.properties[query].description
    rule: str  # the rule's stable id
    rule_name: str
    matched: str  # at most 80 characters of the text that matched

    def as_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass(frozen=True)
class Report:
    """What one check read and found."""

    tools: int
    strings: int
    findings: tuple[Finding, ...]

    def as_dict(self) -> dict[str, Any]:
        return {
            "tools": self.tools,
            "strings": self.strings,
            "findings": [finding.as_dict() for finding in self.findings],
        }


def read_tools(path: Path) -> list[Any]:
    """The tools in the file at ``path``, or :class:`ToolsFileError`."""
    try:
        with path.open("rb") as handle:
            raw = handle.read(MAX_FILE_BYTES + 1)
    except OSError as exc:
        raise ToolsFileError(f"Cannot read {path}: {exc.strerror or exc}.") from None
    if len(raw) > MAX_FILE_BYTES:
        raise ToolsFileError(
            f"{path} is over {MAX_FILE_BYTES:,} bytes, more than a tools/list answer should be. "
            "Check it holds only the answer."
        )
    return tools_of(_json_document(raw, path), path)


def tools_of(document: Any, path: Path) -> list[Any]:
    """The list of tools in a ``tools/list`` result, in the list itself, or in a JSON-RPC response holding one."""
    if isinstance(document, dict) and isinstance(document.get("result"), dict):
        document = document["result"]
    if isinstance(document, dict) and document.get("nextCursor"):
        raise ToolsFileError(
            f"{path} is one page of a longer list: it carries a nextCursor. Ask the server for every page "
            "and check the tools together."
        )
    tools = document.get("tools") if isinstance(document, dict) else document
    if not isinstance(tools, list):
        raise ToolsFileError(
            f'{path} should hold a tools/list answer: an object with a "tools" list, the list itself, or a '
            "JSON-RPC response with one."
        )
    return tools


def check_tools(tools: list[Any]) -> Report:
    """Every string the tools hand a model, against the prompt-injection catalogue."""
    findings = tuple(
        Finding(place=match.field, rule=match.pattern_id, rule_name=match.pattern_name, matched=match.matched_text)
        for match in scan_tool_text(tools, scan_text)
    )
    return Report(
        tools=sum(1 for tool in tools if isinstance(tool, dict)),
        strings=sum(1 for _ in tool_text_strings(tools)),
        findings=findings,
    )


def _json_document(raw: bytes, path: Path) -> Any:
    """Decode as UTF-8, or as UTF-16 behind its byte-order mark, which is what Windows PowerShell 5.1 writes
    for a redirect, then parse."""
    encoding = "utf-16" if raw.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)) else "utf-8-sig"
    try:
        text = raw.decode(encoding)
    except UnicodeDecodeError:
        raise ToolsFileError(f"{path} isn't UTF-8 text. Save the JSON as UTF-8.") from None
    try:
        return json.loads(text)
    except ValueError as exc:
        raise ToolsFileError(
            f"{path} isn't JSON: {getattr(exc, 'msg', exc)} at line {getattr(exc, 'lineno', '?')}, "
            f"column {getattr(exc, 'colno', '?')}. Save the tools/list answer exactly as the server gave it."
        ) from None
