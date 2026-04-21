import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from myx_client import get_all_prices, get_market_price, simulate_order, simulate_close
from database import init_db, save_trade, update_trade, get_open_positions, get_all_trades, get_portfolio_stats

load_dotenv()

# Initialize database on startup
init_db()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

MAX_POSITIONS = 6

def analyze_market(ticker: str, market_data: dict) -> dict:
    prompt = f"""You are an aggressive AI trading agent for MYX Finance perpetual futures on BNB Chain.

Market data for {ticker}:
- Last Price: ${market_data['last_price']}
- 24h High: ${market_data['high_24h']}
- 24h Low: ${market_data['low_24h']}
- Funding Rate: {market_data['funding_rate']}

You MUST make a trading decision. Never skip due to low volume.
Respond ONLY with this exact JSON and nothing else:
{{
  "decision": "LONG" or "SHORT",
  "confidence": 50-95,
  "reasoning": "one sentence explanation",
  "suggested_leverage": 2,
  "collateral_usdc": 10
}}

Rules:
- If price is closer to 24h high than low = LONG
- If price is closer to 24h low than high = SHORT
- Always give confidence between 50-95
- Always pick LONG or SHORT, never SKIP
"""

    models = [
        "llama-3.1-8b-instant",
        "gemma2-9b-it",
        "mixtral-8x7b-32768"
    ]

    votes = []
    model_results = []

    for model in models:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                timeout=30,
            )
            content = response.choices[0].message.content.strip()
            content = content.replace("```json", "").replace("```", "").strip()
            result = json.loads(content)
            votes.append(result.get("decision", "SKIP"))
            model_results.append({
                "model": model,
                "decision": result.get("decision"),
                "confidence": result.get("confidence"),
                "reasoning": result.get("reasoning")
            })
            print(f"  [{model}] -> {result.get('decision')} ({result.get('confidence')}%)")
        except Exception as e:
            print(f"  [{model}] -> Failed: {str(e)[:50]}")
            votes.append("SKIP")

    long_votes = votes.count("LONG")
    short_votes = votes.count("SHORT")

    if long_votes > short_votes:
        final_decision = "LONG"
    elif short_votes > long_votes:
        final_decision = "SHORT"
    else:
        final_decision = "LONG"

    avg_confidence = 70
    try:
        confidences = [r.get("confidence", 70) for r in model_results if r.get("confidence")]
        avg_confidence = int(sum(confidences) / len(confidences))
    except:
        pass

    consensus_reasoning = f"{long_votes}/3 models say LONG, {short_votes}/3 say SHORT. Consensus: {final_decision}"

    return {
        "ticker": ticker,
        "decision": final_decision,
        "confidence": avg_confidence,
        "reasoning": consensus_reasoning,
        "suggested_leverage": 2,
        "collateral_usdc": 10,
        "model_votes": model_results,
        "timestamp": datetime.now().isoformat()
    }


def score_meme_token(token: dict) -> dict:
    """Score meme token based on price action"""
    try:
        change = float(token.get("price_change_24h", 0))
        volume = float(token.get("volume_24h", 0))

        score = 5
        if volume > 10_000_000:
            score += 2
        elif volume > 1_000_000:
            score += 1

        if change > 50:
            score += 3
        elif change > 20:
            score += 2
        elif change > 5:
            score += 1
        elif change < -50:
            score -= 3
        elif change < -20:
            score -= 2
        elif change < -5:
            score -= 1

        score = max(1, min(10, score))
        sentiment = "BULLISH" if change > 5 else "BEARISH" if change < -5 else "NEUTRAL"
        risk = "HIGH" if abs(change) > 50 else "MEDIUM" if abs(change) > 20 else "LOW"
        reasoning = f"{'High' if volume > 1e6 else 'Low'} volume with {change:+.1f}% price change"

        return {
            "name": token.get("name", ""),
            "symbol": token.get("symbol", ""),
            "score": score,
            "sentiment": sentiment,
            "reasoning": reasoning,
            "risk": risk,
            "price": token.get("price", 0),
            "volume_24h": token.get("volume_24h", 0),
            "price_change_24h": token.get("price_change_24h", 0)
        }
    except Exception as e:
        return {
            "name": token.get("name", ""),
            "symbol": token.get("symbol", ""),
            "score": 5,
            "sentiment": "NEUTRAL",
            "reasoning": "Insufficient data",
            "risk": "MEDIUM",
            "price": token.get("price", 0),
            "volume_24h": token.get("volume_24h", 0),
            "price_change_24h": token.get("price_change_24h", 0)
        }


