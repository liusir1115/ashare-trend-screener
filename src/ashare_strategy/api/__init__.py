try:
    from ashare_strategy.api.http import app
except RuntimeError:
    app = None

__all__ = ["app"]
