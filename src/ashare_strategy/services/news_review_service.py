from __future__ import annotations

from typing import Any

from ashare_strategy.repositories import fetch_market_review


def build_news_review(*, force_fallback: bool) -> dict[str, Any]:
    market_review = fetch_market_review(force_fallback=force_fallback)
    return market_review.get("news", {})


__all__ = ["build_news_review"]
