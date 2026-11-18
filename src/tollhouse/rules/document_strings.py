# Copied from the Sigrix platform's rule set. A change is made there and copied here, never in place.
"""What a reader is handed from a document a scan reads as text.

A scan is a regex catalogue run over text. Where the text is a document in a format with spellings of its
own, the raw text is how the file is written and not what its reader gets: a double-quoted YAML scalar writes
any character as an escape and joins a line that ends in a backslash onto the next, and ``yaml.safe_load``
decodes both. So a scan of such a document reads it twice: the raw text, and then each string a reader
decodes from it (:func:`yaml_strings`), each one alone. :func:`decoded_findings` says how one phrase both
readings find is reported once. PyYAML is imported only when a YAML document is read.
"""

from __future__ import annotations

import base64
import binascii
from collections.abc import Callable, Collection, Iterable
from functools import lru_cache
from typing import Any

_BINARY_TAG = "tag:yaml.org,2002:binary"


@lru_cache(maxsize=64)
def yaml_strings(text: str) -> tuple[str, ...]:
    """Every string a YAML reader is handed from ``text``, in the file's order: each scalar, decoded.

    Read with the parser ``yaml.safe_load`` uses and stopped short of building objects, so:

    - a key is read as a value is, and where a mapping writes one key twice both values are, though
      the loader keeps the last;
    - an alias is read once, at its anchor, however often the file repeats it, and a file that
      nests aliases to make a small text a vast one costs what its text costs;
    - every document in the file is read, though the loader refuses a second;
    - a scalar of any type is read as its text, and one tagged ``!!binary`` as the bytes it encodes
      too: the runner hands a model ``str()`` of whatever a backstory is, and for bytes that prints
      them.

    A file the parser cannot read ends the reading there, and so does one nested too deeply for it:
    the loader cannot read that file either, so no runner hands anything of it to a model, and its
    raw text is still scanned. The documents before the fault are kept.

    The answer is kept for the last few texts asked: the moderators' feed derives a verdict from each
    row on every read, and a form at its size cap takes a third of a second to parse.
    """
    import yaml

    strings: list[str] = []
    try:
        for root in yaml.compose_all(text, Loader=yaml.SafeLoader):
            # An alias points within its own document, and ``root`` keeps that document's nodes alive
            # while it is walked, so an ``id`` names one node for as long as it is in ``seen``.
            seen: set[int] = set()
            pending: list[Any] = [root]
            while pending:
                node = pending.pop()
                if node is None or id(node) in seen:
                    continue
                seen.add(id(node))
                if isinstance(node, yaml.ScalarNode):
                    strings.append(node.value)
                    if node.tag == _BINARY_TAG:
                        strings.append(_binary_text(node.value))
                elif isinstance(node, yaml.MappingNode):
                    # Last pushed is first read: each key, then all its value holds, then the next key.
                    for key, value in reversed(node.value):
                        pending.append(value)
                        pending.append(key)
                elif isinstance(node, yaml.SequenceNode):
                    pending.extend(reversed(node.value))
    except (yaml.YAMLError, RecursionError):
        pass
    return tuple(string for string in strings if string.strip())


def _binary_text(encoded: str) -> str:
    """The bytes a ``!!binary`` scalar encodes, as text; nothing for a scalar the loader would refuse."""
    try:
        return base64.decodebytes(encoded.encode("ascii")).decode("utf-8", "replace")
    except (binascii.Error, ValueError):
        return ""


def decoded_findings(
    scan_text: Callable[[str, str], Iterable[Any]],
    field: str,
    strings: Iterable[str],
    reported: Collection[str],
) -> list[Any]:
    """What the strings a reader decodes from a document add to its raw text's findings.

    ``reported`` holds the catalog entries (``pattern_id``) the raw text was already reported for. A
    file is reported once for an entry, as a file read whole always was: for the raw text's match
    when it has one, which is the spelling the seller finds by searching the file, and otherwise for
    the first decoded string's. Each string is scanned alone, since a phrase is words with spaces
    between them and two strings joined would make one out of the end of the first and the start of
    the next.
    """
    found: list[Any] = []
    held = set(reported)
    for string in strings:
        for match in scan_text(field, string):
            if match.pattern_id not in held:
                held.add(match.pattern_id)
                found.append(match)
    return found


__all__ = ["decoded_findings", "yaml_strings"]
