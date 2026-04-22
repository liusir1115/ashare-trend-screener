from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import os
import time
from typing import Any

from ashare_strategy.market import MARKET_SCOPE_ALL
from ashare_strategy.providers.akshare_provider import AKShareProvider
from ashare_strategy.strategy import ScreeningEngine

SCOPE_LABELS = {
    "all": "全市场",
    "main_board": "主板",
    "star_market": "科创板",
    "growth_board": "成长板",
}

LIVE_SAMPLE_SYMBOLS = {
    "all": ["600519", "600036", "300750", "688981", "601318", "002594"],
    "main_board": ["600519", "600036", "601318", "600276", "000001", "002594"],
    "star_market": ["688981", "688111", "688041", "688036"],
    "growth_board": ["300750", "300308", "300274", "300124"],
}

CACHE_TTL_SECONDS = int(os.getenv("MVP_CACHE_TTL_SECONDS", "900"))
FORCE_FALLBACK = os.getenv("MVP_FORCE_FALLBACK", "").strip().lower() in {"1", "true", "yes"}
_RESULT_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}


def _demo_item(
    symbol: str,
    market_segment: str,
    score_total: float,
    passed: bool,
    volume_ratio: float,
    overhead_pressure: float,
    base_days: int,
    *,
    trade_date: str = "2026-04-22",
    reasons: list[str] | None = None,
    failed_reasons: list[str] | None = None,
    preview_mock: bool = True,
) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "market_segment": market_segment,
        "trade_date": trade_date,
        "passed_filters": passed,
        "preview_mock": preview_mock,
        "score": {
            "chip": round(score_total * 0.95, 2),
            "technical": round(score_total * 1.02, 2),
            "base": round(score_total * 0.92, 2),
            "valuation": round(score_total * 0.88, 2),
            "total": score_total,
            "reasons": reasons or [],
        },
        "failed_reasons": failed_reasons or [],
        "metrics": {
            "volume_ratio": volume_ratio,
            "overhead_pressure": overhead_pressure,
            "base_days": base_days,
        },
    }


DEMO_RESULTS = {
    "all": {
        "label": "全市场",
        "note": "全市场视图适合观察，不适合直接把不同市场混成一套阈值去下结论。",
        "items": [
            _demo_item(
                "300750.SZ",
                "growth_board",
                61.87,
                False,
                1.6398,
                0.0,
                120,
                trade_date="2026-04-21",
                reasons=["Low overhead chip pressure", "Base-building period is long enough"],
                failed_reasons=["close/high_250=0.97 above 0.85", "upside_to_high_250=2.77% below 15.00%"],
                preview_mock=False,
            ),
            _demo_item(
                "600036.SH",
                "main_board",
                58.85,
                False,
                0.8919,
                0.0464,
                120,
                trade_date="2026-04-21",
                reasons=["Chip distribution is compact", "Base-building period is long enough"],
                failed_reasons=["missing breakout confirmation", "volume_ratio=0.89 below 1.50"],
                preview_mock=False,
            ),
            _demo_item(
                "688981.SH",
                "star_market",
                76.4,
                True,
                2.31,
                0.021,
                98,
                reasons=["Preview mock for STAR board pass state", "Volume expanded sharply"],
            ),
        ],
    },
    "main_board": {
        "label": "主板",
        "note": "主板更适合估值修复和中等波段，先在这里把策略跑稳再扩市场。",
        "items": [
            _demo_item(
                "600036.SH",
                "main_board",
                58.85,
                False,
                0.8919,
                0.0464,
                120,
                trade_date="2026-04-21",
                reasons=["Chip distribution is compact", "Base-building period is long enough"],
                failed_reasons=["missing breakout confirmation", "volume_ratio=0.89 below 1.50"],
                preview_mock=False,
            ),
            _demo_item(
                "600519.SH",
                "main_board",
                43.51,
                False,
                0.6801,
                0.0657,
                120,
                trade_date="2026-04-21",
                reasons=["Chip distribution is compact", "Base-building period is long enough"],
                failed_reasons=["moving averages are not in bullish alignment", "volume_ratio=0.68 below 1.50"],
                preview_mock=False,
            ),
            _demo_item(
                "600276.SH",
                "main_board",
                72.2,
                True,
                2.06,
                0.028,
                102,
                reasons=["Preview mock for main-board pass state", "Low overhead chip pressure"],
            ),
        ],
    },
    "star_market": {
        "label": "科创板",
        "note": "科创板波动更大，和主板分开回测才更有意义。",
        "items": [
            _demo_item(
                "688981.SH",
                "star_market",
                76.4,
                True,
                2.31,
                0.021,
                98,
                reasons=["Preview mock for STAR board pass state", "Volume expanded sharply"],
            ),
            _demo_item(
                "688111.SH",
                "star_market",
                48.6,
                False,
                1.18,
                0.072,
                61,
                reasons=["Preview mock for STAR board blocked state"],
                failed_reasons=["missing breakout confirmation", "range_90=42.00% above 40.00%"],
            ),
            _demo_item(
                "688041.SH",
                "star_market",
                41.3,
                False,
                0.77,
                0.093,
                85,
                reasons=["Preview mock for STAR board blocked state"],
                failed_reasons=["ma20_slope=-0.0021 below 0.0008", "volume_ratio=0.77 below 1.50"],
            ),
        ],
    },
    "growth_board": {
        "label": "成长板",
        "note": "成长板先独立观察，避免和主板估值口径混在一起。",
        "items": [
            _demo_item(
                "300750.SZ",
                "growth_board",
                61.87,
                False,
                1.6398,
                0.0,
                120,
                trade_date="2026-04-21",
                reasons=["Low overhead chip pressure", "Base-building period is long enough"],
                failed_reasons=["close/high_250=0.97 above 0.85", "upside_to_high_250=2.77% below 15.00%"],
                preview_mock=False,
            ),
            _demo_item(
                "300308.SZ",
                "growth_board",
                49.17,
                False,
                0.9019,
                0.0,
                0,
                trade_date="2026-04-21",
                reasons=["Low overhead chip pressure"],
                failed_reasons=["base_days=0 below 50", "range_90=73.71% above 40.00%"],
                preview_mock=False,
            ),
        ],
    },
}


