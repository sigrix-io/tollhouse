"""``tollhouse``: the command line."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from tollhouse import __version__
from tollhouse.check import Report, ToolsFileError, check_tools, read_tools

#: The last line of a check read by a person: where a server can be sold once it is clean.
SELL_LINE = (
    "Selling an MCP server? Sigrix runs this check at upload, and a moderator reviews the server before anyone "
    "can buy it: https://sigrix.io/sell"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tollhouse",
        description="Check an MCP server's tools before you install or publish it.",
    )
    parser.add_argument("--version", action="version", version=f"tollhouse {__version__}")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser(
        "check",
        help="check a server's tools/list answer",
        description=(
            "Read a server's tools/list answer and report the prompt-injection phrases in any string a model is "
            "handed: each tool's name, title, description and annotations, and every string in its input schema. "
            "Reads the file only. Exits 1 on a finding and 2 when the file cannot be read."
        ),
    )
    check.add_argument("tools", type=Path, help="a file holding the server's tools/list answer")
    check.add_argument("--json", action="store_true", help="print the answer as JSON")
    return parser


def render(report: Report, *, source: str) -> str:
    """The answer for a person: what was read, each finding by its place, and what to do."""
    lines = [
        f"tollhouse {__version__}: read {_count(report.strings, 'string')} from {_count(report.tools, 'tool')} in {source}."
    ]
    if report.findings:
        for finding in report.findings:
            lines.append(f"  {finding.place}")
            lines.append(f"    {finding.rule_name} ({finding.rule}): {finding.matched!r}")
        lines.append(
            f"{_count(len(report.findings), 'finding')}. A model reads each as an instruction: take it out of the "
            "server's tools."
        )
    else:
        lines.append(
            "No finding: none of the prompt-injection catalogue's phrases is in them. This checks a list of "
            "phrases, not the server itself."
        )
    lines.extend(["", SELL_LINE])
    return "\n".join(lines) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    _escape_what_the_output_cannot_encode()
    args = build_parser().parse_args(argv)
    try:
        report = check_tools(read_tools(args.tools))
    except ToolsFileError as exc:
        sys.stderr.write(f"tollhouse: {exc}\n")
        return 2
    if args.json:
        sys.stdout.write(json.dumps(report.as_dict(), indent=2) + "\n")
    else:
        sys.stdout.write(render(report, source=str(args.tools)))
    return 1 if report.findings else 0


def _count(number: int, noun: str) -> str:
    return f"{number} {noun}" + ("" if number == 1 else "s")


def _escape_what_the_output_cannot_encode() -> None:
    """A finding quotes the text it matched, and a pipe on Windows is not UTF-8: escape, never fail."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(errors="backslashreplace")
