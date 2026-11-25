# Tollhouse

Check an MCP server's tools before you install or publish it.

> **Early days.** It reads an MCP server's `tools/list` answer, reports the prompt-injection phrases and credentials in it, and warns on what the tools say about the data they hand out. Hidden characters, tool-poisoning patterns, a server's code and checking a running server come next.

## Why

An MCP client hands the model every tool's name, title and description, and its input schema whole. A tool can carry instructions aimed at your AI rather than at you, and a person reading the tool list skims straight past them. Tollhouse reads what the model would read, one string at a time, and says where each finding is.

## Check a server's tools

Save the server's `tools/list` answer to a file, for example with the [MCP Inspector](https://modelcontextprotocol.io/docs/tools/inspector) in its command-line mode: run it with `--cli <your server command> --method tools/list` and redirect what it prints to `tools.json`.

Then:

```sh
uvx tollhouse check tools.json
```

`pipx run tollhouse check tools.json` works as well. Each finding is printed with its place, such as `tools[search].inputSchema.properties[query].description`, the rule it matched and the text that matched it (for a credential, its first and last few characters, never the key). A finding is one to fix, or a warning: words a person should weigh because they can be innocent.

It exits 1 when there is a finding to fix, 0 when there is only a warning or nothing, and 2 when the file cannot be read; `--strict` exits 1 on a warning too. `tollhouse check --json` prints the same answer for a script, each finding with its `level` (`block` or `warn`). It reads the file you name: no network call, and nothing written.

The file can be the `tools/list` result (`{"tools": [...]}`), the list of tools itself, or a whole JSON-RPC response.

## What it checks

| | |
| --- | --- |
| **What it reads** | Every string a model is handed: each tool's name, title and description, its annotations, and every string in its input schema, including descriptions, titles, allowed values, defaults and examples. |
| **Findings to fix** | The prompt-injection catalogue: "ignore previous instructions" and its kin, a new system prompt, a role tag written inline, developer mode, asking for the system prompt, and sending an environment variable or a key somewhere. And credentials: provider keys and tokens (AWS, OpenAI, Anthropic, GitHub, Google, Slack, Stripe, Azure and others) as shapes that are a key or nothing, with documented sample keys left alone. |
| **Warnings** | What the tools say about the data they hand out: personal contact data (phone numbers, email or home addresses) offered for outreach, contact data beside a scraped source, and an open-data claim beside one. A word alone warns of nothing: an SMS tool takes a phone number, and a scraper reads a page. |

Each string is read alone, the way the model reads it: two fields are never joined into one phrase, and the file's JSON escapes are decoded first, so a phrase broken over a line break inside one description is still found.

## What it does not catch

It catches accidents and obvious abuse, not a determined attacker: a fixed list of phrases can be reworded around. A clean answer means no rule matched the tools' text, not that the server is safe, and every answer says what it did not check. It does not start the server, read its code, or watch what it does when a tool is called. A server that forwards its tool calls to another server can read clean here while that other server, which can change at any time, decides every answer.

## What comes next

- hidden characters, such as invisible Unicode and direction overrides, in the same strings;
- tool-poisoning patterns: asking the model to read a secret file, to keep an action from the user, or to change how another tool behaves;
- a skill's `SKILL.md`, a Python wheel's contents (its code, and where it connects) and an MCP server's launch command;
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
