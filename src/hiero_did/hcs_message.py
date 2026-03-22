# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""HCS message format for `did:hedera` DID operations.

All DID state changes are recorded as signed messages on a Hedera Consensus Service topic.
This module handles constructing, signing, and parsing those messages.
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from hiero_sdk_python import PrivateKey


class DidOperation(str, Enum):
    """DID operations that can be published to HCS."""

    CREATE = "create"
    UPDATE = "update"
    REVOKE = "revoke"
    DELETE = "delete"


@dataclass
class HcsDidMessage:
    """A signed HCS message representing a DID operation.

    Follows the did:hedera method specification message format:
    ```json
    {
      "message": {
        "operation": "create",
        "did": "did:hedera:testnet:...",
        "event": "<base64-encoded-event>",
        "timestamp": "2024-01-01T12:00:00.000Z"
      },
      "signature": "<base64-encoded-signature>"
    }
    ```
    """

    operation: DidOperation
    did: str
    event: dict[str, Any]
    timestamp: str
    signature: bytes | None = None

    @classmethod
    def create_did_owner_event(
        cls,
        did: str,
        public_key_multibase: str,
        private_key: PrivateKey,
    ) -> HcsDidMessage:
        """Build and sign a DID create message with a DIDOwner event.

        Args:
            did: The DID string being created.
            public_key_multibase: The base58btc-encoded public key.
            private_key: The Ed25519 private key for signing.

        Returns:
            A signed HcsDidMessage ready for submission to HCS.
        """
        event = {
            "DIDOwner": {
                "id": did,
                "type": "Ed25519VerificationKey2018",
                "controller": did,
                "publicKeyMultibase": public_key_multibase,
            }
        }
        msg = cls(
            operation=DidOperation.CREATE,
            did=did,
            event=event,
            timestamp=_utc_now_iso(),
        )
        msg.sign(private_key)
        return msg

    @classmethod
    def create_delete_event(cls, did: str, private_key: PrivateKey) -> HcsDidMessage:
        """Build and sign a DID delete (deactivate) message.

        Args:
            did: The DID string to deactivate.
            private_key: The Ed25519 private key for signing.

        Returns:
            A signed HcsDidMessage ready for submission to HCS.
        """
        msg = cls(
            operation=DidOperation.DELETE,
            did=did,
            event={},
            timestamp=_utc_now_iso(),
        )
        msg.sign(private_key)
        return msg

    def sign(self, private_key: PrivateKey) -> None:
        """Sign the message attributes with the given private key."""
        message_bytes = self._message_bytes()
        self.signature = private_key.sign(message_bytes)

    def to_json(self) -> str:
        """Serialize the full signed message to JSON for HCS submission."""
        encoded_event = base64.b64encode(json.dumps(self.event).encode("utf-8")).decode("utf-8")

        message_attr = {
            "operation": self.operation.value,
            "did": self.did,
            "event": encoded_event,
            "timestamp": self.timestamp,
        }

        signature_b64 = ""
        if self.signature:
            signature_b64 = base64.b64encode(self.signature).decode("utf-8")

        return json.dumps(
            {
                "message": message_attr,
                "signature": signature_b64,
            }
        )

    @classmethod
    def from_mirror_message(cls, raw_base64: str) -> HcsDidMessage | None:
        """Parse an HCS message retrieved from a mirror node.

        Args:
            raw_base64: The base64-encoded message content from the mirror node.

        Returns:
            A parsed HcsDidMessage, or None if the message is malformed.
        """
        try:
            decoded = base64.b64decode(raw_base64).decode("utf-8")
            msg_json = json.loads(decoded)
            message_attr = msg_json.get("message", {})

            operation_str = message_attr.get("operation", "")
            try:
                operation = DidOperation(operation_str)
            except ValueError:
                return None

            event: dict[str, Any] = {}
            event_b64 = message_attr.get("event")
            if event_b64:
                event_str = base64.b64decode(event_b64).decode("utf-8")
                event = json.loads(event_str)

            signature = None
            sig_b64 = msg_json.get("signature")
            if sig_b64:
                signature = base64.b64decode(sig_b64)

            return cls(
                operation=operation,
                did=message_attr.get("did", ""),
                event=event,
                timestamp=message_attr.get("timestamp", ""),
                signature=signature,
            )
        except Exception:
            return None

    def _message_bytes(self) -> bytes:
        """Compute the canonical message bytes for signing."""
        encoded_event = base64.b64encode(json.dumps(self.event).encode("utf-8")).decode("utf-8")

        message_attr = {
            "operation": self.operation.value,
            "did": self.did,
            "event": encoded_event,
            "timestamp": self.timestamp,
        }
        return json.dumps(message_attr, separators=(",", ":")).encode("utf-8")


def _utc_now_iso() -> str:
    """Return the current UTC time in ISO 8601 format with millisecond precision."""
    now = datetime.now(timezone.utc)
    return now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
