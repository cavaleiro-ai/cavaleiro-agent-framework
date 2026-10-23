# Changelog

All notable changes to Cavaleiro Agent Framework are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases use [Semantic Versioning](https://semver.org/).

The repository version (Cavaleiro Agent Framework 1.0.0) is separate from the version of each Python package. Packages keep their original names and version numbers (for example `langchain-core` 1.6.12), so you can always tell which original release they are based on.

## [Unreleased]

<a id="1.0.0"></a>

## [1.0.0] - 2026-10-17

First release of **Cavaleiro Agent Framework 1.0.0**. It is based on the original project's commit `bd5b134d876ef47858beef27bd29c81eeda03293` (`master`, 2026-10-16: `langchain-core` 1.6.12, `langchain` 1.4.6, `langchain-text-splitters` 1.1.3).

Every fix below has a regression test that fails on the original code and passes here. [ENGINEERING.md](docs/cavaleiro/ENGINEERING.md) has the evidence for each one.

<a id="fixed"></a>

### Fixed

- **`with_retry()` batches could return another input's result.** In `RunnableRetry.batch`/`abatch` (`langchain_core/runnables/retry.py`), when one input recovered on a later attempt and another kept failing, the failing input received the recovered input's output in its slot. With `return_exceptions=False`, the batch then returned that wrong value instead of raising. Each input now keeps its own latest exception. (original issue #41162)
- **A non-retryable error no longer wipes out the rest of a `with_retry()` batch.** When one input raised an exception outside `retry_if_exception_type`, every input in the batch, including successful ones, came back as that exception, and every run was reported to callbacks as failed. Successful inputs now keep their results, and each failed input keeps its own error. (Found during this review.)
- **`RouterRunnable.batch`/`abatch` ignored `return_exceptions=True` for unknown routes.** One unknown `key` raised for the whole batch. It is now a per-input `ValueError`, the same as `invoke`. Without `return_exceptions`, the batch still fails fast before running anything. (original issue #41280)
- **`merge_message_runs` turned invalid tool calls into valid ones.** Merging two `AIMessage`s re-parsed malformed or truncated tool-call arguments leniently, so a call with `args="{bad json"` became a valid call with `args={}` that an agent could execute with default parameters. Merged messages now keep `tool_calls` and `invalid_tool_calls` exactly as they were. Merging streamed `AIMessageChunk`s is unchanged. (original issue #41254)
- **`merge_message_runs` raised `ValueError` for consecutive `ChatMessage`s with different roles, or `FunctionMessage`s with different names.** These messages now stay separate, and messages with the same role or name still merge. (original issue #41138)
- **`convert_to_openai_messages` raised `KeyError: 'type'`** in the default `text_format="string"` mode for content blocks without a `type` key, such as Bedrock Converse `{"text": ...}` and `{"toolUse": ...}` blocks. Such blocks are now passed through, the same as with `text_format="block"`. (original issue #41021)
- **`count_tokens_approximately(tools=[...])` raised `AttributeError` for plain functions**, although its docstring says callables are accepted. They are now converted to the OpenAI function schema before counting, and the type hint includes callables. (original issue #41289)
- **`count_tokens_approximately` ignored tool calls when an `AIMessage` had list content.** A 4,000-character tool argument counted as 6 tokens instead of about 1,027, so `trim_messages` kept messages that exceeded the budget. Tool calls are now skipped only when a content block (`tool_use`, `tool_call`, or `function_call`) already carries them. (original issue #41166)
- **`XMLOutputParser.parse()` removed valid elements that have an `encoding` attribute** followed by a newline (for example `<root encoding="utf-8">`), because the regex meant for the `<?xml ... encoding=...?>` declaration also matched ordinary tags. The regex now matches only real XML declarations. (original issue #41149)
- **`MarkdownTextSplitter` and `LatexTextSplitter` never split on headings or sections.** Their language separators are regular expressions (for example `"\n#{1,6} "`), but the splitters escaped them. They now behave like `RecursiveCharacterTextSplitter.from_language(...)`. An explicit `is_separator_regex` argument is still honored. (original issue #41184)

<a id="security"></a>

### Security

- **Mustache prompt templates no longer render unrelated data from outer scopes.** Inside a section, a dotted name such as `{{profile.name}}` whose last part was missing fell back to a top-level `profile.name` and rendered it into the prompt silently. Following the mustache specification ("Dotted Names - Context Precedence"), once the first part of a dotted name resolves, a missing remainder renders as empty. This affects `PromptTemplate` and `ChatPromptTemplate` with `template_format="mustache"`. (original issue #41281)
- **Fork safety:** 18 workflows that publish to PyPI, use non-`GITHUB_TOKEN` secrets (provider API keys, LangSmith, CodSpeed, GitHub Apps), or enforce the original organization's policy with write permissions were moved to [`.github/workflows-disabled/`](.github/workflows-disabled/README.md). Nothing in this repository publishes or deploys under the original project's identity.
- Private vulnerability reporting through the [security policy](SECURITY.md).

<a id="added"></a>

### Added

- 30 regression tests: 27 in `libs/core` and 3 in `libs/text-splitters`.
- Windows instructions for the unit tests. On Windows, the `--disable-socket` flag of `pytest-socket` also blocks the loopback `socket.socketpair()` that asyncio's event loop needs, so `--allow-hosts=127.0.0.1,::1` is documented as the equivalent (see [CONTRIBUTING.md](CONTRIBUTING.md#windows)).
- [README.md](README.md) and [README.pt-BR.md](README.pt-BR.md) with *What Cavaleiro Agent Framework adds*, *Compatibility*, and *License* sections; a complete Portuguese guide, [docs/cavaleiro/GUIA-PT-BR.md](docs/cavaleiro/GUIA-PT-BR.md); and an engineering report, [docs/cavaleiro/ENGINEERING.md](docs/cavaleiro/ENGINEERING.md).
- Community files: [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) (Contributor Covenant 2.1), and adapted issue and pull request templates.

<a id="changed"></a>

### Changed

- Rebranded the project as **Cavaleiro Agent Framework**. Package, import, CLI, and environment variable names are unchanged; see [Compatibility](README.md#compatibility).
- `Repository`, `Issues`, and `Changelog` URLs in every `libs/**/pyproject.toml`, the Code of Conduct and contributing links in the package READMEs, and the dev-container clone link now point to this repository. `langchain-core` and `langchain-text-splitters` list Cavaleiro AI as author and maintainer, and their homepage and documentation URLs point here. Social and community URLs were removed from every `libs/**/pyproject.toml`.
- Package READMEs, `libs/README.md`, and `AGENTS.md` use the Cavaleiro Agent Framework name in prose. Social, community, course, and promotional links were removed from them.
- CI runs on pushes to `main` (the original project used `master`). `check_extras_sync.yml` and `check_versions.yml` run for the `cavaleiro-ai` owner.
- `CODEOWNERS` is now `* @cavaleiro-ai`. The original maintainer-only issue forms (`privileged.yml`, `task.yml`) were removed, and the bug report, feature request, contact links, and pull request template were adapted for this fork.
- `AGENTS.md` starts with a note on the fork's differences: release workflows are disabled and the default branch is `main`.
- The MIT `LICENSE` files at the root, in `libs/core`, and in `libs/text-splitters` (the packages changed here) add the derivative-work notice and a Cavaleiro AI copyright line. The original text and copyright lines are kept verbatim.

[Unreleased]: https://github.com/cavaleiro-ai/cavaleiro-agent-framework/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/cavaleiro-ai/cavaleiro-agent-framework/releases/tag/v1.0.0

---

## Earlier history

Changes made before this fork belong to the original project and are not listed here.
