from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable

from ashare_strategy.retry import load_with_retry


def _require_akshare() -> Any:
    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("AKShare is not installed.") from exc
    return ak


def _pick(row: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in row:
            return row[name]
    return None


def _as_float(value: Any) -> float:
    if value in (None, "", "-", "--"):
        return 0.0
    try:
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return 0.0


def _format_money(value: float) -> str:
    if abs(value) >= 100_000_000:
        return f"{value / 100_000_000:.1f}亿"
    if abs(value) >= 10_000:
        return f"{value / 10_000:.1f}万"
    return f"{value:.0f}"


@dataclass(slots=True)
class SectorFlow:
    name: str
    change_pct: float
    net_inflow: float
    source: str


@dataclass(slots=True)
class NewsItem:
    title: str
    time_text: str
    tag: str
    source: str


def _read_sector_flows(loader: Callable[[], Any], source: str) -> list[SectorFlow]:
    try:
        frame = load_with_retry(loader)
    except Exception:
        return []
    if frame is None or frame.empty:
        return []

    flows: list[SectorFlow] = []
    for row in frame.to_dict(orient="records"):
        name = str(_pick(row, "名称", "板块名称", "行业", "概念") or "")
        if not name:
            continue
        flows.append(
            SectorFlow(
                name=name,
                change_pct=_as_float(_pick(row, "涨跌幅", "今日涨跌幅", "涨跌幅%")),
                net_inflow=_as_float(_pick(row, "主力净流入", "今日主力净流入", "净流入", "资金净流入")),
                source=source,
            )
        )
    return flows


def _read_news_items(loader: Callable[[], Any], source: str, limit: int = 8) -> list[NewsItem]:
    try:
        frame = load_with_retry(loader)
    except Exception:
        return []
    if frame is None or frame.empty:
        return []

    items: list[NewsItem] = []
    for row in frame.to_dict(orient="records"):
        title = str(_pick(row, "标题", "内容", "摘要", "消息", "新闻标题") or "").strip()
        if not title:
            continue
        items.append(
            NewsItem(
                title=title[:120],
                time_text=str(_pick(row, "时间", "发布时间", "日期") or ""),
                tag=_news_tag(title),
                source=source,
            )
        )
        if len(items) >= limit:
            break
    return items


def _read_board_changes(loader: Callable[[], Any], limit: int = 8) -> list[NewsItem]:
    try:
        frame = load_with_retry(loader)
    except Exception:
        return []
    if frame is None or frame.empty:
        return []

    items: list[NewsItem] = []
    for row in frame.to_dict(orient="records"):
        board_name = str(_pick(row, "板块名称", "名称", "板块") or "").strip()
        change_reason = str(_pick(row, "异动类型", "异动原因", "事件") or "").strip()
        if not board_name and not change_reason:
            continue
        title = f"{board_name}：{change_reason}".strip("：")
        items.append(NewsItem(title=title[:120], time_text="", tag="板块异动", source="板块异动"))
        if len(items) >= limit:
            break
    return items


def _news_tag(title: str) -> str:
    rules = [
        ("海外", ["美联储", "美元", "美股", "纳斯达克", "道琼斯", "欧洲", "日本"]),
        ("商品", ["原油", "黄金", "铜", "煤炭", "天然气", "大宗"]),
        ("政策", ["国务院", "发改委", "工信部", "证监会", "央行", "政策"]),
        ("科技", ["AI", "人工智能", "算力", "芯片", "半导体", "机器人"]),
        ("新能源", ["光伏", "储能", "锂电", "电力", "能源", "新能源"]),
    ]
    for tag, keywords in rules:
        if any(keyword.lower() in title.lower() for keyword in keywords):
            return tag
    return "综合"


def _build_news_summary(news_items: list[NewsItem], board_changes: list[NewsItem]) -> dict[str, Any]:
    combined = [*news_items, *board_changes]
    tag_counts: dict[str, int] = {}
    for item in combined:
        tag_counts[item.tag] = tag_counts.get(item.tag, 0) + 1

    hot_tags = sorted(tag_counts.items(), key=lambda item: item[1], reverse=True)[:4]
    if hot_tags:
        headline = "热点集中在：" + "、".join(tag for tag, _count in hot_tags)
    else:
        headline = "暂未抓到明显热点。"

    risk_keywords = ["加息", "制裁", "下跌", "风险", "调查", "冲突", "减持"]
    risk_items = [item for item in combined if any(keyword in item.title for keyword in risk_keywords)][:5]

    return {
        "headline": headline,
        "hot_tags": [{"name": tag, "count": count} for tag, count in hot_tags],
        "items": [_serialize_news(item) for item in combined[:10]],
        "risks": [_serialize_news(item) for item in risk_items],
        "candidate_links": [],
        "candidate_note": "这里会结合候选池补充更值得联动观察的股票。",
    }


def _serialize_news(item: NewsItem) -> dict[str, str]:
    return {
        "title": item.title,
        "time": item.time_text,
        "tag": item.tag,
        "source": item.source,
    }


def _build_flow_summary(industry_flows: list[SectorFlow], concept_flows: list[SectorFlow]) -> dict[str, Any]:
    all_flows = [*industry_flows, *concept_flows]
    inflow = sorted(all_flows, key=lambda item: item.net_inflow, reverse=True)[:5]
    outflow = sorted(all_flows, key=lambda item: item.net_inflow)[:5]
    low_level_inflow = [
        item for item in inflow if item.net_inflow > 0 and item.change_pct <= 1.5
    ]
    high_level_outflow = [
        item for item in outflow if item.net_inflow < 0 and item.change_pct >= 1.5
    ]

    if low_level_inflow and high_level_outflow:
        rotation_text = "出现高切低迹象：部分涨幅较高方向流出，低位或涨幅较小方向承接资金。"
    elif low_level_inflow:
        rotation_text = "有低位承接迹象：资金流入涨幅不高的方向，但高位流出还不明显。"
    elif high_level_outflow:
        rotation_text = "高位方向有资金流出迹象，但低位承接方向还不够集中。"
    else:
        rotation_text = "暂未看到明显高切低，资金更像是在少数强势方向里集中。"

    return {
        "top_inflow": [_serialize_flow(item) for item in inflow],
        "top_outflow": [_serialize_flow(item) for item in outflow],
        "rotation": {
            "summary": rotation_text,
            "low_level_inflow": [_serialize_flow(item) for item in low_level_inflow[:3]],
            "high_level_outflow": [_serialize_flow(item) for item in high_level_outflow[:3]],
        },
    }


def _serialize_flow(flow: SectorFlow) -> dict[str, Any]:
    return {
        "name": flow.name,
        "change_pct": round(flow.change_pct, 2),
        "net_inflow": round(flow.net_inflow, 2),
        "net_inflow_text": _format_money(flow.net_inflow),
        "source": flow.source,
    }


def _demo_news_summary() -> dict[str, Any]:
    return {
        "headline": "热点集中在：政策、科技、商品",
        "hot_tags": [
            {"name": "政策", "count": 3},
            {"name": "科技", "count": 2},
            {"name": "商品", "count": 2},
        ],
        "items": [
            {"title": "政策端继续强调稳增长和新质生产力方向", "time": "盘后", "tag": "政策", "source": "演示快讯"},
            {"title": "海外科技股波动加大，AI 算力方向分歧提升", "time": "盘后", "tag": "科技", "source": "演示快讯"},
            {"title": "原油和煤炭价格走强，资源方向关注度上升", "time": "盘后", "tag": "商品", "source": "演示快讯"},
        ],
        "risks": [
            {"title": "高位题材出现资金流出，短线追高风险增加", "time": "盘后", "tag": "风险", "source": "演示快讯"}
        ],
        "candidate_links": [],
        "candidate_note": "这里会结合候选池补充更值得联动观察的股票。",
    }


def build_demo_market_review() -> dict[str, Any]:
    industry_flows = [
        SectorFlow("电力", 0.8, 1_620_000_000, "演示行业资金"),
        SectorFlow("煤炭", 1.1, 980_000_000, "演示行业资金"),
        SectorFlow("算力", 3.4, -1_250_000_000, "演示概念资金"),
        SectorFlow("半导体", 2.2, -860_000_000, "演示行业资金"),
        SectorFlow("银行", 0.4, 720_000_000, "演示行业资金"),
    ]
    concept_flows = [
        SectorFlow("中特估", 0.9, 890_000_000, "演示概念资金"),
        SectorFlow("低空经济", 4.2, -930_000_000, "演示概念资金"),
        SectorFlow("储能", 1.3, 620_000_000, "演示概念资金"),
    ]
    summary = _build_flow_summary(industry_flows, concept_flows)
    summary.update(
        {
            "trade_date": date.today().isoformat(),
            "live_data": False,
            "flow_live_data": False,
            "news_live_data": False,
            "headline": "演示复盘：资金偏向低位防守和能源方向，高位题材有分歧。",
            "note": "当前为演示资金流和演示快讯，用来保证页面流程稳定。",
            "news": _demo_news_summary(),
        }
    )
    return summary


def build_market_review() -> dict[str, Any]:
    ak = _require_akshare()
    industry_flows = _read_sector_flows(
        lambda: ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流"),
        "行业资金流",
    )
    concept_flows = _read_sector_flows(
        lambda: ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="概念资金流"),
        "概念资金流",
    )

    news_items = _read_news_items(lambda: ak.stock_info_global_em(), "全球财经快讯")
    board_changes = _read_board_changes(lambda: ak.stock_board_change_em())

    flow_live_data = bool(industry_flows or concept_flows)
    news_live_data = bool(news_items or board_changes)
    summary = _build_flow_summary(industry_flows, concept_flows) if flow_live_data else _build_flow_summary(
        [
            SectorFlow("电力", 0.8, 1_620_000_000, "演示行业资金"),
            SectorFlow("煤炭", 1.1, 980_000_000, "演示行业资金"),
            SectorFlow("算力", 3.4, -1_250_000_000, "演示概念资金"),
            SectorFlow("半导体", 2.2, -860_000_000, "演示行业资金"),
            SectorFlow("银行", 0.4, 720_000_000, "演示行业资金"),
        ],
        [
            SectorFlow("中特估", 0.9, 890_000_000, "演示概念资金"),
            SectorFlow("低空经济", 4.2, -930_000_000, "演示概念资金"),
            SectorFlow("储能", 1.3, 620_000_000, "演示概念资金"),
        ],
    )
    news_summary = _build_news_summary(news_items, board_changes) if news_live_data else _demo_news_summary()
    leader = summary["top_inflow"][0]["name"] if summary["top_inflow"] else "暂无明显主线"

    if flow_live_data and news_live_data:
        headline = f"盘后资金主线：{leader} 方向资金靠前。"
        note = "资金流和新闻都来自 AKShare。"
    elif flow_live_data:
        headline = f"盘后资金主线：{leader} 方向资金靠前。"
        note = "资金流来自 AKShare；新闻暂时用演示快讯。"
    elif news_live_data:
        headline = "新闻快讯已切到真实数据，资金流暂时保留演示兜底。"
        note = "新闻来自 AKShare；资金流暂时用演示数据。"
    else:
        headline = "演示复盘：资金偏向低位防守和能源方向，高位题材有分歧。"
        note = "当前为演示资金流和演示快讯，用来保证页面流程稳定。"

    summary.update(
        {
            "trade_date": date.today().isoformat(),
            "live_data": flow_live_data and news_live_data,
            "flow_live_data": flow_live_data,
            "news_live_data": news_live_data,
            "headline": headline,
            "note": note,
            "news": news_summary,
        }
    )
    return summary
