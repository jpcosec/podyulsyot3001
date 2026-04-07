"""Tests for automation credential contracts."""

from __future__ import annotations

from pydantic import ValidationError
import pytest

from src.automation.credentials import CredentialStore
from src.automation.storage import AutomationStorage


def test_load_credential_store_returns_empty_model_by_default() -> None:
    storage = AutomationStorage.__new__(AutomationStorage)

    store = storage.load_credential_store()

    assert store == CredentialStore()


def test_credential_store_resolves_domain_binding_and_secrets(monkeypatch) -> None:
    storage = AutomationStorage.__new__(AutomationStorage)
    monkeypatch.setenv("LINKEDIN_PASSWORD", "super-secret")

    store = storage.load_credential_store(
        {
            "bindings": [
                {
                    "portal_name": "linkedin",
                    "domains": ["linkedin.com"],
                    "auth_strategy": "mixed",
                    "login_url": "https://www.linkedin.com/login",
                    "secrets": {
                        "password": {
                            "env_var": "LINKEDIN_PASSWORD",
                            "required": True,
                        }
                    },
                }
            ]
        }
    )

    resolved = store.resolve("linkedin", "https://www.linkedin.com/jobs/view/123")

    assert resolved is not None
    assert resolved.matched_domain == "www.linkedin.com"
    assert (
        resolved.setup_url("https://www.linkedin.com")
        == "https://www.linkedin.com/login"
    )
    assert resolved.effective_browser_profile_dir == "~/.config/browser-os/Default"
    assert resolved.model_dump()["secret_env_vars"]["password"] == "LINKEDIN_PASSWORD"
    assert resolved.get_secret("password") == "super-secret"
    assert resolved.missing_required_secrets() == []


def test_load_credential_store_rejects_unknown_secret_fields() -> None:
    storage = AutomationStorage.__new__(AutomationStorage)

    with pytest.raises(ValidationError):
        storage.load_credential_store(
            {
                "bindings": [
                    {
                        "portal_name": "linkedin",
                        "domains": ["linkedin.com"],
                        "secrets": {
                            "password": {
                                "env_var": "LINKEDIN_PASSWORD",
                                "value": "do-not-store-me",
                            }
                        },
                    }
                ]
            }
        )
