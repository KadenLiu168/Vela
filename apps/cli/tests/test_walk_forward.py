from pathlib import Path

from vela_cli import main as cli
from vela_core.walk_forward.report import WalkForwardReport


def test_walk_forward_writes_report_to_output(tmp_path: Path, monkeypatch) -> None:
    output = tmp_path / "report.txt"
    calls: list[tuple[str, Path]] = []

    def fake_run(database_url: str, *, config_path: Path) -> WalkForwardReport:
        calls.append((database_url, config_path))
        return WalkForwardReport()

    monkeypatch.setattr(cli, "run_walk_forward", fake_run)

    assert cli.main(["walk-forward", "--config", "config.yaml", "--output", str(output)]) == 0
    assert calls == [("sqlite+pysqlite:///vela.db", Path("config.yaml"))]
    assert "Walk-forward report" in output.read_text()


def test_walk_forward_prints_persisted_id_after_managed_run(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        cli, "run_walk_forward", lambda *_args, **_kwargs: WalkForwardReport(walk_forward_run_id=12)
    )

    assert cli.main(["walk-forward", "--config", "config.yaml"]) == 0

    assert "Walk-forward run id: 12" in capsys.readouterr().out


def test_walk_forward_commit_failure_does_not_print_flushed_id(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "run_walk_forward",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("commit failed")),
    )

    assert cli.main(["walk-forward", "--config", "config.yaml"]) == 1

    assert "Walk-forward run id:" not in capsys.readouterr().out


def test_walk_forward_reports_runtime_failure(capsys, monkeypatch) -> None:
    monkeypatch.setattr(
        cli,
        "run_walk_forward",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(ValueError("bad config")),
    )

    assert cli.main(["walk-forward", "--config", "missing.yaml"]) == 1
    assert "Failed to run walk-forward" in capsys.readouterr().err


def test_walk_forward_reports_missing_config(capsys) -> None:
    assert cli.main(["walk-forward", "--config", "does-not-exist.yaml"]) == 1
    assert "Failed to read configuration file" in capsys.readouterr().err