def scan_and_score_memes() -> list:
    from fourmeme_scanner import get_trending_tokens
    tokens = get_trending_tokens(limit=6)
    scored = []
    for token in tokens:
        print(f"Scoring {token.get('name')}...")
        score = score_meme_token(token)
        scored.append(score)
    scored.sort(key=lambda x: x.get("score", 0), reverse=True)
    return scored


def run_agent_cycle():
    print(f"\n{'='*50}")
    print(f"Agent cycle started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")

    prices = get_all_prices()

    if not prices:
        return {"error": "Could not fetch MYX market data", "trades": [], "positions": []}

    cycle_results = []

    # Load positions from DB
    open_positions = get_open_positions()

    if len(open_positions) >= MAX_POSITIONS:
        print(f"Max positions ({MAX_POSITIONS}) reached — skipping new trades")
        top_markets = []
    else:
        open_tickers = [p["ticker"] for p in open_positions]
        top_markets = [m for m in prices[:10] if m["ticker"] not in open_tickers][:3]

    for market in top_markets:
        ticker = market["ticker"]
        print(f"\nAnalyzing {ticker}...")

        detailed = get_market_price(ticker)
        if not detailed:
            continue

        analysis = analyze_market(ticker, detailed)
        print(f"Decision: {analysis['decision']} | Confidence: {analysis.get('confidence', 0)}%")

        if analysis["decision"] in ["LONG", "SHORT"] and analysis.get("confidence", 0) > 30:
            is_long = analysis["decision"] == "LONG"
            order = simulate_order(
                ticker=ticker,
                is_long=is_long,
                collateral=analysis.get("collateral_usdc", 10),
                leverage=analysis.get("suggested_leverage", 2),
                entry_price=float(detailed["last_price"])
            )

            order["analysis"] = analysis
            order["id"] = f"trade_{int(datetime.now().timestamp())}_{ticker}"
            order["created_at"] = datetime.now().isoformat()

            save_trade(order)
            print(f"Opened {order['direction']} on {ticker}")
            cycle_results.append(order)

    # Check open positions for exit
    open_positions = get_open_positions()
    for pos in open_positions:
        current_data = get_market_price(pos["ticker"])
        if not current_data:
            continue

        current_price = float(current_data["last_price"])
        entry_price = float(pos["entry_price"])
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        if pos.get("direction") != "LONG":
            pnl_pct = -pnl_pct

        if pnl_pct >= 1 or pnl_pct <= -1:
            close = simulate_close(
                ticker=pos["ticker"],
                is_long=pos["direction"] == "LONG",
                entry_price=entry_price,
                current_price=current_price,
                size=pos["size_amount"],
                collateral=pos["collateral_usdc"]
            )
            update_trade(pos["id"], {
                "status": "SIMULATED_CLOSE",
                "current_price": current_price,
                "pnl_usdc": close["pnl_usdc"],
                "pnl_percent": close["pnl_percent"],
                "closed_at": datetime.now().isoformat()
            })
            print(f"Closed {pos['ticker']} | PnL: {close['pnl_percent']}%")

    stats = get_portfolio_stats()
    return {
        "cycle_time": datetime.now().isoformat(),
        "markets_analyzed": len(top_markets),
        "trades_this_cycle": cycle_results,
        "total_trades": stats["total_trades"]
    }


def get_portfolio_summary():
    stats = get_portfolio_stats()
    trades = get_all_trades()
    open_positions = get_open_positions()

    return {
        "total_trades": stats["total_trades"],
        "open_positions": stats["open_positions"],
        "closed_positions": stats["closed_positions"],
        "total_pnl_usdc": stats["total_pnl_usdc"],
        "trade_log": trades[:20],
        "open_positions_detail": open_positions
    }
