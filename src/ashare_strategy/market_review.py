from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any, Callable


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


def _read_sector_flows(loader: Callable[[], Any], source: str) -> list[SectorFlow]:
    try:
        frame = loader()
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
            "headline": "演示复盘：资金偏向低位防守和能源方向，高位题材有分歧。",
            "note": "当前为演示资金流，用来保证页面流程稳定。",
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

    if not industry_flows and not concept_flows:
        return build_demo_market_review()

    summary = _build_flow_summary(industry_flows, concept_flows)
    leader = summary["top_inflow"][0]["name"] if summary["top_inflow"] else "暂无明显主线"
    summary.update(
        {
            "trade_date": date.today().isoformat(),
            "live_data": True,
            "headline": f"盘后资金主线：{leader} 方向资金靠前。",
            "note": "资金流来自 AKShare 东方财富板块资金流接口。",
        }
    )
    return summary
