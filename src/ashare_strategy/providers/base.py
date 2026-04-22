from __future__ import annotations

from datetime import date
from typing import Protocol

from ashare_strategy.models import DailyBar, DailySnapshot


class MarketDataProvider(Protocol):
    def fetch_daily_snapshots(self, trade_date: date) -> list[DailySnapshot]:
        """Return normalized stock snapshots for one trading day."""

    def fetch_daily_bars(self, symbol: str, start_date: date, end_date: date) -> list[DailyBar]:
        """Return normalized daily bars for backtesting."""

