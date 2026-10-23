# Disabled workflows

GitHub only runs workflows stored in `.github/workflows/`. The files in this folder came from the original project's repository. They were moved here when Cavaleiro Agent Framework was forked, so that nothing in this repository publishes, deploys, or uses credentials under the original project's identity.

The workflows still active in `.github/workflows/` only build, lint, and test. They need nothing beyond the default `GITHUB_TOKEN` with read permissions: `check_diffs.yml` and its reusable `_lint.yml`, `_test.yml`, `_test_pydantic.yml`, `_test_vcr.yml`, and `_compile_integration_test.yml` workflows, plus `check_extras_sync.yml`, `check_versions.yml`, and `pr_lint.yml`.

## Why each workflow is disabled

| Workflow | Reason |
|---|---|
| `_release.yml` | Builds every package, publishes it to TestPyPI and PyPI under the upstream names (`langchain-core`, `langchain`, `langchain-openai`, …), and creates GitHub releases and tags. It also uses about 40 provider API secrets for pre-release integration tests. |
| `check_release_deps.yml` | Part of the PyPI release process: it checks `release(...)` pull requests against the published upstream packages. |
| `integration_tests.yml` | Calls paid model-provider APIs with repository secrets (OpenAI, Anthropic, Azure, AWS, Google, and others), and sends traces to LangSmith with `LANGSMITH_API_KEY`. |
| `codspeed.yml` | Uploads benchmark results to CodSpeed with `CODSPEED_TOKEN`. |
| `openwiki-update.yml` | Runs on a schedule, calls the Anthropic API and LangSmith with secrets, and commits regenerated `openwiki/` pages. |
| `refresh_model_profiles.yml`, `_refresh_model_profiles.yml` | Use a GitHub App (`MODEL_PROFILE_BOT_*` secrets) to open pull requests with refreshed model-profile data. |
| `pr_labeler.yml`, `pr_labeler_backfill.yml`, `tag-external-issues.yml`, `close_unchecked_issues.yml` | Use the upstream organization-membership GitHub App (`ORG_MEMBERSHIP_APP_*` secrets) to label and triage issues and pull requests. |
| `require_issue_link.yml`, `reopen_on_assignment.yml`, `block_fork_main_prs.yml`, `remove_waiting_on_author.yml`, `auto-label-by-package.yml`, `pr_lint_trailer.yml` | Enforce upstream maintainer policy (issue assignment, closing pull requests, organization rulesets and labels) with write permissions. They only run for the `langchain-ai` organization. |
| `bump_uv_pin.yml` | Opens pull requests with write permissions on a schedule. It only runs for the `langchain-ai` organization. |

## How to re-enable one

1. Read the workflow and decide whether this fork needs it. Most of the governance bots only make sense for a large public project.
2. Create your own credentials and add them as repository or environment secrets. Never reuse upstream credentials. For example: your own PyPI trusted publisher, CodSpeed project, LangSmith workspace, or GitHub App.
3. Release workflows: publish under package names you own. The distributions in this repository keep their upstream names (`langchain-core`, `langchain`, `langchain-text-splitters`, …) for import compatibility, and those names on PyPI belong to the upstream project. Rename the distribution in `pyproject.toml` before you publish anything.
4. Replace `github.repository_owner == 'langchain-ai'` conditions with your organization, and `master` with `main`.
5. Move the file back to `.github/workflows/` and run it once with `workflow_dispatch` or on a test branch before relying on it.
