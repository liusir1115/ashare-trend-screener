from __future__ import annotations

import csv
from dataclasses import fields
from datetime import date
from pathlib import Path
from typing import Any, get_type_hints

from ashare_strategy.models import DailyBar, DailySnapshot


def _coerce_value(raw: str, annotation: Any) -> Any:
    if raw == "":
        return None
    text = raw.strip()
    origin = getattr(annotation, "__origin__", None)
    if origin is not None:
        args = [item for item in getattr(annotation, "__args__", ()) if item is not type(None)]
        if args:
            return _coerce_value(text, args[0])
    if annotation is date:
        return date.fromisoformat(text)
    if annotation is bool:
        return text.lower() in {"1", "true", "yes", "y"}
    if annotation is int:
        return int(float(text))
    if annotation is float:
        return float(text)
    return text


class CSVProvider:
    def __init__(self, snapshot_path: str | Path, bar_path: str | Path | None = None) -> None:
        self.snapshot_path = Path(snapshot_path)
        self.bar_path = Path(bar_path) if bar_path else None

    def fetch_daily_snapshots(self, trade_date: date) -> list[DailySnapshot]:
        snapshots = self._read_rows(self.snapshot_path, DailySnapshot)
        return [item for item in snapshots if item.trade_date == trade_date]

    def fetch_daily_bars(self, symbol: str, start_date: date, end_date: date) -> list[DailyBar]:
        if not self.bar_path:
            return []
        bars = self._read_rows(self.bar_path, DailyBar)
        return [
            item
            for item in bars
            if item.symbol == symbol and start_date <= item.trade_date <= end_date
        ]

    def _read_rows(self, path: Path, model_cls: type[DailySnapshot] | type[DailyBar]) -> list[Any]:
        type_hints = get_type_hints(model_cls)
        model_fields = {field_item.name: type_hints.get(field_item.name, field_item.type) for field_item in fields(model_cls)}
        output: list[Any] = []
        with path.open("r", encoding="utf-8-sig", newline="") as file_obj:
            reader = csv.DictReader(file_obj)
            for row in reader:
                payload = {}
                for key, value in row.items():
                    if key not in model_fields:
                        continue
                    payload[key] = _coerce_value(value, model_fields[key])
                output.append(model_cls(**payload))
        return output
