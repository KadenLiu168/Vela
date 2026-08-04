from __future__ import annotations

from typing import TypedDict

SKIP_REASON_KEYS = (
    "invalid_config",
    "training_error",
    "training_non_success",
    "missing_train_sharpe",
)


class CandidateAudit(TypedDict):
    candidate_count: int
    eligible_count: int
    skipped_count: int
    skip_reason_counts: dict[str, int]


def build_candidate_audit(
    *, candidate_count: int, eligible_count: int, reason_counts: dict[str, int]
) -> CandidateAudit:
    if candidate_count < 0 or eligible_count < 0 or eligible_count > candidate_count:
        raise ValueError("candidate and eligible counts must be non-negative and reconciled")
    if set(reason_counts) - set(SKIP_REASON_KEYS):
        raise ValueError("unsupported candidate skip reason")
    if any(type(value) is not int or value <= 0 for value in reason_counts.values()):
        raise ValueError("candidate skip reason counts must be positive integers")
    skipped_count = sum(reason_counts.values())
    if candidate_count != eligible_count + skipped_count:
        raise ValueError("candidate count must equal eligible plus skipped count")
    return {
        "candidate_count": candidate_count,
        "eligible_count": eligible_count,
        "skipped_count": skipped_count,
        "skip_reason_counts": dict(reason_counts),
    }
