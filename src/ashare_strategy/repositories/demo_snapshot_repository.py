from __future__ import annotations

from datetime import date

from ashare_strategy.core.models import DailySnapshot


LIVE_SAMPLE_SYMBOLS = {
    "all": ["600519", "600036", "300750", "688981", "601318", "002594"],
    "main_board": ["600519", "600036", "601318", "600276", "000001", "002594"],
    "star_market": ["688981", "688111", "688041", "688036"],
    "growth_board": ["300750", "300308", "300274", "300124"],
}


def _snapshot(
    symbol: str,
    *,
    trade_date: date,
    close: float,
    volume_ratio: float,
    ma5: float,
    ma10: float,
    ma20: float,
    ma60: float,
    ma20_slope: float,
    ma60_slope: float,
    breakout_high_120: float,
    cost_5pct: float,
    cost_50pct: float,
    cost_95pct: float,
    winner_rate: float,
    base_days: int,
    range_90: float,
    high_250: float,
    industry_hot_score: float,
    board_hot_score: float,
    industry_pe_ratio: float | None = None,
    industry_pb_ratio: float | None = None,
    limit_up: bool = False,
    relimit: bool = False,
) -> DailySnapshot:
    return DailySnapshot(
        symbol=symbol,
        trade_date=trade_date,
        close=close,
        volume=1_000_000,
        volume_ratio=volume_ratio,
        ma5=ma5,
        ma10=ma10,
        ma20=ma20,
        ma60=ma60,
        ma20_slope=ma20_slope,
        ma60_slope=ma60_slope,
        breakout_high_120=breakout_high_120,
        cost_5pct=cost_5pct,
        cost_50pct=cost_50pct,
        cost_95pct=cost_95pct,
        winner_rate=winner_rate,
        base_days=base_days,
        range_90=range_90,
        high_250=high_250,
        industry_hot_score=industry_hot_score,
        board_hot_score=board_hot_score,
        industry_pe_ratio=industry_pe_ratio,
        industry_pb_ratio=industry_pb_ratio,
        limit_up=limit_up,
        relimit=relimit,
    )


