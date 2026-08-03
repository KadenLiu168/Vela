from datetime import date
from pathlib import Path

import pytest
from vela_core.config import ConfigError
from vela_core.walk_forward.config import load_walk_forward_config


def test_load_walk_forward_config_resolves_base_strategy_path(tmp_path: Path) -> None:
    config_path = tmp_path / "walk-forward.yaml"
    config_path.write_text(
        """strategy:
  base_config: strategy.yaml
window:
  scheme: anchored_rolling
  start_date: 2019-01-01
  end_date: 2024-12-31
  train_years: 3
  test_years: 1
  step_years: 1
objective: sharpe_ratio
parameter_space:
  - name: parameters.selection.top_n
    type: int_range
    low: 1
    high: 2
    step: 1
"""
    )

    config = load_walk_forward_config(config_path)

    assert config.strategy.base_config == tmp_path / "strategy.yaml"
    assert config.window.start_date == date(2019, 1, 1)
    assert config.parameter_space[0].name == "parameters.selection.top_n"


@pytest.mark.parametrize(
    ("content", "message"),
    [
        ("parameter_space: []", "parameter_space"),
        (
            """strategy: {base_config: strategy.yaml}
window:
  {scheme: anchored_rolling, start_date: 2024-01-02, end_date: 2024-01-01,
  train_years: 3, test_years: 1, step_years: 1}
objective: sharpe_ratio
parameter_space: [{name: parameters.selection.top_n, type: int_range, low: 1, high: 2, step: 1}]
""",
            "end_date",
        ),
    ],
)
def test_load_walk_forward_config_wraps_invalid_content(
    tmp_path: Path, content: str, message: str
) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(content)

    with pytest.raises(ConfigError, match=message):
        load_walk_forward_config(path)


def test_load_walk_forward_config_rejects_duplicate_parameter_names(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(
        """strategy: {base_config: strategy.yaml}
window:
  {scheme: anchored_rolling, start_date: 2019-01-01, end_date: 2024-12-31,
  train_years: 3, test_years: 1, step_years: 1}
objective: sharpe_ratio
parameter_space:
  - {name: parameters.selection.top_n, type: choice, values: [1]}
  - {name: parameters.selection.top_n, type: choice, values: [2]}
"""
    )

    with pytest.raises(ConfigError, match="duplicate parameter name"):
        load_walk_forward_config(path)


def test_load_walk_forward_config_rejects_removed_baseline(tmp_path: Path) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(
        """strategy: {base_config: strategy.yaml}
window: {scheme: anchored_rolling, start_date: 2019-01-01, end_date: 2024-12-31,
  train_years: 3, test_years: 1, step_years: 1}
objective: sharpe_ratio
parameter_space: [{name: parameters.selection.top_n, type: choice, values: [1]}]
baseline: {type: equal_weight, strategy_id: ignored, version: v1}
"""
    )

    with pytest.raises(ConfigError, match="baseline"):
        load_walk_forward_config(path)


def test_repository_walk_forward_config_matches_current_contract() -> None:
    repository_root = Path(__file__).parents[3]

    config = load_walk_forward_config(repository_root / "config/walk_forward_v1.yaml")

    assert config.objective == "sharpe_ratio"


@pytest.mark.parametrize(
    "content",
    [
        "strategy: [",
        """strategy: {base_config: strategy.yaml}
window: {scheme: anchored_rolling, start_date: 2019-01-01, end_date: 2024-12-31,
  train_years: 3, test_years: 1, step_years: 1}
objective: not_sharpe
parameter_space: [{name: parameters.selection.top_n, type: choice, values: []}]
""",
        """strategy: {base_config: strategy.yaml}
window: {scheme: anchored_rolling, start_date: 2019-01-01, end_date: 2024-12-31,
  train_years: 3, test_years: 1, step_years: 1}
objective: sharpe_ratio
parameter_space: [{name: parameters.selection.top_n, type: int_range, low: 2, high: 1, step: 1}]
""",
    ],
)
def test_load_walk_forward_config_wraps_yaml_and_validation_failures(
    tmp_path: Path, content: str
) -> None:
    path = tmp_path / "invalid.yaml"
    path.write_text(content)

    with pytest.raises(ConfigError):
        load_walk_forward_config(path)


def test_load_walk_forward_config_wraps_missing_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="Failed to read"):
        load_walk_forward_config(tmp_path / "missing.yaml")
