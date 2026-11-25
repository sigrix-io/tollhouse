# Copied from the Sigrix platform's rule set. A change is made there and copied here, never in place.
"""What a server's tools say about the data they hand out, read as data.

The injection catalogue reads text that tries to take over a model, and the credential scan text that holds a key.
Neither reads what a tool says about its own data, so a server whose tools hand out "leads with phone numbers
populated, for outreach", say their listings are "scraped from portals", and whose summary calls it all "open
datasets", passes both clean. This catalogue reads for those words, as signals:

- ``contact_data``: phone, mobile or telephone numbers, email or home addresses, contact details, personal data;
- ``scraped_source``: scraped, scraping, crawled, harvested;
- ``outreach_use``: outreach, cold calls or emails, lead generation, prospecting, mailing lists, telemarketing;
- ``open_data_claim``: open data or datasets, public or publicly available data, official data or records.

A signal alone is ordinary: an SMS tool takes a phone number, a CRM reads its user's leads, a scraper reads a page,
an open-data portal's client says open data. A finding is a combination, which a person then weighs:

- ``contact_data_for_outreach``: one tool hands out personal contact data and says it is for outreach;
- ``scraped_contact_data``: a tool hands out personal contact data, and the server says its data is scraped;
- ``open_data_contradicted``: the server calls its data open or official, and a tool says it is scraped.

Every finding is a warning, never a failure: the words can be innocent, and a regular expression cannot read
"never" before them. Each names the tool, the places (as ``tool_text`` names them) and the signals.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from typing import Any, Final

from tollhouse.rules.tool_text import tool_text_strings

#: The place a server's own summary is named by, beside the tools' places.
SUMMARY_PLACE: Final = "summary"


@dataclass(frozen=True)
class DataSignal:
    """One catalogue entry: a stable id, a name a person reads, and the words it matches."""

    id: str
    name: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class DataMatch:
    """A signal found at one place: the place, the signal, and the words that matched (at most 80 characters)."""

    field: str
    signal_id: str
    signal_name: str
    matched_text: str


@dataclass(frozen=True)
class DataFinding:
    """A combination of signals a person weighs: the rule, the tool it is about, and every match behind it."""

    rule: str
    tool: str
    matches: tuple[DataMatch, ...]

    @property
    def places(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(match.field for match in self.matches))


def _compile(source: str) -> re.Pattern[str]:
    return re.compile(source, re.IGNORECASE)


CONTACT_DATA: Final = "contact_data"
SCRAPED_SOURCE: Final = "scraped_source"
OUTREACH_USE: Final = "outreach_use"
OPEN_DATA_CLAIM: Final = "open_data_claim"

DATA_SIGNALS: Final[tuple[DataSignal, ...]] = (
    DataSignal(
        id=CONTACT_DATA,
        name="personal contact data",
        pattern=_compile(
            r"\b(?:(?:tele)?phone|mobile|cell(?:ular)?)[\s-]*(?:numbers?|nos?\b\.?)"
            r"|\be-?mail[\s-]+addresse?s?\b"
            r"|\b(?:home|postal|street|residential)[\s-]+addresse?s?\b"
            r"|\bcontact[\s-]+(?:details|info(?:rmation)?|data)\b"
            r"|\bpersonal[\s-]+(?:data|information|details)\b"
        ),
    ),
    DataSignal(
        id=SCRAPED_SOURCE,
        name="a scraped source",
        pattern=_compile(r"\bscrap(?:e|ed|es|ing|ers?)\b|\bcrawl(?:s|ed|ing|ers?)?\b|\bharvest(?:s|ed|ing)?\b"),
    ),
    DataSignal(
        id=OUTREACH_USE,
        name="outreach or marketing to people",
        pattern=_compile(
            r"\boutreach\b"
            r"|\bcold[\s-]+(?:call(?:s|ing)?|e-?mails?|e-?mailing|outreach|messages?|messaging|leads?)\b"
            r"|\blead[\s-]+gen(?:eration)?\b"
            r"|\bprospect(?:s|ing)?\b"
            r"|\bmailing[\s-]+lists?\b"
            r"|\btele-?marketing\b"
        ),
    ),
    DataSignal(
        id=OPEN_DATA_CLAIM,
        name="a claim of open or official data",
        pattern=_compile(
            r"\bopen[\s-]+(?:government[\s-]+)?data(?:[\s-]?sets?)?\b"
            r"|\bpublic(?:ly)?[\s-]+(?:available[\s-]+)?data(?:[\s-]?sets?)?\b"
            r"|\bofficial[\s-]+(?:data(?:[\s-]?sets?)?|sources?|records?|statistics)\b"
        ),
    ),
)

#: Each finding's rule, and the words a person reads for it.
FINDING_RULES: Final[dict[str, str]] = {
    "contact_data_for_outreach": "Personal contact data offered for outreach",
    "scraped_contact_data": "Personal contact data from a scraped source",
    "open_data_contradicted": "An open-data claim its own tools contradict",
}


def scan_text(field: str, text: str) -> list[DataMatch]:
    """Every signal ``text`` holds, each once, tagged with ``field``, in the catalogue's order."""
    matches: list[DataMatch] = []
    for signal in DATA_SIGNALS:
        match = signal.pattern.search(text)
        if match is None:
            continue
        snippet = " ".join(match.group(0).split())
        matches.append(
            DataMatch(
                field=field,
                signal_id=signal.id,
                signal_name=signal.name,
                matched_text=snippet if len(snippet) <= 80 else snippet[:77] + "...",
            )
        )
    return matches


