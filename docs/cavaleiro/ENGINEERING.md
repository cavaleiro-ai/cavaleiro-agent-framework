# Cavaleiro Agent Framework: engineering report

This report records how Cavaleiro Agent Framework 1.0.0 was derived from the original project:

- the architecture of the codebase;
- the test baseline;
- every finding, with its severity and status;
- how each change was verified;
- what was deliberately left alone.

Portuguese readers: see the [guia completo em português](GUIA-PT-BR.md).

| | |
|---|---|
| Original project | branch `master` |
| Original commit | `bd5b134d876ef47858beef27bd29c81eeda03293` (2026-10-16, `release(core): 1.6.12`) |
| License | MIT (see [LICENSE](../../LICENSE)); modifications © 2026 Cavaleiro AI |
| Packages changed | `langchain-core` (`libs/core`), `langchain-text-splitters` (`libs/text-splitters`) |
| Verification platform | Windows 10 (x64), Python 3.12.2, uv 0.11.3, project-local `.venv` per package |

<a id="architecture-map"></a>

## Architecture map

### Components

The repository is a monorepo of independently versioned Python packages. There is no root project. Each `libs/<package>` directory has its own `pyproject.toml`, `uv.lock`, `Makefile`, and tests.

```text
                 user application
                        │
          ┌─────────────┴──────────────┐
          ▼                            ▼
  langchain (libs/langchain_v1)   langchain-core (libs/core)  ◄── implemented by ──┐
  create_agent, middleware,        Runnable protocol, messages,                      │
  init_chat_model                  prompts, parsers, tools,              libs/partners/* (openai,
          │                        callbacks/tracers, documents,         anthropic, ollama, groq, …)
          │ depends on             vector stores, indexing
          ├──────────► langgraph (external: state-graph engine)
          └──────────► langchain-core
  langchain-text-splitters ──► langchain-core (Document, BaseDocumentTransformer)
  langchain-classic (libs/langchain) ──► langchain-core (legacy chains)
  langchain-tests (libs/standard-tests): shared test suites for integrations
  langchain-model-profiles (libs/model-profiles): model capability data + `langchain-profiles` CLI
```

| Component | Responsibility | Key modules |
|---|---|---|
| **Runnables** | The `Runnable[Input, Output]` protocol: `invoke`/`ainvoke`, `batch`/`abatch`, `stream`/`astream`, `astream_events`, plus composition with `\|` (`RunnableSequence`), `RunnableParallel`, `RunnableLambda`, `RouterRunnable`, `RunnableBranch`, retries (`with_retry` → `RunnableRetry`), fallbacks, configurable fields, and the config and executor plumbing | `langchain_core/runnables/` (`base.py`, `retry.py`, `router.py`, `config.py`, `fallbacks.py`) |
| **Language models** | `BaseChatModel` and `BaseLLM`: message encoding, streaming, caching, rate limiting, structured output, and fake models for tests | `language_models/`, `rate_limiters.py`, `caches.py` |
| **Messages** | `AIMessage`, `HumanMessage`, `SystemMessage`, `ToolMessage`, `ChatMessage`, `FunctionMessage` and their chunks; standard content blocks; provider block translators; utilities such as `trim_messages`, `filter_messages`, `merge_message_runs`, `convert_to_openai_messages`, and `count_tokens_approximately` | `messages/` (`ai.py`, `utils.py`, `content.py`, `block_translators/`) |
| **Prompts** | `PromptTemplate`, `ChatPromptTemplate`, message prompt templates, and loading from files. Formats: f-string, mustache (vendored chevron in `utils/mustache.py`), and Jinja2 (sandboxed) | `prompts/`, `utils/formatting.py`, `utils/mustache.py` |
| **Output parsers** | String, JSON (with partial streaming), XML (defusedxml by default), list, Pydantic, and OpenAI tool parsers | `output_parsers/` |
| **Tools** | `BaseTool`, `StructuredTool`, the `@tool` decorator, argument-schema inference from signatures and docstrings, injected arguments, and conversion to provider tool schemas | `tools/`, `utils/function_calling.py`, `utils/pydantic.py` |
| **Callbacks and tracers** | Callback managers, run trees, the LangSmith tracer, event streaming, and the in-memory stream | `callbacks/`, `tracers/` |
| **Data** | `Document`, loaders, embeddings, vector stores (in-memory reference implementation), retrievers, and indexing with record managers | `documents/`, `vectorstores/`, `retrievers.py`, `indexing/` |
| **Serialization and security** | `dumps`/`loads` with an allowlist of class paths; SSRF-safe HTTP transport and policy | `load/`, `_security/` |
| **Agents** | `create_agent` builds a LangGraph state machine with model and tool nodes and middleware hooks (`before_model`, `wrap_model_call`, `wrap_tool_call`, …). `init_chat_model` resolves `provider:model` strings to partner classes lazily | `libs/langchain_v1/langchain/agents/`, `libs/langchain_v1/langchain/chat_models/` |
| **Text splitters** | Character, recursive (with per-language separators), token, Markdown header, HTML, JSON, code, spaCy, and NLTK splitters | `libs/text-splitters/langchain_text_splitters/` |

