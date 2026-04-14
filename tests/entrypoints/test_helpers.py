from unittest.mock import MagicMock

import click

import pytest

from flowger.entrypoints.cli.helpers import resolve_bank_country


def _make_settings(
    bank: str | None = None,
    country: str | None = None,
    default_bank: str | None = None,
    default_country: str | None = None,
) -> MagicMock:
    s = MagicMock()
    s.bank = bank
    s.country = country
    s.default_bank = default_bank
    s.default_country = default_country
    return s


def test_resolve_bank_country_cli_flag_wins() -> None:
    """CLI flags take priority over all env vars and defaults."""
    settings = _make_settings(bank="EnvBank", country="DE", default_bank="Default", default_country="FR")
    bank, country = resolve_bank_country(settings, "CLIBank", "ES")
    assert bank == "CLIBank"
    assert country == "ES"


def test_resolve_bank_country_docker_env_used_when_no_flag() -> None:
    """Docker env (settings.bank/country) is used when no CLI flag is given."""
    settings = _make_settings(bank="EnvBank", country="DE", default_bank="Default", default_country="FR")
    bank, country = resolve_bank_country(settings, None, None)
    assert bank == "EnvBank"
    assert country == "DE"


def test_resolve_bank_country_whitespace_env_falls_back_to_default() -> None:
    """A whitespace-only Docker env var must NOT block the .env default fallback."""
    settings = _make_settings(bank="   ", country="  ", default_bank="Default", default_country="FR")
    bank, country = resolve_bank_country(settings, None, None)
    assert bank == "Default"
    assert country == "FR"


def test_resolve_bank_country_missing_raises() -> None:
    """Resolve fails fast when all sources are empty."""
    settings = _make_settings(bank=None, country=None, default_bank=None, default_country=None)
    with pytest.raises(click.exceptions.Exit):
        resolve_bank_country(settings, None, None)


def test_resolve_bank_country_values_are_stripped() -> None:
    """Resolved values are stripped of surrounding whitespace."""
    settings = _make_settings(bank="  Imagin  ", country="  ES  ")
    bank, country = resolve_bank_country(settings, None, None)
    assert bank == "Imagin"
    assert country == "ES"
