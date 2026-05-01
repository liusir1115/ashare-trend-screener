from __future__ import annotations

from typing import Any

from ashare_strategy.mappers.strategy_plan_mapper import serialize_screening_result


def serialize_screening_results(results: list[Any]) -> list[dict[str, Any]]:
    return [serialize_screening_result(item) for item in results]


def build_source_status_payload(results: dict[str, Any], market_review: dict[str, Any]) -> dict[str, Any]:
    items = results.get("items", [])
    real_chip_count = sum(1 for item in items if item.get("metrics", {}).get("chip_source") == "akshare_stock_cyq_em")
    real_limit_count = sum(1 for item in items if item.get("metrics", {}).get("limit_source") == "akshare_stock_zt_pool_em")
    sample_count = len(items)
    screening_is_live = bool(results.get("live_data"))
    flow_is_live = bool(market_review.get("flow_live_data"))
    news_is_live = bool(market_review.get("news_live_data"))
    return {
        "headline": "真实数据优先，拿不到时自动切到演示兜底。",
        "items": [
            {"name": "候选股扫描", "state": "真实 AKShare" if screening_is_live else "演示兜底", "detail": f"本次样本 {sample_count} 只；真实模式会读取日线、实时行情和策略评分。", "ok": screening_is_live},
            {"name": "筹码分布", "state": f"{real_chip_count}/{sample_count} 只真实筹码" if sample_count else "暂无样本", "detail": "真实筹码来自 AKShare 的东方财富筹码接口；拿不到时用历史价格近似，页面会标出来。", "ok": real_chip_count > 0},
            {"name": "涨停/炸板", "state": f"{real_limit_count}/{sample_count} 只涨停池命中" if sample_count else "暂无样本", "detail": "优先读取东方财富涨停池和炸板池；不在池内时只用涨跌幅做粗略判断。", "ok": real_limit_count > 0},
            {"name": "新闻快讯", "state": "真实 AKShare" if news_is_live else "演示兜底", "detail": "用于盘前盘后看热点、政策、海外风险和新闻摘要。", "ok": news_is_live},
            {"name": "资金流复盘", "state": "真实 AKShare" if flow_is_live else "演示兜底", "detail": "用于盘后看行业/概念资金和高切低线索，免费接口偶尔会抽风。", "ok": flow_is_live},
            {"name": "策略问答", "state": "免费规则版", "detail": "能回答策略量化、候选原因、资金流和热点风险；开放式聊天以后再接大模型。", "ok": True},
        ],
        "tips": [
            "如果这里显示演示兜底，说明页面能用，但不能把结果当作真实盘后扫描。",
            "筹码分布最关键：优先看候选卡片里的“筹码来源”是不是东方财富筹码。",
        ],
    }


def attach_news_candidate_links(results: dict[str, Any], market_review: dict[str, Any]) -> dict[str, Any]:
    tag_keywords = {
        "科技": ["科技", "芯片", "半导体", "算力", "机器人", "AI"],
        "新能源": ["新能源", "能源", "电力", "储能", "锂电", "光伏"],
        "商品": ["煤炭", "原油", "黄金", "铜", "资源"],
        "政策": ["国企", "央企", "医药", "金融", "稳增长"],
        "海外": ["出口", "航运", "黄金", "资源"],
    }
    news_summary = market_review.get("news", {})
    hot_tags = [str(item.get("name", "")) for item in news_summary.get("hot_tags", [])]
    candidate_pool = [item for item in results.get("items", []) if item.get("passed_filters") or float(item.get("score", {}).get("total", 0)) >= 55][:5]
    linked_candidates: list[dict[str, str]] = []
    for item in candidate_pool:
        metrics = item.get("metrics", {})
        candidate_text = " ".join([str(metrics.get("limit_reason", "")), " ".join(item.get("score", {}).get("reasons", [])), " ".join(item.get("failed_reasons", []))])
        matched_tags = [tag for tag in hot_tags if any(keyword in candidate_text for keyword in tag_keywords.get(tag, []))]
        if matched_tags:
            note = f"更贴近今日“{matched_tags[0]}”线索，可优先结合新闻复核。"
        elif item.get("passed_filters"):
            note = "当前已经通过筛选，适合配合今天的热点继续跟踪。"
        else:
            note = "当前分数靠前，可结合新闻催化继续观察。"
        linked_candidates.append({"symbol": str(item.get("symbol", "")), "status": "通过" if item.get("passed_filters") else "观察", "note": note})
    candidate_note = "下面这些票是当天候选池里更值得和新闻一起看的。" if linked_candidates else "当前候选池还没有特别贴近热点的票，先以新闻摘要为主。"
    market_review["news"] = {**news_summary, "candidate_links": linked_candidates[:3], "candidate_note": candidate_note}
    return market_review
