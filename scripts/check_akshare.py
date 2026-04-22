from __future__ import annotations

try:
    import akshare as ak  # type: ignore
except ImportError as exc:
    print(f"missing:{exc}")
else:
    print(f"ok:{ak.__version__}")

