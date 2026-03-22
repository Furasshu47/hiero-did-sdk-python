# Copyright 2025 ClearBrick Contributors
# SPDX-License-Identifier: Apache-2.0

"""W3C DID Document model for the `did:hedera` method."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

DID_CONTEXT = "https://www.w3.org/ns/did/v1"
DEFAULT_KEY_TYPE = "Ed25519VerificationKey2018"


@dataclass
class VerificationMethod:
    """A single verification method within a DID Document."""

    id: str
    type: str
    controller: str
    public_key_multibase: str

    def to_dict(self) -> dict[str, str]:
        """Serialize to a W3C-compliant dictionary."""
        return {
            "id": self.id,
            "type": self.type,
            "controller": self.controller,
            "publicKeyMultibase": self.public_key_multibase,
        }

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> VerificationMethod:
        """Deserialize from a W3C-compliant dictionary."""
        return cls(
            id=data["id"],
            type=data["type"],
            controller=data["controller"],
            public_key_multibase=data["publicKeyMultibase"],
        )


@dataclass
class DidDocument:
    """A W3C DID Document for the `did:hedera` method.

    Implements the subset of DID Core required for `did:hedera`:
    - One root verification method (Ed25519)
    - Authentication and assertion method relationships
    - Optional service endpoints
    """

    id: str
    verification_methods: list[VerificationMethod] = field(default_factory=list)
    authentication: list[str] = field(default_factory=list)
    assertion_method: list[str] = field(default_factory=list)
    services: list[dict[str, Any]] = field(default_factory=list)

    @classmethod
    def create_root(cls, did: str, public_key_multibase: str) -> DidDocument:
        """Create a new DID Document with a single root verification key.

        Args:
            did: The DID string.
            public_key_multibase: The base58btc-encoded Ed25519 public key.

        Returns:
            A new DidDocument with the root key configured.
        """
        root_key_id = f"{did}#did-root-key"
        root_method = VerificationMethod(
            id=root_key_id,
            type=DEFAULT_KEY_TYPE,
            controller=did,
            public_key_multibase=public_key_multibase,
        )
        return cls(
            id=did,
            verification_methods=[root_method],
            authentication=[root_key_id],
            assertion_method=[root_key_id],
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize to a W3C-compliant DID Document dictionary."""
        doc: dict[str, Any] = {
            "@context": DID_CONTEXT,
            "id": self.id,
            "verificationMethod": [vm.to_dict() for vm in self.verification_methods],
            "authentication": list(self.authentication),
            "assertionMethod": list(self.assertion_method),
        }
        if self.services:
            doc["service"] = list(self.services)
        return doc

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DidDocument:
        """Deserialize from a W3C-compliant DID Document dictionary."""
        methods = [VerificationMethod.from_dict(vm) for vm in data.get("verificationMethod", [])]
        return cls(
            id=data["id"],
            verification_methods=methods,
            authentication=list(data.get("authentication", [])),
            assertion_method=list(data.get("assertionMethod", [])),
            services=list(data.get("service", [])),
        )

    def add_verification_method(self, method: VerificationMethod) -> None:
        """Add a verification method to the document."""
        self.verification_methods.append(method)

    def add_service(self, service_id: str, service_type: str, endpoint: str) -> None:
        """Add a service endpoint to the document.

        Args:
            service_id: The service identifier (fragment).
            service_type: The service type.
            endpoint: The service endpoint URL.
        """
        self.services.append(
            {
                "id": f"{self.id}#{service_id}",
                "type": service_type,
                "serviceEndpoint": endpoint,
            }
        )
