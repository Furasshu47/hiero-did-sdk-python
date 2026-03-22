# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for did_parser module."""

import pytest

from hiero_did.did_parser import DidParser


class TestDidParser:
    """Tests for DidParser.parse()."""

    def test_parse_valid_testnet_did(self) -> None:
        did = "did:hedera:testnet:z6MkubW6fwkWSA97RbKs17MtLgWGHBtShQygUc5SeHueFCaG_0.0.29613327"
        parsed = DidParser.parse(did)

        assert parsed.did == did
        assert parsed.network == "testnet"
        assert parsed.public_key_multibase == "z6MkubW6fwkWSA97RbKs17MtLgWGHBtShQygUc5SeHueFCaG"
        assert parsed.topic_id == "0.0.29613327"

    def test_parse_valid_mainnet_did(self) -> None:
        did = "did:hedera:mainnet:zAbCdEf123456_0.0.100"
        parsed = DidParser.parse(did)

        assert parsed.network == "mainnet"
        assert parsed.topic_id == "0.0.100"

    def test_parse_valid_previewnet_did(self) -> None:
        did = "did:hedera:previewnet:zKey123_0.0.999"
        parsed = DidParser.parse(did)

        assert parsed.network == "previewnet"

    def test_parse_invalid_method(self) -> None:
        with pytest.raises(ValueError, match="Invalid did:hedera format"):
            DidParser.parse("did:example:testnet:zKey_0.0.1")

    def test_parse_missing_topic(self) -> None:
        with pytest.raises(ValueError, match="Invalid did:hedera format"):
            DidParser.parse("did:hedera:testnet:zKey")

    def test_parse_invalid_network(self) -> None:
        with pytest.raises(ValueError, match="Invalid did:hedera format"):
            DidParser.parse("did:hedera:devnet:zKey_0.0.1")

    def test_parse_empty_string(self) -> None:
        with pytest.raises(ValueError, match="Invalid did:hedera format"):
            DidParser.parse("")

    def test_parse_garbage(self) -> None:
        with pytest.raises(ValueError, match="Invalid did:hedera format"):
            DidParser.parse("not-a-did")

    def test_root_key_id(self) -> None:
        did = "did:hedera:testnet:zKey123_0.0.42"
        parsed = DidParser.parse(did)
        assert parsed.root_key_id == "did:hedera:testnet:zKey123_0.0.42#did-root-key"


class TestDidParserIsValid:
    """Tests for DidParser.is_valid()."""

    def test_valid(self) -> None:
        assert DidParser.is_valid("did:hedera:testnet:zKey123_0.0.1") is True

    def test_invalid(self) -> None:
        assert DidParser.is_valid("garbage") is False

    def test_wrong_method(self) -> None:
        assert DidParser.is_valid("did:web:example.com") is False


class TestDidParserBuild:
    """Tests for DidParser.build()."""

    def test_build_valid(self) -> None:
        result = DidParser.build("testnet", "zPubKey123", "0.0.42")
        assert result == "did:hedera:testnet:zPubKey123_0.0.42"

    def test_build_unsupported_network(self) -> None:
        with pytest.raises(ValueError, match="Unsupported network"):
            DidParser.build("devnet", "zKey", "0.0.1")

    def test_build_roundtrip(self) -> None:
        built = DidParser.build("mainnet", "zABC", "0.0.999")
        parsed = DidParser.parse(built)
        assert parsed.network == "mainnet"
        assert parsed.public_key_multibase == "zABC"
        assert parsed.topic_id == "0.0.999"
