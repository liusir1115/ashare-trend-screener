from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from ashare_strategy.models import DailyBar, DailySnapshot


@dataclass(slots=True)
class TushareProvider:
    token: str

    def fetch_daily_snapshots(self, trade_date: date) -> list[DailySnapshot]:
        raise NotImplementedError(
            "Tushare raw integration is the next step. "
            "This project already defines the normalized DailySnapshot schema; "
            "the recommended pipeline is to pull daily_basic, cyq_perf, limit_list_d and "
            "your local daily bar cache, then map them into DailySnapshot objects."
        )

    def fetch_daily_bars(self, symbol: str, start_date: date, end_date: date) -> list[DailyBar]:
        raise NotImplementedError(
            "Implement this after wiring your Tushare token and local bar cache."
        )

