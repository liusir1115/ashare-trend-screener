from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Any

SCOPE_LABELS = {
    "all": "全市场",
    "main_board": "主板",
    "star_market": "科创板",
    "growth_board": "成长板",
}

STYLE_LABELS = {
    "breakout": "平台突破",
    "trend_start": "趋势启动",
    "rebound": "底部反转",
}

HOLDING_LABELS = {
    "swing": "波段持有",
    "short": "短线快进快出",
    "trend": "趋势跟随",
}

PRIORITY_LABELS = {
    "chip": "筹码结构",
    "volume": "放量突破",
    "base": "筑底时长",
    "valuation": "估值修复",
}


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


def build_parsed_rules(directives: NarrativeDirectives) -> list[dict[str, str]]:
    rules: list[dict[str, str]] = []

    if directives.min_base_days is not None:
        rules.append({"group": "数值规则", "label": f"筑底时长 >= {directives.min_base_days} 天"})
    if directives.max_overhead_pressure is not None:
        rules.append({"group": "数值规则", "label": f"上方压力 <= {directives.max_overhead_pressure:.0%}"})
    if directives.min_volume_ratio is not None:
        rules.append({"group": "数值规则", "label": f"量比 >= {directives.min_volume_ratio:.1f}"})
    if directives.stop_loss is not None:
        rules.append({"group": "交易管理", "label": f"止损 {abs(directives.stop_loss):.0%}"})
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
        rules.append({"group": "风格偏好", "label": "强调趋势和均线"})

    return rules or [{"group": "系统判断", "label": "未识别到额外文字约束"}]


def translate_reason(reason: str) -> str:
    exact_map = {
        "Low overhead chip pressure": "上方筹码压力较小",
        "Chip distribution is compact": "筹码分布较集中",
        "Limit-up confirmation appeared": "出现涨停确认",
        "Re-sealed after opening intraday": "盘中开板后回封",
        "Volume expanded sharply": "量能明显放大",
        "Base-building period is long enough": "筑底时长较充分",
        "There is still room to prior highs": "距离前高仍有上涨空间",
        "Sector heat is elevated": "行业热度较高",
        "moving averages are not in bullish alignment": "均线尚未形成多头排列",
        "missing breakout confirmation": "突破确认不足",
        "limit-up style confirmation required by config": "当前策略要求涨停或回封确认",
    }
    if reason in exact_map:
        return exact_map[reason]

    patterns: list[tuple[str, str]] = [
        (r"overhead_pressure=([\d.]+%) above ([\d.]+%)", r"上方压力 \1 高于阈值 \2"),
        (r"chip_compact=([\d.]+%) above ([\d.]+%)", r"筹码集中区间 \1 高于阈值 \2"),
        (r"winner_rate=([\d.]+%) below ([\d.]+%)", r"获利盘比例 \1 低于阈值 \2"),
        (r"ma20_slope=([-\d.]+) below ([-\d.]+)", r"MA20 斜率 \1 低于阈值 \2"),
        (r"ma60_slope=([-\d.]+) below ([-\d.]+)", r"MA60 斜率 \1 低于阈值 \2"),
        (r"volume_ratio=([\d.]+) below ([\d.]+)", r"量比 \1 低于阈值 \2"),
        (r"base_days=(\d+) below (\d+)", r"筑底天数 \1 低于阈值 \2"),
        (r"range_90=([\d.]+%) above ([\d.]+%)", r"近90天振幅 \1 高于阈值 \2"),
        (r"close/high_250=([\d.]+) above ([\d.]+)", r"当前价格离250日高点太近：\1，高于阈值 \2"),
        (r"upside_to_high_250=([\d.]+%) below ([\d.]+%)", r"距离前高空间 \1 低于阈值 \2"),
        (r"industry_pe_ratio=([\d.]+) above ([\d.]+)", r"行业相对PE \1 高于阈值 \2"),
        (r"industry_pb_ratio=([\d.]+) above ([\d.]+)", r"行业相对PB \1 高于阈值 \2"),
        (r"industry_hot_score=([\d.]+) below ([\d.]+)", r"行业热度 \1 低于阈值 \2"),
        (r"board_hot_score=([\d.]+) below ([\d.]+)", r"板块热度 \1 低于阈值 \2"),
    ]

    for pattern, replacement in patterns:
        if re.search(pattern, reason):
            return re.sub(pattern, replacement, reason)

    return reason


