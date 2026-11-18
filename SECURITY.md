# Security

## Reporting

Email security@sigrix.io with what you found and how to reproduce it. Do not
open a public issue for a vulnerability. You will get an acknowledgement
within three working days.

## What this release does

`tollhouse check` reads the one file you name, decodes it as JSON and prints
what it found. It makes no network call, starts nothing and writes no file. A
finding quotes up to 80 characters of the text that matched, so its output
can carry a phrase from the tools it read.

## What a clean answer means

That none of the catalogue's phrases is in the strings the tools hand a model.
It does not mean the server is safe: a determined author can word an
instruction around a fixed list, and nothing here reads the server's code or
watches it run.

## A finding in someone else's server

Tell its author. For a server sold on Sigrix, use the report link on its
listing's page, or the address above.
