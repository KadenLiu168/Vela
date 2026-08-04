from __future__ import annotations

import pytest
from vela_core.walk_forward.candidate_audit import build_candidate_audit


def test_candidate_audit_reconciles_the_four_bounded_skip_categories() -> None:
    audit = build_candidate_audit(
        candidate_count=10,
        eligible_count=3,
        reason_counts={
            "invalid_config": 1,
            "training_error": 2,
            "training_non_success": 1,
            "missing_train_sharpe": 3,
        },
    )

    assert audit == {
        "candidate_count": 10,
        "eligible_count": 3,
        "skipped_count": 7,
        "skip_reason_counts": {
            "invalid_config": 1,
            "training_error": 2,
            "training_non_success": 1,
            "missing_train_sharpe": 3,
        },
    }


@pytest.mark.parametrize(
    "kwargs",
    [
        {"candidate_count": 2, "eligible_count": 1, "reason_counts": {"unknown": 1}},
        {"candidate_count": 2, "eligible_count": 2, "reason_counts": {"training_error": 1}},
        {"candidate_count": 2, "eligible_count": 1, "reason_counts": {"training_error": 2}},
    ],
)
def test_candidate_audit_rejects_unreconciled_or_dynamic_reason_documents(
    kwargs: dict[str, object],
) -> None:
    with pytest.raises(ValueError):
        build_candidate_audit(**kwargs)
