# Copied from the Sigrix platform's rule set. A change is made there and copied here, never in place.
"""Every string a declared MCP tool hands a model, each alone and named by where it sits.

A client hands the model each tool's ``tools/list`` entry: its name, title and description, its annotations,
and its ``inputSchema`` whole. So every string in the schema is text the model reads, not only the
descriptions: an ``enum`` value, a ``default``, an ``examples`` entry or a ``$defs`` title is read as surely
as a description is.

Each string is yielded alone, never the file as JSON text: a phrase broken over a JSON escape, or one made of
the end of one field and the start of the next, is not a phrase any model is handed.

A string is named by its path, so that a finding names the tool and the place, and a record of the finding
can carry the place without the text. A schema keyword is spelled as it is, and a name the tool's author
chose sits in brackets: ``tools[watch_models].inputSchema.properties[provider].description``. A name is
spelled only when it is an identifier, as MCP's own tool names are; any other is named by its position
(``tools[#2]``), so that a path never carries prose, and a tool named after the phrase a scan reports cannot
put that phrase into the record.
"""

from __future__ import annotations

import re
from collections.abc import Callable, Iterable, Iterator, Mapping
from typing import Any

#: The members of a tool, besides its annotations and schema, that a model is handed as text.
TOOL_TEXT_MEMBERS: tuple[str, ...] = ("name", "title", "description")

#: Schema keywords whose value maps names the seller chose to schemas: a key there is a name, not a keyword.
NAMED_SCHEMA_KEYWORDS: frozenset[str] = frozenset(
    {"properties", "patternProperties", "$defs", "definitions", "dependentSchemas"}
)

#: A name a path spells as it is: the characters MCP allows in a tool name, and no more than this many.
IDENTIFIER = re.compile(r"[A-Za-z0-9_.\-/]{1,64}")

#: A schema keyword a path spells as it is (``description``, ``$defs``, ``x-order``). A key of any other
#: shape where a keyword belongs is named by its position, as a name is.
KEYWORD = re.compile(r"[$A-Za-z0-9_\-]{1,64}")


def tool_text_strings(tools: Iterable[Any]) -> Iterator[tuple[str, str]]:
    """``(path, text)`` for every string a declared tool hands a model. A blank string is no text."""
    for position, tool in enumerate(tools, start=1):
        if not isinstance(tool, Mapping):
            continue
        prefix = f"tools[{_name(tool.get('name'), position)}]"
        for member in TOOL_TEXT_MEMBERS:
            yield from _strings(tool.get(member), f"{prefix}.{member}")
        yield from _strings(tool.get("annotations"), f"{prefix}.annotations")
        yield from _strings(tool.get("inputSchema"), f"{prefix}.inputSchema")


def scan_tool_text(tools: Iterable[Any], scan: Callable[[str, str], Iterable[Any]]) -> list[Any]:
    """One catalogue's ``scan_text`` over every string a declared tool hands a model, its matches in order.

    Two places holding one phrase are two findings, as two fields of a listing are.
    """
    return [match for path, text in tool_text_strings(tools) for match in scan(path, text)]


def _strings(value: Any, path: str, *, named: bool = False) -> Iterator[tuple[str, str]]:
    """Every string in ``value``, depth first in the order it is written. ``named``: its keys are names."""
    if isinstance(value, str):
        if value.strip():
            yield path, value
    elif isinstance(value, Mapping):
        for position, (key, child) in enumerate(value.items(), start=1):
            if named:
                yield from _strings(child, f"{path}[{_name(key, position)}]")
            else:
                keyword = key if isinstance(key, str) and KEYWORD.fullmatch(key) else f"#{position}"
                yield from _strings(child, f"{path}.{keyword}", named=keyword in NAMED_SCHEMA_KEYWORDS)
    elif isinstance(value, list | tuple):
        for position, child in enumerate(value):
            yield from _strings(child, f"{path}[{position}]")


def _name(value: Any, position: int) -> str:
    """A name the seller chose as a path spells it: itself when it is an identifier, else its position."""
    return value if isinstance(value, str) and IDENTIFIER.fullmatch(value) else f"#{position}"


__all__ = [
    "IDENTIFIER",
    "KEYWORD",
    "NAMED_SCHEMA_KEYWORDS",
    "TOOL_TEXT_MEMBERS",
    "scan_tool_text",
    "tool_text_strings",
]
