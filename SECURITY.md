# Security policy

Cavaleiro Agent Framework is used to build applications that send untrusted text to language models, run tools chosen by a model, load prompts and serialized objects, and fetch remote content. A flaw in these paths can affect every application built on it, so security reports are taken seriously.

## Reporting a vulnerability

**Please do not open a public issue.** Report privately through GitHub:

1. Go to the repository's **Security** tab.
2. Select **Report a vulnerability** (private vulnerability reporting), or open the form directly at <https://github.com/cavaleiro-ai/cavaleiro-agent-framework/security/advisories/new>.

Include the affected package, module, and version or commit, a minimal reproduction, and the impact you expect. Redact API keys, tokens, and private data.

## Vulnerabilities in the original code

Most of the code in this repository comes from the original project. If the vulnerability is also present in the original packages published on PyPI, say so in your report. You may also report it to the original project through its own security policy, so its users are protected too.

## What is in scope

- Code in this repository, including changes made by Cavaleiro Agent Framework (see the [changelog](CHANGELOG.md)) and integration issues that only affect this fork.
- Especially sensitive areas:
  - Prompt templates (f-string, mustache, Jinja2) and prompt loading from files.
  - Deserialization (`langchain_core.load`).
  - Output parsers that handle XML or JSON.
  - Tool argument parsing and execution.
  - The SSRF protections in `langchain_core._security`.
  - Anything that could leak secrets into logs, traces, or prompts.
- The CI workflows in `.github/workflows/`, for example excessive permissions or script injection.

## What is out of scope

- Vulnerabilities in third-party model providers, vector stores, or other services an integration talks to. Report those to the provider.
- Code you wrote in an application built with this framework, including prompt injection that the application does not defend against.
- Workflows in `.github/workflows-disabled/`, which do not run.

## What to expect

This is a community-maintained project, so timelines are best effort:

- Acknowledgement of your report within **7 days**.
- An initial assessment, and a plan or a request for more information, within **14 days**.
- A fix on `main` and a published advisory crediting you (unless you prefer to stay anonymous) once the issue is resolved.

## Supported versions

Only the latest release and the `main` branch receive security fixes.
