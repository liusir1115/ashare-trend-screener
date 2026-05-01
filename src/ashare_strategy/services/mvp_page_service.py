from __future__ import annotations

import os
from typing import Any

from ashare_strategy.contracts import StrategyInput
from ashare_strategy.core.config import StrategyConfig
from ashare_strategy.mappers.strategy_plan_mapper import build_playbook_headline, build_strategy_plan as mapper_build_strategy_plan
from ashare_strategy.services.mvp_result_service import build_mvp_payload_data, cache_key as service_cache_key, get_scope_results as service_get_scope_results
from ashare_strategy.services.strategy_config_service import apply_playbook_overrides, config_from_strategy, normalize_weights
from ashare_strategy.services.strategy_language_service import (
    build_parsed_rules,
    build_playbooks,
    extract_narrative_directives,
    strategy_labels,
    translate_reason,
    translate_reasons,
)

CACHE_TTL_SECONDS = int(os.getenv("MVP_CACHE_TTL_SECONDS", "900"))
FORCE_FALLBACK = os.getenv("MVP_FORCE_FALLBACK", "").strip().lower() in {"1", "true", "yes"}
RESULT_CACHE: dict[str, tuple[float, dict[str, Any]]] = {}
_RESULT_CACHE = RESULT_CACHE
_build_parsed_rules = build_parsed_rules
_build_playbooks = build_playbooks
_extract_narrative_directives = extract_narrative_directives
_strategy_labels = strategy_labels
_translate_reason = translate_reason
_translate_reasons = translate_reasons


def build_strategy_plan(strategy: StrategyInput) -> dict[str, Any]:
    return mapper_build_strategy_plan(
        strategy,
        apply_playbook_overrides=apply_playbook_overrides,
        build_playbooks=build_playbooks,
        strategy_labels=strategy_labels,
        config_from_strategy=config_from_strategy,
        extract_narrative_directives=extract_narrative_directives,
        build_parsed_rules=build_parsed_rules,
        build_playbook_headline=build_playbook_headline,
    )


def build_mvp_payload(strategy: StrategyInput) -> dict[str, Any]:
    return build_mvp_payload_data(
        strategy,
        force_fallback=FORCE_FALLBACK,
        result_cache=RESULT_CACHE,
        cache_ttl_seconds=CACHE_TTL_SECONDS,
        config_from_strategy=config_from_strategy,
        build_strategy_plan=build_strategy_plan,
    )


def cache_key(strategy: StrategyInput) -> str:
    return service_cache_key(strategy, force_fallback=FORCE_FALLBACK)


def _cache_key(strategy: StrategyInput) -> str:
    return cache_key(strategy)


def get_scope_results(strategy: StrategyInput) -> dict[str, Any]:
    return service_get_scope_results(
        strategy,
        force_fallback=FORCE_FALLBACK,
        result_cache=RESULT_CACHE,
        cache_ttl_seconds=CACHE_TTL_SECONDS,
        config_from_strategy=config_from_strategy,
    )


__all__ = [
    "CACHE_TTL_SECONDS",
    "FORCE_FALLBACK",
    "RESULT_CACHE",
    "StrategyInput",
    "apply_playbook_overrides",
    "build_mvp_payload",
    "build_parsed_rules",
    "build_playbooks",
    "build_strategy_plan",
    "cache_key",
    "config_from_strategy",
    "extract_narrative_directives",
    "get_scope_results",
    "normalize_weights",
    "strategy_labels",
    "translate_reason",
    "translate_reasons",
]
