# Changelog

All notable changes to this project are recorded here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/); the versioning is
described in `VERSIONING.md`.

## [Unreleased]

## [0.0.1] — 2026-11-18

First release: the name, and the first check.

### Added

- `tollhouse check <tools.json>`: reads an MCP server's `tools/list` answer,
  every string a model is handed, each alone and named by its place, and
  reports the phrases of the prompt-injection catalogue in it. Exits 1 on a
  finding and 2 when the file cannot be read; `--json` prints the answer for
  a script.
- `tollhouse --version`.
