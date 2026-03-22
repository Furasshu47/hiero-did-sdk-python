# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for hcs_message module."""

import base64
import json

from hiero_did.hcs_message import DidOperation, HcsDidMessage


class TestHcsDidMessage:
    """Tests for HcsDidMessage."""

    def test_to_json_structure(self) -> None:
        msg = HcsDidMessage(
            operation=DidOperation.CREATE,
            did="did:hedera:testnet:zKey_0.0.1",
            event={"DIDOwner": {"id": "did:hedera:testnet:zKey_0.0.1"}},
            timestamp="2024-01-01T00:00:00.000Z",
            signature=b"fakesig",
        )
        result = json.loads(msg.to_json())

        assert "message" in result
        assert "signature" in result
        assert result["message"]["operation"] == "create"
        assert result["message"]["did"] == "did:hedera:testnet:zKey_0.0.1"

        # Event should be base64-encoded
        event_decoded = json.loads(base64.b64decode(result["message"]["event"]))
        assert "DIDOwner" in event_decoded

    def test_from_mirror_message_valid(self) -> None:
        inner = {
            "message": {
                "operation": "create",
                "did": "did:hedera:testnet:zKey_0.0.1",
                "event": base64.b64encode(json.dumps({"DIDOwner": {"id": "test"}}).encode()).decode(),
                "timestamp": "2024-01-01T00:00:00.000Z",
            },
            "signature": base64.b64encode(b"sig").decode(),
        }
        raw_b64 = base64.b64encode(json.dumps(inner).encode()).decode()

        parsed = HcsDidMessage.from_mirror_message(raw_b64)

        assert parsed is not None
        assert parsed.operation == DidOperation.CREATE
        assert parsed.did == "did:hedera:testnet:zKey_0.0.1"
        assert "DIDOwner" in parsed.event

    def test_from_mirror_message_invalid_operation(self) -> None:
        inner = {
            "message": {
                "operation": "invalid_op",
                "did": "did:hedera:testnet:zKey_0.0.1",
                "event": base64.b64encode(b"{}").decode(),
                "timestamp": "2024-01-01T00:00:00.000Z",
            },
            "signature": "",
        }
        raw_b64 = base64.b64encode(json.dumps(inner).encode()).decode()

        result = HcsDidMessage.from_mirror_message(raw_b64)
        assert result is None

    def test_from_mirror_message_garbage(self) -> None:
        result = HcsDidMessage.from_mirror_message("not-valid-base64!!!")
        assert result is None

    def test_delete_event_structure(self) -> None:
        msg = HcsDidMessage(
            operation=DidOperation.DELETE,
            did="did:hedera:testnet:zKey_0.0.1",
            event={},
            timestamp="2024-01-01T00:00:00.000Z",
            signature=b"sig",
        )
        result = json.loads(msg.to_json())
        assert result["message"]["operation"] == "delete"

    def test_all_operations_have_values(self) -> None:
        assert DidOperation.CREATE.value == "create"
        assert DidOperation.UPDATE.value == "update"
        assert DidOperation.REVOKE.value == "revoke"
        assert DidOperation.DELETE.value == "delete"
