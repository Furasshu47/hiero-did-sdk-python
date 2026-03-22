# Contributing to hiero-did-sdk-python

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing.

## Code of Conduct

This project follows the [Contributor Covenant Code of Conduct](https://www.contributor-covenant.org/version/2/1/code_of_conduct/). By participating, you are expected to uphold this code.

## Developer Certificate of Origin (DCO)

All contributions must be signed off in compliance with the [Developer Certificate of Origin (DCO)](https://developercertificate.org/). This means every commit must contain a `Signed-off-by` line:

```
Signed-off-by: Your Name <your.email@example.com>
```

Use `git commit -s` to add this automatically.

## GPG-Signed Commits

We require GPG-signed commits. Configure Git:

```bash
git config commit.gpgsign true
```

## Getting Started

### Prerequisites

- Python 3.10+
- [UV](https://docs.astral.sh/uv/) package manager

### Setup

```bash
git clone https://github.com/baseramp/hiero-did-sdk-python.git
cd hiero-did-sdk-python
uv sync --all-extras --dev
```

### Running Tests

```bash
# Unit tests
uv run pytest tests/unit/ -v

# Integration tests (requires Hedera testnet credentials)
export HEDERA_OPERATOR_ID="0.0.xxxxx"
export HEDERA_OPERATOR_KEY="302e..."
uv run pytest tests/integration/ -v -m integration
```

### Linting & Formatting

```bash
uv run ruff check src/ tests/      # Lint
uv run ruff format src/ tests/     # Format
uv run mypy src/                   # Type check
```

## Pull Request Process

1. Fork the repository and create a feature branch from `main`.
2. Write tests for any new functionality.
3. Ensure all tests pass and linting is clean.
4. Update `CHANGELOG.md` under `[Unreleased]`.
5. Submit a PR targeting `main` with a clear description.
6. All commits must be signed (`-s` for DCO, `-S` for GPG).

## Versioning

This project uses [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking API changes
- **MINOR**: Backward-compatible new features
- **PATCH**: Bug fixes

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