@dataclass(slots=True)
class StrategyInput:
    narrative: str
    market_scope: str = "main_board"
    style_focus: str = "breakout"
    holding_period: str = "swing"
    risk_tolerance: str = "balanced"
    valuation_weight: str = "medium"
    priority_signal: str = "chip"


def _strategy_labels(strategy: StrategyInput) -> tuple[str, str, str]:
    style = {
        "breakout": "平台突破",
        "trend_start": "趋势启动",
        "rebound": "底部反转",
    }.get(strategy.style_focus, strategy.style_focus)
    holding = {
        "swing": "波段持有",
        "short": "短线快进快出",
        "trend": "趋势跟随",
    }.get(strategy.holding_period, strategy.holding_period)
    priority = {
        "chip": "筹码结构",
        "volume": "量价突破",
        "base": "筑底时长",
        "valuation": "估值修复",
    }.get(strategy.priority_signal, strategy.priority_signal)
    return style, holding, priority


def build_strategy_plan(strategy: StrategyInput) -> dict[str, Any]:
    style, holding, priority = _strategy_labels(strategy)
    overhead_pressure = (
        "3% - 5%"
        if strategy.risk_tolerance == "conservative"
        else "4% - 6%"
        if strategy.risk_tolerance == "balanced"
        else "5% - 8%"
    )
    volume_ratio = (
        ">= 1.8"
        if strategy.style_focus == "breakout"
        else ">= 1.5"
        if strategy.style_focus == "trend_start"
        else ">= 1.3"
    )
    base_days = (
        "90 - 150 天"
        if strategy.holding_period == "trend"
        else "60 - 120 天"
        if strategy.holding_period == "swing"
        else "35 - 80 天"
    )
    valuation_rule = (
        "要求行业内偏低估"
        if strategy.valuation_weight == "high"
        else "估值不过热即可"
        if strategy.valuation_weight == "medium"
        else "估值只做辅助"
    )

    return {
        "advice": [
            {
                "title": "建议市场",
                "value": (
                    "主板优先"
                    if strategy.market_scope == "main_board"
                    else "科创板单测"
                    if strategy.market_scope == "star_market"
                    else "先分组后汇总"
                ),
                "detail": "不同市场的波动和估值结构不同，阈值最好分开回测。",
            },
            {
                "title": "建议阈值",
                "value": overhead_pressure,
                "detail": "把上方筹码压力收敛成明确区间，后面更容易优化。",
            },
            {
                "title": "建议驱动",
                "value": priority,
                "detail": "建议保留一个主驱动信号，避免所有条件都变成平均主义。",
            },
        ],
        "parameters": [
            {
                "label": "上方筹码压力",
                "value": overhead_pressure,
                "hint": "风险偏好越保守，越建议把压力阈值收紧。",
            },
            {
                "label": "放量门槛",
                "value": volume_ratio,
                "hint": "突破型策略更适合提高量比要求。",
            },
            {
                "label": "筑底时长",
                "value": base_days,
                "hint": "持股越久，越需要更充分的底部整理。",
            },
            {
                "label": "估值规则",
                "value": valuation_rule,
                "hint": "主板更适合强调估值，科创板更适合把估值作为辅助。",
            },
        ],
        "summary": (
            f"你的策略更接近“{style} + {holding}”。"
            f"建议先在{SCOPE_LABELS.get(strategy.market_scope, strategy.market_scope)}里验证“{priority}”是否真的有效，"
            f"再决定是否扩大到全市场。当前策略描述是：{strategy.narrative.strip()}"
        ),
    }


