from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import Any

from ashare_strategy.analytics import build_snapshot_from_bars
from ashare_strategy.market import MARKET_SCOPE_ALL, matches_market_scope
from ashare_strategy.models import DailyBar, DailySnapshot
from ashare_strategy.retry import load_with_retry


def _require_akshare() -> Any:
    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:  # pragma: no cover - depends on local environment
        raise RuntimeError(
            "AKShare is not installed. Install project dependencies before using AKShareProvider."
        ) from exc
    return ak


def _normalize_symbol(symbol: str) -> str:
    cleaned = symbol.strip().upper()
    if "." in cleaned:
        return cleaned.split(".")[0]
    if cleaned.startswith(("SZ", "SH", "BJ")) and len(cleaned) >= 8:
        return cleaned[-6:]
    return cleaned


def _as_float(value: Any) -> float | None:
    if value in (None, "", "-", "--"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _pick(row: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None


def _as_int(value: Any) -> int:
    number = _as_float(value)
    return int(number) if number is not None else 0


def _as_ratio(value: Any) -> float | None:
    number = _as_float(value)
    if number is None:
        return None
    if number > 1:
        return number / 100
    return number


def _chip_profile_from_row(row: dict[str, Any]) -> tuple[float, float, float, float] | None:
    cost_low = _as_float(_pick(row, "90成本-低", "90成本低", "90%成本-低", "90%成本低"))
    cost_high = _as_float(_pick(row, "90成本-高", "90成本高", "90%成本-高", "90%成本高"))
    average_cost = _as_float(_pick(row, "平均成本", "加权平均成本"))
    winner_rate = _as_ratio(_pick(row, "获利比例", "获利盘比例", "获利盘"))
    if None in (cost_low, cost_high, average_cost, winner_rate):
        return None
    return cost_low, average_cost, cost_high, winner_rate


@dataclass(slots=True)
class AKShareProvider:
    symbols: list[str] | None = None
    max_symbols: int | None = 200
    adjust: str = "qfq"
    lookback_days: int = 320
    market_scope: str = MARKET_SCOPE_ALL
    neutral_hot_score: float = 0.50
    neutral_industry_ratio: float = 0.95
    _spot_cache: dict[str, dict[str, Any]] = field(default_factory=dict, init=False)
    _limit_up_cache: dict[str, dict[str, Any]] = field(default_factory=dict, init=False)
    _broken_limit_cache: dict[str, dict[str, Any]] = field(default_factory=dict, init=False)
    _limit_cache_date: date | None = field(default=None, init=False)

    def fetch_daily_snapshots(self, trade_date: date) -> list[DailySnapshot]:
        today = date.today()
        if trade_date > today:
            raise ValueError("trade_date cannot be in the future")
        self._load_spot_cache()
        self._load_limit_pool_cache(trade_date)
        codes = self.symbols or list(self._spot_cache.keys())
        codes = [code for code in codes if matches_market_scope(code, self.market_scope)]
        if not codes:
            raise RuntimeError(
                "No symbols available for AKShare scan. "
                "Pass an explicit symbols list or retry when spot cache is reachable."
            )
        if self.max_symbols is not None:
            codes = codes[: self.max_symbols]

        snapshots: list[DailySnapshot] = []
        for code in codes:
            try:
                snapshots.append(self.fetch_symbol_snapshot(code, trade_date))
            except Exception:
                continue
        return snapshots

    def fetch_symbol_snapshot(self, symbol: str, trade_date: date) -> DailySnapshot:
        code = _normalize_symbol(symbol)
        bars = self.fetch_daily_bars(
            code,
            start_date=trade_date - timedelta(days=self.lookback_days * 2),
            end_date=trade_date,
        )
        if len(bars) < 120:
            raise ValueError(f"Not enough daily bars for {code}")
        spot = self._spot_cache.get(code, {})
        limit_row = self._limit_up_cache.get(code, {})
        broken_limit_row = self._broken_limit_cache.get(code, {})
        volume_ratio = _as_float(_pick(spot, "量比"))
        pe_ttm = _as_float(_pick(spot, "市盈率-动态", "市盈率"))
        pb = _as_float(_pick(spot, "市净率"))
        change_pct = _as_float(_pick(spot, "涨跌幅")) or 0.0
        chip_profile = self.fetch_chip_profile(code, trade_date)
        open_limit_times = _as_int(_pick(limit_row, "炸板次数", "打开次数"))
        limit_up = bool(limit_row) or change_pct >= 9.8
        relimit = bool(limit_row) and open_limit_times > 0
        return build_snapshot_from_bars(
            symbol=f"{code}.{self._exchange_suffix(code)}",
            bars=bars,
            trade_date=bars[-1].trade_date,
            volume_ratio=volume_ratio,
            pe_ttm=pe_ttm,
            pb=pb,
            industry_hot_score=self.neutral_hot_score,
            board_hot_score=self.neutral_hot_score,
            industry_pe_ratio=self.neutral_industry_ratio if pe_ttm is not None else None,
            industry_pb_ratio=self.neutral_industry_ratio if pb is not None else None,
            limit_up=limit_up,
            relimit=relimit,
            chip_profile=chip_profile,
            extra={
                "data_source": "akshare",
                "chip_source": "akshare_stock_cyq_em" if chip_profile is not None else "approx_close_quantiles",
                "limit_source": "akshare_stock_zt_pool_em" if limit_row else "spot_change_pct",
                "broken_limit": bool(broken_limit_row),
                "first_limit_time": str(_pick(limit_row, "首次封板时间", "首次涨停时间") or ""),
                "last_limit_time": str(_pick(limit_row, "最后封板时间", "最后涨停时间") or ""),
                "limit_open_times": open_limit_times,
                "limit_reason": str(_pick(limit_row, "涨停原因类别", "涨停原因", "所属行业") or ""),
                "spot_change_pct": change_pct,
            },
        )

    def fetch_chip_profile(self, symbol: str, trade_date: date) -> tuple[float, float, float, float] | None:
        ak = _require_akshare()
        code = _normalize_symbol(symbol)
        try:
            frame = load_with_retry(lambda: ak.stock_cyq_em(symbol=code, adjust=self.adjust))
        except Exception:
            return None
        if frame is None or frame.empty:
            return None

        rows = frame.to_dict(orient="records")
        rows = [row for row in rows if self._row_trade_date(row) <= trade_date]
        if not rows:
            return None

        # 这里取目标日期之前最近的一天筹码数据，避免未来数据混进盘后筛选。
        latest_row = max(rows, key=self._row_trade_date)
        return _chip_profile_from_row(latest_row)

    def fetch_daily_bars(self, symbol: str, start_date: date, end_date: date) -> list[DailyBar]:
        ak = _require_akshare()
        code = _normalize_symbol(symbol)
        frame = load_with_retry(
            lambda: ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust=self.adjust,
            )
        )
        if frame is None or frame.empty:
            return []
        rows = frame.to_dict(orient="records")
        bars: list[DailyBar] = []
        for row in rows:
            trade_date_raw = _pick(row, "日期", "date")
            trade_date_value = (
                trade_date_raw.date()
                if isinstance(trade_date_raw, datetime)
                else date.fromisoformat(str(trade_date_raw))
            )
            open_price = _as_float(_pick(row, "开盘", "open"))
            close_price = _as_float(_pick(row, "收盘", "close"))
            high_price = _as_float(_pick(row, "最高", "high"))
            low_price = _as_float(_pick(row, "最低", "low"))
            volume = _as_float(_pick(row, "成交量", "volume"))
            if None in (open_price, close_price, high_price, low_price, volume):
                continue
            bars.append(
                DailyBar(
                    symbol=f"{code}.{self._exchange_suffix(code)}",
                    trade_date=trade_date_value,
                    open=open_price,
                    high=high_price,
                    low=low_price,
                    close=close_price,
                    volume=volume,
                )
            )
        return bars

    def _load_spot_cache(self) -> None:
        if self._spot_cache:
            return
        ak = _require_akshare()
        try:
            frame = load_with_retry(ak.stock_zh_a_spot_em)
        except Exception:
            self._spot_cache = {}
            return
        if frame is None or frame.empty:
            self._spot_cache = {}
            return
        rows = frame.to_dict(orient="records")
        cache: dict[str, dict[str, Any]] = {}
        for row in rows:
            code = _normalize_symbol(str(_pick(row, "代码", "symbol", "股票代码")))
            if code:
                cache[code] = row
        self._spot_cache = cache

    def _load_limit_pool_cache(self, trade_date: date) -> None:
        if self._limit_cache_date == trade_date:
            return

        ak = _require_akshare()
        trade_date_text = trade_date.strftime("%Y%m%d")
        self._limit_up_cache = self._load_code_row_cache(
            lambda: ak.stock_zt_pool_em(date=trade_date_text)
        )
        self._broken_limit_cache = self._load_code_row_cache(
            lambda: ak.stock_zt_pool_zbgc_em(date=trade_date_text)
        )
        self._limit_cache_date = trade_date

    def _load_code_row_cache(self, loader: Any) -> dict[str, dict[str, Any]]:
        try:
            frame = load_with_retry(loader)
        except Exception:
            return {}
        if frame is None or frame.empty:
            return {}

        cache: dict[str, dict[str, Any]] = {}
        for row in frame.to_dict(orient="records"):
            code = _normalize_symbol(str(_pick(row, "代码", "股票代码", "symbol")))
            if code:
                cache[code] = row
        return cache

    @staticmethod
    def _row_trade_date(row: dict[str, Any]) -> date:
        raw_value = _pick(row, "日期", "date", "交易日期")
        if isinstance(raw_value, datetime):
            return raw_value.date()
        if isinstance(raw_value, date):
            return raw_value
        return date.fromisoformat(str(raw_value)[:10])

    @staticmethod
    def _exchange_suffix(code: str) -> str:
        if code.startswith(("600", "601", "603", "605", "688")):
            return "SH"
        if code.startswith(
            (
                "430",
                "830",
                "831",
                "832",
                "833",
                "834",
                "835",
                "836",
                "837",
                "838",
                "839",
                "870",
                "871",
                "872",
                "873",
                "874",
                "875",
                "876",
                "877",
                "878",
                "879",
            )
        ):
            return "BJ"
        return "SZ"
