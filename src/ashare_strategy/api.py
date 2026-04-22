from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

try:
    from fastapi import FastAPI
    from fastapi.responses import RedirectResponse
    from fastapi.staticfiles import StaticFiles
    from pydantic import BaseModel, Field
except ImportError as exc:  # pragma: no cover - exercised only when API deps are missing
    FastAPI = None
    BaseModel = object
    Field = None
    StaticFiles = None
    RedirectResponse = None
    _IMPORT_ERROR = exc
else:
    _IMPORT_ERROR = None

from ashare_strategy.backtest import BacktestEngine
from ashare_strategy.config import StrategyConfig
from ashare_strategy.market import MARKET_SCOPE_ALL, matches_market_scope
from ashare_strategy.models import DailyBar, DailySnapshot
from ashare_strategy.mvp_service import StrategyInput, build_mvp_payload
from ashare_strategy.strategy import ScreeningEngine


def _missing_dependency_error() -> RuntimeError:
    return RuntimeError(
        "FastAPI dependencies are not installed. "
        "Install project dependencies from pyproject.toml before starting the API."
    )


if FastAPI is not None:
    class SnapshotPayload(BaseModel):
        symbol: str
        trade_date: date
        close: float
        volume: float
        volume_ratio: float
        ma5: float
        ma10: float
        ma20: float
        ma60: float
        ma20_slope: float
        ma60_slope: float
        breakout_high_120: float
        cost_5pct: float
        cost_50pct: float
        cost_95pct: float
        winner_rate: float
        base_days: int
        range_90: float
        high_250: float
        industry_hot_score: float
        board_hot_score: float
        pe_ttm: float | None = None
        pb: float | None = None
        industry_pe_ratio: float | None = None
        industry_pb_ratio: float | None = None
        limit_up: bool = False
        relimit: bool = False
        extra: dict[str, Any] = Field(default_factory=dict)

        def to_model(self) -> DailySnapshot:
            return DailySnapshot(**self.model_dump())


    class BarPayload(BaseModel):
        symbol: str
        trade_date: date
        open: float
        high: float
        low: float
        close: float
        volume: float

        def to_model(self) -> DailyBar:
            return DailyBar(**self.model_dump())


    class ScreenRequest(BaseModel):
        snapshots: list[SnapshotPayload]
        config: dict[str, Any] | None = None
        market_scope: str = MARKET_SCOPE_ALL


    class BacktestRequest(BaseModel):
        snapshots_by_date: dict[date, list[SnapshotPayload]]
        bars_by_symbol: dict[str, list[BarPayload]]
        config: dict[str, Any] | None = None
        market_scope: str = MARKET_SCOPE_ALL


    class StrategyRequest(BaseModel):
        narrative: str
        market_scope: str = "main_board"
        style_focus: str = "breakout"
        holding_period: str = "swing"
        risk_tolerance: str = "balanced"
        valuation_weight: str = "medium"
        priority_signal: str = "chip"


def _resolve_frontend_dir() -> Path | None:
    candidates = [
        Path.cwd() / "frontend",
        Path(__file__).resolve().parents[2] / "frontend",
        Path(__file__).resolve().parents[1] / "frontend",
    ]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return None


app = FastAPI(title="A-Share Trend Screener", version="0.3.0")

frontend_dir = _resolve_frontend_dir()
if frontend_dir is not None:
    app.mount("/preview", StaticFiles(directory=frontend_dir, html=True), name="preview")



    @app.get("/")
    def root() -> RedirectResponse:
        return RedirectResponse(url="/preview/")



    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}


    @app.get("/config/default")
    def default_config() -> dict[str, Any]:
        return StrategyConfig().to_dict()


    @app.get("/api/mvp/bootstrap")
    def bootstrap() -> dict[str, Any]:
        return build_mvp_payload(
            StrategyInput(
                narrative="我想先从主板里找几个月筑底后刚开始走强、上方压力轻、估值还没完全修复的票。"
            )
        )


    @app.post("/api/mvp/strategy")
    def strategy_plan(request: StrategyRequest) -> dict[str, Any]:
        return build_mvp_payload(
            StrategyInput(
                narrative=request.narrative,
                market_scope=request.market_scope,
                style_focus=request.style_focus,
                holding_period=request.holding_period,
                risk_tolerance=request.risk_tolerance,
                valuation_weight=request.valuation_weight,
                priority_signal=request.priority_signal,
            )
        )


    @app.post("/screen")
    def screen(request: ScreenRequest) -> list[dict[str, Any]]:
        engine = ScreeningEngine(StrategyConfig.from_dict(request.config))
        models = [item.to_model() for item in request.snapshots]
        if request.market_scope != MARKET_SCOPE_ALL:
            models = [item for item in models if matches_market_scope(item.symbol, request.market_scope)]
        results = engine.rank(models, only_passed=False)
        return [
            {
                "symbol": result.symbol,
                "market_segment": result.snapshot.market_segment,
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
                "overhead_pressure": round(result.snapshot.overhead_pressure, 4),
                "chip_compact": round(result.snapshot.chip_compact, 4),
            }
            for result in results
        ]


    @app.post("/backtest")
    def backtest(request: BacktestRequest) -> dict[str, Any]:
        engine = BacktestEngine(StrategyConfig.from_dict(request.config))
        snapshots_by_date = {
            trade_date: [item.to_model() for item in snapshots]
            for trade_date, snapshots in request.snapshots_by_date.items()
        }
        if request.market_scope != MARKET_SCOPE_ALL:
            snapshots_by_date = {
                trade_date: [
                    item for item in snapshots if matches_market_scope(item.symbol, request.market_scope)
                ]
                for trade_date, snapshots in snapshots_by_date.items()
            }
        report = engine.run(
            snapshots_by_date=snapshots_by_date,
            bars_by_symbol={
                symbol: [bar.to_model() for bar in bars]
                for symbol, bars in request.bars_by_symbol.items()
            },
        )
        return {
            "total_trades": report.total_trades,
            "win_rate": report.win_rate,
            "average_return": report.average_return,
            "cumulative_return": report.cumulative_return,
            "max_drawdown": report.max_drawdown,
            "trades": [
                {
                    "symbol": trade.symbol,
                    "signal_date": trade.signal_date.isoformat(),
                    "entry_date": trade.entry_date.isoformat(),
                    "exit_date": trade.exit_date.isoformat(),
                    "entry_price": trade.entry_price,
                    "exit_price": trade.exit_price,
                    "raw_return": trade.raw_return,
                    "holding_days": trade.holding_days,
                    "score": trade.score,
                }
                for trade in report.trades
            ],
        }
else:
    app = None


    def __getattr__(name: str) -> Any:
        if name == "app":
            return None
        raise _missing_dependency_error() from _IMPORT_ERROR
