from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from ashare_strategy.market import classify_market_segment


@dataclass(slots=True)
class DailyBar:
    symbol: str
    trade_date: date
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(slots=True)
class DailySnapshot:
    symbol: str
    trade_date: date
    close: float
    volume: float
    volume_ratio: float
    ma5: float
    ma10: float
    ma20: float
    ma60: float
    ma20_slope: float
    ma60_slope: float
    breakout_high_120: float
    cost_5pct: float
    cost_50pct: float
    cost_95pct: float
    winner_rate: float
    base_days: int
    range_90: float
    high_250: float
    industry_hot_score: float
    board_hot_score: float
    pe_ttm: float | None = None
    pb: float | None = None
    industry_pe_ratio: float | None = None
    industry_pb_ratio: float | None = None
    limit_up: bool = False
    relimit: bool = False
    extra: dict[str, float | str | bool] = field(default_factory=dict)

    @property
    def overhead_pressure(self) -> float:
        return max(self.cost_95pct - self.close, 0.0) / self.close if self.close else 1.0

    @property
    def chip_compact(self) -> float:
        return (self.cost_95pct - self.cost_5pct) / self.close if self.close else 1.0

    @property
    def close_to_high_250(self) -> float:
        return self.close / self.high_250 if self.high_250 else 1.0

    @property
    def upside_to_high_250(self) -> float:
        return max(self.high_250 - self.close, 0.0) / self.close if self.close else 0.0

    @property
    def market_segment(self) -> str:
        return classify_market_segment(self.symbol)


@dataclass(slots=True)
class ScoreBreakdown:
    chip: float
    technical: float
    base: float
    valuation: float
    total: float
    reasons: list[str]


@dataclass(slots=True)
class ScreeningResult:
    symbol: str
    trade_date: date
    passed_filters: bool
    score: ScoreBreakdown
    snapshot: DailySnapshot
    failed_reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class TradeRecord:
    symbol: str
    signal_date: date
    entry_date: date
    exit_date: date
    entry_price: float
    exit_price: float
    raw_return: float
    holding_days: int
    score: float


@dataclass(slots=True)
class BacktestReport:
    total_trades: int
    win_rate: float
    average_return: float
    cumulative_return: float
    max_drawdown: float
    trades: list[TradeRecord]
