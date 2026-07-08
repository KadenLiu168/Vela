import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

from sqlalchemy.orm import Session

from vela_core.app_config import AppConfig
from vela_core.etf_pool_sync import ETFPoolSyncResult, sync_etf_pool_to_db
from vela_core.market_data_fetcher import MarketDataFetchResult, fetch_full_market_prices
from vela_core.market_data_provider import MarketDataProvider
from vela_core.migration import run_alembic_upgrade

StepName = Literal["migrate", "sync_etf_pool", "fetch_full_market_data"]
StepStatus = Literal["success", "failed"]


@dataclass(frozen=True)
class BootstrapStepResult:
    name: StepName
    status: StepStatus
    duration_seconds: float
    error_message: str | None = None
    sync_result: ETFPoolSyncResult | None = None
    fetch_result: MarketDataFetchResult | None = None


@dataclass(frozen=True)
class BootstrapResult:
    status: StepStatus
    steps: list[BootstrapStepResult] = field(default_factory=list)
    failed_step: StepName | None = None
    total_duration_seconds: float = 0.0


def run_local_setup_bootstrap(
    session: Session,
    *,
    provider: MarketDataProvider,
    app_config: AppConfig,
    database_url: str,
    script_location: Path,
) -> BootstrapResult:
    steps: list[BootstrapStepResult] = []
    total_start = time.monotonic()

    # Step 1: migrate
    step_start = time.monotonic()
    try:
        run_alembic_upgrade(database_url, script_location)
        steps.append(
            BootstrapStepResult(
                name="migrate",
                status="success",
                duration_seconds=time.monotonic() - step_start,
            )
        )
    except Exception as exc:
        steps.append(
            BootstrapStepResult(
                name="migrate",
                status="failed",
                duration_seconds=time.monotonic() - step_start,
                error_message=str(exc),
            )
        )
        return BootstrapResult(
            status="failed",
            steps=steps,
            failed_step="migrate",
            total_duration_seconds=time.monotonic() - total_start,
        )

    # Step 2: sync_etf_pool
    step_start = time.monotonic()
    try:
        sync_result = sync_etf_pool_to_db(session, pool=app_config.etf_pool)
        steps.append(
            BootstrapStepResult(
                name="sync_etf_pool",
                status="success",
                duration_seconds=time.monotonic() - step_start,
                sync_result=sync_result,
            )
        )
    except Exception as exc:
        steps.append(
            BootstrapStepResult(
                name="sync_etf_pool",
                status="failed",
                duration_seconds=time.monotonic() - step_start,
                error_message=str(exc),
            )
        )
        return BootstrapResult(
            status="failed",
            steps=steps,
            failed_step="sync_etf_pool",
            total_duration_seconds=time.monotonic() - total_start,
        )

    # Step 3: fetch_full_market_data
    step_start = time.monotonic()
    try:
        fetch_result = fetch_full_market_prices(session, provider=provider)
        steps.append(
            BootstrapStepResult(
                name="fetch_full_market_data",
                status="success" if fetch_result.status != "failed" else "failed",
                duration_seconds=time.monotonic() - step_start,
                fetch_result=fetch_result,
                error_message=fetch_result.error_message,
            )
        )
    except Exception as exc:
        steps.append(
            BootstrapStepResult(
                name="fetch_full_market_data",
                status="failed",
                duration_seconds=time.monotonic() - step_start,
                error_message=str(exc),
            )
        )
        return BootstrapResult(
            status="failed",
            steps=steps,
            failed_step="fetch_full_market_data",
            total_duration_seconds=time.monotonic() - total_start,
        )

    all_success = all(step.status == "success" for step in steps)
    failed = next((step for step in steps if step.status == "failed"), None)

    return BootstrapResult(
        status="success" if all_success else "failed",
        steps=steps,
        failed_step=failed.name if failed else None,
        total_duration_seconds=time.monotonic() - total_start,
    )
