from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
import hashlib
import os
import re
import time
from typing import Any

from ashare_strategy.config import StrategyConfig
from ashare_strategy.market import MARKET_SCOPE_ALL
from ashare_strategy.models import DailySnapshot
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
        _snapshot(
            "600276.SH",
            trade_date=date(2026, 4, 22),
            close=56.4,
            volume_ratio=2.06,
            ma5=55.7,
            ma10=55.1,
            ma20=54.0,
            ma60=49.8,
            ma20_slope=0.0026,
            ma60_slope=0.0010,
            breakout_high_120=55.6,
            cost_5pct=50.2,
            cost_50pct=53.8,
            cost_95pct=58.0,
            winner_rate=0.64,
            base_days=102,
            range_90=0.23,
            high_250=70.0,
            industry_hot_score=0.76,
            board_hot_score=0.71,
            industry_pe_ratio=0.78,
            industry_pb_ratio=0.81,
        ),
        _snapshot(
            "600036.SH",
            trade_date=date(2026, 4, 21),
            close=44.1,
            volume_ratio=0.89,
            ma5=44.0,
            ma10=43.7,
            ma20=43.5,
            ma60=42.4,
            ma20_slope=0.0014,
            ma60_slope=0.0007,
            breakout_high_120=45.0,
            cost_5pct=40.5,
            cost_50pct=42.7,
            cost_95pct=46.1,
            winner_rate=0.58,
            base_days=120,
            range_90=0.22,
            high_250=52.0,
            industry_hot_score=0.63,
            board_hot_score=0.58,
            industry_pe_ratio=0.84,
            industry_pb_ratio=0.86,
        ),
        _snapshot(
            "600519.SH",
            trade_date=date(2026, 4, 21),
            close=1580.0,
            volume_ratio=0.68,
            ma5=1572.0,
            ma10=1574.0,
            ma20=1570.0,
            ma60=1565.0,
            ma20_slope=0.0006,
            ma60_slope=0.0004,
            breakout_high_120=1610.0,
            cost_5pct=1490.0,
            cost_50pct=1530.0,
            cost_95pct=1684.0,
            winner_rate=0.55,
            base_days=120,
            range_90=0.25,
            high_250=1710.0,
            industry_hot_score=0.59,
            board_hot_score=0.55,
            industry_pe_ratio=1.02,
            industry_pb_ratio=1.06,
        ),
        _snapshot(
            "000001.SZ",
            trade_date=date(2026, 4, 22),
            close=14.6,
            volume_ratio=1.42,
            ma5=14.2,
            ma10=14.0,
            ma20=13.9,
            ma60=13.8,
            ma20_slope=0.0010,
            ma60_slope=0.0006,
            breakout_high_120=14.8,
            cost_5pct=13.1,
            cost_50pct=13.8,
            cost_95pct=15.0,
            winner_rate=0.47,
            base_days=58,
            range_90=0.31,
            high_250=18.2,
            industry_hot_score=0.57,
            board_hot_score=0.55,
            industry_pe_ratio=0.79,
            industry_pb_ratio=0.74,
            relimit=True,
        ),
    ],
    "star_market": [
        _snapshot(
            "688981.SH",
            trade_date=date(2026, 4, 22),
            close=53.5,
            volume_ratio=2.31,
            ma5=52.9,
            ma10=51.8,
            ma20=50.5,
            ma60=46.7,
            ma20_slope=0.0030,
            ma60_slope=0.0014,
            breakout_high_120=52.0,
            cost_5pct=46.9,
            cost_50pct=49.8,
            cost_95pct=54.6,
            winner_rate=0.67,
            base_days=98,
            range_90=0.28,
            high_250=65.0,
            industry_hot_score=0.82,
            board_hot_score=0.79,
            industry_pe_ratio=1.04,
            industry_pb_ratio=1.08,
        ),
        _snapshot(
            "688111.SH",
            trade_date=date(2026, 4, 22),
            close=39.8,
            volume_ratio=1.18,
            ma5=39.0,
            ma10=38.8,
            ma20=38.4,
            ma60=37.2,
            ma20_slope=0.0012,
            ma60_slope=0.0008,
            breakout_high_120=40.5,
            cost_5pct=36.5,
            cost_50pct=38.0,
            cost_95pct=42.9,
            winner_rate=0.44,
            base_days=61,
            range_90=0.42,
            high_250=49.5,
            industry_hot_score=0.72,
            board_hot_score=0.76,
            industry_pe_ratio=0.93,
            industry_pb_ratio=0.97,
        ),
        _snapshot(
            "688041.SH",
            trade_date=date(2026, 4, 22),
            close=27.2,
            volume_ratio=0.77,
            ma5=26.9,
            ma10=27.0,
            ma20=27.1,
            ma60=28.0,
            ma20_slope=-0.0021,
            ma60_slope=-0.0009,
            breakout_high_120=28.4,
            cost_5pct=25.8,
            cost_50pct=26.7,
            cost_95pct=29.7,
            winner_rate=0.41,
            base_days=85,
            range_90=0.34,
            high_250=36.5,
            industry_hot_score=0.69,
            board_hot_score=0.71,
            industry_pe_ratio=0.88,
            industry_pb_ratio=0.95,
        ),
    ],
    "growth_board": [
        _snapshot(
            "300750.SZ",
            trade_date=date(2026, 4, 21),
            close=204.0,
            volume_ratio=1.64,
            ma5=203.5,
            ma10=202.2,
            ma20=198.5,
            ma60=188.0,
            ma20_slope=0.0023,
            ma60_slope=0.0012,
            breakout_high_120=201.0,
            cost_5pct=189.0,
            cost_50pct=196.0,
            cost_95pct=204.0,
            winner_rate=0.63,
            base_days=120,
            range_90=0.24,
            high_250=209.7,
            industry_hot_score=0.78,
            board_hot_score=0.80,
            industry_pe_ratio=0.95,
            industry_pb_ratio=1.01,
        ),
        _snapshot(
            "300308.SZ",
            trade_date=date(2026, 4, 21),
            close=16.1,
            volume_ratio=0.90,
            ma5=15.7,
            ma10=15.6,
            ma20=15.8,
            ma60=16.4,
            ma20_slope=-0.0005,
            ma60_slope=-0.0004,
            breakout_high_120=18.2,
            cost_5pct=14.9,
            cost_50pct=15.5,
            cost_95pct=16.1,
            winner_rate=0.36,
            base_days=0,
            range_90=0.7371,
            high_250=24.0,
            industry_hot_score=0.61,
            board_hot_score=0.63,
            industry_pe_ratio=0.81,
            industry_pb_ratio=0.84,
        ),
        _snapshot(
            "300274.SZ",
            trade_date=date(2026, 4, 22),
            close=22.8,
            volume_ratio=1.52,
            ma5=22.4,
            ma10=22.2,
            ma20=21.6,
            ma60=21.0,
            ma20_slope=0.0015,
            ma60_slope=0.0008,
            breakout_high_120=23.1,
            cost_5pct=20.7,
            cost_50pct=21.8,
            cost_95pct=23.9,
            winner_rate=0.48,
            base_days=74,
            range_90=0.31,
            high_250=29.7,
            industry_hot_score=0.67,
            board_hot_score=0.71,
            industry_pe_ratio=0.79,
            industry_pb_ratio=0.88,
            relimit=True,
        ),
    ],
}
DEMO_SNAPSHOTS["all"] = [
    *DEMO_SNAPSHOTS["main_board"],
    *DEMO_SNAPSHOTS["star_market"],
    *DEMO_SNAPSHOTS["growth_board"],
]


