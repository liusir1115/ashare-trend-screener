from __future__ import annotations

from datetime import date
import hashlib
import time
from typing import Any

from ashare_strategy.contracts import StrategyInput
from ashare_strategy.core.models import DailySnapshot
from ashare_strategy.mappers import attach_news_candidate_links, build_source_status_payload, serialize_screening_results
from ashare_strategy.mappers.strategy_plan_mapper import scope_note
from ashare_strategy.repositories import fetch_demo_snapshots, fetch_live_snapshots, fetch_market_review
from ashare_strategy.core.scoring import ScreeningEngine
from ashare_strategy.services.strategy_language_service import SCOPE_LABELS
from ashare_strategy.utils.market_scope import MARKET_SCOPE_ALL


def cache_key(strategy: StrategyInput, *, force_fallback: bool) -> str:
    narrative_hash = hashlib.sha1(strategy.narrative.strip().encode("utf-8")).hexdigest()[:12]
    return "|".join(
        [
            strategy.market_scope or MARKET_SCOPE_ALL,
            strategy.style_focus,
            strategy.holding_period,
            strategy.risk_tolerance,
            strategy.valuation_weight,
            strategy.priority_signal,
            strategy.playbook_id or "no-playbook",
            narrative_hash,
            "fallback" if force_fallback else "live",
        ]
    )


def evaluate_snapshots(
    snapshots: list[DailySnapshot],
    strategy: StrategyInput,
    *,
    live_data: bool,
    config_from_strategy,
) -> dict[str, Any]:
    engine = ScreeningEngine(config_from_strategy(strategy))
    ranked = engine.rank(snapshots, only_passed=False)
    return {
        "label": SCOPE_LABELS.get(strategy.market_scope, SCOPE_LABELS["all"]),
        "note": scope_note(strategy.market_scope, live_data),
        "items": serialize_screening_results(ranked),
        "live_data": live_data,
    }


def get_scope_results(
    strategy: StrategyInput,
    *,
    force_fallback: bool,
    result_cache: dict[str, tuple[float, dict[str, Any]]],
    cache_ttl_seconds: int,
    config_from_strategy,
) -> dict[str, Any]:
    scope = strategy.market_scope or MARKET_SCOPE_ALL
    request_key = cache_key(strategy, force_fallback=force_fallback)
    now = time.time()
    cached = result_cache.get(request_key)
    if cached and now - cached[0] <= cache_ttl_seconds:
        return cached[1]

    fallback_snapshots = fetch_demo_snapshots(scope)
    if force_fallback:
        result = evaluate_snapshots(
            fallback_snapshots,
            strategy,
            live_data=False,
            config_from_strategy=config_from_strategy,
        )
        result_cache[request_key] = (now, result)
        return result

    try:
        snapshots = fetch_live_snapshots(scope, date.today())
        if not snapshots:
            raise RuntimeError("No live snapshots returned")
        result = evaluate_snapshots(
            snapshots,
            strategy,
            live_data=True,
            config_from_strategy=config_from_strategy,
        )
        result_cache[request_key] = (now, result)
        return result
    except Exception:
        result = evaluate_snapshots(
            fallback_snapshots,
            strategy,
            live_data=False,
            config_from_strategy=config_from_strategy,
        )
        result_cache[request_key] = (now, result)
        return result


def build_mvp_payload_data(
    strategy: StrategyInput,
    *,
    force_fallback: bool,
    result_cache: dict[str, tuple[float, dict[str, Any]]],
    cache_ttl_seconds: int,
    config_from_strategy,
    build_strategy_plan,
) -> dict[str, Any]:
    config = config_from_strategy(strategy)
    results = get_scope_results(
        strategy,
        force_fallback=force_fallback,
        result_cache=result_cache,
        cache_ttl_seconds=cache_ttl_seconds,
        config_from_strategy=config_from_strategy,
    )
    market_review = fetch_market_review(force_fallback=force_fallback)
    market_review = attach_news_candidate_links(results, market_review)
    return {
        "generated_at": date.today().isoformat(),
        "strategy": build_strategy_plan(strategy),
        "results": results,
        "market_review": market_review,
        "source_status": build_source_status_payload(results, market_review),
        "backtest": {
            "hold_days": config.backtest.hold_days,
            "stop_loss": f"{config.backtest.stop_loss:.0%}",
            "take_profit": f"{config.backtest.take_profit:.0%}",
            "max_positions": config.backtest.max_positions,
        },
    }