DEMO_SNAPSHOTS: dict[str, list[DailySnapshot]] = {
    "main_board": [
        _snapshot("600276.SH", trade_date=date(2026, 4, 22), close=56.4, volume_ratio=2.06, ma5=55.7, ma10=55.1, ma20=54.0, ma60=49.8, ma20_slope=0.0026, ma60_slope=0.0010, breakout_high_120=55.6, cost_5pct=50.2, cost_50pct=53.8, cost_95pct=58.0, winner_rate=0.64, base_days=102, range_90=0.23, high_250=70.0, industry_hot_score=0.76, board_hot_score=0.71, industry_pe_ratio=0.78, industry_pb_ratio=0.81),
        _snapshot("600036.SH", trade_date=date(2026, 4, 21), close=44.1, volume_ratio=0.89, ma5=44.0, ma10=43.7, ma20=43.5, ma60=42.4, ma20_slope=0.0014, ma60_slope=0.0007, breakout_high_120=45.0, cost_5pct=40.5, cost_50pct=42.7, cost_95pct=46.1, winner_rate=0.58, base_days=120, range_90=0.22, high_250=52.0, industry_hot_score=0.63, board_hot_score=0.58, industry_pe_ratio=0.84, industry_pb_ratio=0.86),
        _snapshot("600519.SH", trade_date=date(2026, 4, 21), close=1580.0, volume_ratio=0.68, ma5=1572.0, ma10=1574.0, ma20=1570.0, ma60=1565.0, ma20_slope=0.0006, ma60_slope=0.0004, breakout_high_120=1610.0, cost_5pct=1490.0, cost_50pct=1530.0, cost_95pct=1684.0, winner_rate=0.55, base_days=120, range_90=0.25, high_250=1710.0, industry_hot_score=0.59, board_hot_score=0.55, industry_pe_ratio=1.02, industry_pb_ratio=1.06),
        _snapshot("000001.SZ", trade_date=date(2026, 4, 22), close=14.6, volume_ratio=1.42, ma5=14.2, ma10=14.0, ma20=13.9, ma60=13.8, ma20_slope=0.0010, ma60_slope=0.0006, breakout_high_120=14.8, cost_5pct=13.1, cost_50pct=13.8, cost_95pct=15.0, winner_rate=0.47, base_days=58, range_90=0.31, high_250=18.2, industry_hot_score=0.57, board_hot_score=0.55, industry_pe_ratio=0.79, industry_pb_ratio=0.74, relimit=True),
    ],
    "star_market": [
        _snapshot("688981.SH", trade_date=date(2026, 4, 22), close=53.5, volume_ratio=2.31, ma5=52.9, ma10=51.8, ma20=50.5, ma60=46.7, ma20_slope=0.0030, ma60_slope=0.0014, breakout_high_120=52.0, cost_5pct=46.9, cost_50pct=49.8, cost_95pct=54.6, winner_rate=0.67, base_days=98, range_90=0.28, high_250=65.0, industry_hot_score=0.82, board_hot_score=0.79, industry_pe_ratio=1.04, industry_pb_ratio=1.08),
        _snapshot("688111.SH", trade_date=date(2026, 4, 22), close=39.8, volume_ratio=1.18, ma5=39.0, ma10=38.8, ma20=38.4, ma60=37.2, ma20_slope=0.0012, ma60_slope=0.0008, breakout_high_120=40.5, cost_5pct=36.5, cost_50pct=38.0, cost_95pct=42.9, winner_rate=0.44, base_days=61, range_90=0.42, high_250=49.5, industry_hot_score=0.72, board_hot_score=0.76, industry_pe_ratio=0.93, industry_pb_ratio=0.97),
        _snapshot("688041.SH", trade_date=date(2026, 4, 22), close=27.2, volume_ratio=0.77, ma5=26.9, ma10=27.0, ma20=27.1, ma60=28.0, ma20_slope=-0.0021, ma60_slope=-0.0009, breakout_high_120=28.4, cost_5pct=25.8, cost_50pct=26.7, cost_95pct=29.7, winner_rate=0.41, base_days=85, range_90=0.34, high_250=36.5, industry_hot_score=0.69, board_hot_score=0.71, industry_pe_ratio=0.88, industry_pb_ratio=0.95),
    ],
    "growth_board": [
        _snapshot("300750.SZ", trade_date=date(2026, 4, 21), close=204.0, volume_ratio=1.64, ma5=203.5, ma10=202.2, ma20=198.5, ma60=188.0, ma20_slope=0.0023, ma60_slope=0.0012, breakout_high_120=201.0, cost_5pct=189.0, cost_50pct=196.0, cost_95pct=204.0, winner_rate=0.63, base_days=120, range_90=0.24, high_250=209.7, industry_hot_score=0.78, board_hot_score=0.80, industry_pe_ratio=0.95, industry_pb_ratio=1.01),
        _snapshot("300308.SZ", trade_date=date(2026, 4, 21), close=16.1, volume_ratio=0.90, ma5=15.7, ma10=15.6, ma20=15.8, ma60=16.4, ma20_slope=-0.0005, ma60_slope=-0.0004, breakout_high_120=18.2, cost_5pct=14.9, cost_50pct=15.5, cost_95pct=16.1, winner_rate=0.36, base_days=0, range_90=0.7371, high_250=24.0, industry_hot_score=0.61, board_hot_score=0.63, industry_pe_ratio=0.81, industry_pb_ratio=0.84),
        _snapshot("300274.SZ", trade_date=date(2026, 4, 22), close=22.8, volume_ratio=1.52, ma5=22.4, ma10=22.2, ma20=21.6, ma60=21.0, ma20_slope=0.0015, ma60_slope=0.0008, breakout_high_120=23.1, cost_5pct=20.7, cost_50pct=21.8, cost_95pct=23.9, winner_rate=0.48, base_days=74, range_90=0.31, high_250=29.7, industry_hot_score=0.67, board_hot_score=0.71, industry_pe_ratio=0.79, industry_pb_ratio=0.88, relimit=True),
    ],
}

DEMO_SNAPSHOTS["all"] = [*DEMO_SNAPSHOTS["main_board"], *DEMO_SNAPSHOTS["star_market"], *DEMO_SNAPSHOTS["growth_board"]]