@dataclass(slots=True)
class StrategyInput:
    narrative: str
    market_scope: str = "main_board"
    style_focus: str = "breakout"
    holding_period: str = "swing"
    risk_tolerance: str = "balanced"
    valuation_weight: str = "medium"
    priority_signal: str = "chip"
    playbook_id: str | None = None


@dataclass(slots=True)
class NarrativeDirectives:
    min_base_days: int | None = None
    ideal_base_days: int | None = None
    max_overhead_pressure: float | None = None
    min_volume_ratio: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    require_limit_up: bool = False
    prefer_left_side: bool = False
    prefer_right_side: bool = False
    require_hot_sector: bool = False
    emphasize_valuation: bool = False
    emphasize_chip: bool = False
    emphasize_trend: bool = False
    notes: list[str] | None = None


def _build_parsed_rules(directives: NarrativeDirectives) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []
    if directives.min_base_days is not None:
        rules.append({"group": "数值规则", "label": f"筑底时长 >= {directives.min_base_days} 天"})
    if directives.max_overhead_pressure is not None:
        rules.append({"group": "数值规则", "label": f"上方压力 <= {directives.max_overhead_pressure:.0%}"})
    if directives.min_volume_ratio is not None:
        rules.append({"group": "数值规则", "label": f"量比 >= {directives.min_volume_ratio:.1f}"})
    if directives.stop_loss is not None:
        rules.append({"group": "交易管理", "label": f"止损 {directives.stop_loss:.0%}"})
    if directives.take_profit is not None:
        rules.append({"group": "交易管理", "label": f"止盈 {directives.take_profit:.0%}"})
    if directives.require_limit_up:
        rules.append({"group": "交易管理", "label": "要求涨停或回封确认"})
    if directives.prefer_left_side:
        rules.append({"group": "风格偏好", "label": "偏好左侧切入"})
    if directives.prefer_right_side:
        rules.append({"group": "风格偏好", "label": "偏好右侧确认"})
    if directives.require_hot_sector:
        rules.append({"group": "风格偏好", "label": "优先热门行业"})
    if directives.emphasize_valuation:
        rules.append({"group": "风格偏好", "label": "强调估值修复"})
    if directives.emphasize_chip:
        rules.append({"group": "风格偏好", "label": "强调筹码结构"})
    if directives.emphasize_trend:
        rules.append({"group": "风格偏好", "label": "强调趋势与均线"})
    return rules or [{"group": "系统判断", "label": "未识别到额外文字约束"}]


