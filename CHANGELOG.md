# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the versioning is
described in `VERSIONING.md`.

## [Unreleased]

### Added

- `CODE_OF_CONDUCT.md`, issue forms and a pull request template, the set the
  other open repositories carry. Blank issues are off: a report is a wrong
  finding or a change, and the links beside the forms send a security report
  to security@sigrix.io, a finding in someone else's server to its author, and
  a conduct concern to conduct@sigrix.io. Nothing in the package changes.

### Changed

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
