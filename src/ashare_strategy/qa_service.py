from __future__ import annotations

from typing import Any

from ashare_strategy.mvp_service import StrategyInput, build_mvp_payload


def answer_question(question: str, strategy: StrategyInput) -> dict[str, Any]:
    payload = build_mvp_payload(strategy)
    text = question.strip()
    lower_text = text.lower()

    if not text:
        return _answer("你可以问：为什么某只票被淘汰、今天有没有高切低、反转策略怎么量化。", payload)

    if _has_any(text, ["高切低", "切换", "资金流向", "资金去了哪里", "资金"]):
        return _answer_market_flow(payload)

    if _has_any(text, ["反转", "怎么量化", "策略怎么设", "参数"]):
        return _answer_strategy_quant(payload)

    if _has_any(text, ["为什么", "淘汰", "入选", "通过", "候选"]):
        symbol = _find_symbol(text, payload["results"]["items"])
        return _answer_candidate(symbol, payload)

    if _has_any(text, ["风险", "热点", "新闻", "资讯"]):
        return _answer_news(payload)

    if "保守" in text:
        return _answer("可以把风险偏好改成“偏稳”，同时把上方压力收紧到 3%-5%，量比保持 1.5 以上。", payload)

    if "激进" in text:
        return _answer("可以把风险偏好改成“偏激进”，允许上方压力到 5%-8%，但最好配合更紧的止损。", payload)

    return _answer(
        "这个免费问答目前只覆盖策略解释、候选原因、资金流、高切低和热点风险。更开放的发散问答后面需要接大模型。",
        payload,
    )


def _answer_market_flow(payload: dict[str, Any]) -> dict[str, Any]:
    review = payload["market_review"]
    inflow = review.get("top_inflow", [])[:3]
    outflow = review.get("top_outflow", [])[:3]
    rotation = review.get("rotation", {})
    lines = [rotation.get("summary", "暂时没有高切低判断。")]
    if inflow:
        lines.append("流入靠前：" + "、".join(f"{item['name']}({item['net_inflow_text']})" for item in inflow))
    if outflow:
        lines.append("流出靠前：" + "、".join(f"{item['name']}({item['net_inflow_text']})" for item in outflow))
    return _answer("\n".join(lines), payload)


def _answer_strategy_quant(payload: dict[str, Any]) -> dict[str, Any]:
    strategy = payload["strategy"]
    parameters = strategy.get("parameters", [])
    lines = [strategy.get("summary", "当前没有策略摘要。")]
    for item in parameters[:4]:
        lines.append(f"{item['label']}：{item['value']}。{item['hint']}")
    return _answer("\n".join(lines), payload)


def _answer_candidate(symbol: str | None, payload: dict[str, Any]) -> dict[str, Any]:
    items = payload["results"]["items"]
    candidate = next((item for item in items if item["symbol"] == symbol), items[0] if items else None)
    if candidate is None:
        return _answer("当前没有候选结果可以解释。", payload)

    reasons = candidate["score"]["reasons"] if candidate["passed_filters"] else candidate["failed_reasons"]
    status = "通过" if candidate["passed_filters"] else "未通过"
    metrics = candidate["metrics"]
    answer = (
        f"{candidate['symbol']} 当前状态：{status}，总分 {candidate['score']['total']}。\n"
        f"主要原因：{'；'.join(reasons[:3]) or '暂无原因'}。\n"
        f"关键数据：上方压力 {metrics['overhead_pressure']:.1%}，获利盘 {metrics.get('winner_rate', 0):.1%}，"
        f"量比 {metrics['volume_ratio']}，筹码来源 {metrics.get('chip_source_label', '未知')}。"
    )
    return _answer(answer, payload)


def _answer_news(payload: dict[str, Any]) -> dict[str, Any]:
    news = payload["market_review"].get("news", {})
    risks = news.get("risks", [])
    lines = [news.get("headline", "暂时没有热点摘要。")]
    if risks:
        lines.append("风险提示：" + "；".join(item["title"] for item in risks[:3]))
    return _answer("\n".join(lines), payload)


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)


def _find_symbol(text: str, items: list[dict[str, Any]]) -> str | None:
    for item in items:
        symbol = item["symbol"]
        if symbol in text or symbol[:6] in text:
            return symbol
    return None


def _answer(answer: str, payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "answer": answer,
        "mode": "规则问答",
        "suggestions": [
            "为什么第一只票被淘汰？",
            "今天有没有高切低？",
            "反转策略怎么量化？",
            "当前有什么风险？",
        ],
        "generated_at": payload["generated_at"],
    }
