import requests

MYX_BASE_URL = "https://api.myx.finance"

def get_markets():
    """Fetch all available trading pairs from MYX"""
    try:
        response = requests.get(f"{MYX_BASE_URL}/v2/quote/market/contracts", timeout=10)
        data = response.json()
        print(f"MYX API response code: {data.get('code')}, markets: {len(data.get('data', []))}")
        return data.get("data", [])
    except Exception as e:
        print(f"Error fetching markets: {e}")
        return []

def get_market_price(ticker_id: str):
    """Get current price for a specific trading pair"""
    markets = get_markets()
    for market in markets:
        if market.get("ticker_id") == ticker_id:
            return {
                "ticker": ticker_id,
                "last_price": market.get("last_price", 0),
                "high_24h": market.get("high", 0),
                "low_24h": market.get("low", 0),
                "funding_rate": market.get("funding_rate") or 0,
                "open_interest": market.get("open_interest", 0),
                "base_volume": market.get("base_volume", 0),
            }
    return None

def get_all_prices():
    """Get prices for all markets"""
    markets = get_markets()
    prices = []
    for market in markets:
        try:
            prices.append({
                "ticker": market.get("ticker_id", ""),
                "last_price": market.get("last_price", 0),
                "high_24h": market.get("high", 0),
                "low_24h": market.get("low", 0),
                "funding_rate": market.get("funding_rate") or 0,
                "base_volume": market.get("base_volume", 0),
            })
        except Exception:
            continue
    return prices

def simulate_order(ticker: str, is_long: bool, collateral: float, leverage: int, entry_price: float):
    """
    Simulate a MYX perp order.
    Generates the exact payload that would be submitted to MYX Router contract.
    """
    size = (collateral * leverage) / entry_price
    direction = "LONG" if is_long else "SHORT"
    tp_price = entry_price * 1.05 if is_long else entry_price * 0.95
    sl_price = entry_price * 0.97 if is_long else entry_price * 1.03

    order = {
        "status": "SIMULATED",
        "ticker": ticker,
        "direction": direction,
        "collateral_usdc": collateral,
        "leverage": leverage,
        "entry_price": entry_price,
        "size_amount": round(size, 6),
        "tp_price": round(tp_price, 4),
        "sl_price": round(sl_price, 4),
        "trade_type": "MARKET",
        "network_fee_payment": "ETH",
        "router_function": "createIncreaseOrderWithTpSl",
        "contract": "MYX_Router_BNBChain",
    }
    return order

def simulate_close(ticker: str, is_long: bool, entry_price: float, current_price: float, size: float, collateral: float):
    """Simulate closing a position and calculate PnL"""
    if is_long:
        pnl = (current_price - entry_price) * size
    else:
        pnl = (entry_price - current_price) * size

    pnl_pct = (pnl / collateral) * 100

    return {
        "status": "SIMULATED_CLOSE",
        "ticker": ticker,
        "entry_price": entry_price,
        "exit_price": current_price,
        "pnl_usdc": round(pnl, 4),
        "pnl_percent": round(pnl_pct, 2),
        "router_function": "createDecreaseOrder",
    }