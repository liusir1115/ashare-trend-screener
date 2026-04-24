from __future__ import annotations

import time
from typing import Any, Callable, TypeVar

T = TypeVar("T")


def load_with_retry(loader: Callable[[], T], retries: int = 3, delay_seconds: float = 1.0) -> T:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            return loader()
        except Exception as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(delay_seconds)
    if last_error is None:
        raise RuntimeError("loader failed without raising an error")
    raise last_error
