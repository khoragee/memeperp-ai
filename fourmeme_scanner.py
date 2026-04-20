import requests
from datetime import datetime

GECKO_BASE = "https://api.geckoterminal.com/api/v2"

def get_new_tokens(limit: int = 10) -> list:
    """Fetch newly launched tokens on four.meme via GeckoTerminal"""
    try:
        response = requests.get(
            f"{GECKO_BASE}/networks/bsc/pools",
            params={
                "page": 1,
                "sort": "h24_volume_usd_liquidity_desc"
            },
            headers={"Accept": "application/json"},
            timeout=10
        )
        data = response.json()
        pools = data.get("data", [])

        tokens = []
        for pool in pools[:limit]:
            attr = pool.get("attributes", {})
            base = attr.get("base_token_price_usd", 0)
            tokens.append({
                "name": attr.get("name", ""),
                "symbol": attr.get("name", "").split("/")[0],
                "address": pool.get("id", "").replace("bsc_", ""),
                "price": base,
                "volume_24h": attr.get("volume_usd", {}).get("h24", 0),
                "market_cap": attr.get("market_cap_usd", 0),
                "price_change_24h": attr.get("price_change_percentage", {}).get("h24", 0),
                "created_at": attr.get("pool_created_at", ""),
            })
        return tokens

    except Exception as e:
        print(f"Error fetching tokens: {e}")
        return []

def get_trending_tokens(limit: int = 5) -> list:
    """Fetch trending BSC meme tokens"""
    try:
        response = requests.get(
            f"{GECKO_BASE}/networks/bsc/trending_pools",
            headers={"Accept": "application/json"},
            timeout=10
        )
        data = response.json()
        pools = data.get("data", [])

        tokens = []
        for pool in pools[:limit]:
            attr = pool.get("attributes", {})
            tokens.append({
                "name": attr.get("name", ""),
                "symbol": attr.get("name", "").split("/")[0],
                "address": pool.get("id", "").replace("bsc_", ""),
                "price": attr.get("base_token_price_usd", 0),
                "volume_24h": attr.get("volume_usd", {}).get("h24", 0),
                "price_change_24h": attr.get("price_change_percentage", {}).get("h24", 0),
            })
        return tokens

    except Exception as e:
        print(f"Error fetching trending: {e}")
        return []