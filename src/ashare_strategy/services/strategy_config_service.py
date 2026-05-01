from __future__ import annotations

from copy import deepcopy

from ashare_strategy.core.config import StrategyConfig
from ashare_strategy.contracts import StrategyInput
from ashare_strategy.services.strategy_language_service import build_playbooks, extract_narrative_directives


def apply_playbook_overrides(strategy: StrategyInput) -> StrategyInput:
    playbooks, _recommended_id, selected_id = build_playbooks(strategy)
    if not selected_id:
        return strategy

    selected_playbook = next((item for item in playbooks if item["id"] == selected_id), None)
    if not selected_playbook:
        return strategy

    overrides = selected_playbook.get("overrides", {})
    # 这里是把用户选中的方案正式套到策略里，后面所有计算都按这套参数跑。
    return StrategyInput(
        narrative=strategy.narrative,
        market_scope=strategy.market_scope,
        style_focus=overrides.get("style_focus", strategy.style_focus),
        holding_period=overrides.get("holding_period", strategy.holding_period),
        risk_tolerance=overrides.get("risk_tolerance", strategy.risk_tolerance),
        valuation_weight=overrides.get("valuation_weight", strategy.valuation_weight),
        priority_signal=overrides.get("priority_signal", strategy.priority_signal),
        playbook_id=selected_id,
    )


def normalize_weights(config: StrategyConfig) -> None:
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


def config_from_strategy(strategy: StrategyInput) -> StrategyConfig:
    strategy = apply_playbook_overrides(strategy)
    config = deepcopy(StrategyConfig())
    directives = extract_narrative_directives(strategy.narrative)

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

    normalize_weights(config)
    return config