def translate_reasons(reasons: list[str]) -> list[str]:
    return [translate_reason(reason) for reason in reasons]


def extract_narrative_directives(narrative: str) -> NarrativeDirectives:
    text = narrative.lower()
    directives = NarrativeDirectives(notes=[])

    month_match = re.search(r"(?:筑底|横盘|盘整|底部).{0,10}?(\d{1,2})\s*个?\s*月", text)
    if month_match:
        months = int(month_match.group(1))
        directives.min_base_days = months * 20
        directives.ideal_base_days = months * 20 + 20
        directives.notes.append(f"识别到筑底时长约 {months} 个月")
    else:
        day_match = re.search(r"(?:筑底|横盘|盘整|底部).{0,10}?(\d{2,3})\s*天", text)
        if day_match:
            days = int(day_match.group(1))
            directives.min_base_days = days
            directives.ideal_base_days = days + 20
            directives.notes.append(f"识别到筑底时长约 {days} 天")

    pressure_match = re.search(r"(?:上方压力|压力|套牢盘).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%", text)
    if pressure_match:
        directives.max_overhead_pressure = float(pressure_match.group(1)) / 100
        directives.notes.append(f"识别到上方压力阈值 {pressure_match.group(1)}%")

    volume_match = re.search(r"(?:量比|放量).{0,8}?(\d(?:\.\d+)?)", text)
    if volume_match:
        directives.min_volume_ratio = float(volume_match.group(1))
        directives.notes.append(f"识别到量比门槛 {volume_match.group(1)}")

    stop_loss_match = re.search(r"(?:止损|回撤).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%", text)
    if stop_loss_match:
        directives.stop_loss = -float(stop_loss_match.group(1)) / 100
        directives.notes.append(f"识别到止损 {stop_loss_match.group(1)}%")

    take_profit_match = re.search(r"(?:止盈|目标收益).{0,8}?(\d{1,2}(?:\.\d+)?)\s*%", text)
    if take_profit_match:
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


def strategy_labels(strategy: Any) -> tuple[str, str, str]:
    return (
        STYLE_LABELS.get(strategy.style_focus, strategy.style_focus),
        HOLDING_LABELS.get(strategy.holding_period, strategy.holding_period),
        PRIORITY_LABELS.get(strategy.priority_signal, strategy.priority_signal),
    )


def build_playbooks(strategy: Any) -> tuple[list[dict[str, Any]], str | None, str | None]:
    text = strategy.narrative.lower()
    playbooks: list[dict[str, Any]]

    if any(keyword in text for keyword in ["反转", "反弹", "v反", "拐头"]):
        playbooks = [
            {
                "id": "reversal_base",
                "title": "底部反转型",
                "thesis": "更强调筑底、均线拐头和压力释放，不追求最强爆量。",
                "fit_for": "适合想做中短波段反转、能接受先试错后确认的人。",
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
                "thesis": "更早介入，放松放量要求，但更看重筹码和空间。",
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
                "thesis": "要求站回均线和放量确认，宁可晚一点，也更稳一点。",
                "fit_for": "适合不想猜底，想看到转强信号再上车。",
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
                "fit_for": "适合你原本的趋势启动思路。",
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
                "thesis": "在突破逻辑里，额外强调估值不过热和行业匹配。",
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
                "highlights": ["量比 >= 2.0", "持有 3-7 天", "更强调强信号"],
            },
        ]
        recommended_id = "breakout_classic"
    else:
        playbooks = [
            {
                "id": "balanced_default",
                "title": "平衡试探型",
                "thesis": "先用一套中性参数把策略跑通，再决定往哪边加码。",
                "fit_for": "适合描述还比较模糊时先验证方向。",
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

    return playbooks, recommended_id, strategy.playbook_id
