# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for did_client module (resolution logic, no network calls)."""

import base64
import json
from unittest.mock import MagicMock, patch

import pytest

from hiero_did.did_client import DidClient


def _make_mirror_message(operation: str, did: str, event: dict) -> dict:
    """Helper: build a mirror-node-style message dict."""
    encoded_event = base64.b64encode(json.dumps(event).encode()).decode()
    inner = {
        "message": {
            "operation": operation,
            "did": did,
            "event": encoded_event,
            "timestamp": "2024-01-01T00:00:00.000Z",
        },
        "signature": base64.b64encode(b"sig").decode(),
    }
    return {
        "consensus_timestamp": "1704067200.000000000",
        "message": base64.b64encode(json.dumps(inner).encode()).decode(),
    }


class TestDidClientResolve:
    """Tests for DidClient.resolve() using mocked mirror node responses."""

    def setup_method(self) -> None:
        self.mock_client = MagicMock()
        self.did_client = DidClient(self.mock_client, network="testnet")
        self.did = "did:hedera:testnet:zPubKey123_0.0.42"

    @patch("hiero_did.did_client.requests.get")
    def test_resolve_create_only(self, mock_get: MagicMock) -> None:
        create_msg = _make_mirror_message(
            "create",
            self.did,
            {
                "DIDOwner": {
                    "id": self.did,
                    "type": "Ed25519VerificationKey2018",
                    "controller": self.did,
                    "publicKeyMultibase": "zPubKey123",
                }
            },
        )
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"messages": [create_msg], "links": {}},
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = self.did_client.resolve(self.did)

        assert result.did == self.did
        assert result.deactivated is False
        assert result.document["id"] == self.did
        assert result.messages_processed == 1
        assert len(result.document["verificationMethod"]) == 1

    @patch("hiero_did.did_client.requests.get")
    def test_resolve_deleted_did(self, mock_get: MagicMock) -> None:
        create_msg = _make_mirror_message(
            "create",
            self.did,
            {
                "DIDOwner": {
                    "id": self.did,
                    "type": "Ed25519VerificationKey2018",
                    "controller": self.did,
                    "publicKeyMultibase": "zPubKey123",
                }
            },
        )
        delete_msg = _make_mirror_message("delete", self.did, {})
        delete_msg["consensus_timestamp"] = "1704067201.000000000"

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"messages": [create_msg, delete_msg], "links": {}},
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = self.did_client.resolve(self.did)

        assert result.deactivated is True
        assert result.document == {}

    @patch("hiero_did.did_client.requests.get")
    def test_resolve_no_messages_raises(self, mock_get: MagicMock) -> None:
        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"messages": [], "links": {}},
        )
        mock_get.return_value.raise_for_status = MagicMock()

        with pytest.raises(ValueError, match="Could not resolve DID"):
            self.did_client.resolve(self.did)

    @patch("hiero_did.did_client.requests.get")
    def test_resolve_invalid_did_format(self, mock_get: MagicMock) -> None:
        with pytest.raises(ValueError, match="Invalid did:hedera format"):
            self.did_client.resolve("did:web:example.com")

    @patch("hiero_did.did_client.requests.get")
    def test_resolve_with_pagination(self, mock_get: MagicMock) -> None:
        create_msg = _make_mirror_message(
            "create",
            self.did,
            {
                "DIDOwner": {
                    "id": self.did,
                    "type": "Ed25519VerificationKey2018",
                    "controller": self.did,
                    "publicKeyMultibase": "zPubKey123",
                }
            },
        )
        page1_resp = MagicMock(
            status_code=200,
            json=lambda: {
                "messages": [create_msg],
                "links": {"next": "/api/v1/topics/0.0.42/messages?sequencenumber=gt:1"},
            },
        )
        page1_resp.raise_for_status = MagicMock()

        page2_resp = MagicMock(
            status_code=200,
            json=lambda: {"messages": [], "links": {}},
        )
        page2_resp.raise_for_status = MagicMock()

        mock_get.side_effect = [page1_resp, page2_resp]

        result = self.did_client.resolve(self.did)
        assert result.did == self.did
        assert mock_get.call_count == 2

    @patch("hiero_did.did_client.requests.get")
    def test_resolve_with_update(self, mock_get: MagicMock) -> None:
        create_msg = _make_mirror_message(
            "create",
            self.did,
            {
                "DIDOwner": {
                    "id": self.did,
                    "type": "Ed25519VerificationKey2018",
                    "controller": self.did,
                    "publicKeyMultibase": "zPubKey123",
                }
            },
        )
        update_msg = _make_mirror_message(
            "update",
            self.did,
            {
                "Service": {
                    "id": "linked-domain",
                    "type": "LinkedDomains",
                    "serviceEndpoint": "https://example.com",
                }
            },
        )
        update_msg["consensus_timestamp"] = "1704067201.000000000"

        mock_get.return_value = MagicMock(
            status_code=200,
            json=lambda: {"messages": [create_msg, update_msg], "links": {}},
        )
        mock_get.return_value.raise_for_status = MagicMock()

        result = self.did_client.resolve(self.did)
        assert "service" in result.document
        assert result.messages_processed == 2