def _translate_reason(reason: str) -> str:
    exact_map = {
        "Low overhead chip pressure": "上方筹码压力较小",
        "Chip distribution is compact": "筹码分布较集中",
        "Limit-up confirmation appeared": "出现涨停确认",
        "Re-sealed after opening intraday": "盘中开板后回封",
        "Volume expanded sharply": "量能明显放大",
        "Base-building period is long enough": "筑底时长较充分",
        "There is still room to prior highs": "距离前高仍有空间",
        "Sector heat is elevated": "行业热度较高",
        "moving averages are not in bullish alignment": "均线尚未形成多头排列",
        "missing breakout confirmation": "突破确认不足",
        "limit-up style confirmation required by config": "当前策略要求涨停或回封确认",
    }
    if reason in exact_map:
        return exact_map[reason]

    patterns: list[tuple[str, str]] = [
        (r"overhead_pressure=([\d.]+%) above ([\d.]+%)", "上方压力 \\1 高于阈值 \\2"),
        (r"chip_compact=([\d.]+%) above ([\d.]+%)", "筹码集中度区间 \\1 高于阈值 \\2"),
        (r"winner_rate=([\d.]+%) below ([\d.]+%)", "获利盘比例 \\1 低于阈值 \\2"),
        (r"ma20_slope=([-\d.]+) below ([-\d.]+)", "MA20 斜率 \\1 低于阈值 \\2"),
        (r"ma60_slope=([-\d.]+) below ([-\d.]+)", "MA60 斜率 \\1 低于阈值 \\2"),
        (r"volume_ratio=([\d.]+) below ([\d.]+)", "量比 \\1 低于阈值 \\2"),
        (r"base_days=(\d+) below (\d+)", "筑底天数 \\1 低于阈值 \\2"),
        (r"range_90=([\d.]+%) above ([\d.]+%)", "近 90 天振幅 \\1 高于阈值 \\2"),
        (r"close/high_250=([\d.]+) above ([\d.]+)", "当前价格距离 250 日高点过近：\\1，高于阈值 \\2"),
        (r"upside_to_high_250=([\d.]+%) below ([\d.]+%)", "距离前高空间 \\1 低于阈值 \\2"),
        (r"industry_pe_ratio=([\d.]+) above ([\d.]+)", "行业相对 PE \\1 高于阈值 \\2"),
        (r"industry_pb_ratio=([\d.]+) above ([\d.]+)", "行业相对 PB \\1 高于阈值 \\2"),
        (r"industry_hot_score=([\d.]+) below ([\d.]+)", "行业热度 \\1 低于阈值 \\2"),
        (r"board_hot_score=([\d.]+) below ([\d.]+)", "板块热度 \\1 低于阈值 \\2"),
    ]
    for pattern, replacement in patterns:
        if re.search(pattern, reason):
            return re.sub(pattern, replacement, reason)
    return reason


def _translate_reasons(reasons: list[str]) -> list[str]:
    return [_translate_reason(reason) for reason in reasons]


