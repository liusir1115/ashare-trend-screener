from __future__ import annotations

from typing import Any

from ashare_strategy.repositories import fetch_market_review


def build_market_flow_review(*, force_fallback: bool) -> dict[str, Any]:
    market_review = fetch_market_review(force_fallback=force_fallback)
    return {
        "headline": market_review.get("headline", ""),
        "top_inflow": market_review.get("top_inflow", []),
        "top_outflow": market_review.get("top_outflow", []),
        "rotation": market_review.get("rotation", {}),
        "flow_live_data": market_review.get("flow_live_data", False),
    }


__all__ = ["build_market_flow_review"]
