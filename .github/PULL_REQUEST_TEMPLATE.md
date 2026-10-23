Fixes #

---

<!-- Keep the `Fixes #xx` keyword at the top (it auto-closes the issue on merge) and replace this comment with a 1-2 sentence description: who benefits, what problem they had, and how this solves it. -->

## What changed

<!-- Packages and public APIs touched. Package, import, and CLI names stay the same as in the original project; call out anything that changes behavior or a public signature. -->

-

## How it was verified

<!-- Tick only what you actually ran, from the package directory you changed (e.g. libs/core). Paste relevant output. -->

- [ ] `uv run --group test pytest tests/unit_tests/` (no network, no API keys)
- [ ] For a bug fix: a regression test that fails before the fix and passes after it
- [ ] `uv run --group lint ruff check <changed files>`
- [ ] `uv run --group lint ruff format --diff <changed files>`
- [ ] `uv run --group typing mypy <changed files>` (packages that use mypy)

## Release note

<!-- Required for new features or behavior-changing bug fixes: the user-visible change in release-note-ready language. Omit for chores, refactors, or test-only changes. -->

## Checklist

- [ ] The pull request title follows Conventional Commits with a scope, e.g. `fix(core): keep per-input errors in batch retries` (see [`pr_lint.yml`](workflows/pr_lint.yml)).
- [ ] A line was added to the Unreleased section of [CHANGELOG.md](../CHANGELOG.md).
- [ ] No secrets, API keys, private URLs, or personal settings were added.
- [ ] The change touches one package unless more were strictly necessary.
- [ ] No `uv.lock` updates or new dependencies, unless discussed in the linked issue.
- [ ] If AI agents helped write this change, it says so briefly here.
