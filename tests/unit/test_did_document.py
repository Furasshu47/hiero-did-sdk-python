# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""Unit tests for did_document module."""

from hiero_did.did_document import DID_CONTEXT, DidDocument, VerificationMethod


class TestDidDocument:
    """Tests for DidDocument."""

    def test_create_root(self) -> None:
        did = "did:hedera:testnet:zPubKey_0.0.1"
        doc = DidDocument.create_root(did, "zPubKey")

        assert doc.id == did
        assert len(doc.verification_methods) == 1
        assert doc.verification_methods[0].public_key_multibase == "zPubKey"
        assert doc.authentication == [f"{did}#did-root-key"]
        assert doc.assertion_method == [f"{did}#did-root-key"]

    def test_to_dict_structure(self) -> None:
        did = "did:hedera:testnet:zKey_0.0.42"
        doc = DidDocument.create_root(did, "zKey")
        d = doc.to_dict()

        assert d["@context"] == DID_CONTEXT
        assert d["id"] == did
        assert len(d["verificationMethod"]) == 1
        assert d["verificationMethod"][0]["publicKeyMultibase"] == "zKey"
        assert d["verificationMethod"][0]["type"] == "Ed25519VerificationKey2018"
        assert d["verificationMethod"][0]["controller"] == did
        assert "service" not in d

    def test_to_dict_with_service(self) -> None:
        did = "did:hedera:testnet:zKey_0.0.42"
        doc = DidDocument.create_root(did, "zKey")
        doc.add_service("linked-domain", "LinkedDomains", "https://example.com")
        d = doc.to_dict()

        assert len(d["service"]) == 1
        assert d["service"][0]["type"] == "LinkedDomains"
        assert d["service"][0]["serviceEndpoint"] == "https://example.com"

    def test_roundtrip_serialization(self) -> None:
        did = "did:hedera:testnet:zKey_0.0.42"
        doc = DidDocument.create_root(did, "zKey")
        doc.add_service("svc1", "SomeType", "https://example.com")

        serialized = doc.to_dict()
        restored = DidDocument.from_dict(serialized)

        assert restored.id == doc.id
        assert len(restored.verification_methods) == len(doc.verification_methods)
        assert restored.authentication == doc.authentication
        assert restored.assertion_method == doc.assertion_method

    def test_add_verification_method(self) -> None:
        did = "did:hedera:testnet:zKey_0.0.42"
        doc = DidDocument.create_root(did, "zKey")

        new_method = VerificationMethod(
            id=f"{did}#key-2",
            type="Ed25519VerificationKey2018",
            controller=did,
            public_key_multibase="zOtherKey",
        )
        doc.add_verification_method(new_method)

        assert len(doc.verification_methods) == 2
        assert doc.verification_methods[1].id == f"{did}#key-2"


class TestVerificationMethod:
    """Tests for VerificationMethod."""

    def test_to_dict(self) -> None:
        vm = VerificationMethod(
            id="did:hedera:testnet:zKey_0.0.1#did-root-key",
            type="Ed25519VerificationKey2018",
            controller="did:hedera:testnet:zKey_0.0.1",
            public_key_multibase="zKey",
        )
        d = vm.to_dict()
        assert d["id"] == "did:hedera:testnet:zKey_0.0.1#did-root-key"
        assert d["publicKeyMultibase"] == "zKey"

    def test_from_dict(self) -> None:
        data = {
            "id": "did:hedera:testnet:zKey_0.0.1#did-root-key",
            "type": "Ed25519VerificationKey2018",
            "controller": "did:hedera:testnet:zKey_0.0.1",
            "publicKeyMultibase": "zKey",
        }
        vm = VerificationMethod.from_dict(data)
        assert vm.public_key_multibase == "zKey"
        assert vm.type == "Ed25519VerificationKey2018"
