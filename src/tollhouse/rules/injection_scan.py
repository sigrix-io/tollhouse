# Copied from the Sigrix platform's rule set. A change is made there and copied here, never in place.
"""The prompt-injection catalogue: phrases that try to take over a model, as regular expressions.

Each pattern catches a phrase that turns up in copy-pasted jailbreak templates, system-instruction overrides
and tool-coercion strings. The intent is accident prevention, not adversarial defence: a determined author
will route around any regex, and the catalogue catches the obvious patterns.

Adding a pattern: give it a stable ``id``, the regex (matched case-insensitively) and a human-readable name.
A finding reports both, so whoever wrote the text can revise it.

The catalogue is plain Python, with no pattern feed, because:

  - it is versioned with the code that reads it;
  - a pattern must be reviewable in code, never an opaque classifier;
  - a false positive costs a revised sentence, and a false negative hands a model an instruction to set
    aside its own; both are recoverable.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class InjectionPattern:
    """One catalog entry."""

    id: str
    name: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class InjectionMatch:
    """A pattern that fired against a specific scanned field."""

    field: str
    pattern_id: str
    pattern_name: str
    matched_text: str  # ≤80 chars; for surfacing in the seller error message


def _compile(source: str) -> re.Pattern[str]:
    return re.compile(source, re.IGNORECASE | re.DOTALL)


# Catalog of patterns. Keep it small and high-precision: each addition
# expands the surface for false positives. Patterns are intentionally
# loose-ish (one pattern can match many phrasings) but anchored on
# distinctive verbs / phrases so generic English does not trip them.
INJECTION_PATTERNS: Final[tuple[InjectionPattern, ...]] = (
    InjectionPattern(
        id="ignore_previous_instructions",
        name="Ignore previous instructions",
        pattern=_compile(
            r"ignore\s+(?:(?:all|the|any)\s+)*(?:previous|prior|above|earlier)\s+(?:instructions|prompts|rules)"
        ),
    ),
    InjectionPattern(
        id="disregard_previous_instructions",
        name="Disregard previous instructions",
        pattern=_compile(
            r"disregard\s+(?:(?:all|the|any)\s+)*(?:previous|prior|above|earlier)\s+(?:instructions|prompts|rules)"
        ),
    ),
    InjectionPattern(
        id="forget_previous_instructions",
        name="Forget previous instructions",
        pattern=_compile(
            r"forget\s+(?:(?:all|the|any)\s+)*(?:previous|prior|above|earlier)\s+(?:instructions|prompts|rules)"
        ),
    ),
    InjectionPattern(
        id="system_prompt_override",
        name="System prompt override",
        pattern=_compile(r"(?:new|updated|revised)\s+system\s+(?:prompt|instructions?|message)"),
    ),
    InjectionPattern(
        id="system_role_injection",
        name="Inline system-role tag",
        pattern=_compile(r"<\s*\|?\s*(?:system|assistant)\s*\|?\s*>"),
    ),
    InjectionPattern(
        id="developer_mode",
        name="Developer / DAN mode jailbreak",
        pattern=_compile(r"(?:developer|dan|jailbreak)\s+mode\s+(?:enabled|on|activated)"),
    ),
    InjectionPattern(
        id="reveal_system_prompt",
        name="Reveal system prompt",
        pattern=_compile(
            r"(?:reveal|print|show|repeat|output)\s+(?:your|the)\s+(?:system|hidden|secret)\s+(?:prompt|instructions?)"
        ),
    ),
    InjectionPattern(
        id="exfiltrate_env",
        name="Exfiltrate environment / API key",
        pattern=_compile(
            r"(?:print|reveal|leak|exfiltrate|send|email|post)\s+(?:the\s+)?(?:env(?:ironment)?\s+(?:vars?|variables?)|api[\s_-]?key|secret[s]?)"
        ),
    ),
)


def scan_text(field: str, text: str) -> list[InjectionMatch]:
    """Return every pattern that matches ``text``, tagged with ``field``."""
    matches: list[InjectionMatch] = []
    for pattern in INJECTION_PATTERNS:
        match = pattern.pattern.search(text)
        if match is None:
            continue
        snippet = match.group(0).strip()
        if len(snippet) > 80:
            snippet = snippet[:77] + "..."
        matches.append(
            InjectionMatch(
                field=field,
                pattern_id=pattern.id,
                pattern_name=pattern.name,
                matched_text=snippet,
            )
        )
    return matches


def scan_yaml_text_fields(*, agents_yaml: str, tasks_yaml: str) -> list[InjectionMatch]:
    """Scan the seller-controlled prose in both YAML files: each file's text, then what a reader decodes.

    The raw YAML text is scanned because:

      - A comment is text a person or a model handed the file reads, and a
        parser drops it.
      - The bundle parser already validates structure separately; this
        scan is purely about content.
      - Scanning raw text means we cover backstory, role, goal, task
        description, and expected_output without enumerating fields.

    It is not enough alone: a double-quoted scalar spells a character
    as an escape and joins a line ending in a backslash onto the next, and the
    runner's ``yaml.safe_load`` hands a model the decoded text. So each string a
    YAML reader decodes from the file is scanned too, alone, and reported only
    for a catalog entry the file's text was not (``document_strings``).
    """
    from tollhouse.rules.document_strings import decoded_findings, yaml_strings

    matches: list[InjectionMatch] = []
    for field, text in (("agents.yaml", agents_yaml), ("tasks.yaml", tasks_yaml)):
        as_text = scan_text(field, text)
        reported = {match.pattern_id for match in as_text}
        matches += as_text + decoded_findings(scan_text, field, yaml_strings(text), reported)
    return matches


__all__ = [
    "INJECTION_PATTERNS",
    "InjectionMatch",
    "InjectionPattern",
    "scan_text",
    "scan_yaml_text_fields",
]
