from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class StrategyInput:
    """这里是前后端共用的策略输入结构，统一一套字段名字。"""

    narrative: str
    market_scope: str = "main_board"
    style_focus: str = "breakout"
    holding_period: str = "swing"
    risk_tolerance: str = "balanced"
    valuation_weight: str = "medium"
    priority_signal: str = "chip"
    playbook_id: str | None = None
