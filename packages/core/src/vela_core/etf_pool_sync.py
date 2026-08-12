from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from vela_core.config import ETFConfig, ETFPoolConfig
from vela_core.models import ETFInfo


@dataclass(frozen=True)
class ETFPoolSyncResult:
    pool_id: str
    total_etfs: int
    inserted_count: int
    updated_count: int
    unchanged_count: int


def sync_etf_pool_to_db(session: Session, pool: ETFPoolConfig) -> ETFPoolSyncResult:
    inserted_count = 0
    updated_count = 0
    unchanged_count = 0

    for configured_etf in pool.etfs:
        etf = session.scalar(
            select(ETFInfo).where(
                ETFInfo.exchange == configured_etf.exchange,
                ETFInfo.symbol == configured_etf.symbol,
            )
        )
        if etf is None:
            session.add(
                ETFInfo(
                    exchange=configured_etf.exchange,
                    symbol=configured_etf.symbol,
                    name=configured_etf.name,
                    currency=pool.currency,
                    category=configured_etf.category,
                    inception_date=configured_etf.inception_date,
                    listing_date=configured_etf.listing_date,
                    is_active=configured_etf.is_active,
                )
            )
            inserted_count += 1
            continue

        changed = _update_existing_etf(etf, pool=pool, configured_etf=configured_etf)
        if changed:
            updated_count += 1
        else:
            unchanged_count += 1

    session.flush()
    return ETFPoolSyncResult(
        pool_id=pool.pool_id,
        total_etfs=len(pool.etfs),
        inserted_count=inserted_count,
        updated_count=updated_count,
        unchanged_count=unchanged_count,
    )


def _update_existing_etf(etf: ETFInfo, *, pool: ETFPoolConfig, configured_etf: ETFConfig) -> bool:
    changed = False
    updates = {
        "name": configured_etf.name,
        "currency": pool.currency,
        "category": configured_etf.category,
        "inception_date": configured_etf.inception_date,
        "listing_date": configured_etf.listing_date,
        "is_active": configured_etf.is_active,
    }
    for field_name, value in updates.items():
        if getattr(etf, field_name) != value:
            setattr(etf, field_name, value)
            changed = True
    return changed
