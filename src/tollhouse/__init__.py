"""Tollhouse: check an MCP server's tools before you install or publish it.

An MCP client hands the model every tool's name, title, description and input
schema. Tollhouse reads what the model would read, one string at a time, and
reports what its rules find there, with the place each finding sits.

This first release carries one command, ``tollhouse check``, which reads a
server's ``tools/list`` answer for the prompt-injection catalogue. It reads the
file it is given and nothing else: no network call, nothing started, nothing
written.
"""

__version__ = "0.0.1"
