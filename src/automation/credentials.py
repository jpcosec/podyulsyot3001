"""Credential contracts for login-required automation flows.

This module defines the metadata-only credential store used by apply flows.
Secrets are referenced by environment-variable name and resolved lazily at
runtime so passwords never need to be persisted in run artifacts.
"""

from __future__ import annotations

import os
from typing import Literal
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, PrivateAttr, model_validator

DEFAULT_BROWSEROS_PROFILE_DIR = "~/.config/browser-os/Default"


def _normalize_domain(domain: str) -> str:
    """Normalize one host or domain fragment for matching."""
    return domain.strip().lower().lstrip(".")


def _extract_host(url: str | None) -> str | None:
    """Return the hostname for a URL or bare host string."""
    if not url:
        return None
    parsed = urlparse(url if "://" in url else f"https://{url}")
    return _normalize_domain(parsed.hostname or "") or None


class CredentialSecretRef(BaseModel):
    """Metadata describing how one secret is resolved at runtime."""

    model_config = ConfigDict(extra="forbid")

    env_var: str = Field(
        description="Environment variable name holding the secret value.",
    )
    required: bool = Field(
        default=True,
        description="Whether the runtime must provide this secret when no persisted session is available.",
    )
    description: str | None = Field(
        default=None,
        description="Short human hint describing what the secret is used for.",
    )


class PortalCredentialBinding(BaseModel):
    """Domain-bound login metadata for one portal or ATS family."""

    model_config = ConfigDict(extra="forbid")

    portal_name: str = Field(
        description="Logical portal name that owns this login contract, for example 'linkedin'.",
    )
    domains: list[str] = Field(
        min_length=1,
        description="Hostnames or parent domains covered by this login contract.",
    )
    login_url: str | None = Field(
        default=None,
        description="Optional login URL to open during manual session setup.",
    )
    auth_strategy: Literal["persistent_profile", "env_secrets", "mixed"] = Field(
        default="persistent_profile",
        description="Preferred login strategy for the bound domains.",
    )
    browser_profile_dir: str | None = Field(
        default=None,
        description="Persistent browser profile directory to reuse when the motor supports it.",
    )
    secrets: dict[str, CredentialSecretRef] = Field(
        default_factory=dict,
        description="Secret aliases exposed to runtime code without embedding secret values.",
    )

    @model_validator(mode="after")
    def _normalize_domains(self) -> "PortalCredentialBinding":
        self.domains = [_normalize_domain(domain) for domain in self.domains]
        return self

    def matches(self, portal_name: str, url: str | None = None) -> bool:
        """Return whether this binding covers the given portal and URL."""
        if self.portal_name != portal_name:
            return False
        host = _extract_host(url)
        if host is None:
            return True
        return any(
            host == domain or host.endswith(f".{domain}") for domain in self.domains
        )


class ResolvedPortalCredentials(BaseModel):
    """Minimal runtime view of credential metadata for one apply session."""

    model_config = ConfigDict(extra="forbid")

    portal_name: str = Field(
        description="Portal name that requested the credential binding."
    )
    matched_domain: str = Field(
        description="Concrete hostname that matched the binding for this run.",
    )
    auth_strategy: Literal["persistent_profile", "env_secrets", "mixed"] = Field(
        description="Preferred login strategy for the current run.",
    )
    login_url: str | None = Field(
        default=None,
        description="Login URL the operator should open when seeding a session manually.",
    )
    browser_profile_dir: str | None = Field(
        default=None,
        description="Persistent profile directory metadata for motors or operators.",
    )
    secret_env_vars: dict[str, str] = Field(
        default_factory=dict,
        description="Secret alias to environment-variable mapping. Values stay outside the model.",
    )
    required_secret_keys: list[str] = Field(
        default_factory=list,
        description="Secret aliases that must exist in the environment when secret-based login is used.",
    )
    optional_secret_keys: list[str] = Field(
        default_factory=list,
        description="Secret aliases that may exist in the environment for this portal.",
    )

    _binding: PortalCredentialBinding | None = PrivateAttr(default=None)

    @classmethod
    def from_binding(
        cls, binding: PortalCredentialBinding, *, matched_domain: str
    ) -> "ResolvedPortalCredentials":
        """Build a runtime credential view from validated metadata."""
        resolved = cls(
            portal_name=binding.portal_name,
            matched_domain=matched_domain,
            auth_strategy=binding.auth_strategy,
            login_url=binding.login_url,
            browser_profile_dir=binding.browser_profile_dir,
            secret_env_vars={key: ref.env_var for key, ref in binding.secrets.items()},
            required_secret_keys=[
                key for key, ref in binding.secrets.items() if ref.required
            ],
            optional_secret_keys=[
                key for key, ref in binding.secrets.items() if not ref.required
            ],
        )
        resolved._binding = binding
        return resolved

    def get_secret(self, alias: str) -> str | None:
        """Resolve one secret value directly from the environment."""
        env_var = self.secret_env_vars.get(alias)
        if not env_var:
            return None
        return os.getenv(env_var)

    def missing_required_secrets(self) -> list[str]:
        """List required secret aliases whose env vars are not currently set."""
        return [
            alias for alias in self.required_secret_keys if not self.get_secret(alias)
        ]

    def setup_url(self, default_url: str) -> str:
        """Return the login URL or the caller-provided default URL."""
        return self.login_url or default_url

    @property
    def effective_browser_profile_dir(self) -> str | None:
        """Return the declared profile dir or the BrowserOS default when applicable."""
        if self.browser_profile_dir:
            return self.browser_profile_dir
        if self.auth_strategy in {"persistent_profile", "mixed"}:
            return DEFAULT_BROWSEROS_PROFILE_DIR
        return None


class CredentialStore(BaseModel):
    """Collection of domain-bound login metadata for automation flows."""

    model_config = ConfigDict(extra="forbid")

    bindings: list[PortalCredentialBinding] = Field(
        default_factory=list,
        description="All portal and ATS login bindings available to automation.",
    )

    def resolve(
        self, portal_name: str, url: str | None = None
    ) -> ResolvedPortalCredentials | None:
        """Return the first binding matching the portal and URL host."""
        host = _extract_host(url)
        for binding in self.bindings:
            if binding.matches(portal_name, url):
                return ResolvedPortalCredentials.from_binding(
                    binding,
                    matched_domain=host or binding.domains[0],
                )
        return None