def _extract_narrative_directives(narrative: str) -> NarrativeDirectives:
    text = narrative.lower()
    directives = NarrativeDirectives(notes=[])

    if month_match := re.search(r"(?:筑底|横盘|盘整|底部).{0,10}?(\d{1,2})\s*个?月", text):
        months = int(month_match.group(1))
        directives.min_base_days = months * 20
        directives.ideal_base_days = months * 20 + 20
        directives.notes.append(f"识别到筑底时长约 {months} 个月")
    elif day_match := re.search(r"(?:筑底|横盘|盘整|底部).{0,10}?(\d{2,3})\s*天", text):
        days = int(day_match.group(1))
        directives.min_base_days = days
        directives.ideal_base_days = days + 20
        directives.notes.append(f"识别到筑底时长约 {days} 天")

    if pressure_match := re.search(r"(?:上方压力|压力|套牢盘).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%", text):
        directives.max_overhead_pressure = float(pressure_match.group(1)) / 100
        directives.notes.append(f"识别到上方压力阈值 {pressure_match.group(1)}%")

    if volume_match := re.search(r"(?:量比|放量).{0,8}?(\d(?:\.\d+)?)", text):
        directives.min_volume_ratio = float(volume_match.group(1))
        directives.notes.append(f"识别到量比门槛 {volume_match.group(1)}")

    if stop_loss_match := re.search(r"(?:止损|回撤).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%", text):
        directives.stop_loss = -float(stop_loss_match.group(1)) / 100
        directives.notes.append(f"识别到止损 {stop_loss_match.group(1)}%")

    if take_profit_match := re.search(r"(?:止盈|目标收益).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%", text):
        directives.take_profit = float(take_profit_match.group(1)) / 100
        directives.notes.append(f"识别到止盈 {take_profit_match.group(1)}%")

    if any(keyword in text for keyword in ["涨停", "首板", "回封"]):
        directives.require_limit_up = True
        directives.notes.append("识别到涨停/回封偏好")

    if "左侧" in text:
        directives.prefer_left_side = True
        directives.notes.append("识别到左侧切入偏好")

    if "右侧" in text:
        directives.prefer_right_side = True
        directives.notes.append("识别到右侧确认偏好")

    if any(keyword in text for keyword in ["热门行业", "主线", "景气", "热点板块"]):
        directives.require_hot_sector = True
        directives.notes.append("识别到热门行业要求")

    if any(keyword in text for keyword in ["低估", "估值修复", "便宜", "估值"]):
        directives.emphasize_valuation = True
        directives.notes.append("识别到估值修复要求")

    if "筹码" in text:
        directives.emphasize_chip = True
        directives.notes.append("识别到筹码结构要求")

    if any(keyword in text for keyword in ["多头排列", "均线", "趋势"]):
        directives.emphasize_trend = True
        directives.notes.append("识别到趋势/均线要求")

    return directives


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
        "volume": "放量突破",
        "base": "筑底时长",
        "valuation": "估值修复",
    }.get(strategy.priority_signal, strategy.priority_signal)
    return style, holding, priority


def _build_playbooks(strategy: StrategyInput) -> tuple[list[dict[str, Any]], str | None, str | None]:
    text = strategy.narrative.lower()
    playbooks: list[dict[str, Any]]

    if any(keyword in text for keyword in ["反转", "反弹", "v反", "拐头"]):
        playbooks = [
            {
                "id": "reversal_base",
                "title": "底部反转型",
                "thesis": "更强调筑底、均线拐头和压力释放，不追求最强爆量。",
                "fit_for": "适合想做中短波段反转、接受先试错后确认的场景。",
                "overrides": {
                    "style_focus": "rebound",
                    "holding_period": "swing",
                    "risk_tolerance": "balanced",
                    "priority_signal": "base",
                },
                "highlights": ["筑底 60-120 天", "量比 >= 1.3", "上方压力 <= 6%"],
            },
            {
                "id": "reversal_left",
                "title": "左侧试错型",
                "thesis": "更早介入，放松放量要求，但要求筹码和空间更干净。",
                "fit_for": "适合偏左侧、愿意用更紧止损换更早位置。",
                "overrides": {
                    "style_focus": "rebound",
                    "holding_period": "short",
                    "risk_tolerance": "aggressive",
                    "priority_signal": "chip",
                },
                "highlights": ["筑底 40-90 天", "量比 >= 1.1", "止损偏紧"],
            },
            {
                "id": "reversal_right",
                "title": "右侧确认型",
                "thesis": "要求站回均线和放量确认，宁可晚一点，也提高胜率。",
                "fit_for": "适合不想猜底、希望看到明显转强信号再进。",
                "overrides": {
                    "style_focus": "trend_start",
                    "holding_period": "swing",
                    "risk_tolerance": "conservative",
                    "priority_signal": "volume",
                },
                "highlights": ["量比 >= 1.8", "更看重均线和突破", "上方压力 <= 5%"],
            },
        ]
        recommended_id = "reversal_base"
    elif any(keyword in text for keyword in ["突破", "启动", "主升", "放量"]):
        playbooks = [
            {
                "id": "breakout_classic",
                "title": "经典突破型",
                "thesis": "以平台突破和放量确认为核心，先求确定性。",
                "fit_for": "适合你原始的趋势启动思路。",
                "overrides": {
                    "style_focus": "breakout",
                    "holding_period": "swing",
                    "risk_tolerance": "balanced",
                    "priority_signal": "volume",
                },
                "highlights": ["量比 >= 1.8", "突破确认优先", "筑底 60-120 天"],
            },
            {
                "id": "breakout_value",
                "title": "估值修复突破型",
                "thesis": "在突破逻辑里额外强调估值不过热和行业匹配。",
                "fit_for": "适合主板、偏低估修复的趋势启动。",
                "overrides": {
                    "style_focus": "breakout",
                    "holding_period": "trend",
                    "risk_tolerance": "balanced",
                    "valuation_weight": "high",
                    "priority_signal": "valuation",
                },
                "highlights": ["估值阈值更严", "持有更久", "行业热度仍需达标"],
            },
            {
                "id": "breakout_fast",
                "title": "短线爆量型",
                "thesis": "更强调爆量和短周期反馈，适合快进快出。",
                "fit_for": "适合强信号博弈，不适合太长持有。",
                "overrides": {
                    "style_focus": "breakout",
                    "holding_period": "short",
                    "risk_tolerance": "aggressive",
                    "priority_signal": "volume",
                },
                "highlights": ["量比 >= 2.0", "持有 3-7 天", "更强调强信号日"],
            },
        ]
        recommended_id = "breakout_classic"
    else:
        playbooks = [
            {
                "id": "balanced_default",
                "title": "平衡试探型",
                "thesis": "先用一版中性参数把策略跑通，再决定往哪边加码。",
                "fit_for": "适合描述还比较模糊的时候先验证方向。",
                "overrides": {},
                "highlights": ["风险平衡", "波段持有", "优先主板验证"],
            },
            {
                "id": "chip_first",
                "title": "筹码优先型",
                "thesis": "先把上方压力和筹码干净度放在第一位。",
                "fit_for": "适合你原本强调上方筹码干净的思路。",
                "overrides": {
                    "priority_signal": "chip",
                    "risk_tolerance": "conservative",
                },
                "highlights": ["上方压力更严", "筹码集中度更重要", "容忍更少噪音"],
            },
            {
                "id": "trend_first",
                "title": "趋势确认型",
                "thesis": "先确认均线、斜率和量能，再决定是否上车。",
                "fit_for": "适合不想太主观猜底，更看重右侧确认。",
                "overrides": {
                    "style_focus": "trend_start",
                    "priority_signal": "volume",
                    "risk_tolerance": "conservative",
                },
                "highlights": ["均线多头优先", "放量确认更严", "适合右侧交易"],
            },
        ]
        recommended_id = "balanced_default"

    selected_id = strategy.playbook_id
    return playbooks, recommended_id, selected_id


