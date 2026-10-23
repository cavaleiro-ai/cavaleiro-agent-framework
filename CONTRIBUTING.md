# Contributing to Cavaleiro Agent Framework

Thanks for helping improve Cavaleiro Agent Framework. It is a Python monorepo derived from the original project, so most of its development practices apply here too. This guide covers them and the few things that differ in this fork.

By participating you agree to the [Code of Conduct](CODE_OF_CONDUCT.md). Report vulnerabilities privately, as described in the [security policy](SECURITY.md).

## Ways to contribute

- **Report a bug** with a minimal, runnable reproduction, using the [bug report form](https://github.com/cavaleiro-ai/cavaleiro-agent-framework/issues/new/choose).
- **Fix a bug**: the best contributions add a regression test that fails before the fix and passes after it.
- **Propose an improvement**: open an issue first so the approach can be agreed before you write a large change.
- **Improve the documentation**, in English or in Portuguese (`README.pt-BR.md` and `docs/cavaleiro/GUIA-PT-BR.md`).

If a bug also exists in the original project, consider reporting it there as well. Fixes made there benefit everyone, and this fork can pick them up.

## Ground rules

1. **Keep identifiers stable.** Do not rename distributions (`langchain-core`, …), import paths (`langchain_core`, …), CLI commands, environment variables, or serialization namespaces. They are the compatibility contract of this fork. See [Compatibility](README.md#compatibility).
2. **Keep public interfaces stable.** Preserve function signatures, argument positions, and names of exported APIs. Add new parameters as keyword-only (`*, new_param: str = "default"`). If a bug fix changes behavior, say so in the changelog.
3. **No network in unit tests.** Unit tests live in `tests/unit_tests/`, must not call external services, and must not need API keys. Integration tests (`tests/integration_tests/`) are not run by this fork's CI.
4. **Never weaken a check to get a green run.** Do not skip, delete, or loosen existing tests, assertions, or lint rules to make a change pass.
5. **Type hints and Google-style docstrings** on all public functions, as in the existing code. Use single backticks for code in docstrings and American English spelling.
6. **No new dependencies or `uv.lock` updates** unless they are required and discussed in the issue first.
7. **Security basics:** no `eval()`, `exec()`, or `pickle` on user-controlled input, no bare `except:`, and close files, sockets, and threads properly.

## Development setup

Requirements: Git, Python 3.10–3.14, and [uv](https://docs.astral.sh/uv/). There is no workspace-level project at the repository root. Work inside the package you are changing:

```bash
git clone https://github.com/cavaleiro-ai/cavaleiro-agent-framework.git
cd cavaleiro-agent-framework/libs/core      # or libs/langchain_v1, libs/text-splitters, libs/partners/<name>
uv sync --all-groups                         # creates a project-local .venv
```

Dependencies between packages resolve to your working tree through `[tool.uv.sources]` in each `pyproject.toml`. Use `uv` for all environment operations. Do not install with `pip` into a global interpreter.

## Running the checks

Each package has a `Makefile` that wraps the commands below. On systems without `make`, such as a default Windows setup, run the commands directly.

### Linux and macOS

```bash
# Unit tests (network blocked by pytest-socket; tracing variables unset)
env -u LANGCHAIN_TRACING_V2 -u LANGCHAIN_API_KEY -u LANGSMITH_API_KEY -u LANGSMITH_TRACING -u LANGCHAIN_PROJECT \
  uv run --group test pytest -n 4 --benchmark-disable --disable-socket --allow-unix-socket tests/unit_tests/

# A single file or test
uv run --group test pytest tests/unit_tests/runnables/test_runnable.py -k retry

# Lint, format check, and type check (only the files you changed)
uv run --group lint ruff check path/to/file.py
uv run --group lint ruff format --diff path/to/file.py
uv run --group typing mypy path/to/file.py
```

`--benchmark-disable` applies to `libs/core`, the package that uses `pytest-benchmark`.

<a id="windows"></a>

### Windows

The original `--disable-socket --allow-unix-socket` flags do not work on Windows. There, asyncio's event loop calls `socket.socketpair()`, which on Windows is a loopback TCP connection, and `pytest-socket` blocks it, so every async test errors out. Allow loopback only, which still blocks the external network:

```powershell
Remove-Item Env:LANGCHAIN_TRACING_V2, Env:LANGCHAIN_API_KEY, Env:LANGSMITH_API_KEY, Env:LANGSMITH_TRACING, Env:LANGCHAIN_PROJECT -ErrorAction SilentlyContinue
uv run --group test pytest -n 4 --benchmark-disable --allow-hosts=127.0.0.1,::1 tests/unit_tests/
```

Some `libs/core` tests are known to fail on Windows for environment reasons, not because of a code defect:

- `tests/unit_tests/prompts/test_loading.py::test_*symlink*` (3 tests) need permission to create symbolic links. Enable Windows Developer Mode or run as administrator.
- `tests/unit_tests/language_models/chat_models/test_rate_limiting.py` asserts tight timing windows (±50 ms) that the Windows timer and a busy machine can miss.
- `tests/unit_tests/indexing/test_indexing.py::test_index_into_document_index` and its async variant rely on two consecutive `time.time()` readings being different, which the coarse Windows clock on Python 3.12 does not guarantee.

[ENGINEERING.md](docs/cavaleiro/ENGINEERING.md#baseline) records the exact baseline numbers.

## Pull requests

- Title in [Conventional Commits](https://www.conventionalcommits.org/) format with a scope, for example `fix(core): keep per-input errors in batch retries`. Allowed types and scopes are listed in [`.github/workflows/pr_lint.yml`](.github/workflows/pr_lint.yml).
- One package per pull request, unless more are strictly necessary.
- Fill in the [pull request template](.github/PULL_REQUEST_TEMPLATE.md), ticking only the checks you actually ran.
- Bug fixes include a regression test. Mention the original project's issue number if there is one.
- Add a line under **Unreleased** in the [changelog](CHANGELOG.md).
- If AI agents helped write the change, say so briefly in the description.

## What CI runs

`.github/workflows/check_diffs.yml` detects which packages changed and runs lint, unit tests, Pydantic compatibility tests, integration-test compilation, and VCR cassette tests for them, using only the default `GITHUB_TOKEN`. Release, integration-test, benchmark, and bot workflows are kept in [`.github/workflows-disabled/`](.github/workflows-disabled/README.md) and do not run.

## License

By contributing, you agree that your contributions are licensed under the [MIT License](LICENSE) of this repository.
