# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the versioning is
described in `VERSIONING.md`.

## [Unreleased]

### Added

- The credential catalogue (`rules/credential_scan.py`) and the data-claims
  rules (`rules/data_claims.py`), copied from the Sigrix platform's rule set
  with the data-claims case table, and tested here on it. The platform could
  not offer the credential catalogue for copying before: it sat beside the
  platform's event recording.
- `CODE_OF_CONDUCT.md`, issue forms and a pull request template, the set the
  other open repositories carry. Blank issues are off: a report is a wrong
  finding or a change, and the links beside the forms send a security report
  to security@sigrix.io, a finding in someone else's server to its author, and
  a conduct concern to conduct@sigrix.io. Nothing in the package changes.
- `py.typed`: the package's annotations, the copied rules' included, are
  checked with mypy in strict mode, so a type checker reading code that
  imports Tollhouse can trust them.

### Changed

- Each finding has a level: `block`, a finding to fix, or `warn`, words a
  person should weigh because they can be innocent. A check exits 1 on a
  finding to fix, and on a warning too only with the new `--strict`. In
  `--json` each finding gains `level` and `related` (the other places a
  finding drawn from several strings rests on), so a script reading it sees
  a new shape.
- The release checks the wheel before the upload, then installs the published
  version from PyPI by name and checks that it reports that version, carries
  `py.typed`, and that its `tollhouse` command passes a clean file and finds a
  catalogue phrase.
- Every GitHub Action the workflows run is pinned to a commit, with its release
  named beside it, and Dependabot keeps those pins and the dev tools current.
  CI ends in one `ci-passed` job for the branch ruleset to require. The release
  refuses to build in a fork and is never cancelled mid-upload. ruff is pinned
  to the version the Sigrix platform formats the rules with. Nothing in the
  package changes.

## [0.0.1] — 2026-11-18

First release: the name, and the first check.

### Added

- `tollhouse check <tools.json>`: reads an MCP server's `tools/list` answer,
  every string a model is handed, each alone and named by its place, and
  reports the phrases of the prompt-injection catalogue in it. Exits 1 on a
  finding and 2 when the file cannot be read; `--json` prints the answer for
  a script.
- `tollhouse --version`.
