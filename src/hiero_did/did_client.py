# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""High-level client for creating and resolving `did:hedera` identifiers."""

from __future__ import annotations

import logging
from typing import Any

import multibase
import requests
from hiero_sdk_python import Client, PrivateKey, TopicCreateTransaction, TopicMessageSubmitTransaction

from hiero_did.did_document import DidDocument
from hiero_did.did_parser import DidParser
from hiero_did.hcs_message import DidOperation, HcsDidMessage
from hiero_did.types import DidResult, ResolveResult

logger = logging.getLogger(__name__)

_MIRROR_URLS: dict[str, str] = {
    "mainnet": "https://mainnet.mirrornode.hedera.com",
    "testnet": "https://testnet.mirrornode.hedera.com",
    "previewnet": "https://previewnet.mirrornode.hedera.com",
}


class DidClient:
    """Client for `did:hedera` DID operations.

    Wraps the hiero-sdk-python Client to provide high-level DID
    create and resolve operations.

    Example:
        ```python
        from hiero_sdk_python import Client, Network, AccountId, PrivateKey
        from hiero_did import DidClient

        network = Network("testnet")
        client = Client(network)
        client.set_operator(
            AccountId.from_string("0.0.1234"),
            PrivateKey.from_string_ecdsa("302e..."),
        )

        did_client = DidClient(client, network="testnet")

        # Create a DID
        result = did_client.create()
        print(result.did)

        # Resolve a DID
        resolved = did_client.resolve(result.did)
        print(resolved.document)
        ```
    """

    def __init__(
        self,
        client: Client,
        network: str = "testnet",
        mirror_url: str | None = None,
    ) -> None:
        """Initialize the DID client.

        Args:
            client: A configured hiero-sdk-python Client with an operator set.
            network: The Hiero network name (mainnet, testnet, previewnet).
            mirror_url: Override the mirror node URL. If None, uses the default for the network.
        """
        self._client = client
        self._network = network
        self._mirror_url = mirror_url or _MIRROR_URLS.get(network, _MIRROR_URLS["testnet"])

    @property
    def network(self) -> str:
        """The Hiero network this client targets."""
        return self._network

    def create(self) -> DidResult:
        """Create a new `did:hedera` identifier.

        Generates an Ed25519 keypair, creates an HCS topic as the DID event log,
        and publishes a signed DIDOwner create event.

        Returns:
            A DidResult containing the DID string, document, keys, and topic ID.
        """
        private_key = PrivateKey.generate("Ed25519")
        public_key = private_key.public_key()

        public_key_multibase = multibase.encode("base58btc", public_key.to_bytes_ed25519()).decode("utf-8")

        logger.info("Creating HCS topic for DID event log...")
        receipt = TopicCreateTransaction().execute(self._client)
        topic_id = str(receipt.topic_id)

        did_str = DidParser.build(self._network, public_key_multibase, topic_id)

        document = DidDocument.create_root(did_str, public_key_multibase)

        hcs_message = HcsDidMessage.create_did_owner_event(
            did=did_str,
            public_key_multibase=public_key_multibase,
            private_key=private_key,
        )

        logger.info("Publishing DID create event to HCS topic %s...", topic_id)
        TopicMessageSubmitTransaction(
            topic_id=receipt.topic_id,
            message=hcs_message.to_json(),
        ).execute(self._client)

        logger.info("DID created: %s", did_str)

        return DidResult(
            did=did_str,
            did_document=document.to_dict(),
            topic_id=topic_id,
            public_key=public_key_multibase,
            private_key=private_key.to_string(),
            network=self._network,
        )

    def resolve(self, did: str) -> ResolveResult:
        """Resolve a `did:hedera` identifier to its DID Document.

        Queries the mirror node for all HCS messages on the DID's topic,
        replays them in consensus order, and reconstructs the current
        DID Document state.

        Args:
            did: The DID string to resolve.

        Returns:
            A ResolveResult containing the resolved document and metadata.

        Raises:
            ValueError: If the DID format is invalid or cannot be resolved.
        """
        parsed = DidParser.parse(did)
        messages = self._fetch_topic_messages(parsed.topic_id)

        messages.sort(key=lambda m: m.get("consensus_timestamp", ""))

        document: DidDocument | None = None
        deactivated = False
        count = 0

        for msg in messages:
            raw_b64 = msg.get("message")
            if not raw_b64:
                continue

            hcs_msg = HcsDidMessage.from_mirror_message(raw_b64)
            if hcs_msg is None:
                continue

            count += 1

            if hcs_msg.operation == DidOperation.CREATE:
                document = self._apply_create(did, hcs_msg)
            elif hcs_msg.operation == DidOperation.UPDATE and document is not None:
                document = self._apply_update(document, hcs_msg)
            elif hcs_msg.operation == DidOperation.DELETE:
                document = None
                deactivated = True

        if document is None:
            if deactivated:
                return ResolveResult(
                    did=did,
                    document={},
                    topic_id=parsed.topic_id,
                    network=parsed.network,
                    deactivated=True,
                    messages_processed=count,
                )
            raise ValueError(f"Could not resolve DID: {did}")

        return ResolveResult(
            did=did,
            document=document.to_dict(),
            topic_id=parsed.topic_id,
            network=parsed.network,
            deactivated=False,
            messages_processed=count,
        )

    def _fetch_topic_messages(self, topic_id: str) -> list[dict[str, Any]]:
        """Fetch all messages from a mirror node topic with pagination."""
        messages: list[dict[str, Any]] = []
        url: str | None = f"{self._mirror_url}/api/v1/topics/{topic_id}/messages"

        while url:
            resp = requests.get(url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            messages.extend(data.get("messages", []))

            next_link = data.get("links", {}).get("next")
            url = f"{self._mirror_url}{next_link}" if next_link else None

        return messages

    @staticmethod
    def _apply_create(did: str, msg: HcsDidMessage) -> DidDocument | None:
        """Apply a create operation to initialize a DID Document."""
        owner = msg.event.get("DIDOwner")
        if not owner:
            return None
        public_key = owner.get("publicKeyMultibase", "")
        return DidDocument.create_root(did, public_key)

    @staticmethod
    def _apply_update(document: DidDocument, msg: HcsDidMessage) -> DidDocument:
        """Apply an update operation to modify an existing DID Document."""
        from hiero_did.did_document import VerificationMethod

        if "VerificationMethod" in msg.event:
            vm_data = msg.event["VerificationMethod"]
            method = VerificationMethod.from_dict(vm_data)
            document.add_verification_method(method)

        if "Service" in msg.event:
            svc = msg.event["Service"]
            document.add_service(
                service_id=svc.get("id", ""),
                service_type=svc.get("type", ""),
                endpoint=svc.get("serviceEndpoint", ""),
            )

        return document