def _normalize_weights(config: StrategyConfig) -> None:
    total = (
        config.weights.chip
        + config.weights.technical
        + config.weights.base
        + config.weights.valuation
    )
    if total <= 0:
        config.weights.chip = 0.35
        config.weights.technical = 0.30
        config.weights.base = 0.20
        config.weights.valuation = 0.15
        return
    config.weights.chip = round(config.weights.chip / total, 4)
    config.weights.technical = round(config.weights.technical / total, 4)
    config.weights.base = round(config.weights.base / total, 4)
    config.weights.valuation = round(config.weights.valuation / total, 4)


def _config_from_strategy(strategy: StrategyInput) -> StrategyConfig:
    config = deepcopy(StrategyConfig())
    directives = _extract_narrative_directives(strategy.narrative)
    playbooks, _recommended_playbook_id, selected_playbook_id = _build_playbooks(strategy)

    selected_playbook = next(
        (item for item in playbooks if item["id"] == selected_playbook_id),
        None,
    )
    if selected_playbook:
        overrides = selected_playbook.get("overrides", {})
        strategy = StrategyInput(
            narrative=strategy.narrative,
            market_scope=strategy.market_scope,
            style_focus=overrides.get("style_focus", strategy.style_focus),
            holding_period=overrides.get("holding_period", strategy.holding_period),
            risk_tolerance=overrides.get("risk_tolerance", strategy.risk_tolerance),
            valuation_weight=overrides.get("valuation_weight", strategy.valuation_weight),
            priority_signal=overrides.get("priority_signal", strategy.priority_signal),
            playbook_id=selected_playbook_id,
        )

    if strategy.risk_tolerance == "conservative":
        config.chip.max_overhead_pressure = 0.05
        config.chip.min_winner_rate = 0.50
        config.technical.min_volume_ratio += 0.10
        config.base.max_range_90 = 0.30
        config.base.min_upside_to_high_250 = 0.18
        config.backtest.stop_loss = -0.06
        config.backtest.max_positions = 4
    elif strategy.risk_tolerance == "aggressive":
        config.chip.max_overhead_pressure = 0.08
        config.chip.min_winner_rate = 0.38
        config.technical.min_volume_ratio = 1.40
        config.base.max_range_90 = 0.45
        config.base.min_upside_to_high_250 = 0.10
        config.backtest.stop_loss = -0.10
        config.backtest.max_positions = 8

    if strategy.style_focus == "breakout":
        config.technical.min_volume_ratio = max(config.technical.min_volume_ratio, 1.80)
        config.technical.breakout_margin = 0.01
        config.weights.technical = 0.40
        config.weights.base = 0.18
    elif strategy.style_focus == "trend_start":
        config.technical.min_volume_ratio = max(1.50, config.technical.min_volume_ratio - 0.10)
        config.technical.breakout_margin = 0.03
        config.base.min_base_days = max(45, config.base.min_base_days - 10)
        config.weights.technical = 0.35
        config.weights.chip = 0.32
    elif strategy.style_focus == "rebound":
        config.technical.min_volume_ratio = 1.20
        config.technical.min_ma20_slope = 0.0002
        config.technical.min_ma60_slope = 0.0
        config.base.min_base_days = 35
        config.base.ideal_base_days = 80
        config.chip.min_winner_rate = min(config.chip.min_winner_rate, 0.38)
        config.weights.base = 0.28
        config.weights.technical = 0.24

    if strategy.holding_period == "short":
        config.base.min_base_days = min(config.base.min_base_days, 40)
        config.base.ideal_base_days = 80
        config.technical.min_volume_ratio += 0.10
        config.backtest.hold_days = 7
        config.backtest.stop_loss = max(config.backtest.stop_loss, -0.05)
        config.backtest.take_profit = 0.12
    elif strategy.holding_period == "trend":
        config.base.min_base_days = max(config.base.min_base_days, 90)
        config.base.ideal_base_days = 150
        config.base.max_close_to_high_250 = 0.75
        config.backtest.hold_days = 30
        config.backtest.stop_loss = min(config.backtest.stop_loss, -0.10)
        config.backtest.take_profit = 0.30

    if strategy.valuation_weight == "high":
        config.valuation.max_industry_pe_ratio = 0.80
        config.valuation.max_industry_pb_ratio = 0.82
        config.weights.valuation = 0.26
        config.weights.technical = max(0.20, config.weights.technical - 0.06)
    elif strategy.valuation_weight == "low":
        config.valuation.max_industry_pe_ratio = 1.10
        config.valuation.max_industry_pb_ratio = 1.10
        config.weights.valuation = 0.08
        config.weights.technical += 0.04

    if strategy.priority_signal == "chip":
        config.weights.chip = 0.45
        config.weights.technical = 0.24
        config.weights.base = 0.19
        config.weights.valuation = 0.12
    elif strategy.priority_signal == "volume":
        config.technical.min_volume_ratio += 0.20
        config.weights.chip = 0.24
        config.weights.technical = 0.46
        config.weights.base = 0.16
        config.weights.valuation = 0.14
    elif strategy.priority_signal == "base":
        config.base.min_base_days = max(config.base.min_base_days, 80)
        config.base.ideal_base_days = max(config.base.ideal_base_days, 140)
        config.weights.chip = 0.24
        config.weights.technical = 0.22
        config.weights.base = 0.38
        config.weights.valuation = 0.16
    elif strategy.priority_signal == "valuation":
        config.valuation.max_industry_pe_ratio = min(config.valuation.max_industry_pe_ratio, 0.85)
        config.valuation.max_industry_pb_ratio = min(config.valuation.max_industry_pb_ratio, 0.88)
        config.weights.chip = 0.23
        config.weights.technical = 0.20
        config.weights.base = 0.20
        config.weights.valuation = 0.37

    narrative = strategy.narrative.lower()
    if "涨停" in narrative or "limit up" in narrative:
        config.technical.require_limit_up_bonus = True
    if "放量" in narrative:
        config.technical.min_volume_ratio = max(config.technical.min_volume_ratio, 1.8)
    if "左侧" in narrative:
        config.technical.min_volume_ratio = max(1.20, config.technical.min_volume_ratio - 0.20)
        config.base.min_base_days = max(60, config.base.min_base_days)
    if "估值" in narrative:
        config.valuation.max_industry_pe_ratio = min(config.valuation.max_industry_pe_ratio, 0.90)
    if "筹码" in narrative:
        config.weights.chip += 0.05

    if directives.min_base_days is not None:
        config.base.min_base_days = directives.min_base_days
    if directives.ideal_base_days is not None:
        config.base.ideal_base_days = max(directives.ideal_base_days, config.base.min_base_days + 10)
    if directives.max_overhead_pressure is not None:
        config.chip.max_overhead_pressure = min(max(directives.max_overhead_pressure, 0.01), 0.20)
        config.chip.excellent_overhead_pressure = min(
            config.chip.excellent_overhead_pressure,
            max(config.chip.max_overhead_pressure * 0.6, 0.01),
        )
    if directives.min_volume_ratio is not None:
        config.technical.min_volume_ratio = max(1.0, min(directives.min_volume_ratio, 5.0))
    if directives.stop_loss is not None:
        config.backtest.stop_loss = directives.stop_loss
    if directives.take_profit is not None:
        config.backtest.take_profit = directives.take_profit
    if directives.require_limit_up:
        config.technical.require_limit_up_bonus = True
    if directives.prefer_left_side:
        config.technical.min_volume_ratio = max(1.1, config.technical.min_volume_ratio - 0.2)
        config.technical.breakout_margin = max(config.technical.breakout_margin, 0.04)
        config.weights.base += 0.03
        config.weights.technical -= 0.03
    if directives.prefer_right_side:
        config.technical.min_volume_ratio += 0.2
        config.technical.breakout_margin = min(config.technical.breakout_margin, 0.01)
        config.weights.technical += 0.04
    if directives.require_hot_sector:
        config.valuation.min_industry_hot_score = max(config.valuation.min_industry_hot_score, 0.68)
        config.valuation.min_board_hot_score = max(config.valuation.min_board_hot_score, 0.64)
    if directives.emphasize_valuation:
        config.valuation.max_industry_pe_ratio = min(config.valuation.max_industry_pe_ratio, 0.85)
        config.valuation.max_industry_pb_ratio = min(config.valuation.max_industry_pb_ratio, 0.88)
        config.weights.valuation += 0.05
    if directives.emphasize_chip:
        config.chip.max_chip_compact = min(config.chip.max_chip_compact, 0.15)
        config.weights.chip += 0.05
    if directives.emphasize_trend:
        config.technical.min_ma20_slope = max(config.technical.min_ma20_slope, 0.0012)
        config.technical.min_ma60_slope = max(config.technical.min_ma60_slope, 0.0006)
        config.weights.technical += 0.04

    _normalize_weights(config)
    return config


