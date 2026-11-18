# Versioning

Semantic versioning, `MAJOR.MINOR.PATCH`, released from a `vX.Y.Z` tag.

Before 1.0, a MINOR release may change or remove what an earlier one offered,
and the changelog says so when it does. From 1.0:

- **PATCH**: a fix that changes no command, option, rule id or field of the
  JSON answer, and makes no clean input fail.
- **MINOR**: a new command, option or rule. A new rule can fail a check that
  passed before, so it is never a PATCH, and the changelog names it.
- **MAJOR**: a removed or renamed command, option, rule id or field of the
  JSON answer.

## Releasing

A release is a tag. `release.yml` builds the distribution and publishes it on
any `v*` tag pushed to this repository; nothing is uploaded by hand and no API
token exists to leak.

That works because PyPI is configured to trust this repository rather than a
credential, which takes two things that must both be in place before the first
tag, and neither fails loudly if it is missing, so check them rather than
assume:

1. On PyPI, a **trusted publisher** for `sigrix-io/tollhouse`, workflow
   `release.yml`, environment `pypi`. Before the first release it is a
   *pending* publisher, which does not reserve the name: the name is ours only
   once a release has been published to it.
2. In this repository's settings, an **environment named `pypi`**. The
   publisher's claim names it, so a workflow running outside it is refused.

The version lives in two places, `pyproject.toml` and `src/tollhouse/__init__.py`;
move both, and `tests/test_package_metadata.py` fails while they differ. Then:

```sh
git tag v0.0.1 && git push origin v0.0.1
```

The release workflow refuses a tag that differs from the version in
`pyproject.toml`. Allow about ten minutes after the upload before expecting
`uvx tollhouse` to resolve the new version: that is the index CDN's cache, not
a failed publish. The release's `verify` job waits it out, installs the new
version from PyPI by name, and fails the run if that never arrives, reports
another version, lacks `py.typed`, or its `tollhouse` command does not answer
with that version and find a catalogue phrase in a file carrying one. The build
job runs the same checks against the wheel before the upload, because a version
on PyPI can never be reused.
