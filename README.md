# hiero-did-sdk-python

A Python SDK for creating and resolving [W3C Decentralized Identifiers (DIDs)](https://www.w3.org/TR/did-core/) on [Hiero](https://hiero.org/) / [Hedera](https://hedera.com/) networks using the [`did:hedera` method](https://github.com/hashgraph/did-method).

[![CI](https://github.com/baseramp/hiero-did-sdk-python/actions/workflows/ci.yml/badge.svg)](https://github.com/baseramp/hiero-did-sdk-python/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

## What it does

This library wraps the [hiero-sdk-python](https://github.com/hiero-ledger/hiero-sdk-python) to provide high-level, typed utilities for `did:hedera` operations:

- **Create** a DID — generates Ed25519 keys, creates an HCS topic, publishes a signed DIDOwner event
- **Resolve** a DID — queries the mirror node, replays HCS messages, reconstructs the DID Document

All DID state is stored on-chain via the Hedera Consensus Service (HCS) as an append-only event log, following the [did:hedera method specification](https://github.com/hashgraph/did-method).

## Installation

```bash
pip install hiero-did-sdk-python
```

Or with [UV](https://docs.astral.sh/uv/):

```bash
uv add hiero-did-sdk-python
```

## Quickstart

```python
import os
from hiero_sdk_python import AccountId, Client, Network, PrivateKey
from hiero_did import DidClient

# Configure the Hiero client
network = Network("testnet")
client = Client(network)
client.set_operator(
    AccountId.from_string(os.environ["HEDERA_OPERATOR_ID"]),
    PrivateKey.from_string_ecdsa(os.environ["HEDERA_OPERATOR_KEY"]),
)

# Create a DID
did_client = DidClient(client, network="testnet")
result = did_client.create()
print(result.did)        # did:hedera:testnet:z6Mk..._0.0.12345
print(result.topic_id)   # 0.0.12345
print(result.public_key) # z6Mk...

# Resolve a DID (after mirror node indexes the message)
import time; time.sleep(10)
resolved = did_client.resolve(result.did)
print(resolved.document)  # W3C DID Document
```

## API Reference

### `DidClient(client, network="testnet", mirror_url=None)`

Main entry point. Wraps a `hiero_sdk_python.Client`.

| Method | Description |
|--------|-------------|
| `create() -> DidResult` | Create a new DID with generated Ed25519 keys |
| `resolve(did: str) -> ResolveResult` | Resolve a DID from the mirror node |

### `DidResult`

| Field | Type | Description |
|-------|------|-------------|
| `did` | `str` | The full DID string |
| `did_document` | `dict` | W3C DID Document |
| `topic_id` | `str` | HCS topic ID |
| `public_key` | `str` | Base58btc-encoded public key |
| `private_key` | `str` | Private key string (store securely!) |

### `ResolveResult`

| Field | Type | Description |
|-------|------|-------------|
| `did` | `str` | The resolved DID string |
| `document` | `dict` | Reconstructed W3C DID Document |
| `deactivated` | `bool` | Whether the DID has been deleted |
| `messages_processed` | `int` | Number of HCS messages replayed |

### `DidParser`

Static utility for parsing and validating `did:hedera` strings.

```python
from hiero_did import DidParser

parsed = DidParser.parse("did:hedera:testnet:zKey_0.0.42")
parsed.network          # "testnet"
parsed.public_key_multibase  # "zKey"
parsed.topic_id         # "0.0.42"

DidParser.is_valid("did:hedera:testnet:zKey_0.0.42")  # True
DidParser.build("testnet", "zKey", "0.0.42")  # "did:hedera:testnet:zKey_0.0.42"
```

### `DidDocument`

W3C DID Document model with serialization.

```python
from hiero_did import DidDocument

doc = DidDocument.create_root("did:hedera:testnet:zKey_0.0.42", "zKey")
doc.add_service("website", "LinkedDomains", "https://example.com")
print(doc.to_dict())
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `HEDERA_OPERATOR_ID` | Operator account ID (e.g. `0.0.1234`) |
| `HEDERA_OPERATOR_KEY` | Operator ECDSA private key (DER hex) |
| `HEDERA_NETWORK` | Network name: `testnet`, `mainnet`, or `previewnet` |

## Development

```bash
git clone https://github.com/baseramp/hiero-did-sdk-python.git
cd hiero-did-sdk-python
uv sync --all-extras --dev

# Run tests
uv run pytest tests/unit/ -v

# Lint & format
uv run ruff check src/ tests/
uv run ruff format src/ tests/
uv run mypy src/
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for full contribution guidelines including DCO sign-off and GPG signing requirements.

## Architecture

```
did:hedera:testnet:z6Mk..._0.0.12345
                   ^^^^^^^ ^^^^^^^^^^
                   Ed25519  HCS Topic
                   PubKey   (event log)
```

DIDs on Hedera use the **Hedera Consensus Service (HCS)** as an append-only event log. Each DID is associated with an HCS topic. The current DID Document state is reconstructed by replaying all signed messages from the topic via a mirror node.

This follows the [did:hedera method specification](https://github.com/hashgraph/did-method) which conforms to [W3C DID Core 1.0](https://www.w3.org/TR/did-core/).

## License

[Apache License 2.0](LICENSE)
