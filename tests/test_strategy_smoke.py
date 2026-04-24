from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
import unittest

import ashare_strategy.mvp_service as mvp_service
import ashare_strategy.providers.akshare_provider as akshare_provider
from ashare_strategy.market_review import SectorFlow, _build_flow_summary, _build_news_summary, build_demo_market_review
from ashare_strategy.analytics import build_snapshot_from_bars
from ashare_strategy.backtest import BacktestEngine
from ashare_strategy.market import classify_market_segment, matches_market_scope
from ashare_strategy.models import DailyBar, DailySnapshot
from ashare_strategy.mvp_service import StrategyInput, build_mvp_payload, build_strategy_plan
from ashare_strategy.qa_service import answer_question
from ashare_strategy.providers.akshare_provider import AKShareProvider, _chip_profile_from_row
from ashare_strategy.providers.csv_provider import CSVProvider
from ashare_strategy.retry import load_with_retry
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
        result = ScreeningEngine().evaluate(self._snapshot())
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
            rows = CSVProvider(csv_path).fetch_daily_snapshots(snapshot.trade_date)
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
        original_force_fallback = mvp_service.FORCE_FALLBACK
        try:
            mvp_service.FORCE_FALLBACK = True
            mvp_service._RESULT_CACHE.clear()
            payload = build_mvp_payload(
                StrategyInput(
                    narrative="测试科创板策略",
                    market_scope="star_market",
                )
            )
        finally:
            mvp_service.FORCE_FALLBACK = original_force_fallback
            mvp_service._RESULT_CACHE.clear()
        self.assertIn("generated_at", payload)
        self.assertIn("strategy", payload)
        self.assertIn("results", payload)
        self.assertIn("market_review", payload)
        self.assertIn("source_status", payload)
        self.assertIn("backtest", payload)
        self.assertIsInstance(payload["results"]["items"], list)
        self.assertIn("playbooks", payload["strategy"])
        self.assertGreaterEqual(len(payload["strategy"]["playbooks"]), 1)
        metrics = payload["results"]["items"][0]["metrics"]
        self.assertIn("winner_rate", metrics)
        self.assertIn("chip_source_label", metrics)
        self.assertIn("limit_up", metrics)
        self.assertIn("broken_limit", metrics)
        self.assertIn("limit_open_times", metrics)
        self.assertIn("top_inflow", payload["market_review"])
        self.assertIn("top_outflow", payload["market_review"])
        self.assertIn("rotation", payload["market_review"])
        self.assertIn("news", payload["market_review"])
        self.assertIn("candidate_links", payload["market_review"]["news"])
        self.assertIn("candidate_note", payload["market_review"]["news"])
        self.assertGreaterEqual(len(payload["source_status"]["items"]), 5)

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
            [
                "Low overhead chip pressure",
                "moving averages are not in bullish alignment",
                "volume_ratio=0.89 below 1.50",
            ]
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
                    narrative="主板趋势启动，筑底3个月，上方压力5%，量比1.9，止损6%，止盈25%，最好涨停回封。",
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

    def test_akshare_chip_row_maps_to_strategy_costs(self) -> None:
        profile = _chip_profile_from_row(
            {
                "90成本-低": 10.0,
                "平均成本": 12.0,
                "90成本-高": 15.0,
                "获利比例": 65.0,
            }
        )
        self.assertEqual(profile, (10.0, 12.0, 15.0, 0.65))

    def test_akshare_provider_reads_chip_profile_without_network(self) -> None:
        class FakeFrame:
            empty = False

            def to_dict(self, orient: str) -> list[dict[str, object]]:
                return [
                    {"日期": "2026-04-20", "90成本-低": 8.0, "平均成本": 9.0, "90成本-高": 10.0, "获利比例": 45.0},
                    {"日期": "2026-04-22", "90成本-低": 9.0, "平均成本": 10.0, "90成本-高": 11.0, "获利比例": 0.60},
                ]

        class FakeAK:
            def stock_cyq_em(self, symbol: str, adjust: str) -> FakeFrame:
                self.symbol = symbol
                self.adjust = adjust
                return FakeFrame()

        original_loader = akshare_provider._require_akshare
        fake_ak = FakeAK()
        try:
            akshare_provider._require_akshare = lambda: fake_ak
            provider = AKShareProvider(adjust="qfq")
            profile = provider.fetch_chip_profile("000001.SZ", date(2026, 4, 22))
        finally:
            akshare_provider._require_akshare = original_loader

        self.assertEqual(profile, (9.0, 10.0, 11.0, 0.60))
        self.assertEqual(fake_ak.symbol, "000001")
        self.assertEqual(fake_ak.adjust, "qfq")

    def test_akshare_provider_reads_limit_pool_without_network(self) -> None:
        class FakeFrame:
            def __init__(self, rows: list[dict[str, object]]) -> None:
                self.rows = rows
                self.empty = False

            def to_dict(self, orient: str) -> list[dict[str, object]]:
                return self.rows

        class FakeAK:
            def stock_zt_pool_em(self, date: str) -> FakeFrame:
                return FakeFrame([{"代码": "000001", "炸板次数": 2, "首次封板时间": "09:35:00"}])

            def stock_zt_pool_zbgc_em(self, date: str) -> FakeFrame:
                return FakeFrame([{"代码": "600000"}])

        original_loader = akshare_provider._require_akshare
        try:
            akshare_provider._require_akshare = lambda: FakeAK()
            provider = AKShareProvider()
            provider._load_limit_pool_cache(date(2026, 4, 22))
        finally:
            akshare_provider._require_akshare = original_loader

        self.assertIn("000001", provider._limit_up_cache)
        self.assertIn("600000", provider._broken_limit_cache)

    def test_market_review_detects_high_low_rotation(self) -> None:
        summary = _build_flow_summary(
            [
                SectorFlow("电力", 0.8, 1_000_000_000, "行业资金流"),
                SectorFlow("半导体", 2.8, -900_000_000, "行业资金流"),
            ],
            [
                SectorFlow("算力", 3.2, -1_200_000_000, "概念资金流"),
                SectorFlow("煤炭", 0.7, 800_000_000, "行业资金流"),
            ],
        )
        self.assertIn("高切低", summary["rotation"]["summary"])
        self.assertEqual(summary["rotation"]["low_level_inflow"][0]["name"], "电力")
        self.assertEqual(summary["rotation"]["high_level_outflow"][0]["name"], "算力")

    def test_demo_market_review_shape(self) -> None:
        review = build_demo_market_review()
        self.assertIn("headline", review)
        self.assertFalse(review["live_data"])
        self.assertFalse(review["flow_live_data"])
        self.assertFalse(review["news_live_data"])
        self.assertGreaterEqual(len(review["top_inflow"]), 1)
        self.assertIn("news", review)
        self.assertGreaterEqual(len(review["news"]["items"]), 1)
        self.assertIn("candidate_links", review["news"])

    def test_news_summary_groups_hot_tags_and_risks(self) -> None:
        news = _build_news_summary(
            news_items=[
                type("NewsItem", (), {"title": "美联储释放降息信号", "time_text": "09:00", "tag": "海外", "source": "测试"})(),
                type("NewsItem", (), {"title": "AI 算力板块继续活跃", "time_text": "10:00", "tag": "科技", "source": "测试"})(),
                type("NewsItem", (), {"title": "高位题材出现下跌风险", "time_text": "11:00", "tag": "综合", "source": "测试"})(),
            ],
            board_changes=[],
        )
        self.assertIn("热点集中", news["headline"])
        self.assertGreaterEqual(len(news["hot_tags"]), 1)
        self.assertEqual(news["risks"][0]["tag"], "综合")

    def test_retry_helper_can_retry_once_then_succeed(self) -> None:
        attempts = {"count": 0}

        def flaky_loader() -> str:
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeError("temporary error")
            return "ok"

        result = load_with_retry(flaky_loader, retries=2, delay_seconds=0)
        self.assertEqual(result, "ok")
        self.assertEqual(attempts["count"], 2)

    def test_retry_helper_raises_last_error(self) -> None:
        with self.assertRaises(RuntimeError):
            load_with_retry(lambda: (_ for _ in ()).throw(RuntimeError("still failing")), retries=2, delay_seconds=0)

    def test_rule_qa_answers_market_flow_question(self) -> None:
        original_force_fallback = mvp_service.FORCE_FALLBACK
        try:
            mvp_service.FORCE_FALLBACK = True
            answer = answer_question("今天有没有高切低？", StrategyInput(narrative="反转策略"))
        finally:
            mvp_service.FORCE_FALLBACK = original_force_fallback

        self.assertEqual(answer["mode"], "规则问答")
        self.assertIn("高切低", answer["answer"])

    def test_rule_qa_answers_strategy_question(self) -> None:
        original_force_fallback = mvp_service.FORCE_FALLBACK
        try:
            mvp_service.FORCE_FALLBACK = True
            answer = answer_question("反转策略怎么量化？", StrategyInput(narrative="反转策略"))
        finally:
            mvp_service.FORCE_FALLBACK = original_force_fallback

        self.assertIn("筑底", answer["answer"])
        self.assertIn("回测口径", answer["answer"])

    def test_rule_qa_answers_candidate_question(self) -> None:
        original_force_fallback = mvp_service.FORCE_FALLBACK
        try:
            mvp_service.FORCE_FALLBACK = True
            answer = answer_question("为什么 600036 被淘汰？", StrategyInput(narrative="主板策略"))
        finally:
            mvp_service.FORCE_FALLBACK = original_force_fallback

        self.assertIn("600036", answer["answer"])
        self.assertIn("关键数据", answer["answer"])


if __name__ == "__main__":
    unittest.main()