def build_strategy_plan(strategy: StrategyInput) -> dict[str, Any]:
    playbooks, recommended_playbook_id, selected_playbook_id = _build_playbooks(strategy)
    if selected_playbook_id:
        selected = next((item for item in playbooks if item["id"] == selected_playbook_id), None)
        if selected:
            strategy = StrategyInput(
                narrative=strategy.narrative,
                market_scope=strategy.market_scope,
                style_focus=selected.get("overrides", {}).get("style_focus", strategy.style_focus),
                holding_period=selected.get("overrides", {}).get("holding_period", strategy.holding_period),
                risk_tolerance=selected.get("overrides", {}).get("risk_tolerance", strategy.risk_tolerance),
                valuation_weight=selected.get("overrides", {}).get("valuation_weight", strategy.valuation_weight),
                priority_signal=selected.get("overrides", {}).get("priority_signal", strategy.priority_signal),
                playbook_id=selected_playbook_id,
            )
    style, holding, priority = _strategy_labels(strategy)
    config = _config_from_strategy(strategy)
    directives = _extract_narrative_directives(strategy.narrative)
    parsed_signal = "，".join(directives.notes[:3]) if directives.notes else "未识别到额外文字约束"

    return {
        "advice": [
            {
                "title": "推荐市场",
                "value": (
                    "先测主板"
                    if strategy.market_scope == "main_board"
                    else "单测科创板"
                    if strategy.market_scope == "star_market"
                    else "分市场分别测试"
                ),
                "detail": "不同市场波动差异大，参数不要直接混用。",
            },
            {
                "title": "上方压力",
                "value": f"{config.chip.excellent_overhead_pressure:.0%} - {config.chip.max_overhead_pressure:.0%}",
                "detail": "这是当前策略最关键的筹码阈值。",
            },
            {
                "title": "量比门槛",
                "value": f">= {config.technical.min_volume_ratio:.1f}",
                "detail": "量比越高，突破确认通常越强。",
            },
            {
                "title": "文字识别",
                "value": parsed_signal,
                "detail": "这部分来自你输入的自由描述，不是下拉框固定值。",
            },
        ],
        "parameters": [
            {
                "label": "核心风格",
                "value": f"{style} / {holding}",
                "hint": f"当前把 {priority} 作为主要驱动信号。",
            },
            {
                "label": "筑底时长",
                "value": f"{config.base.min_base_days} - {config.base.ideal_base_days} 天",
                "hint": "持股周期越长，通常越需要更完整的底部整理。",
            },
            {
                "label": "估值阈值",
                "value": f"PE <= {config.valuation.max_industry_pe_ratio:.2f}x 行业",
                "hint": "估值权重越高，对行业相对估值的要求越严。",
            },
            {
                "label": "回测口径",
                "value": f"持有 {config.backtest.hold_days} 天",
                "hint": f"止损 {config.backtest.stop_loss:.0%} / 止盈 {config.backtest.take_profit:.0%}",
            },
        ],
        "playbooks": playbooks,
        "selected_playbook_id": selected_playbook_id,
        "recommended_playbook_id": recommended_playbook_id,
        "parsed_rules": _build_parsed_rules(directives),
        "summary": (
            f"当前策略按“{style} + {holding}”理解，优先在"
            f"{SCOPE_LABELS.get(strategy.market_scope, strategy.market_scope)}里验证“{priority}”是否有效。"
            f"系统会根据你的风险偏好、估值要求和文字描述动态调整阈值。"
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
            "reasons": _translate_reasons(result.score.reasons),
        },
        "failed_reasons": _translate_reasons(result.failed_reasons),
        "metrics": {
            "volume_ratio": round(snapshot.volume_ratio, 4),
            "overhead_pressure": round(snapshot.overhead_pressure, 4),
            "base_days": snapshot.base_days,
        },
    }


