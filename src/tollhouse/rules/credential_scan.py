# Copied from the Sigrix platform's rule set. A change is made there and copied here, never in place.
"""The credential catalogue: provider keys and tokens, as shapes that are a key or nothing.

Every pattern matches a structurally distinctive provider credential, which is what keeps the catalogue usable
without a confidence score. The tempting second tier (``api_key = "..."``, ``password: ...``) is left out on purpose:
it fires on documentation, on placeholder blocks and on prose that merely discusses credentials, and a check that
cries wolf is worse than none. A match that spells documentation (AWS's own sample key, ``your-key``) is not one.

Nothing here carries a secret onward: :func:`scan_text` reports a redacted locator, the first and last few
characters, and never the key.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True)
class SecretPattern:
    """One catalog entry."""

    id: str
    name: str
    pattern: re.Pattern[str]


@dataclass(frozen=True)
class SecretMatch:
    """A credential shape that fired against a specific scanned field."""

    field: str
    pattern_id: str
    pattern_name: str
    #: First and last few characters only. Enough for a moderator to find the
    #: string in the field; never enough to use it.
    redacted: str


def _compile(source: str) -> re.Pattern[str]:
    # Not IGNORECASE: every shape below is case-significant, and folding case
    # turns `AKIA` into a match for prose containing "akia".
    return re.compile(source)


#: A Telegram bot token: the bot's id, a colon and a 35-character secret. The Bot
#: API takes the token in every method's path (`https://api.telegram.org/bot<token>/…`),
#: so the id may follow `/bot`, after which `\b` finds no boundary; anywhere else
#: it must start a run of the secret's alphabet, so digits ending a word or a dated
#: name (`nightly-20261115:`) are not an id. Eight to eleven digits: ids run to ten
#: today and the eleventh is headroom. Twelve would take an AWS account id, which
#: an SQS or SNS ARN puts before a colon and a name that can be 35 characters of
#: this alphabet. The lookahead, not `\b`, closes the secret: `\b` refuses one that
#: ends in `-` and takes the first 35 characters of a longer run.
#: `telegram_bot_api._TOKEN_SHAPE` is looser on purpose: it vets a token an admin
#: configured and redacts Telegram's error text, where an over-match costs nothing.
TELEGRAM_BOT_TOKEN_RE: Final[re.Pattern[str]] = _compile(
    r"(?:(?<=/bot)|(?<![A-Za-z0-9_-]))[0-9]{8,11}:[A-Za-z0-9_-]{35}(?![A-Za-z0-9_-])"
)


#: Structurally distinctive provider credentials. Each is a shape that is a key
#: or is nothing — which is what keeps this catalog usable without a confidence
#: score. Stripe's `sk_test_` is absent on purpose: test keys are designed to be
#: shareable, so flagging one is a false positive by definition. The runnable-artifact
#: scrub (`artifact_scrub`) takes every shape here out of the files a product ships,
#: so an entry is a shape that is a key in a shipped workflow as well as in a listing.
SECRET_PATTERNS: Final[tuple[SecretPattern, ...]] = (
    SecretPattern(
        id="aws_access_key_id",
        name="AWS access key id",
        pattern=_compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    SecretPattern(
        id="openai_api_key",
        name="OpenAI API key",
        # The negative lookahead is load-bearing: `sk-ant-` is a strict prefix
        # of `sk-`, so without it every Anthropic key is reported twice and
        # named as OpenAI's. A moderator acting on the wrong provider is worse
        # than a moderator acting on a count.
        pattern=_compile(r"\bsk-(?!ant-)(?:proj-)?[A-Za-z0-9_-]{20,}"),
    ),
    SecretPattern(
        id="anthropic_api_key",
        name="Anthropic API key",
        pattern=_compile(r"\bsk-ant-[A-Za-z0-9_-]{20,}"),
    ),
    SecretPattern(
        id="github_token",
        name="GitHub token",
        pattern=_compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}"),
    ),
    SecretPattern(
        id="google_api_key",
        name="Google API key",
        # Closed by the lookahead, as a Telegram token is: the alphabet has `-`,
        # so `\b` missed a key ending in one and took 35 characters of a longer run.
        pattern=_compile(r"\bAIza[0-9A-Za-z_-]{35}(?![A-Za-z0-9_-])"),
    ),
    SecretPattern(
        id="slack_token",
        name="Slack token",
        pattern=_compile(r"\bxox[baprs]-[0-9A-Za-z-]{10,}"),
    ),
    SecretPattern(
        id="stripe_live_secret_key",
        name="Stripe live secret key",
        pattern=_compile(r"\b[sr]k_live_[0-9A-Za-z]{24,}"),
    ),
    SecretPattern(
        id="sendgrid_api_key",
        name="SendGrid API key",
        # Closed by the lookahead, for the Google key's reason.
        pattern=_compile(r"\bSG\.[A-Za-z0-9_-]{22}\.[A-Za-z0-9_-]{43}(?![A-Za-z0-9_-])"),
    ),
    SecretPattern(
        id="telegram_bot_token",
        name="Telegram bot token",
        pattern=TELEGRAM_BOT_TOKEN_RE,
    ),
    SecretPattern(
        id="azure_account_key",
        name="Azure account key",
        # A Storage or Cosmos DB account key, 64 bytes of base64, after the label a
        # connection string gives it. The label is what makes it a key: 88 characters
        # of base64 alone is also a SHA-512 digest. The match is the key alone, so a
        # scrubbed connection string keeps its shape.
        pattern=_compile(r"(?<=AccountKey=)[A-Za-z0-9+/]{86}=="),
    ),
    SecretPattern(
        id="azure_shared_access_key",
        name="Azure shared access key",
        # A Service Bus, Event Hubs or IoT Hub key, 32 bytes or more of base64 after its
        # connection string's label, taken whole; the policy's name,
        # `SharedAccessKeyName=`, is not read.
        pattern=_compile(r"(?<=SharedAccessKey=)[A-Za-z0-9+/]{42,}={0,2}"),
    ),
    SecretPattern(
        id="azure_sas_token",
        name="Azure SAS token",
        # A shared access signature, from the version Azure stamps on one to the end of
        # the signature that makes it a credential. The version is what makes a `sig=`
        # Azure's, and the SDK writes other parameters before it (`?se=…&sp=…&sv=…`),
        # which the match leaves, as it leaves the address.
        pattern=_compile(r"\bsv=[0-9]{4}-[0-9]{2}-[0-9]{2}(?:&[A-Za-z]{2,6}=[^&#\s\"'<>]*)*?&sig=[A-Za-z0-9%+/=]{40,}"),
    ),
    SecretPattern(
        id="entra_client_secret",
        name="Microsoft Entra client secret",
        # An app registration's client secret: three characters, a digit and `Q~`,
        # then 31 to 34 more of its alphabet, which has `~`, `.` and `-` in it.
        pattern=_compile(r"(?<![A-Za-z0-9_~.-])[A-Za-z0-9_~.]{3}[0-9]Q~[A-Za-z0-9_~.-]{31,34}(?![A-Za-z0-9_~.-])"),
    ),
    SecretPattern(
        id="private_key_block",
        name="Private key block",
        pattern=_compile(r"-----BEGIN (?:[A-Z ]+ )?PRIVATE KEY-----"),
    ),
    SecretPattern(
        id="json_web_token",
        name="JSON Web Token",
        pattern=_compile(r"\beyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ),
)

#: Substrings that mark a match as documentation rather than a credential.
#: Checked case-insensitively against the matched text itself, so a real key is
#: only suppressed if it literally spells one of these — which a random key does
#: not. ``AKIAIOSFODNN7EXAMPLE`` is AWS's own documented sample and appears in
#: a great deal of legitimate setup prose, which is exactly the case that makes
#: this list worth having.
_PLACEHOLDER_HINTS: Final[tuple[str, ...]] = (
    "example",
    "placeholder",
    "your-key",
    "yourkey",
    "your_key",
    "changeme",
    "change-me",
    "replace-me",
    "replaceme",
    "redacted",
    "xxxxxxxx",
    "notarealkey",
    # The account key Microsoft publishes for the Azurite storage emulator's
    # `devstoreaccount1`, which setup prose for local development quotes as it
    # quotes AWS's sample.
    "eby8vdm02xnocqflquwjpllm",
)


def looks_like_a_placeholder(text: str) -> bool:
    """Whether a match spells documentation. The artifact scrub asks it of the shapes it takes from this catalog."""
    lowered = text.lower()
    return any(hint in lowered for hint in _PLACEHOLDER_HINTS)


def redact(text: str) -> str:
    """A locator, not a value: the first and last few characters only."""

    stripped = text.strip()
    if len(stripped) <= 12:
        # Too short to reveal a head and a tail without revealing most of it.
        # The private-key banner is the case that lands here, and it carries no
        # secret material anyway.
        return stripped[:4] + "…"
    return f"{stripped[:4]}…{stripped[-4:]}"


def scan_text(field: str, text: str) -> list[SecretMatch]:
    """Return every credential shape in ``text``, tagged with ``field``.

    One match per pattern, not per occurrence: a moderator opening the field
    sees all of them at once, and a count of seventeen would only obscure which
    *kinds* are present.
    """

    matches: list[SecretMatch] = []
    for pattern in SECRET_PATTERNS:
        for found in pattern.pattern.finditer(text):
            snippet = found.group(0)
            if looks_like_a_placeholder(snippet):
                continue
            matches.append(
                SecretMatch(
                    field=field,
                    pattern_id=pattern.id,
                    pattern_name=pattern.name,
                    redacted=redact(snippet),
                )
            )
            break
    return matches


__all__ = [
    "SECRET_PATTERNS",
    "TELEGRAM_BOT_TOKEN_RE",
    "SecretMatch",
    "SecretPattern",
    "looks_like_a_placeholder",
    "redact",
    "scan_text",
]
