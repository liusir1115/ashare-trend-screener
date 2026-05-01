from __future__ import annotations

from datetime import date
import os

from ashare_strategy.core.models import DailySnapshot
from ashare_strategy.providers.akshare_provider import AKShareProvider
from ashare_strategy.repositories.demo_snapshot_repository import DEMO_SNAPSHOTS, LIVE_SAMPLE_SYMBOLS

DEFAULT_LIVE_SCAN_LIMIT = int(os.getenv("MVP_LIVE_MAX_SYMBOLS", "120"))


def fetch_demo_snapshots(scope: str) -> list[DailySnapshot]:
    return DEMO_SNAPSHOTS.get(scope, DEMO_SNAPSHOTS["all"])


def fetch_live_snapshots(scope: str, trade_day: date | None = None) -> list[DailySnapshot]:
    provider = AKShareProvider(symbols=None, max_symbols=DEFAULT_LIVE_SCAN_LIMIT, market_scope=scope)
    return provider.fetch_daily_snapshots(trade_day or date.today())


def fetch_live_snapshot_batch(scope: str, trade_day: date | None = None) -> tuple[list[DailySnapshot], dict[str, object]]:
    provider = AKShareProvider(symbols=None, max_symbols=DEFAULT_LIVE_SCAN_LIMIT, market_scope=scope)
    return provider.fetch_daily_snapshot_batch(trade_day or date.today())
