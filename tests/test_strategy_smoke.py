from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import unittest

import ashare_strategy.mvp_service as mvp_service
from ashare_strategy.analytics import build_snapshot_from_bars
from ashare_strategy.backtest import BacktestEngine
from ashare_strategy.market import classify_market_segment, matches_market_scope
from ashare_strategy.models import DailyBar, DailySnapshot
from ashare_strategy.mvp_service import StrategyInput, build_mvp_payload, build_strategy_plan
from ashare_strategy.providers.csv_provider import CSVProvider
from ashare_strategy.strategy import ScreeningEngine


class ScreeningSmokeTest(unittest.TestCase):
    def _snapshot(self) -> DailySnapshot:
        return DailySnapshot(
            symbol="000001.SZ",
            trade_date=date(2026, 4, 21),
            close=10.0,
            volume=1_000_000,
            volume_ratio=2.8,
            ma5=10.2,
            ma10=10.0,
            ma20=9.7,
            ma60=9.2,
            ma20_slope=0.003,
            ma60_slope=0.0012,
            breakout_high_120=10.1,
            cost_5pct=8.9,
            cost_50pct=9.5,
            cost_95pct=10.2,
            winner_rate=0.62,
            base_days=115,
            range_90=0.21,
            high_250=13.5,
            industry_hot_score=0.78,
            board_hot_score=0.71,
            industry_pe_ratio=0.75,
            industry_pb_ratio=0.82,
            limit_up=True,
        )

    def test_snapshot_passes_filters(self) -> None:
        engine = ScreeningEngine()
        result = engine.evaluate(self._snapshot())
        self.assertTrue(result.passed_filters)
        self.assertGreater(result.score.total, 70.0)

    def test_backtest_generates_trade(self) -> None:
        screening_snapshot = self._snapshot()
        bars = []
        start = screening_snapshot.trade_date
        prices = [10.1, 10.4, 10.8, 11.1, 11.4, 11.8]
        for offset, close in enumerate(prices):
            trade_day = start + timedelta(days=offset)
            bars.append(
                DailyBar(
                    symbol="000001.SZ",
                    trade_date=trade_day,
                    open=10.0 + offset * 0.1,
                    high=close + 0.1,
                    low=close - 0.2,
                    close=close,
                    volume=800_000 + offset * 10_000,
                )
            )
        report = BacktestEngine().run(
            snapshots_by_date={screening_snapshot.trade_date: [screening_snapshot]},
            bars_by_symbol={"000001.SZ": bars},
        )
        self.assertEqual(report.total_trades, 1)
        self.assertGreater(report.trades[0].raw_return, 0.0)

    def test_csv_provider_reads_snapshot(self) -> None:
        snapshot = self._snapshot()
        csv_path = Path("C:/Users/LENOVO/Documents/Codex/2026-04-21-codex/tests/.tmp_snapshots.csv")
        try:
            csv_path.write_text(
                "\n".join(
                    [
                        "symbol,trade_date,close,volume,volume_ratio,ma5,ma10,ma20,ma60,ma20_slope,ma60_slope,breakout_high_120,cost_5pct,cost_50pct,cost_95pct,winner_rate,base_days,range_90,high_250,industry_hot_score,board_hot_score,industry_pe_ratio,industry_pb_ratio,limit_up,relimit",
                        f"{snapshot.symbol},{snapshot.trade_date.isoformat()},{snapshot.close},{snapshot.volume},{snapshot.volume_ratio},{snapshot.ma5},{snapshot.ma10},{snapshot.ma20},{snapshot.ma60},{snapshot.ma20_slope},{snapshot.ma60_slope},{snapshot.breakout_high_120},{snapshot.cost_5pct},{snapshot.cost_50pct},{snapshot.cost_95pct},{snapshot.winner_rate},{snapshot.base_days},{snapshot.range_90},{snapshot.high_250},{snapshot.industry_hot_score},{snapshot.board_hot_score},{snapshot.industry_pe_ratio},{snapshot.industry_pb_ratio},{str(snapshot.limit_up).lower()},{str(snapshot.relimit).lower()}",
                    ]
                ),
                encoding="utf-8",
            )
            provider = CSVProvider(csv_path)
            rows = provider.fetch_daily_snapshots(snapshot.trade_date)
        finally:
            if csv_path.exists():
                csv_path.unlink()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].symbol, snapshot.symbol)
        self.assertTrue(rows[0].limit_up)

    def test_build_snapshot_from_bars(self) -> None:
        bars = []
        start = date(2025, 1, 1)
        price = 8.0
        for offset in range(260):
            trade_day = start + timedelta(days=offset)
            bars.append(
                DailyBar(
                    symbol="000001.SZ",
                    trade_date=trade_day,
                    open=price,
                    high=price * 1.02,
                    low=price * 0.99,
                    close=price * 1.01,
                    volume=800_000 + offset * 1_000,
                )
            )
            price += 0.02
        snapshot = build_snapshot_from_bars(
            "000001.SZ",
            bars,
            industry_hot_score=0.5,
            board_hot_score=0.5,
        )
        self.assertEqual(snapshot.symbol, "000001.SZ")
        self.assertGreater(snapshot.ma20, snapshot.ma60)
        self.assertGreater(snapshot.base_days, 0)
        self.assertIn("chip_source", snapshot.extra)

    def test_market_scope_helpers(self) -> None:
        self.assertEqual(classify_market_segment("600519.SH"), "main_board")
        self.assertEqual(classify_market_segment("688981.SH"), "star_market")
        self.assertEqual(classify_market_segment("300750.SZ"), "growth_board")
        self.assertTrue(matches_market_scope("600519.SH", "main_board"))
        self.assertFalse(matches_market_scope("688981.SH", "main_board"))

    def test_strategy_plan_shape(self) -> None:
        plan = build_strategy_plan(
            StrategyInput(
                narrative="测试主板波段突破策略",
                market_scope="main_board",
                style_focus="breakout",
                holding_period="swing",
                risk_tolerance="balanced",
                valuation_weight="medium",
                priority_signal="chip",
            )
        )
        self.assertEqual(len(plan["advice"]), 4)
        self.assertEqual(len(plan["parameters"]), 4)
        self.assertIn("parsed_rules", plan)
        self.assertIsInstance(plan["parsed_rules"], list)
        self.assertIn("group", plan["parsed_rules"][0])
        self.assertIn("label", plan["parsed_rules"][0])
        self.assertIn("主板", plan["summary"])

    def test_mvp_payload_shape(self) -> None:
        payload = build_mvp_payload(
            StrategyInput(
                narrative="测试科创板策略",
                market_scope="star_market",
            )
        )
        self.assertIn("generated_at", payload)
        self.assertIn("strategy", payload)
        self.assertIn("results", payload)
        self.assertIn("backtest", payload)
        self.assertIsInstance(payload["results"]["items"], list)
        self.assertIn("playbooks", payload["strategy"])
        self.assertGreaterEqual(len(payload["strategy"]["playbooks"]), 1)

    def test_strategy_changes_affect_fallback_results(self) -> None:
        original_force_fallback = mvp_service.FORCE_FALLBACK
        try:
            mvp_service.FORCE_FALLBACK = True
            mvp_service._RESULT_CACHE.clear()
            conservative = build_mvp_payload(
                StrategyInput(
                    narrative="主板 筹码 估值 左侧",
                    market_scope="main_board",
                    style_focus="breakout",
                    holding_period="swing",
                    risk_tolerance="conservative",
                    valuation_weight="high",
                    priority_signal="chip",
                )
            )
            aggressive = build_mvp_payload(
                StrategyInput(
                    narrative="主板 放量 趋势启动",
                    market_scope="main_board",
                    style_focus="trend_start",
                    holding_period="trend",
                    risk_tolerance="aggressive",
                    valuation_weight="low",
                    priority_signal="volume",
                )
            )
        finally:
            mvp_service.FORCE_FALLBACK = original_force_fallback
            mvp_service._RESULT_CACHE.clear()

        conservative_items = conservative["results"]["items"]
        aggressive_items = aggressive["results"]["items"]
        self.assertNotEqual(conservative["backtest"]["hold_days"], aggressive["backtest"]["hold_days"])
        self.assertNotEqual(conservative_items[0]["score"]["total"], aggressive_items[0]["score"]["total"])

    def test_mvp_cache_key_uses_full_strategy(self) -> None:
        key_a = mvp_service._cache_key(
            StrategyInput(
                narrative="主板策略A",
                market_scope="main_board",
                style_focus="breakout",
                holding_period="swing",
                risk_tolerance="balanced",
                valuation_weight="medium",
                priority_signal="chip",
            )
        )
        key_b = mvp_service._cache_key(
            StrategyInput(
                narrative="主板策略B",
                market_scope="main_board",
                style_focus="trend_start",
                holding_period="trend",
                risk_tolerance="aggressive",
                valuation_weight="low",
                priority_signal="volume",
            )
        )
        self.assertNotEqual(key_a, key_b)

    def test_narrative_directives_extract_numeric_rules(self) -> None:
        directives = mvp_service._extract_narrative_directives(
            "我想做左侧，筑底3个月，上方压力5%，量比1.9，止损8%，止盈20%，最好有涨停回封。"
        )
        self.assertEqual(directives.min_base_days, 60)
        self.assertAlmostEqual(directives.max_overhead_pressure, 0.05)
        self.assertAlmostEqual(directives.min_volume_ratio, 1.9)
        self.assertAlmostEqual(directives.stop_loss, -0.08)
        self.assertAlmostEqual(directives.take_profit, 0.20)
        self.assertTrue(directives.require_limit_up)
        self.assertTrue(directives.prefer_left_side)

    def test_reason_translation_outputs_chinese(self) -> None:
        translated = mvp_service._translate_reasons(
            ["Low overhead chip pressure", "moving averages are not in bullish alignment", "volume_ratio=0.89 below 1.50"]
        )
        self.assertEqual(translated[0], "上方筹码压力较小")
        self.assertEqual(translated[1], "均线尚未形成多头排列")
        self.assertIn("量比", translated[2])

    def test_reversal_narrative_generates_playbooks(self) -> None:
        playbooks, recommended_id, selected_id = mvp_service._build_playbooks(
            StrategyInput(
                narrative="反转策略",
                market_scope="main_board",
            )
        )
        self.assertGreaterEqual(len(playbooks), 3)
        self.assertEqual(recommended_id, "reversal_base")
        self.assertIsNone(selected_id)

    def test_selected_playbook_changes_payload(self) -> None:
        original_force_fallback = mvp_service.FORCE_FALLBACK
        try:
            mvp_service.FORCE_FALLBACK = True
            mvp_service._RESULT_CACHE.clear()
            base = build_mvp_payload(
                StrategyInput(
                    narrative="反转策略",
                    market_scope="main_board",
                    playbook_id="reversal_base",
                )
            )
            right = build_mvp_payload(
                StrategyInput(
                    narrative="反转策略",
                    market_scope="main_board",
                    playbook_id="reversal_right",
                )
            )
        finally:
            mvp_service.FORCE_FALLBACK = original_force_fallback
            mvp_service._RESULT_CACHE.clear()

        self.assertNotEqual(base["strategy"]["selected_playbook_id"], right["strategy"]["selected_playbook_id"])
        self.assertNotEqual(base["strategy"]["summary"], right["strategy"]["summary"])
        self.assertNotEqual(base["strategy"]["parameters"][0]["value"], right["strategy"]["parameters"][0]["value"])

    def test_narrative_alone_can_change_results(self) -> None:
        original_force_fallback = mvp_service.FORCE_FALLBACK
        try:
            mvp_service.FORCE_FALLBACK = True
            mvp_service._RESULT_CACHE.clear()
            plain = build_mvp_payload(
                StrategyInput(
                    narrative="主板趋势启动",
                    market_scope="main_board",
                    style_focus="trend_start",
                    holding_period="swing",
                    risk_tolerance="balanced",
                    valuation_weight="medium",
                    priority_signal="chip",
                )
            )
            detailed = build_mvp_payload(
                StrategyInput(
                    narrative="主板趋势启动，筑底3个月，上方压力5%，量比1.9，止损6%，止盈25%，最好涨停回封",
                    market_scope="main_board",
                    style_focus="trend_start",
                    holding_period="swing",
                    risk_tolerance="balanced",
                    valuation_weight="medium",
                    priority_signal="chip",
                )
            )
        finally:
            mvp_service.FORCE_FALLBACK = original_force_fallback
            mvp_service._RESULT_CACHE.clear()

        self.assertNotEqual(plain["backtest"]["stop_loss"], detailed["backtest"]["stop_loss"])
        self.assertNotEqual(plain["backtest"]["take_profit"], detailed["backtest"]["take_profit"])
        self.assertNotEqual(plain["results"]["items"][0]["score"]["total"], detailed["results"]["items"][0]["score"]["total"])


if __name__ == "__main__":
    unittest.main()
