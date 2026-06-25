from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _clean_env() -> dict[str, str]:
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    return env


def test_installed_cli_help_runs_without_pythonpath() -> None:
    result = subprocess.run(
        ["uv", "run", "vela", "--help"],
        check=False,
        capture_output=True,
        env=_clean_env(),
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "init-db" in result.stdout


def test_installed_cli_init_db_runs_without_pythonpath(tmp_path: Path) -> None:
    database_path = tmp_path / "vela-smoke.db"
    database_url = f"sqlite+pysqlite:///{database_path}"

    result = subprocess.run(
        ["uv", "run", "vela", "init-db", "--database-url", database_url],
        check=False,
        capture_output=True,
        env=_clean_env(),
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Initialized database at" in result.stdout
    assert database_path.exists()
