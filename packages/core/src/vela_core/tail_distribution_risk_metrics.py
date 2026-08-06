from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from decimal import Context, Decimal, localcontext
from typing import Literal

from vela_core.strategy_equity_curve import StrategyEquityCurvePoint

_SIX_PLACES = Decimal("0.000001")
# Wide quantization context so extreme final values still quantize to six
# decimal places without raising InvalidOperation.
_QUANTIZE_CONTEXT = Context(prec=60)
_SHAPE_PRECISION = 60

MINIMUM_PUBLICATION_OBSERVATIONS = 100
TAIL_DISTRIBUTION_METRIC_VERSION = "tail_distribution_metrics_v1"

DistributionEvidenceStatus = Literal["sufficient", "insufficient_evidence"]


def _quantize_six_places(value: Decimal) -> Decimal:
    return value.quantize(_SIX_PLACES, context=_QUANTIZE_CONTEXT)


@dataclass(frozen=True)
class TailDistributionRiskMetrics:
    """Immutable one-day historical distribution-risk evidence for one curve.

    VaR/CVaR are positive loss magnitudes; skewness is the adjusted
    Fisher-Pearson sample skewness; kurtosis is the bias-corrected Fisher
    excess kurtosis with the normal-distribution baseline of zero. All four
    metrics are null unless at least ``MINIMUM_PUBLICATION_OBSERVATIONS``
    effective daily returns are available; counts are always retained.
    """

    observation_count: int
    tail_observation_count: int
    evidence_status: DistributionEvidenceStatus
    historical_var_95: Decimal | None = None
    historical_cvar_95: Decimal | None = None
    return_skewness: Decimal | None = None
    return_excess_kurtosis: Decimal | None = None


def calculate_tail_distribution_risk_metrics(
    points: Sequence[StrategyEquityCurvePoint],
) -> TailDistributionRiskMetrics:
    """Calculate one-day 95% historical VaR/CVaR and bias-corrected shape metrics.

    The first placeholder point is excluded; effective daily returns are used
    as-is. With fewer than ``MINIMUM_PUBLICATION_OBSERVATIONS`` effective
    observations every metric is null, the retained tail count is
    ``ceil(0.05 * observation_count)``, and evidence is ``insufficient_evidence``.
    Otherwise VaR uses the nearest-rank cutoff at fixed tail cardinality and
    CVaR the mean of exactly that tail, both quantized to six places, and
    skewness/excess kurtosis are computed from unquantized population central
    moments (null when the second central moment is zero).
    """
    effective_returns = [point.daily_return for point in points[1:]]
    observation_count = len(effective_returns)
    tail_observation_count = (observation_count + 19) // 20  # ceil(0.05 * n)
    if observation_count < MINIMUM_PUBLICATION_OBSERVATIONS:
        return TailDistributionRiskMetrics(
            observation_count=observation_count,
            tail_observation_count=tail_observation_count,
            evidence_status="insufficient_evidence",
        )

    sorted_returns = sorted(effective_returns)
    cutoff_return = sorted_returns[tail_observation_count - 1]
    tail_returns = sorted_returns[:tail_observation_count]
    historical_var_95 = _quantize_six_places(max(Decimal("0"), -cutoff_return))
    historical_cvar_95 = _quantize_six_places(
        max(Decimal("0"), -sum(tail_returns, Decimal("0")) / Decimal(len(tail_returns)))
    )
    skewness, excess_kurtosis = _shape_metrics(effective_returns)
    return TailDistributionRiskMetrics(
        observation_count=observation_count,
        tail_observation_count=tail_observation_count,
        evidence_status="sufficient",
        historical_var_95=historical_var_95,
        historical_cvar_95=historical_cvar_95,
        return_skewness=skewness,
        return_excess_kurtosis=excess_kurtosis,
    )


def _shape_metrics(returns: list[Decimal]) -> tuple[Decimal | None, Decimal | None]:
    """Bias-corrected Fisher-Pearson skewness and Fisher excess kurtosis.

    Population central moments are computed unquantized; a zero second central
    moment (constant distribution) yields null shape metrics.
    """
    with localcontext() as context:
        context.prec = _SHAPE_PRECISION
        count = Decimal(len(returns))
        mean = sum(returns, Decimal("0")) / count
        m2 = sum((value - mean) * (value - mean) for value in returns) / count
        if m2 == 0:
            return None, None
        m3 = sum((value - mean) ** 3 for value in returns) / count
        m4 = sum((value - mean) ** 4 for value in returns) / count
        skewness = (count * (count - 1)).sqrt() / (count - 2) * m3 / (m2.sqrt() * m2)
        excess_kurtosis = (
            (count - 1) / ((count - 2) * (count - 3)) * ((count + 1) * (m4 / (m2 * m2) - 3) + 6)
        )
    return _quantize_six_places(skewness), _quantize_six_places(excess_kurtosis)
