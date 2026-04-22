"""A-share trend screener package."""

from .config import StrategyConfig, load_strategy_config
from .strategy import ScreeningEngine

__all__ = ["StrategyConfig", "ScreeningEngine", "load_strategy_config"]

