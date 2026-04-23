from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Callable


@dataclass(slots=True)
class CheckResult:
    name: str
    ok: bool
    detail: str


def _row_count(frame: Any) -> int:
    if frame is None:
        return 0
    if hasattr(frame, "empty") and frame.empty:
        return 0
    if hasattr(frame, "__len__"):
        return len(frame)
    return 0


def _run_check(name: str, loader: Callable[[], Any], success_text: str) -> CheckResult:
    try:
        frame = loader()
        count = _row_count(frame)
    except Exception as exc:
        return CheckResult(name=name, ok=False, detail=f"失败：{exc}")

    if count <= 0:
        return CheckResult(name=name, ok=False, detail="没有返回数据，可能是接口临时不可用或当天非交易日。")

    return CheckResult(name=name, ok=True, detail=f"{success_text}，返回 {count} 行。")


def _print_results(results: list[CheckResult]) -> None:
    print("AKShare 数据源体检")
    print("=" * 28)
    for result in results:
        mark = "OK" if result.ok else "WARN"
        print(f"[{mark}] {result.name}: {result.detail}")

    failed = [item.name for item in results if not item.ok]
    print("=" * 28)
    if failed:
        print("结论：页面可以继续用兜底模式，但这些真实数据暂时不稳：" + "、".join(failed))
    else:
        print("结论：核心免费数据源目前都能访问，可以做本地真实数据测试。")


def main() -> None:
    parser = argparse.ArgumentParser(description="Check AKShare data sources used by the MVP")
    parser.add_argument("--symbol", default="000001", help="Test stock code, for example 000001 or 600519")
    parser.add_argument("--quick", action="store_true", help="Only check whether AKShare is installed")
    args = parser.parse_args()

    try:
        import akshare as ak  # type: ignore
    except ImportError as exc:
        _print_results([CheckResult("AKShare 安装", False, f"没有安装：{exc}")])
        return

    results = [CheckResult("AKShare 安装", True, f"版本 {ak.__version__}")]
    if args.quick:
        _print_results(results)
        return

    today = date.today()
    start_day = today - timedelta(days=45)
    today_text = today.strftime("%Y%m%d")
    start_text = start_day.strftime("%Y%m%d")

    results.extend(
        [
            _run_check(
                "A 股实时行情",
                lambda: ak.stock_zh_a_spot_em(),
                "可用于候选池和量比/估值粗筛",
            ),
            _run_check(
                "日线行情",
                lambda: ak.stock_zh_a_hist(
                    symbol=args.symbol,
                    period="daily",
                    start_date=start_text,
                    end_date=today_text,
                    adjust="qfq",
                ),
                "可用于均线、突破、筑底和回测",
            ),
            _run_check(
                "真实筹码分布",
                lambda: ak.stock_cyq_em(symbol=args.symbol, adjust="qfq"),
                "可用于上方筹码压力和获利盘判断",
            ),
            _run_check(
                "涨停池",
                lambda: ak.stock_zt_pool_em(date=today_text),
                "可用于涨停、炸板、回封识别",
            ),
            _run_check(
                "行业资金流",
                lambda: ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流"),
                "可用于盘后资金流和高切低判断",
            ),
            _run_check(
                "全球快讯",
                lambda: ak.stock_info_global_em(),
                "可用于热点和风险摘要",
            ),
        ]
    )
    _print_results(results)


if __name__ == "__main__":
    main()
