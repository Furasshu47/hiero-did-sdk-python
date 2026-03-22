# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""Integration tests for DID create + resolve against a live Hiero network.

These tests require environment variables:
    HEDERA_OPERATOR_ID: Operator account ID (e.g. 0.0.1234)
    HEDERA_OPERATOR_KEY: Operator ECDSA private key (DER hex)
    HEDERA_NETWORK: Network name (default: testnet)

Run with: uv run pytest tests/integration/ -m integration
"""

import os
import time
from pathlib import Path

import pytest
from dotenv import load_dotenv

from hiero_did import DidClient

# Load .env from project root
load_dotenv(Path(__file__).resolve().parents[2] / ".env")

pytestmark = pytest.mark.integration


def _get_client():  # type: ignore[no-untyped-def]
    """Create a configured hiero-sdk-python Client from environment."""
    from hiero_sdk_python import AccountId, Client, Network, PrivateKey

    operator_id = os.environ.get("HEDERA_OPERATOR_ID", "")
    operator_key = os.environ.get("HEDERA_OPERATOR_KEY", "")
    network_name = os.environ.get("HEDERA_NETWORK", "testnet")

    if not operator_id or not operator_key:
        pytest.skip("HEDERA_OPERATOR_ID and HEDERA_OPERATOR_KEY must be set")

    network = Network(network_name)
    client = Client(network)
    client.set_operator(
        AccountId.from_string(operator_id),
        PrivateKey.from_string_ecdsa(operator_key),
    )
    return client, network_name


class TestDidCreateAndResolve:
    """End-to-end DID creation and resolution."""

    def test_create_did(self) -> None:
        client, network = _get_client()
        did_client = DidClient(client, network=network)

        result = did_client.create()

        assert result.did.startswith(f"did:hedera:{network}:")
        assert result.topic_id
        assert result.public_key
        assert result.private_key
        assert result.did_document["@context"] == "https://www.w3.org/ns/did/v1"
        assert len(result.did_document["verificationMethod"]) == 1

    def test_create_and_resolve_did(self) -> None:
        client, network = _get_client()
        did_client = DidClient(client, network=network)

        created = did_client.create()

        # Mirror node needs time to index the message
        time.sleep(10)

        resolved = did_client.resolve(created.did)

        assert resolved.did == created.did
        assert resolved.deactivated is False
        assert resolved.document["id"] == created.did
        assert resolved.messages_processed >= 1
