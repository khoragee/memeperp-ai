import requests

BSCSCAN_API = "https://api.bscscan.com/api"
MYX_API = "https://api.myx.finance"

def get_wallet_myx_positions(wallet_address: str) -> dict:
    """
    Monitor a wallet's MYX positions using MYX API
    """
    try:
        # Get all trading pairs first
        pairs_res = requests.get(f"{MYX_API}/v2/quote/market/contracts", timeout=10)
        pairs = pairs_res.json().get("data", [])

        # Get current prices for risk calculation
        prices = {}
        for pair in pairs:
            prices[pair.get("ticker_id")] = pair.get("last_price", 0)

        # Get wallet transaction history from BscScan (free, no API key needed for basic)
        tx_res = requests.get(
            BSCSCAN_API,
            params={
                "module": "account",
                "action": "txlist",
                "address": wallet_address,
                "startblock": 0,
                "endblock": 99999999,
                "page": 1,
                "offset": 10,
                "sort": "desc",
                "apikey": "YourApiKeyToken"
            },
            timeout=10
        )
        tx_data = tx_res.json()
        recent_txs = tx_data.get("result", [])
        if isinstance(recent_txs, str):
            recent_txs = []

        # Get BNB balance
        bal_res = requests.get(
            BSCSCAN_API,
            params={
                "module": "account",
                "action": "balance",
                "address": wallet_address,
                "tag": "latest",
                "apikey": "YourApiKeyToken"
            },
            timeout=10
        )
        bal_data = bal_res.json()
        bnb_balance = 0
        if bal_data.get("status") == "1":
            bnb_balance = int(bal_data.get("result", 0)) / 1e18

        return {
            "wallet": wallet_address,
            "bnb_balance": round(bnb_balance, 6),
            "recent_transactions": len(recent_txs),
            "last_tx": recent_txs[0].get("hash", "none") if recent_txs else "none",
            "last_tx_time": recent_txs[0].get("timeStamp", "0") if recent_txs else "0",
            "myx_markets_available": len(pairs),
            "status": "monitored"
        }

    except Exception as e:
        return {
            "wallet": wallet_address,
            "error": str(e),
            "status": "error"
        }

def analyze_wallet_risk(wallet_address: str, open_positions: list) -> dict:
    """
    Analyze risk for a wallet's simulated positions
    and suggest adjustments based on current market conditions
    """
    try:
        pairs_res = requests.get(f"{MYX_API}/v2/quote/market/contracts", timeout=10)
        pairs = pairs_res.json().get("data", [])

        prices = {}
        for pair in pairs:
            prices[pair.get("ticker_id")] = float(pair.get("last_price", 0))

        risk_alerts = []
        recommendations = []

        for pos in open_positions:
            ticker = pos.get("ticker")
            entry_price = float(pos.get("entry_price", 0))
            direction = pos.get("direction", "LONG")
            leverage = pos.get("leverage", 2)
            collateral = pos.get("collateral_usdc", 10)

            current_price = prices.get(ticker, entry_price)
            if current_price == 0:
                continue

            # Calculate current PnL
            if direction == "LONG":
                pnl_pct = ((current_price - entry_price) / entry_price) * 100
            else:
                pnl_pct = ((entry_price - current_price) / entry_price) * 100

            pnl_usdc = (pnl_pct / 100) * collateral * leverage

            # Liquidation price estimate
            if direction == "LONG":
                liq_price = entry_price * (1 - (1 / leverage) * 0.9)
            else:
                liq_price = entry_price * (1 + (1 / leverage) * 0.9)

            # Distance to liquidation
            if direction == "LONG":
                liq_distance_pct = ((current_price - liq_price) / current_price) * 100
            else:
                liq_distance_pct = ((liq_price - current_price) / current_price) * 100

            risk_level = "LOW"
            if liq_distance_pct < 5:
                risk_level = "CRITICAL"
                risk_alerts.append(f"⚠️ {ticker} is {liq_distance_pct:.1f}% from liquidation!")
                recommendations.append(f"URGENT: Reduce {ticker} position or add collateral")
            elif liq_distance_pct < 15:
                risk_level = "HIGH"
                risk_alerts.append(f"🔴 {ticker} has high liquidation risk ({liq_distance_pct:.1f}% buffer)")
                recommendations.append(f"Consider reducing {ticker} leverage from {leverage}x to {max(1, leverage-1)}x")
            elif pnl_pct >= 4:
                risk_level = "TAKE_PROFIT"
                recommendations.append(f"💰 {ticker} up {pnl_pct:.1f}% — consider taking profit")

            pos["current_price"] = current_price
            pos["pnl_pct"] = round(pnl_pct, 2)
            pos["pnl_usdc"] = round(pnl_usdc, 4)
            pos["liq_price"] = round(liq_price, 6)
            pos["liq_distance_pct"] = round(liq_distance_pct, 2)
            pos["risk_level"] = risk_level

        return {
            "wallet": wallet_address,
            "positions_analyzed": len(open_positions),
            "risk_alerts": risk_alerts,
            "recommendations": recommendations,
            "positions": open_positions
        }

    except Exception as e:
        return {
            "wallet": wallet_address,
            "error": str(e),
            "positions": open_positions
        }


def generate_myx_trade_link(ticker: str, direction: str, leverage: int = 2) -> str:
    """
    Generate a deep link to MYX Finance with pre-filled trade parameters
    User just needs to connect wallet and confirm
    """
    base = "https://myx.finance/en/trade"
    pair = ticker.replace("_", "-")
    is_long = "true" if direction == "LONG" else "false"
    return f"{base}?pair={pair}&isLong={is_long}&leverage={leverage}"