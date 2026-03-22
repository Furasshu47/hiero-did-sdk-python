# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""Parsing and validation for `did:hedera` identifiers."""

from __future__ import annotations

import re
from dataclasses import dataclass

# did:hedera:<network>:<base58-pubkey>_<shard>.<realm>.<topic>
_DID_PATTERN = re.compile(r"^did:hedera:(mainnet|testnet|previewnet):([A-Za-z0-9]+)_(\d+\.\d+\.\d+)$")

SUPPORTED_NETWORKS = frozenset({"mainnet", "testnet", "previewnet"})


@dataclass(frozen=True)
class ParsedDid:
    """A parsed `did:hedera` identifier."""

    did: str
    network: str
    public_key_multibase: str
    topic_id: str

    @property
    def root_key_id(self) -> str:
        """Return the fragment identifier for the DID root key."""
        return f"{self.did}#did-root-key"


class DidParser:
    """Utilities for parsing and validating `did:hedera` strings."""

    @staticmethod
    def parse(did: str) -> ParsedDid:
        """Parse a `did:hedera` string into its components.

        Args:
            did: A DID string in the format `did:hedera:<network>:<pubkey>_<topic-id>`.

        Returns:
            A ParsedDid with extracted components.

        Raises:
            ValueError: If the DID string does not match the expected format.
        """
        match = _DID_PATTERN.match(did)
        if not match:
            raise ValueError(
                f"Invalid did:hedera format: '{did}'. "
                f"Expected: did:hedera:<network>:<base58-pubkey>_<shard.realm.topic>"
            )

        network, public_key, topic_id = match.groups()
        return ParsedDid(
            did=did,
            network=network,
            public_key_multibase=public_key,
            topic_id=topic_id,
        )

    @staticmethod
    def is_valid(did: str) -> bool:
        """Check whether a string is a valid `did:hedera` identifier.

        Args:
            did: The string to validate.

        Returns:
            True if valid, False otherwise.
        """
        return _DID_PATTERN.match(did) is not None

    @staticmethod
    def build(network: str, public_key_multibase: str, topic_id: str) -> str:
        """Construct a `did:hedera` string from its components.

        Args:
            network: The Hiero network name (mainnet, testnet, previewnet).
            public_key_multibase: The base58btc-encoded public key.
            topic_id: The HCS topic ID in shard.realm.num format.

        Returns:
            The fully-formed DID string.

        Raises:
            ValueError: If the network is not supported.
        """
        if network not in SUPPORTED_NETWORKS:
            raise ValueError(
                f"Unsupported network '{network}'. Must be one of: {', '.join(sorted(SUPPORTED_NETWORKS))}"
            )
        return f"did:hedera:{network}:{public_key_multibase}_{topic_id}"
