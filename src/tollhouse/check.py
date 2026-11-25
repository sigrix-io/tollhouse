"""Reading an MCP server's ``tools/list`` answer, and checking every string in it."""

from __future__ import annotations

import codecs
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tollhouse.rules.credential_scan import scan_text as scan_credentials
from tollhouse.rules.injection_scan import scan_text
from tollhouse.rules.tool_text import scan_tool_text, tool_text_strings

#: A ``tools/list`` answer runs to a few hundred kilobytes at the most. Past this,
#: the file is something else, and it is not read into memory.
MAX_FILE_BYTES = 8 * 1024 * 1024


class ToolsFileError(ValueError):
    """The file is not a ``tools/list`` answer this can read. The message says what to do."""


#: A finding to fix: text no server should hand a model. A check exits 1 on one.
BLOCK = "block"
#: Words a person should weigh: they can be innocent. A check exits 0 on them unless asked to be strict.
WARN = "warn"


@dataclass(frozen=True)
class Finding:
    """One rule's match in the strings a model is handed."""

    place: str  # where the string sits, e.g. tools[search].inputSchema.properties[query].description
    rule: str  # the rule's stable id
    rule_name: str
    matched: str  # at most 80 characters of the text that matched, or a locator that never repeats a key
    level: str = BLOCK  # BLOCK or WARN
    related: tuple[str, ...] = ()  # the other places a finding drawn from several strings rests on

    def as_dict(self) -> dict[str, Any]:
        return {**asdict(self), "related": list(self.related)}


@dataclass(frozen=True)
class Report:
    """What one check read and found."""

    tools: int
    strings: int
    findings: tuple[Finding, ...]

    @property
    def blocking(self) -> tuple[Finding, ...]:
        return tuple(finding for finding in self.findings if finding.level == BLOCK)

    @property
    def warnings(self) -> tuple[Finding, ...]:
        return tuple(finding for finding in self.findings if finding.level == WARN)

    def exit_code(self, *, strict: bool = False) -> int:
        """1 on a blocking finding, or on any finding when ``strict``; else 0."""
        return 1 if self.blocking or (strict and self.findings) else 0

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
    """Every string the tools hand a model, against the prompt-injection catalogue and the credential catalogue.

    A credential is reported by a locator, its first and last few characters, never the key: the answer is printed,
    piped and kept in build logs, and a check that repeated what it found would put the key in a second place.
    """
    injection = [
        Finding(place=match.field, rule=match.pattern_id, rule_name=match.pattern_name, matched=match.matched_text)
        for match in scan_tool_text(tools, scan_text)
    ]
    credentials = [
        Finding(place=match.field, rule=match.pattern_id, rule_name=match.pattern_name, matched=match.redacted)
        for match in scan_tool_text(tools, scan_credentials)
    ]
    findings = (*injection, *credentials)
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
