#!/usr/bin/env python3
# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""Quickstart example: create and resolve a did:hedera identifier.

Prerequisites:
    pip install hiero-did-sdk-python

    Create a .env file with:
        HEDERA_OPERATOR_ID="0.0.xxxxx"
        HEDERA_OPERATOR_KEY="0x..."
        HEDERA_NETWORK="testnet"
"""

import json
import os
import time
from pathlib import Path

from dotenv import load_dotenv
from hiero_sdk_python import AccountId, Client, Network, PrivateKey

from hiero_did import DidClient

# Load .env from project root
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


def main() -> None:
    """Create a DID, then resolve it from the mirror node."""
    # 1. Configure the Hiero client
    operator_id = os.environ["HEDERA_OPERATOR_ID"]
    operator_key = os.environ["HEDERA_OPERATOR_KEY"]
    network_name = os.environ.get("HEDERA_NETWORK", "testnet")

    network = Network(network_name)
    client = Client(network)
    client.set_operator(
        AccountId.from_string(operator_id),
        PrivateKey.from_string_ecdsa(operator_key),
    )

    # 2. Create a DID
    did_client = DidClient(client, network=network_name)
    result = did_client.create()

    print("=== DID Created ===")
    print(f"DID:      {result.did}")
    print(f"Topic:    {result.topic_id}")
    print(f"Document: {json.dumps(result.did_document, indent=2)}")

    # 3. Wait for the mirror node to index the HCS message
    print("\nWaiting 10s for mirror node indexing...")
    time.sleep(10)

    # 4. Resolve the DID
    resolved = did_client.resolve(result.did)

    print("\n=== DID Resolved ===")
    print(f"DID:        {resolved.did}")
    print(f"Active:     {not resolved.deactivated}")
    print(f"Messages:   {resolved.messages_processed}")
    print(f"Document:   {json.dumps(resolved.document, indent=2)}")


if __name__ == "__main__":
    main()
