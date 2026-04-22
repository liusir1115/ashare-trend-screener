from __future__ import annotations

from datetime import date
from statistics import mean
from typing import Iterable

from ashare_strategy.models import DailyBar, DailySnapshot


def simple_moving_average(values: list[float], window: int) -> float:
    if len(values) < window:
        raise ValueError(f"Need at least {window} values, got {len(values)}")
    return mean(values[-window:])


def average_slope_ratio(values: list[float], window: int, lag: int = 5) -> float:
    if len(values) < window + lag:
        raise ValueError(f"Need at least {window + lag} values, got {len(values)}")
    current = mean(values[-window:])
    previous = mean(values[-window - lag : -lag])
    if previous == 0:
        return 0.0
    return (current - previous) / previous


def approximate_chip_metrics(bars: list[DailyBar]) -> tuple[float, float, float, float]:
    """Temporary fallback when true chip-distribution data is unavailable."""
    if len(bars) < 30:
        raise ValueError("Need at least 30 bars to approximate chip metrics")
    closes = sorted(bar.close for bar in bars[-90:])
    current_close = bars[-1].close
    count = len(closes)
    cost_5pct = closes[max(0, int(round((count - 1) * 0.05)))]
    cost_50pct = closes[max(0, int(round((count - 1) * 0.50)))]
    cost_95pct = closes[max(0, int(round((count - 1) * 0.95)))]
    winner_rate = sum(1 for price in closes if price <= current_close) / count
    return cost_5pct, cost_50pct, cost_95pct, winner_rate


def estimate_base_days(bars: list[DailyBar], max_window: int = 120, max_range: float = 0.40) -> int:
    recent = bars[-max_window:]
    best = 0
    for window in range(len(recent), 19, -1):
        segment = recent[-window:]
        low = min(bar.low for bar in segment)
        high = max(bar.high for bar in segment)
        if low <= 0:
            continue
        if (high - low) / low <= max_range:
            best = window
            break
    return best


def build_snapshot_from_bars(
    symbol: str,
    bars: Iterable[DailyBar],
    *,
    trade_date: date | None = None,
    volume_ratio: float | None = None,
    pe_ttm: float | None = None,
    pb: float | None = None,
    industry_hot_score: float = 0.50,
    board_hot_score: float = 0.50,
    industry_pe_ratio: float | None = None,
    industry_pb_ratio: float | None = None,
    limit_up: bool = False,
    relimit: bool = False,
    chip_profile: tuple[float, float, float, float] | None = None,
    extra: dict[str, float | str | bool] | None = None,
) -> DailySnapshot:
    history = sorted(list(bars), key=lambda item: item.trade_date)
    if len(history) < 120:
        raise ValueError("Need at least 120 daily bars to build a snapshot")

    latest = history[-1]
    closes = [bar.close for bar in history]
    volumes = [bar.volume for bar in history]
    highs_120 = [bar.high for bar in history[-120:]]
    highs_250 = [bar.high for bar in history[-250:]] if len(history) >= 250 else [bar.high for bar in history]
    highs_90 = [bar.high for bar in history[-90:]]
    lows_90 = [bar.low for bar in history[-90:]]

    ma5 = simple_moving_average(closes, 5)
    ma10 = simple_moving_average(closes, 10)
    ma20 = simple_moving_average(closes, 20)
    ma60 = simple_moving_average(closes, 60)
    ma20_slope = average_slope_ratio(closes, 20)
    ma60_slope = average_slope_ratio(closes, 60)
    breakout_high_120 = max(highs_120[:-1]) if len(highs_120) > 1 else max(highs_120)
    high_250 = max(highs_250)
    low_90 = min(lows_90)
    high_90 = max(highs_90)
    range_90 = (high_90 - low_90) / low_90 if low_90 else 0.0
    base_days = estimate_base_days(history)

    if volume_ratio is None:
        avg_volume_20 = mean(volumes[-20:])
        volume_ratio = latest.volume / avg_volume_20 if avg_volume_20 else 0.0

    profile = chip_profile or approximate_chip_metrics(history)
    payload_extra = dict(extra or {})
    if chip_profile is None:
        payload_extra.setdefault("chip_source", "approx_close_quantiles")
        payload_extra.setdefault("winner_rate_source", "approx_close_quantiles")

    return DailySnapshot(
        symbol=symbol,
        trade_date=trade_date or latest.trade_date,
        close=latest.close,
        volume=latest.volume,
        volume_ratio=volume_ratio,
        ma5=ma5,
        ma10=ma10,
        ma20=ma20,
        ma60=ma60,
        ma20_slope=ma20_slope,
        ma60_slope=ma60_slope,
        breakout_high_120=breakout_high_120,
        cost_5pct=profile[0],
        cost_50pct=profile[1],
        cost_95pct=profile[2],
        winner_rate=profile[3],
        base_days=base_days,
        range_90=range_90,
        high_250=high_250,
        industry_hot_score=industry_hot_score,
        board_hot_score=board_hot_score,
        pe_ttm=pe_ttm,
        pb=pb,
        industry_pe_ratio=industry_pe_ratio,
        industry_pb_ratio=industry_pb_ratio,
        limit_up=limit_up,
        relimit=relimit,
        extra=payload_extra,
    )