def _cache_key(strategy: StrategyInput) -> str:
    narrative_hash = hashlib.sha1(strategy.narrative.strip().encode("utf-8")).hexdigest()[:12]
    return "|".join(
        [
            strategy.market_scope or MARKET_SCOPE_ALL,
            strategy.style_focus,
            strategy.holding_period,
            strategy.risk_tolerance,
            strategy.valuation_weight,
            strategy.priority_signal,
            narrative_hash,
            "fallback" if FORCE_FALLBACK else "live",
        ]
    )


def _scope_note(scope: str, live_data: bool) -> str:
    prefix = "当前使用真实样本。" if live_data else "当前使用演示样本。"
    if scope == "main_board":
        return prefix + " 主板更适合先验证估值修复和中等波段策略。"
    if scope == "star_market":
        return prefix + " 科创板波动更大，建议与主板分开回测。"
    if scope == "growth_board":
        return prefix + " 成长板更适合单独观察，不要与主板混合阈值。"
    return prefix + " 全市场结果更适合看分布，不适合直接混成一套参数。"


def _evaluate_snapshots(
    snapshots: list[DailySnapshot],
    strategy: StrategyInput,
    *,
    live_data: bool,
) -> dict[str, Any]:
    engine = ScreeningEngine(_config_from_strategy(strategy))
    ranked = engine.rank(snapshots, only_passed=False)
    return {
        "label": SCOPE_LABELS.get(strategy.market_scope, SCOPE_LABELS["all"]),
        "note": _scope_note(strategy.market_scope, live_data),
        "items": [_serialize_screening_result(item) for item in ranked],
        "live_data": live_data,
    }