### Control and data flow

A typical chain is `prompt | model | parser`. `ChatPromptTemplate.invoke(dict)` produces a `ChatPromptValue`. `BaseChatModel.invoke` converts it to messages, checks the cache and rate limiter, calls the provider's `_generate` or `_stream`, and returns an `AIMessage` with `tool_calls` and `usage_metadata`. The parser turns that message into the final value. Every step runs inside `_call_with_config`, which opens a child run in the callback manager, so tracers and `astream_events` see the whole tree. `batch` fans out over a thread pool (`get_executor_for_config`) or `asyncio.gather` with `max_concurrency`. With `return_exceptions=True`, each input reports its own exception.

### Extension points

- Subclass `BaseChatModel` (`_generate`, `_stream`, `_llm_type`) for a new provider; partner packages are the reference implementations, and `langchain-tests` provides the standard test suite.
- Write tools with `@tool` or `BaseTool`, and runnables with `RunnableLambda` or `Runnable` subclasses.
- Add agent middleware by subclassing `AgentMiddleware` in `langchain`.
- Add callback handlers (`BaseCallbackHandler`) and tracers.

### Configuration

Configuration lives in code and environment variables: provider API keys (`OPENAI_API_KEY`, …), LangSmith tracing (`LANGSMITH_TRACING`, `LANGSMITH_API_KEY`, `LANGSMITH_PROJECT`, and the legacy `LANGCHAIN_*` names), and per-call `RunnableConfig` (callbacks, tags, metadata, `max_concurrency`, `recursion_limit`). Tracing is **off** unless enabled.

### Tests

Each package has `tests/unit_tests/`, which must not use the network: `pytest-socket` blocks it, and `blockbuster` catches blocking calls inside the event loop. Some packages also have `tests/integration_tests/`, which call real providers with API keys. Snapshot tests use `syrupy`, and benchmarks use `pytest-benchmark` and CodSpeed.

### Build and release pipeline

