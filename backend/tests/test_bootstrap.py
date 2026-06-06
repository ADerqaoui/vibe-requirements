"""Startup bootstrap tests."""
from pathlib import Path

import pytest
from alembic import command

from app.bootstrap import run_startup_db_setup
from app.config import Settings
from app.seed import run as seed_run


def test_run_startup_db_setup_runs_upgrade_then_seed(monkeypatch: pytest.MonkeyPatch) -> None:
    """Startup setup upgrades to head before running seed."""
    calls: list[str] = []

    def upgrade(_config, revision: str) -> None:
        assert revision == "head"
        calls.append("upgrade")

    def seed() -> None:
        calls.append("seed")

    monkeypatch.setattr(command, "upgrade", upgrade)
    monkeypatch.setattr(seed_run, "main", seed)

    run_startup_db_setup(
        Settings(database_url="sqlite:///bootstrap-test", auto_migrate_on_startup=True)
    )

    assert calls == ["upgrade", "seed"]


def test_run_startup_db_setup_uses_absolute_alembic_location(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Alembic script_location is resolved from the package, not the cwd."""
    captured: dict[str, str] = {}

    def upgrade(config, _revision: str) -> None:
        captured["script_location"] = config.get_main_option("script_location")
        captured["database_url"] = config.get_main_option("sqlalchemy.url")

    monkeypatch.setattr(command, "upgrade", upgrade)
    monkeypatch.setattr(seed_run, "main", lambda: None)

    run_startup_db_setup(
        Settings(
            database_url="sqlite:///absolute-location-test",
            auto_migrate_on_startup=True,
        )
    )

    assert Path(captured["script_location"]).is_absolute()
    assert captured["script_location"].endswith("/backend/alembic")
    assert captured["database_url"] == "sqlite:///absolute-location-test"


def test_run_startup_db_setup_failure_reraises_without_seed_or_stamp(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Migration failures propagate and do not stamp or seed."""
    calls: list[str] = []

    def upgrade(_config, _revision: str) -> None:
        calls.append("upgrade")
        raise RuntimeError("migration failed")

    def stamp(_config, _revision: str) -> None:
        calls.append("stamp")

    monkeypatch.setattr(command, "upgrade", upgrade)
    monkeypatch.setattr(command, "stamp", stamp)
    monkeypatch.setattr(seed_run, "main", lambda: calls.append("seed"))

    with pytest.raises(RuntimeError, match="migration failed"):
        run_startup_db_setup(
            Settings(
                database_url="sqlite:///bootstrap-failure-test",
                auto_migrate_on_startup=True,
            )
        )

    assert calls == ["upgrade"]


def test_run_startup_db_setup_flag_off_does_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    """The startup DB setup can be disabled for tests."""
    calls: list[str] = []
    monkeypatch.setattr(command, "upgrade", lambda _config, _revision: calls.append("upgrade"))
    monkeypatch.setattr(seed_run, "main", lambda: calls.append("seed"))

    run_startup_db_setup(
        Settings(
            database_url="sqlite:///bootstrap-disabled-test",
            auto_migrate_on_startup=False,
        )
    )

    assert calls == []
