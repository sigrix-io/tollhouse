# Contributing

Thanks for looking. Tollhouse is at its first release, which is one command,
`tollhouse check`, over one kind of file, an MCP server's `tools/list` answer.

## What fits now

- A finding it gets wrong. Say what the string was and what it reported, or
  what it missed. Never paste a real key, even a revoked one: describe its
  shape instead.
- A clearer sentence. Say what was found and where; never guess at an intent
  the text does not show.
- A `tools/list` file from a real client that it cannot read.

## What does not

- A rule that judges intent rather than text. A rule here is a pattern a
  reader can review in code; a model or a remote service is not one.
- Anything that reaches the network, starts a server or writes a file. The
  check reads the file it is given and nothing else.
- A dependency in the core. `uvx tollhouse check` installs one package.

## Rules

The rules in `src/tollhouse/rules/` are copied from the Sigrix platform, which
runs the same checks when a seller uploads an MCP server, so the two cannot
disagree. Propose a change to one as an issue or a pull request here, with a
string it should match and one it should leave alone; it is made in the
platform's rule set and copied back.

## Working on it

```sh
python -m venv .venv && . .venv/bin/activate
pip install -e ".[dev]"
ruff check . && ruff format --check . && pytest
```

## Pull requests

- One change per pull request, with a test that fails without it.
- `CHANGELOG.md` gets a line under *Unreleased*.
- A new rule fails checks that passed before. Say so in the changelog.
