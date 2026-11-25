"""Tollhouse: check an MCP server's tools before you install or publish it.

An MCP client hands the model every tool's name, title, description and input
schema. Tollhouse reads what the model would read, one string at a time, and
reports what its rules find there, with the place each finding sits.

One command, ``tollhouse check``, reads a server's ``tools/list`` answer for
prompt-injection phrases and credentials, and warns on what the tools say about
the data they hand out. It reads the file it is given and nothing else: no
network call, nothing started, nothing written.
"""

__version__ = "0.0.1"
