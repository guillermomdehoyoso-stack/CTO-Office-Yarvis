"""Focused tests for the interactive Gate B mailbox-binding helper."""

from __future__ import annotations

import pytest

from scripts import netpay_gmail_gate_b_bind as binding


def test_normalization_rejects_terminal_control_characters() -> None:
    with pytest.raises(ValueError, match="invalid mailbox"):
        binding.normalize_mailbox("\x1b[control@example.invalid")


def test_hidden_double_entry_normalizes_and_matches(monkeypatch) -> None:
    entries = iter((" Pilot@Example.Invalid ", "pilot@example.invalid"))
    monkeypatch.setattr(binding.getpass, "getpass", lambda _prompt: next(entries))

    assert binding.read_mailbox() == "pilot@example.invalid"


def test_hidden_double_entry_rejects_mismatch(monkeypatch) -> None:
    entries = iter(("first@example.invalid", "second@example.invalid"))
    monkeypatch.setattr(binding.getpass, "getpass", lambda _prompt: next(entries))

    with pytest.raises(ValueError, match="do not match"):
        binding.read_mailbox()
