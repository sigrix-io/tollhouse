# Tollhouse

Check an MCP server's tools before you install or publish it.

> **Early days.** This is release 0.0.1. It reads an MCP server's `tools/list` answer and reports the prompt-injection phrases in it. Credentials, hidden characters, tool-poisoning patterns and checking a running server come next.

## Why

An MCP client hands the model every tool's name, title and description, and its input schema whole. A tool can carry instructions aimed at your AI rather than at you, and a person reading the tool list skims straight past them. Tollhouse reads what the model would read, one string at a time, and says where each finding is.

## Check a server's tools

Save the server's `tools/list` answer to a file, for example with the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) in its command-line mode: run it with `--cli <your server command> --method tools/list` and redirect what it prints to `tools.json`.

Then:

```sh
uvx tollhouse check tools.json
```

`pipx run tollhouse check tools.json` works as well. Each finding is printed with its place, such as `tools[search].inputSchema.properties[query].description`, the rule it matched and the text that matched it. It exits 1 when there is a finding and 2 when the file cannot be read, and `tollhouse check --json` prints the same answer for a script. It reads the file you name: no network call, and nothing written.

The file can be the `tools/list` result (`{"tools": [...]}`), the list of tools itself, or a whole JSON-RPC response.

## What 0.0.1 checks

| | |
| --- | --- |
| **What it reads** | Every string a model is handed: each tool's name, title and description, its annotations, and every string in its input schema, including descriptions, titles, allowed values, defaults and examples. |
| **What it looks for** | The prompt-injection catalogue: "ignore previous instructions" and its kin, a new system prompt, a role tag written inline, developer mode, asking for the system prompt, and sending an environment variable or a key somewhere. |

Each string is read alone, the way the model reads it: two fields are never joined into one phrase, and the file's JSON escapes are decoded first, so a phrase broken over a line break inside one description is still found.

## What it does not catch

It catches accidents and obvious abuse, not a determined attacker: a fixed list of phrases can be reworded around. A clean answer means none of these phrases is in the tools, not that the server is safe. It does not start the server, read its code, or watch what it does when a tool is called.

## What comes next

- credentials, and hidden characters such as invisible Unicode and direction overrides, in the same strings;
- tool-poisoning patterns: asking the model to read a secret file, to keep an action from the user, or to change how another tool behaves;
- a skill's `SKILL.md`, a Python wheel's contents and an MCP server's launch command;
- `--run`: start a server on your own machine, read its own `tools/list`, and keep a lock file so that a later change to its tools shows;
- a GitHub Action that fails a pull request on a finding.

## Where it fits

Tollhouse is the check the [Sigrix](https://sigrix.io) marketplace runs when a seller uploads an MCP server, published so that anyone can run it first, on their own machine. A server sold there is checked at upload and then reviewed by a moderator before anyone can buy it: see [sigrix.io/sell](https://sigrix.io/sell). The other open-source projects are on [sigrix.io/open-source](https://sigrix.io/open-source).

## Development

```sh
pip install -e ".[dev]"
ruff check . && ruff format --check . && pytest
```

The rules in `src/tollhouse/rules/` are copied from the Sigrix platform's rule set, which runs the same checks at upload, so the two cannot disagree. A change to a rule is proposed here and made there.

## Licence

Apache-2.0. The Sigrix name and logo are not covered by the licence; see `NOTICE`.
