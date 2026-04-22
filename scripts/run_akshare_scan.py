from __future__ import annotations

import argparse
from datetime import date
import json
from pathlib import Path
from typing import Any

from ashare_strategy import load_strategy_config
from ashare_strategy.market import MARKET_SCOPE_ALL, VALID_MARKET_SCOPES
from ashare_strategy.providers.akshare_provider import AKShareProvider
from ashare_strategy.strategy import ScreeningEngine


def serialize_result(result: Any) -> dict[str, Any]:
    snapshot = result.snapshot
    return {
        "symbol": result.symbol,
        "market_segment": snapshot.market_segment,
        "trade_date": result.trade_date.isoformat(),
        "passed_filters": result.passed_filters,
        "score": {
            "chip": result.score.chip,
            "technical": result.score.technical,
            "base": result.score.base,
            "valuation": result.score.valuation,
            "total": result.score.total,
            "reasons": result.score.reasons,
        },
        "failed_reasons": result.failed_reasons,
        "metrics": {
            "close": snapshot.close,
            "volume_ratio": round(snapshot.volume_ratio, 4),
            "overhead_pressure": round(snapshot.overhead_pressure, 4),
            "chip_compact": round(snapshot.chip_compact, 4),
            "winner_rate": round(snapshot.winner_rate, 4),
            "base_days": snapshot.base_days,
            "range_90": round(snapshot.range_90, 4),
            "upside_to_high_250": round(snapshot.upside_to_high_250, 4),
        },
        "extra": snapshot.extra,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run AKShare-based A-share scan")
    parser.add_argument("--config", default="strategy.plan_a.toml", help="Path to strategy toml")
    parser.add_argument("--limit", type=int, default=20, help="How many results to print")
    parser.add_argument("--max-symbols", type=int, default=200, help="How many symbols to inspect")
    parser.add_argument("--symbols", help="Comma-separated stock codes, e.g. 000001,600519,300750")
    parser.add_argument(
        "--market-scope",
        default=MARKET_SCOPE_ALL,
        choices=sorted(VALID_MARKET_SCOPES),
        help="Limit scan to all, main_board, star_market, or growth_board",
    )
    parser.add_argument("--all", action="store_true", dest="show_all", help="Include failed results")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    config = load_strategy_config(args.config)
    symbols = [item.strip() for item in args.symbols.split(",")] if args.symbols else None
    provider = AKShareProvider(
        symbols=symbols,
        max_symbols=args.max_symbols,
        market_scope=args.market_scope,
    )
    engine = ScreeningEngine(config)
    snapshots = provider.fetch_daily_snapshots(trade_date=date.today())
    results = engine.rank(snapshots, only_passed=not args.show_all)
    serialized = [serialize_result(item) for item in results[: args.limit]]

    if args.output:
        output_path = Path(args.output)
        output_path.write_text(json.dumps(serialized, ensure_ascii=False, indent=2), encoding="utf-8")

    print(json.dumps(serialized, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
