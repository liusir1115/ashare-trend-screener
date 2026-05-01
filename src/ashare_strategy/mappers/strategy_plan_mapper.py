from __future__ import annotations

from typing import Any

from ashare_strategy.services.strategy_language_service import SCOPE_LABELS, translate_reasons


def build_strategy_plan(
    strategy: Any,
    *,
    apply_playbook_overrides: Any,
    build_playbooks: Any,
    strategy_labels: Any,
    config_from_strategy: Any,
    extract_narrative_directives: Any,
    build_parsed_rules: Any,
    build_playbook_headline: Any,
) -> dict[str, Any]:
    playbooks, recommended_playbook_id, selected_playbook_id = build_playbooks(strategy)
    effective_strategy = apply_playbook_overrides(strategy)
    style_label, holding_label, priority_label = strategy_labels(effective_strategy)
    config = config_from_strategy(effective_strategy)
    directives = extract_narrative_directives(effective_strategy.narrative)
    parsed_signal = "；".join(directives.notes[:3]) if directives.notes else "未识别到额外文字约束"
    return {
        "advice": [
            {"title": "推荐市场", "value": "先测主板" if effective_strategy.market_scope == "main_board" else "单测科创板" if effective_strategy.market_scope == "star_market" else "分市场分别测试", "detail": "不同市场波动差别大，参数不要直接混用。"},
            {"title": "上方压力", "value": f"{config.chip.excellent_overhead_pressure:.0%} - {config.chip.max_overhead_pressure:.0%}", "detail": "这是当前策略最关键的筹码阈值。"},
            {"title": "量比门槛", "value": f">= {config.technical.min_volume_ratio:.1f}", "detail": "量比越高，突破确认通常越强。"},
            {"title": "文字识别", "value": parsed_signal, "detail": "这里展示的是系统从你输入的话里读到的内容。"},
        ],
        "parameters": [
            {"label": "核心风格", "value": f"{style_label} / {holding_label}", "hint": f"当前把“{priority_label}”当作主要驱动信号。"},
            {"label": "筑底时长", "value": f"{config.base.min_base_days} - {config.base.ideal_base_days} 天", "hint": "持股周期越长，通常越需要更完整的底部整理。"},
            {"label": "估值阈值", "value": f"PE <= {config.valuation.max_industry_pe_ratio:.2f}x 行业", "hint": "估值权重越高，对相对估值的要求越严。"},
            {"label": "回测口径", "value": f"持有 {config.backtest.hold_days} 天", "hint": f"止损 {config.backtest.stop_loss:.0%} / 止盈 {config.backtest.take_profit:.0%}"},
        ],
        "playbooks": playbooks,
        "selected_playbook_id": selected_playbook_id,
        "recommended_playbook_id": recommended_playbook_id,
        "parsed_rules": build_parsed_rules(directives),
        "playbook_headline": build_playbook_headline(effective_strategy.narrative, playbooks),
        "summary": f"当前策略按“{style_label} + {holding_label}”理解，优先在{SCOPE_LABELS.get(effective_strategy.market_scope, effective_strategy.market_scope)}里验证“{priority_label}”是否有效。系统会根据你的风险偏好、估值要求和文字描述动态调参数。",
    }


def build_playbook_headline(narrative: str, playbooks: list[dict[str, Any]]) -> str:
    narrative_lower = narrative.lower()
    if any(keyword in narrative_lower for keyword in ["反转", "反弹", "v反", "拐头"]):
        return "我把“反转策略”拆成了几套常见做法，你可以先选一套再看结果。"
    if any(keyword in narrative_lower for keyword in ["突破", "启动", "主升", "放量"]):
        return "这段描述更像趋势启动，我先给你几套突破版本。"
    if playbooks:
        return "你的描述还比较模糊，我先给你几套可落地的默认版本。"
    return "系统会先给出几套可量化方案，再由你决定采用哪一套。"


def chip_source_label(source: str) -> str:
    if source == "akshare_stock_cyq_em":
        return "东方财富筹码"
    if source == "approx_close_quantiles":
        return "近似筹码"
    return "未知来源"


def limit_source_label(source: str) -> str:
    if source == "akshare_stock_zt_pool_em":
        return "东方财富涨停池"
    if source == "spot_change_pct":
        return "涨跌幅估算"
    return "未知来源"


def scope_note(scope: str, live_data: bool) -> str:
    prefix = "当前使用真实样本。" if live_data else "当前使用演示样本。"
    if scope == "main_board":
        return prefix + " 主板更适合先验证估值修复和中等波段策略。"
    if scope == "star_market":
        return prefix + " 科创板波动更大，建议与主板分开回测。"
    if scope == "growth_board":
        return prefix + " 成长板更适合单独观察，不建议与主板共用一套阈值。"
    return prefix + " 全市场结果更适合看分布，不适合直接混成一套参数。"


def serialize_screening_result(result: Any) -> dict[str, Any]:
    snapshot = result.snapshot
    chip_source = str(snapshot.extra.get("chip_source", "unknown"))
    limit_source = str(snapshot.extra.get("limit_source", "unknown"))
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
            "reasons": translate_reasons(result.score.reasons),
        },
        "failed_reasons": translate_reasons(result.failed_reasons),
        "metrics": {
            "volume_ratio": round(snapshot.volume_ratio, 4),
            "overhead_pressure": round(snapshot.overhead_pressure, 4),
            "base_days": snapshot.base_days,
            "winner_rate": round(snapshot.winner_rate, 4),
            "cost_5pct": round(snapshot.cost_5pct, 4),
            "cost_50pct": round(snapshot.cost_50pct, 4),
            "cost_95pct": round(snapshot.cost_95pct, 4),
            "chip_source": chip_source,
            "chip_source_label": chip_source_label(chip_source),
            "limit_up": snapshot.limit_up,
            "relimit": snapshot.relimit,
            "broken_limit": bool(snapshot.extra.get("broken_limit", False)),
            "first_limit_time": str(snapshot.extra.get("first_limit_time", "")),
            "last_limit_time": str(snapshot.extra.get("last_limit_time", "")),
            "limit_open_times": int(snapshot.extra.get("limit_open_times", 0) or 0),
            "limit_reason": str(snapshot.extra.get("limit_reason", "")),
            "limit_source": limit_source,
            "limit_source_label": limit_source_label(limit_source),
        },
    }
