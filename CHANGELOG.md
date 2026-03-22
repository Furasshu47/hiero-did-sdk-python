# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2025-03-22

### Added

- `DidClient` for creating and resolving `did:hedera` identifiers
- `DidDocument` model with W3C DID Core compliance
- `DidParser` for parsing and validating `did:hedera` strings
- `HcsDidMessage` for constructing and parsing signed HCS DID events
- Unit tests for all modules
- Integration test scaffold for Hiero Solo / testnet
- GitHub Actions CI with Python 3.10-3.13 matrix
- Apache 2.0 license
- CONTRIBUTING.md with DCO and GPG signing requirements
