# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""Shared type definitions for hiero-did-sdk."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class DidResult:
    """Result returned after creating a DID."""

    did: str
    did_document: dict[str, Any]
    topic_id: str
    public_key: str
    private_key: str
    network: str = "testnet"


@dataclass
class ResolveResult:
    """Result of resolving a DID."""

    did: str
    document: dict[str, Any]
    topic_id: str
    network: str
    deactivated: bool = False
    messages_processed: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
