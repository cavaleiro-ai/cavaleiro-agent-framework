# langchain-model-profiles

[![PyPI - Version](https://img.shields.io/pypi/v/langchain-model-profiles?label=%20)](https://pypi.org/project/langchain-model-profiles/#history)
[![PyPI - License](https://img.shields.io/pypi/l/langchain-model-profiles)](https://opensource.org/licenses/MIT)
[![PyPI - Downloads](https://img.shields.io/pepy/dt/langchain-model-profiles)](https://pypistats.org/packages/langchain-model-profiles)

> [!WARNING]
> This package is currently in development and the API is subject to change.

CLI tool for updating model profile data in Cavaleiro Agent Framework integration packages.

## Quick Install

```bash
uv add langchain-model-profiles
```

## 🤔 What is this?

`langchain-model-profiles` is a CLI tool for fetching and updating model capability data from [models.dev](https://github.com/sst/models.dev) for use in Cavaleiro Agent Framework integration packages.

Cavaleiro Agent Framework chat models expose a `.profile` field that provides programmatic access to model capabilities such as context window sizes, supported modalities, tool calling, structured output, and more. This CLI tool helps maintainers keep that data up-to-date.

## Data sources

This package is built on top of the excellent work by the [models.dev](https://github.com/sst/models.dev) project, an open source initiative that provides model capability data.

Cavaleiro Agent Framework model profiles augment the data from models.dev with some additional fields. We intend to keep this aligned with the upstream project as it evolves.

## 📖 Documentation

For full documentation, see the [API reference](https://reference.langchain.com/python/langchain_model_profiles/). For conceptual guides, tutorials, and examples on using Cavaleiro Agent Framework, see the [documentation](https://docs.langchain.com/oss/python/langchain/overview).

## Usage

Update model profile data for a specific provider:

```bash
langchain-profiles refresh --provider anthropic --data-dir ./langchain_anthropic/data
```

This downloads the latest model data from models.dev, merges it with any augmentations defined in `profile_augmentations.toml`, and generates a `profiles.py` file.

## Resources

- [Code of Conduct](https://github.com/cavaleiro-ai/cavaleiro-agent-framework/blob/main/CODE_OF_CONDUCT.md) — community guidelines and standards
