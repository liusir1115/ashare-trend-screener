from __future__ import annotations

from dataclasses import asdict
from typing import Iterable

from ashare_strategy.config import StrategyConfig
from ashare_strategy.models import DailySnapshot, ScoreBreakdown, ScreeningResult


def _clamp(value: float, lower: float = 0.0, upper: float = 100.0) -> float:
    return max(lower, min(value, upper))


def _score_inverse(value: float, excellent: float, maximum: float) -> float:
    if value <= excellent:
        return 100.0
    if value >= maximum:
        return 0.0
    ratio = (value - excellent) / (maximum - excellent)
    return _clamp(100.0 * (1.0 - ratio))


def _score_forward(value: float, minimum: float, ideal: float) -> float:
    if value <= minimum:
        return 0.0
    if value >= ideal:
        return 100.0
    ratio = (value - minimum) / (ideal - minimum)
    return _clamp(100.0 * ratio)


class ScreeningEngine:
    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()

    def evaluate(self, snapshot: DailySnapshot) -> ScreeningResult:
        failed = self._hard_filters(snapshot)
        score = self._score(snapshot)
        return ScreeningResult(
            symbol=snapshot.symbol,
            trade_date=snapshot.trade_date,
            passed_filters=not failed,
            score=score,
            snapshot=snapshot,
            failed_reasons=failed,
        )

    def rank(self, snapshots: Iterable[DailySnapshot], only_passed: bool = True) -> list[ScreeningResult]:
        results = [self.evaluate(snapshot) for snapshot in snapshots]
        if only_passed:
            results = [item for item in results if item.passed_filters]
        return sorted(results, key=lambda item: item.score.total, reverse=True)

    def _hard_filters(self, snapshot: DailySnapshot) -> list[str]:
        failed: list[str] = []
        chip = self.config.chip
        technical = self.config.technical
        base = self.config.base
        valuation = self.config.valuation

        if snapshot.overhead_pressure > chip.max_overhead_pressure:
            failed.append(
                f"overhead_pressure={snapshot.overhead_pressure:.2%} above {chip.max_overhead_pressure:.2%}"
            )
        if snapshot.chip_compact > chip.max_chip_compact:
            failed.append(
                f"chip_compact={snapshot.chip_compact:.2%} above {chip.max_chip_compact:.2%}"
            )
        if snapshot.winner_rate < chip.min_winner_rate:
            failed.append(f"winner_rate={snapshot.winner_rate:.2%} below {chip.min_winner_rate:.2%}")
        if not (snapshot.ma5 > snapshot.ma10 > snapshot.ma20 > snapshot.ma60):
            failed.append("moving averages are not in bullish alignment")
        if snapshot.ma20_slope < technical.min_ma20_slope:
            failed.append(
                f"ma20_slope={snapshot.ma20_slope:.4f} below {technical.min_ma20_slope:.4f}"
            )
        if snapshot.ma60_slope < technical.min_ma60_slope:
            failed.append(
                f"ma60_slope={snapshot.ma60_slope:.4f} below {technical.min_ma60_slope:.4f}"
            )
        breakout_threshold = snapshot.breakout_high_120 * (1.0 - technical.breakout_margin)
        if snapshot.close < breakout_threshold and not snapshot.limit_up and not snapshot.relimit:
            failed.append("missing breakout confirmation")
        if snapshot.volume_ratio < technical.min_volume_ratio:
            failed.append(
                f"volume_ratio={snapshot.volume_ratio:.2f} below {technical.min_volume_ratio:.2f}"
            )
        if snapshot.base_days < base.min_base_days:
            failed.append(f"base_days={snapshot.base_days} below {base.min_base_days}")
        if snapshot.range_90 > base.max_range_90:
            failed.append(f"range_90={snapshot.range_90:.2%} above {base.max_range_90:.2%}")
        if snapshot.close_to_high_250 > base.max_close_to_high_250:
            failed.append(
                f"close/high_250={snapshot.close_to_high_250:.2f} above {base.max_close_to_high_250:.2f}"
            )
        if snapshot.upside_to_high_250 < base.min_upside_to_high_250:
            failed.append(
                f"upside_to_high_250={snapshot.upside_to_high_250:.2%} below {base.min_upside_to_high_250:.2%}"
            )
        if snapshot.industry_pe_ratio is not None and snapshot.industry_pe_ratio > valuation.max_industry_pe_ratio:
            failed.append(
                f"industry_pe_ratio={snapshot.industry_pe_ratio:.2f} above {valuation.max_industry_pe_ratio:.2f}"
            )
        if snapshot.industry_pb_ratio is not None and snapshot.industry_pb_ratio > valuation.max_industry_pb_ratio:
            failed.append(
                f"industry_pb_ratio={snapshot.industry_pb_ratio:.2f} above {valuation.max_industry_pb_ratio:.2f}"
            )
        if snapshot.industry_hot_score < valuation.min_industry_hot_score:
            failed.append(
                f"industry_hot_score={snapshot.industry_hot_score:.2f} below {valuation.min_industry_hot_score:.2f}"
            )
        if snapshot.board_hot_score < valuation.min_board_hot_score:
            failed.append(
                f"board_hot_score={snapshot.board_hot_score:.2f} below {valuation.min_board_hot_score:.2f}"
            )
        if technical.require_limit_up_bonus and not (snapshot.limit_up or snapshot.relimit):
            failed.append("limit-up style confirmation required by config")
        return failed

    def _score(self, snapshot: DailySnapshot) -> ScoreBreakdown:
        chip_cfg = self.config.chip
        tech_cfg = self.config.technical
        base_cfg = self.config.base

        reasons: list[str] = []

        chip_parts = [
            _score_inverse(
                snapshot.overhead_pressure,
                chip_cfg.excellent_overhead_pressure,
                chip_cfg.max_overhead_pressure,
            ),
            _score_inverse(
                snapshot.chip_compact,
                chip_cfg.excellent_chip_compact,
                chip_cfg.max_chip_compact,
            ),
            _score_forward(snapshot.winner_rate, chip_cfg.min_winner_rate, 0.75),
        ]
        chip_score = sum(chip_parts) / len(chip_parts)
        if snapshot.overhead_pressure <= chip_cfg.excellent_overhead_pressure:
            reasons.append("Low overhead chip pressure")
        if snapshot.chip_compact <= chip_cfg.excellent_chip_compact:
            reasons.append("Chip distribution is compact")

        ma_alignment_score = 100.0 if snapshot.ma5 > snapshot.ma10 > snapshot.ma20 > snapshot.ma60 else 0.0
        breakout_threshold = snapshot.breakout_high_120 * (1.0 - tech_cfg.breakout_margin)
        breakout_score = 100.0 if snapshot.close >= breakout_threshold else 0.0
        volume_score = _score_forward(snapshot.volume_ratio, tech_cfg.min_volume_ratio, tech_cfg.strong_volume_ratio)
        slope_score = (
            _score_forward(snapshot.ma20_slope, tech_cfg.min_ma20_slope, tech_cfg.min_ma20_slope * 4)
            + _score_forward(snapshot.ma60_slope, tech_cfg.min_ma60_slope, tech_cfg.min_ma60_slope * 4)
        ) / 2.0
        limit_up_bonus = 15.0 if snapshot.limit_up else 8.0 if snapshot.relimit else 0.0
        technical_score = _clamp(
            (ma_alignment_score + breakout_score + volume_score + slope_score) / 4.0 + limit_up_bonus
        )
        if snapshot.limit_up:
            reasons.append("Limit-up confirmation appeared")
        elif snapshot.relimit:
            reasons.append("Re-sealed after opening intraday")
        if snapshot.volume_ratio >= tech_cfg.strong_volume_ratio:
            reasons.append("Volume expanded sharply")

        base_days_score = _score_forward(snapshot.base_days, base_cfg.min_base_days, base_cfg.ideal_base_days)
        range_score = _score_inverse(snapshot.range_90, 0.20, base_cfg.max_range_90)
        space_score = _score_forward(snapshot.upside_to_high_250, base_cfg.min_upside_to_high_250, 0.40)
        base_score = (base_days_score + range_score + space_score) / 3.0
        if snapshot.base_days >= base_cfg.ideal_base_days:
            reasons.append("Base-building period is long enough")
        if snapshot.upside_to_high_250 >= 0.30:
            reasons.append("There is still room to prior highs")

        pe_score = 60.0
        pb_score = 60.0
        if snapshot.industry_pe_ratio is not None:
            pe_score = _score_inverse(snapshot.industry_pe_ratio, 0.60, self.config.valuation.max_industry_pe_ratio)
        if snapshot.industry_pb_ratio is not None:
            pb_score = _score_inverse(snapshot.industry_pb_ratio, 0.60, self.config.valuation.max_industry_pb_ratio)
        hot_score = (
            _score_forward(snapshot.industry_hot_score, self.config.valuation.min_industry_hot_score, 0.85)
            + _score_forward(snapshot.board_hot_score, self.config.valuation.min_board_hot_score, 0.80)
        ) / 2.0
        valuation_score = (pe_score + pb_score + hot_score) / 3.0
        if snapshot.industry_hot_score >= 0.75 or snapshot.board_hot_score >= 0.70:
            reasons.append("Sector heat is elevated")

        total = (
            chip_score * self.config.weights.chip
            + technical_score * self.config.weights.technical
            + base_score * self.config.weights.base
            + valuation_score * self.config.weights.valuation
        )
        return ScoreBreakdown(
            chip=round(chip_score, 2),
            technical=round(technical_score, 2),
            base=round(base_score, 2),
            valuation=round(valuation_score, 2),
            total=round(total, 2),
            reasons=reasons,
        )

    def config_dict(self) -> dict[str, object]:
        return asdict(self.config)
