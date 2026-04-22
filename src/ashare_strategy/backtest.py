from __future__ import annotations

from collections import defaultdict
from datetime import date

from ashare_strategy.config import StrategyConfig
from ashare_strategy.models import BacktestReport, DailyBar, DailySnapshot, TradeRecord
from ashare_strategy.strategy import ScreeningEngine


class BacktestEngine:
    def __init__(self, config: StrategyConfig | None = None) -> None:
        self.config = config or StrategyConfig()
        self.screening = ScreeningEngine(self.config)

    def run(
        self,
        snapshots_by_date: dict[date, list[DailySnapshot]],
        bars_by_symbol: dict[str, list[DailyBar]],
    ) -> BacktestReport:
        trade_candidates: list[TradeRecord] = []
        bars_index = {
            symbol: sorted(bars, key=lambda item: item.trade_date)
            for symbol, bars in bars_by_symbol.items()
        }
        bars_lookup = {
            symbol: {bar.trade_date: index for index, bar in enumerate(series)}
            for symbol, series in bars_index.items()
        }

        for signal_date in sorted(snapshots_by_date):
            ranked = self.screening.rank(snapshots_by_date[signal_date], only_passed=True)
            for candidate in ranked[: self.config.backtest.max_positions]:
                series = bars_index.get(candidate.symbol, [])
                index_map = bars_lookup.get(candidate.symbol, {})
                signal_index = index_map.get(signal_date)
                if signal_index is None or signal_index + 1 >= len(series):
                    continue
                entry_bar = series[signal_index + 1]
                exit_bar, holding_days = self._find_exit(series, signal_index + 1)
                raw_return = (exit_bar.close - entry_bar.open) / entry_bar.open
                trade_candidates.append(
                    TradeRecord(
                        symbol=candidate.symbol,
                        signal_date=signal_date,
                        entry_date=entry_bar.trade_date,
                        exit_date=exit_bar.trade_date,
                        entry_price=entry_bar.open,
                        exit_price=exit_bar.close,
                        raw_return=round(raw_return, 4),
                        holding_days=holding_days,
                        score=candidate.score.total,
                    )
                )

        return self._build_report(trade_candidates)

    def _find_exit(self, series: list[DailyBar], entry_index: int) -> tuple[DailyBar, int]:
        cfg = self.config.backtest
        entry_bar = series[entry_index]
        planned_exit = min(entry_index + cfg.hold_days, len(series) - 1)
        for index in range(entry_index, planned_exit + 1):
            bar = series[index]
            change = (bar.close - entry_bar.open) / entry_bar.open
            if change <= cfg.stop_loss or change >= cfg.take_profit:
                return bar, index - entry_index + 1
        return series[planned_exit], planned_exit - entry_index + 1

    def _build_report(self, trades: list[TradeRecord]) -> BacktestReport:
        if not trades:
            return BacktestReport(
                total_trades=0,
                win_rate=0.0,
                average_return=0.0,
                cumulative_return=0.0,
                max_drawdown=0.0,
                trades=[],
            )

        equity = 1.0
        peak = 1.0
        max_drawdown = 0.0
        wins = 0
        total_return = 0.0

        for trade in trades:
            total_return += trade.raw_return
            if trade.raw_return > 0:
                wins += 1
            equity *= 1.0 + trade.raw_return * self.config.backtest.position_size
            peak = max(peak, equity)
            drawdown = (equity - peak) / peak
            max_drawdown = min(max_drawdown, drawdown)

        return BacktestReport(
            total_trades=len(trades),
            win_rate=round(wins / len(trades), 4),
            average_return=round(total_return / len(trades), 4),
            cumulative_return=round(equity - 1.0, 4),
            max_drawdown=round(max_drawdown, 4),
            trades=trades,
        )

