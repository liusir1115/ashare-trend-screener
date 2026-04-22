from __future__ import annotations

MARKET_SCOPE_ALL = "all"
MARKET_SCOPE_MAIN = "main_board"
MARKET_SCOPE_STAR = "star_market"
MARKET_SCOPE_GROWTH = "growth_board"

VALID_MARKET_SCOPES = {
    MARKET_SCOPE_ALL,
    MARKET_SCOPE_MAIN,
    MARKET_SCOPE_STAR,
    MARKET_SCOPE_GROWTH,
}


def classify_market_segment(symbol: str) -> str:
    code = symbol.split(".")[0].upper()
    if code.startswith("688"):
        return MARKET_SCOPE_STAR
    if code.startswith("300") or code.startswith(
        (
            "430",
            "830",
            "831",
            "832",
            "833",
            "834",
            "835",
            "836",
            "837",
            "838",
            "839",
            "870",
            "871",
            "872",
            "873",
            "874",
            "875",
            "876",
            "877",
            "878",
            "879",
        )
    ):
        return MARKET_SCOPE_GROWTH
    if code.startswith(("600", "601", "603", "605", "000", "001", "002", "003")):
        return MARKET_SCOPE_MAIN
    return MARKET_SCOPE_GROWTH


def matches_market_scope(symbol: str, market_scope: str) -> bool:
    if market_scope == MARKET_SCOPE_ALL:
        return True
    return classify_market_segment(symbol) == market_scope