- Packages are built with Hatchling and managed with uv.
- CI (`.github/workflows/check_diffs.yml`) computes the affected packages with `.github/scripts/check_diff.py`. It then runs `_lint.yml` (ruff and mypy), `_test.yml` (unit tests, plus minimum-version tests), `_test_pydantic.yml`, `_compile_integration_test.yml`, and `_test_vcr.yml` (cassette playback, no keys).
- Releases of the original project run `_release.yml`: build, release notes, pre-release checks with provider keys, TestPyPI, PyPI, and a GitHub release. In this fork the release workflow is disabled (see [fork safety](#fork-safety)).

<a id="baseline"></a>

## Baseline

The baseline was measured on the unmodified copy of the original project's commit `bd5b134`, before any change, on Windows 10 with Python 3.12.2 and `-n 4` workers. The tracing environment variables were unset.

| Package | Command (run from the package directory) | Result | Time |
|---|---|---|---|
| `libs/core` | `uv run --group test pytest -n 4 --benchmark-disable --disable-socket --allow-unix-socket -p no:cacheprovider tests/unit_tests/` (the original `make test` flags) | 1947 passed, **18 failed, 433 errors**, 13 skipped, 9 xfailed, 1 xpassed | 193 s |
| `libs/core` | the same command with `--allow-hosts=127.0.0.1,::1` instead of `--disable-socket --allow-unix-socket` | 2391 passed, **7 failed**, 13 skipped, 9 xfailed, 1 xpassed | 107 s |
| `libs/text-splitters` | `uv run --no-default-groups --group test pytest -n 4 --allow-hosts=127.0.0.1,::1 -p no:cacheprovider tests/unit_tests/` | 118 passed, 41 skipped (optional dependencies such as spaCy, NLTK, and transformers are not installed) | 66 s |

**Why the original flags fail on Windows.** With `--disable-socket`, the 433 errors and most of the failures are `SocketBlockedError` from `socket.socketpair()`. On Windows that function is a loopback TCP connection that asyncio's event loop needs. `--allow-unix-socket` does not help, because there are no Unix sockets on Windows. Allowing loopback only is the closest equivalent: external network access stays blocked.

**The 7 remaining baseline failures are pre-existing and caused by the environment:**

| Test | Cause |
|---|---|
| `prompts/test_loading.py::test_symlink_txt_to_py_is_blocked`, `test_symlink_jinja2_rce_is_blocked`, `test_save_symlink_to_py_is_blocked` | `OSError: [WinError 1314]`: creating symbolic links needs Developer Mode or administrator rights (original issue #40241). |
| `language_models/chat_models/test_rate_limiting.py::test_rate_limit_invoke`, `test_rate_limit_ainvoke` (others in the file fail when run alone) | The assertions use timing windows such as `0.10 < elapsed < 0.15` and `0.00 < elapsed`. Windows timer granularity and a machine shared with other jobs miss them. The result changes between runs. |
| `indexing/test_indexing.py::test_index_into_document_index`, `test_aindex_into_document_index` | A full cleanup deletes records with `updated_at < index_start`. With the coarse `time.time()` clock of Python 3.12 on Windows, consecutive calls can return the same timestamp, so `num_deleted` is 0 instead of 2. |

## Findings

Sources:

- careful reading of the core code paths (runnables, messages, prompts, parsers, tools, splitters);
- open issues of the original project labeled `bug` with a concrete reproduction;
- the project's own ruff and mypy configuration;
- a security review of template rendering and parsing.

Each candidate was first reproduced on the unmodified tree with one script, and every case reproduced.

| # | Finding | Severity | Status | Evidence |
|---|---|---|---|---|
| 1 | `RunnableRetry.batch`/`abatch`: a failing input receives a recovered neighbor's result; with `return_exceptions=False` nothing is raised (original issue #41162) | High: silent wrong results | Fixed | `test_retry_batch_keeps_own_exception_when_neighbor_recovers` (+ async) |
| 2 | `RunnableRetry.batch`/`abatch`: a non-retryable error in one input replaces every result, including successes, and marks every run as failed | High: data loss | Fixed | `test_retry_batch_non_retryable_exception_keeps_other_results` (+ async) |
| 3 | `merge_message_runs` promotes invalid tool calls to valid calls with fabricated `args` (original issue #41254) | High: an agent could execute a malformed call | Fixed | `test_merge_message_runs_preserves_invalid_tool_calls` |
| 4 | Mustache dotted name inside a section falls back to an outer scope and renders unrelated data (original issue #41281) | Medium (security): unrelated, possibly sensitive data reaches the prompt | Fixed | `test_mustache_dotted_name_does_not_leak_outer_scope` (4 cases), `test_mustache_chat_prompt_dotted_name_does_not_leak_outer_scope` |
| 5 | `count_tokens_approximately` ignores tool calls when the content is a list, so `trim_messages` keeps oversize messages (original issue #41166) | Medium | Fixed | `test_count_tokens_approximately_counts_tool_calls_missing_from_list_content` (2 cases), `test_count_tokens_approximately_counts_only_unembedded_tool_calls` |
| 6 | `RouterRunnable.batch`/`abatch` ignore `return_exceptions=True` for unknown keys (original issue #41280) | Medium | Fixed | `test_router_runnable_batch_unknown_key_return_exceptions` (+ async) |
| 7 | `XMLOutputParser.parse` removes an element with an `encoding` attribute followed by a newline (original issue #41149) | Medium | Fixed | `test_xml_output_parser_keeps_elements_with_encoding_attribute` (3 inputs × 2 backends) |
| 8 | `MarkdownTextSplitter`/`LatexTextSplitter` escape their regex separators and never split on headings or sections (original issue #41184) | Medium | Fixed | `test_markdown_text_splitter_splits_on_headings`, `test_latex_text_splitter_splits_on_sections` |
| 9 | `merge_message_runs` raises `ValueError` for `ChatMessage`s with different roles or `FunctionMessage`s with different names (original issue #41138) | Low–Medium: crash on valid input | Fixed | `test_merge_message_runs_keeps_chat_message_roles_apart`, `..._function_message_names_apart` |
| 10 | `convert_to_openai_messages` raises `KeyError: 'type'` for typeless blocks in the default string format (original issue #41021) | Low–Medium: crash on Bedrock-style content | Fixed | `test_convert_to_openai_messages_typeless_block_string_format` (3 cases) |
| 11 | `count_tokens_approximately(tools=[function])` raises `AttributeError`, although the docstring says callables are accepted (original issue #41289) | Low | Fixed | `test_count_tokens_approximately_plain_callable_tool` |
| 12 | `pytest-socket`'s `--disable-socket` breaks every async unit test on Windows | DX | Documented ([CONTRIBUTING.md](../../CONTRIBUTING.md#windows)) | Baseline table above |
| 13 | Symlink, rate-limiter, and indexing unit tests fail on Windows for environment reasons | DX | Documented, tests unchanged | Baseline table above |
| 14 | `libs/text-splitters/uv.lock` records the editable `langchain-core` as 1.6.7 with `langsmith>=0.3.45` (locked at 0.9.4), while `libs/core` 1.6.12 needs `langsmith>=0.14.9`. In that environment `import langchain_core.runnables` fails with `ImportError: cannot import name 'address' from 'langsmith'` | Low (dev environment) | Not fixed: needs a lockfile refresh | `uv sync --frozen` in `libs/text-splitters`, then import `langchain_core.runnables` |
| 15 | Publishing, secret-using, and governance workflows would act under the original project's identity in a fork | Fork safety | Fixed (moved to `.github/workflows-disabled/`) | [Fork safety](#fork-safety) |

## Improvements and how each was verified

Every fix followed the same steps:

1. Write the regression test first.
2. Run it against the unmodified code and save the failing log.
3. Apply the smallest change that matches the surrounding style.
4. Re-run the test file or directory and save the passing log.
5. Run `ruff check`, `ruff format --diff`, and (for `libs/core`) `mypy` on every changed file.

The logs are kept outside the repository, in the agent's scratch folder, as `fixN-*-before.log` and `fixN-*-after.log`.

### 1–2. `with_retry()` batches keep each input's own outcome

`libs/core/langchain_core/runnables/retry.py`: `_batch` (line 234), `_abatch` (line 354), and the new helpers `_register_batch_outcomes` (line 295) and `_collect_batch_outputs` (line 319).

After the last attempt, the old code filled every missing index with `result.pop(0)`. But `result` was the full output of the last attempt, successes included, so a failing input could take a neighbor's value. The batch now records each input's latest exception under its original index (`exceptions_map`) next to the successes (`results_map`), and builds the output from both. When an input raises an exception that is not retryable, tenacity re-raises it. That exception is now recognized as the batch's own (`e is first_exception`), so the other inputs keep their outcomes instead of `_batch_with_config` turning every slot into the error. Exceptions from anywhere else still propagate as before.

- Before: `['A', 'A', 'C']` for inputs `a` (recovers), `b` (always fails), `c`; and `[RuntimeError, RuntimeError, RuntimeError]` for `[2, 0, 1]` when 2 raises a non-retryable error.
- After: `['A', ValueError('b always fails'), 'C']` and `[RuntimeError, 0, 1]`. Without `return_exceptions`, `ValueError: b always fails` is raised.
- Tests: 4 new (sync and async). The 6 existing retry tests still pass.

### 3. `merge_message_runs` keeps invalid tool calls invalid

`libs/core/langchain_core/messages/utils.py`, line 1162. Merging goes through an `AIMessage → AIMessageChunk → AIMessage` round trip. That trip flattens `invalid_tool_calls` into `tool_call_chunks` and re-parses their raw arguments with `parse_partial_json`, which turns `"{bad json"` into `{}` and `'{"query": "fo'` into `{"query": "fo"}`. When two complete (non-chunk) `AIMessage`s are merged, the merged message now takes both messages' `tool_calls` and `invalid_tool_calls` as they were (deep-copied). Merging chunks is unchanged, so streaming behaves as before. The test covers both malformed and truncated arguments, together with a valid call.

### 4. Mustache dotted names no longer leak outer-scope data

`libs/core/langchain_core/utils/mustache.py`, lines 381–441 (`_get_key`). The lookup used to retry the whole dotted path in each outer scope. The mustache specification resolves only the first part of the name through the context stack, so after `first_part_resolved` a later miss now ends the search and renders as empty (or keeps the tag if `keep=True`). Four parametrized cases cover the behavior: the two spec "Context Precedence" cases now render empty, the first part still falls back to outer scopes when it is missing, and a complete inner path still wins. The triply nested `{{#baz.qux}}` snapshot tests and all other prompt tests are unchanged.

### 5 and 11. `count_tokens_approximately`

`libs/core/langchain_core/messages/utils.py`: the helper `_tool_calls_missing_from_content` (line 2298) and its call site (line 2453). The old guard skipped `tool_calls` for every list content, to avoid counting Anthropic `tool_use` blocks twice. Now only calls already carried by a `tool_use`, `tool_call`, or `function_call` block (matched by `id` or `call_id`) are skipped. A call without an ID is treated as embedded, which keeps the old, conservative behavior. For plain callables (line 2399), `convert_to_openai_function` builds the same `name`/`description`/`parameters` shape that the `BaseTool` path produces. The callable and the equivalent `@tool` count within 5 tokens of each other; the only difference is the property `title`s.

- Before: `[1027, 6, 6]` for `content=""`, `[]`, and `[{"type": "text", "text": ""}]`, and `AttributeError` for a function.
- After: about 1027 in all three cases, and a count for the function.

### 6. `RouterRunnable` with `return_exceptions=True`

`libs/core/langchain_core/runnables/router.py`, lines 149 and 190. The up-front check for unknown keys now runs only when `return_exceptions=False`, so that mode still fails fast before invoking anything. Otherwise each input looks up its own route and returns `ValueError("No runnable associated with key '<key>'")`, the same message as `invoke`.

### 7. `XMLOutputParser` declaration regex

`libs/core/langchain_core/output_parsers/xml.py`, line 174. The regex `<([^>]*encoding[^>]*)>\n(.*)` became `<\?xml\s([^>]*\bencoding\s*=[^>]*)\?>\n(.*)`. Real declarations are still stripped (all existing tests with headers pass), and ordinary elements with an `encoding` attribute are kept. The test covers both backends (`xml` and `defusedxml`) with `parse` and `aparse`.

### 8. Markdown and LaTeX splitters

`libs/text-splitters/langchain_text_splitters/markdown.py`, line 22, and `latex.py`, line 19. Both now call `kwargs.setdefault("is_separator_regex", True)`, matching `from_language`. The literal fallbacks (`"\n\n"`, `"\n"`, `" "`, `""`) mean the same thing as regexes. An explicit `is_separator_regex` argument is still honored and does not cause a duplicate-keyword error; a separate test checks this, and it passes before and after the fix. Output now matches `RecursiveCharacterTextSplitter.from_language(...)`.

### 9. `merge_message_runs` roles and names

`libs/core/langchain_core/messages/utils.py`, line 1129. A differing `ChatMessage.role` or `FunctionMessage.name` is now a merge boundary, like a change of message class. Messages with equal roles or names still merge.

### 10. `convert_to_openai_messages` typeless blocks

`libs/core/langchain_core/messages/utils.py`, line 2004: `block["type"]` became `block.get("type")` in the check that collapses text blocks into a string. Typeless blocks (Bedrock `{"text": ...}`, `{"toolUse": ...}`, `{}`) now pass through, the same as with `text_format="block"`. Typed text blocks still collapse to a string.

### Docs and developer experience

- Windows test instructions and the list of known environment failures ([CONTRIBUTING.md](../../CONTRIBUTING.md#windows)), plus a note at the top of `AGENTS.md` for coding agents.
- English and Portuguese READMEs, this report, and the [Portuguese guide](GUIA-PT-BR.md).
- Community files and adapted issue and pull request templates.

<a id="fork-safety"></a>

### Fork safety

- 18 workflows were moved to [`.github/workflows-disabled/`](../../.github/workflows-disabled/README.md), and the README there explains each one:
  - PyPI release (`_release.yml`) and release-dependency checks;
  - integration tests with provider keys and LangSmith;
  - CodSpeed;
  - the OpenWiki updater (Anthropic API);
  - model-profile refresh (GitHub App);
  - the labelers and triage bots using the organization-membership GitHub App;
  - policy bots of the original project with write permissions.
- The workflows that stay active need only `GITHUB_TOKEN` with read permissions. They now trigger on `main` (`check_diffs.yml`, `check_extras_sync.yml`), and the owner checks in `check_extras_sync.yml` and `check_versions.yml` point to `cavaleiro-ai`. Actions remain pinned to the same commit SHAs.
- `CODEOWNERS` is now `* @cavaleiro-ai`. The original maintainer-only issue forms were removed. There was no `FUNDING.yml`.

## Final verification

The same commands as the baseline were run after all changes (see [CHANGELOG](../../CHANGELOG.md) for the full list of changes):

| Package | Result | Compared with the baseline |
|---|---|---|
| `libs/core` (`--allow-hosts=127.0.0.1,::1`), run 1 | 2419 passed, 6 failed, 13 skipped, 9 xfailed, 1 xpassed (78 s) | +27 new tests, all passing. The 6 failures are a subset of the 7 pre-existing environment failures: `test_rate_limit_invoke` passed in this run, which shows how timing-dependent it is. |
| `libs/core`, run 2 (after the docs and metadata changes, with the machine shared with other jobs) | 2415 passed, 10 failed, 13 skipped, 9 xfailed, 1 xpassed (251 s) | The same 7 environment failures, plus three timing assertions in modules not touched here: `test_rate_limit_batch` and `test_rate_limit_astream`, and `tracers/test_memory_stream.py::test_queue_for_streaming_via_sync_call`, which missed a 0.15 s tolerance by 37 ms. `test_memory_stream.py` passes when re-run on its own. |
| `libs/text-splitters` | 121 passed, 41 skipped (83 s) | +3 new tests, all passing. No new failures. |

None of the failing tests exercises code changed in this fork. They fail on timing windows, clock resolution, or symlink privileges, as described in the [baseline](#baseline).

Lint and type checks on every changed Python file passed:

- `ruff check` and `ruff format --diff` (ruff from each package's `lint` group);
- `mypy` with the strict `libs/core` configuration, including the changed test files.

`libs/text-splitters` uses `ty` for type checking. Its `typing` group was not installed, because it pulls in PyTorch, transformers, and spaCy (several GB). The change there is a one-line `kwargs.setdefault(...)` per class.

## What was not done, and why

- **Contested or design-level issues of the original project were left alone.** These include `filter_messages` and `invalid_tool_calls` (original issue #41290), where the original maintainers questioned the expected behavior, and `convert_to_openai_messages` dropping invalid tool calls (original issue #41157). The `trim_messages` budget issues (original issues #41250 and #41259) and `add_start_index` positions (original issue #41190) need larger redesigns.
- **The Windows-only test failures were not changed.** Skipping or loosening them would weaken the suite. They are documented instead.
- **`uv.lock` files were not refreshed** (finding 14), to avoid unrelated dependency upgrades.
- **Partner packages, `langchain` (`libs/langchain_v1`), and `langchain-classic` were not modified or re-tested.** Most partner tests need provider credentials.
- **Package names, versions, and PyPI metadata names were kept.** Renaming them would break every import.
- **Links to the original documentation and API reference were kept in the package READMEs**, because they still describe these packages. Social, community, course, and promotional links were removed.
- **The generated `openwiki/` pages were not edited**, because a disabled workflow regenerates them.

## Known limitations

- The fork does not publish packages. Users install from Git or a local path. Because package versions equal the original versions, `pip` may treat the original `langchain-core==1.6.12` from PyPI as already satisfying a requirement. Install the fork's packages explicitly (see the [README](../../README.md#quickstart)).
- The mustache and `merge_message_runs` fixes change behavior that some code could have relied on (rendering outer-scope data, or receiving promoted tool calls). Both old behaviors were wrong, but they are the most visible changes.
- Verification was done on Windows only. Linux and macOS are covered by the unchanged CI workflows once the repository is pushed.

## Recommended next steps

1. Run `uv lock` in `libs/text-splitters` (and check the other packages' locks) so the editable `langchain-core` resolves with its real `langsmith` requirement (finding 14).
2. Make the Windows-sensitive tests portable:
   - skip the symlink tests when `os.symlink` raises `OSError` with `winerror == 1314`;
   - patch the record manager clock in the indexing test;
   - widen the rate-limiter timing windows or use a fake clock.
3. Offer these fixes to the original project. Most correspond to its open issues listed above, so contributing them back would benefit everyone.
4. Follow up on the design-level message issues (`trim_messages` budgeting and invalid tool calls in `convert_to_openai_messages`) with the original project's maintainers.
5. Decide on a distribution strategy, such as private package names or Git tags, before anyone relies on the fork in production.
