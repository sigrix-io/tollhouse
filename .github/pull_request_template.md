## What this changes

<!-- One or two sentences. The diff shows what changed; say why. -->

## Does it change what the check reports?

<!--
Delete the rows that do not apply.

- [ ] No: refactor, docs, tests or tooling only.
- [ ] A rule matches more or less than it did. It comes with a string it should
      match and one it should leave alone, and the changelog says that a check
      which passed before can fail now. The files under src/tollhouse/rules/ are
      copied from the Sigrix platform's rule set, so a maintainer makes the
      change there and copies it back (CONTRIBUTING.md, Rules).
- [ ] A message changed. Say what it printed before and after.
- [ ] What `--json` prints changed shape. A script may read it; the changelog
      says so.
-->

## The test that fails without it

<!--
One change per pull request, with a test that fails without it. Break the
implementation on purpose, confirm the test goes red, then put it back. Say
what you broke and which test caught it.
-->

## Checks

- [ ] `pytest`
- [ ] `ruff check .`
- [ ] `ruff format --check .`
- [ ] `mypy`
- [ ] Still the standard library only, with no network call, no server started and no file written
- [ ] No real key in a test or an example, even a revoked one
- [ ] `CHANGELOG.md` has a line under *Unreleased*
