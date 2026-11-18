"""The rules Tollhouse checks with, copied from the Sigrix platform's rule set.

The platform runs the same rules when a seller uploads an MCP server, so a file
that passes here passes that check, and one it refuses there is reported here.
Each module is a copy, written by the platform's release tooling with this
package's names, never edited in place: a change to a rule is made there and
copied back, so the two cannot disagree.

- ``tool_text``: every string a declared tool hands a model, each alone, named
  by its place.
- ``injection_scan``: the prompt-injection catalogue.
- ``document_strings``: what a reader decodes from a YAML document, for a scan
  that reads one.
"""
