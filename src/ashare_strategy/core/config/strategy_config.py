from __future__ import annotations

from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
import tomllib
from typing import Any, TypeVar

T = TypeVar("T")


def _build_dataclass(cls: type[T], payload: dict[str, Any] | None) -> T:
    payload = payload or {}
    allowed = {item.name for item in fields(cls)}
    return cls(**{key: value for key, value in payload.items() if key in allowed})


@dataclass(slots=True)
class ChipConfig:
    max_overhead_pressure: float = 0.06
    excellent_overhead_pressure: float = 0.03
    max_chip_compact: float = 0.18
    excellent_chip_compact: float = 0.10
    min_winner_rate: float = 0.45


@dataclass(slots=True)
class TechnicalConfig:
    min_volume_ratio: float = 1.8
    strong_volume_ratio: float = 2.5
    min_ma20_slope: float = 0.001
    min_ma60_slope: float = 0.0005
    breakout_lookback_days: int = 120
    breakout_margin: float = 0.02
    require_limit_up_bonus: bool = False


@dataclass(slots=True)
class BaseConfig:
    min_base_days: int = 60
    ideal_base_days: int = 120
    max_range_90: float = 0.35
    max_close_to_high_250: float = 0.80
    min_upside_to_high_250: float = 0.20


@dataclass(slots=True)
class ValuationConfig:
    max_industry_pe_ratio: float = 0.90
    max_industry_pb_ratio: float = 0.90
    min_industry_hot_score: float = 0.55
    min_board_hot_score: float = 0.50


@dataclass(slots=True)
class ScoreWeights:
    chip: float = 0.35
    technical: float = 0.30
    base: float = 0.20
    valuation: float = 0.15


@dataclass(slots=True)
class BacktestConfig:
    hold_days: int = 20
    max_positions: int = 5
    position_size: float = 0.20
    stop_loss: float = -0.08
    take_profit: float = 0.20


@dataclass(slots=True)
class StrategyConfig:
    chip: ChipConfig = field(default_factory=ChipConfig)
    technical: TechnicalConfig = field(default_factory=TechnicalConfig)
    base: BaseConfig = field(default_factory=BaseConfig)
    valuation: ValuationConfig = field(default_factory=ValuationConfig)
    weights: ScoreWeights = field(default_factory=ScoreWeights)
    backtest: BacktestConfig = field(default_factory=BacktestConfig)

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None = None) -> "StrategyConfig":
        payload = payload or {}
        return cls(
            chip=_build_dataclass(ChipConfig, payload.get("chip")),
            technical=_build_dataclass(TechnicalConfig, payload.get("technical")),
            base=_build_dataclass(BaseConfig, payload.get("base")),
            valuation=_build_dataclass(ValuationConfig, payload.get("valuation")),
            weights=_build_dataclass(ScoreWeights, payload.get("weights")),
            backtest=_build_dataclass(BacktestConfig, payload.get("backtest")),
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_strategy_config(path: str | Path | None = None) -> StrategyConfig:
    if path is None:
        return StrategyConfig()
    config_path = Path(path)
    with config_path.open("rb") as file_obj:
        payload = tomllib.load(file_obj)
    return StrategyConfig.from_dict(payload)