def get_scope_results(strategy: StrategyInput) -> dict[str, Any]:
    scope = strategy.market_scope or MARKET_SCOPE_ALL
    cache_key = _cache_key(strategy)
    now = time.time()
    cached = _RESULT_CACHE.get(cache_key)
    if cached and now - cached[0] <= CACHE_TTL_SECONDS:
        return cached[1]

    fallback_snapshots = DEMO_SNAPSHOTS.get(scope, DEMO_SNAPSHOTS["all"])
    if FORCE_FALLBACK:
        result = _evaluate_snapshots(fallback_snapshots, strategy, live_data=False)
        _RESULT_CACHE[cache_key] = (now, result)
        return result

    try:
        symbols = LIVE_SAMPLE_SYMBOLS.get(scope) or LIVE_SAMPLE_SYMBOLS["all"]
        provider = AKShareProvider(symbols=symbols, max_symbols=len(symbols), market_scope=scope)
        snapshots = provider.fetch_daily_snapshots(date.today())
        if not snapshots:
            raise RuntimeError("No live snapshots returned")
        result = _evaluate_snapshots(snapshots, strategy, live_data=True)
        _RESULT_CACHE[cache_key] = (now, result)
        return result
    except Exception:
        result = _evaluate_snapshots(fallback_snapshots, strategy, live_data=False)
        _RESULT_CACHE[cache_key] = (now, result)
        return result


def build_mvp_payload(strategy: StrategyInput) -> dict[str, Any]:
    config = _config_from_strategy(strategy)
    return {
        "generated_at": date.today().isoformat(),
        "strategy": build_strategy_plan(strategy),
        "results": get_scope_results(strategy),
        "backtest": {
            "hold_days": config.backtest.hold_days,
            "stop_loss": f"{config.backtest.stop_loss:.0%}",
            "take_profit": f"{config.backtest.take_profit:.0%}",
            "max_positions": config.backtest.max_positions,
        },
    }