def _serialize_screening_result(result: Any) -> dict[str, Any]:
    snapshot = result.snapshot
    return {
        "symbol": result.symbol,
        "market_segment": snapshot.market_segment,
        "trade_date": result.trade_date.isoformat(),
        "passed_filters": result.passed_filters,
        "preview_mock": False,
        "score": {
            "chip": result.score.chip,
            "technical": result.score.technical,
            "base": result.score.base,
            "valuation": result.score.valuation,
            "total": result.score.total,
            "reasons": result.score.reasons,
        },
        "failed_reasons": result.failed_reasons,
        "metrics": {
            "volume_ratio": round(snapshot.volume_ratio, 4),
            "overhead_pressure": round(snapshot.overhead_pressure, 4),
            "base_days": snapshot.base_days,
        },
    }


def get_scope_results(scope: str) -> dict[str, Any]:
    fallback = DEMO_RESULTS.get(scope, DEMO_RESULTS["all"])
    symbols = LIVE_SAMPLE_SYMBOLS.get(scope) or LIVE_SAMPLE_SYMBOLS["all"]
    now = time.time()
    cached = _RESULT_CACHE.get(scope)
    if cached and now - cached[0] <= CACHE_TTL_SECONDS:
        return cached[1]

    if FORCE_FALLBACK:
        result = dict(fallback)
        result["live_data"] = False
        _RESULT_CACHE[scope] = (now, result)
        return result

    try:
        provider = AKShareProvider(symbols=symbols, max_symbols=len(symbols), market_scope=scope)
        snapshots = provider.fetch_daily_snapshots(date.today())
        if not snapshots:
            raise RuntimeError("No live snapshots returned")
        engine = ScreeningEngine()
        ranked = engine.rank(snapshots, only_passed=False)
        items = [_serialize_screening_result(item) for item in ranked]
        if not items:
            raise RuntimeError("No ranked items available")
        result = {
            "label": SCOPE_LABELS.get(scope, fallback["label"]),
            "note": fallback["note"],
            "items": items,
            "live_data": True,
        }
        _RESULT_CACHE[scope] = (now, result)
        return result
    except Exception:
        result = dict(fallback)
        result["live_data"] = False
        _RESULT_CACHE[scope] = (now, result)
        return result


def build_mvp_payload(strategy: StrategyInput) -> dict[str, Any]:
    scope = strategy.market_scope or MARKET_SCOPE_ALL
    return {
        "generated_at": date.today().isoformat(),
        "strategy": build_strategy_plan(strategy),
        "results": get_scope_results(scope),
        "backtest": {
            "hold_days": 15,
            "stop_loss": "-7%",
            "take_profit": "18%",
            "max_positions": 10,
        },
    }