def _tool_of(path: str) -> str:
    """The tool a place belongs to, as ``tool_text`` names it: ``tools[name]`` or ``tools[#2]``."""
    head, bracket, _ = path.partition("]")
    return head + bracket if bracket else path


def _strings(tools: Iterable[Any], summary: str) -> Iterator[tuple[str, str]]:
    if summary.strip():
        yield SUMMARY_PLACE, summary
    yield from tool_text_strings(tools)


def data_findings(tools: Iterable[Any], *, summary: str = "") -> list[DataFinding]:
    """The combinations a person weighs in what a server's tools, and its summary, say about their data.

    ``tools`` is a ``tools/list`` answer's tools; ``summary`` the server's own one-line summary, read beside them.
    The findings come back in the rules' order, each tool in the order the tools are declared.
    """
    matches = [match for path, text in _strings(tools, summary) for match in scan_text(path, text)]
    by_tool: dict[str, list[DataMatch]] = {}
    for match in matches:
        if match.field != SUMMARY_PLACE:
            by_tool.setdefault(_tool_of(match.field), []).append(match)

    def having(found: Iterable[DataMatch], signal_id: str) -> list[DataMatch]:
        return [match for match in found if match.signal_id == signal_id]

    scraped = having(matches, SCRAPED_SOURCE)
    findings: list[DataFinding] = []
    for tool, found in by_tool.items():
        contact, outreach = having(found, CONTACT_DATA), having(found, OUTREACH_USE)
        if contact and outreach:
            findings.append(DataFinding("contact_data_for_outreach", tool, tuple(contact + outreach)))
    for tool, found in by_tool.items():
        contact = having(found, CONTACT_DATA)
        if contact and scraped:
            findings.append(DataFinding("scraped_contact_data", tool, tuple(contact + scraped)))
    claims = having(matches, OPEN_DATA_CLAIM)
    if claims and scraped:
        tool = _tool_of(scraped[0].field)
        findings.append(DataFinding("open_data_contradicted", tool, tuple(claims + scraped)))
    return findings


__all__ = [
    "CONTACT_DATA",
    "DATA_SIGNALS",
    "FINDING_RULES",
    "OPEN_DATA_CLAIM",
    "OUTREACH_USE",
    "SCRAPED_SOURCE",
    "SUMMARY_PLACE",
    "DataFinding",
    "DataMatch",
    "DataSignal",
    "data_findings",
    "scan_text",
]
