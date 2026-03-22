# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""Hiero DID SDK — create and resolve `did:hedera` identifiers on Hiero networks."""

from hiero_did.did_client import DidClient
from hiero_did.did_document import DidDocument, VerificationMethod
from hiero_did.did_parser import DidParser, ParsedDid
from hiero_did.hcs_message import DidOperation, HcsDidMessage

__all__ = [
    "DidClient",
    "DidDocument",
    "VerificationMethod",
    "DidParser",
    "ParsedDid",
    "HcsDidMessage",
    "DidOperation",
]
