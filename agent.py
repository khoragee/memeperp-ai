import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI
from myx_client import get_all_prices, get_market_price, simulate_order, simulate_close

load_dotenv()

client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),
    base_url="https://api.groq.com/openai/v1"
)

trade_log = []
open_positions = []

def analyze_market(ticker: str, market_data: dict) -> dict:
    """Multi-model consensus — 3 AI models vote on trade direction"""

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
    """AI scores a trending meme token 1-10 for trading potential"""

    prompt = f"""You are a meme coin analyst. Score this BSC token for trading potential.

Token: {token.get('name', '')}
Price: ${token.get('price', 0)}
24h Volume: ${token.get('volume_24h', 0)}
24h Price Change: {token.get('price_change_24h', 0)}%

Respond ONLY with this exact JSON:
{{
  "score": 1-10,
  "sentiment": "BULLISH" or "BEARISH" or "NEUTRAL",
  "reasoning": "one sentence max",
  "risk": "LOW" or "MEDIUM" or "HIGH"
}}

Rules:
- High volume + positive price change = higher score
- Negative price change > 50% = score 1-3
- Score 8-10 only if volume > $1M and price change positive
"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        content = response.choices[0].message.content.strip()
        content = content.replace("```json", "").replace("```", "").strip()
        result = json.loads(content)
        result["name"] = token.get("name", "")
        result["symbol"] = token.get("symbol", "")
        result["price"] = token.get("price", 0)
        result["volume_24h"] = token.get("volume_24h", 0)
        result["price_change_24h"] = token.get("price_change_24h", 0)
        return result
    except Exception as e:
        return {
            "name": token.get("name", ""),
            "symbol": token.get("symbol", ""),
            "score": 5,
            "sentiment": "NEUTRAL",
            "reasoning": f"Analysis failed: {str(e)[:50]}",
            "risk": "MEDIUM",
            "price": token.get("price", 0),
            "volume_24h": token.get("volume_24h", 0),
            "price_change_24h": token.get("price_change_24h", 0)
        }


def scan_and_score_memes() -> list:
    """Scan trending meme tokens and score them with AI"""
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
    """Run one full agent cycle"""

    print(f"\n{'='*50}")
    print(f"Agent cycle started: {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*50}")

    prices = get_all_prices()

    if not prices:
        return {"error": "Could not fetch MYX market data", "trades": [], "positions": open_positions}

    cycle_results = []
    # Only trade markets we don't already have open positions in open_tickers = [p["ticker"] for p in open_positions] top_markets = [m for m in prices[:10] if m["ticker"] not in open_tickers][:3]

    for market in top_markets:
        ticker = market["ticker"]
        print(f"\nAnalyzing {ticker}...")

        detailed = get_market_price(ticker)
        if not detailed:
            continue

        analysis = analyze_market(ticker, detailed)
        print(f"Decision: {analysis['decision']} | Confidence: {analysis.get('confidence', 0)}%")
        print(f"Reasoning: {analysis.get('reasoning', '')}")

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
            order["id"] = f"trade_{len(trade_log)+1}_{int(datetime.now().timestamp())}"

            trade_log.append(order)
            open_positions.append(order)

            print(f"Simulated {order['direction']} position opened on {ticker}")
            cycle_results.append(order)
        else:
            print(f"Skipping {ticker} - confidence too low")
            cycle_results.append({
                "ticker": ticker,
                "decision": "SKIP",
                "analysis": analysis
            })

    positions_to_close = []
    for pos in open_positions:
        current_data = get_market_price(pos["ticker"])
        if not current_data:
            continue

        current_price = float(current_data["last_price"])
        entry_price = pos["entry_price"]
        pnl_pct = ((current_price - entry_price) / entry_price) * 100
        if not pos.get("direction") == "LONG":
            pnl_pct = -pnl_pct

        if pnl_pct >= 5 or pnl_pct <= -3:
            close = simulate_close(
                ticker=pos["ticker"],
                is_long=pos["direction"] == "LONG",
                entry_price=entry_price,
                current_price=current_price,
                size=pos["size_amount"],
                collateral=pos["collateral_usdc"]
            )
            close["original_trade_id"] = pos.get("id")
            trade_log.append(close)
            positions_to_close.append(pos)
            print(f"Closed {pos['ticker']} | PnL: {close['pnl_percent']}%")

    for pos in positions_to_close:
        open_positions.remove(pos)

    return {
        "cycle_time": datetime.now().isoformat(),
        "markets_analyzed": len(top_markets),
        "trades_this_cycle": cycle_results,
        "open_positions": open_positions,
        "total_trades": len(trade_log)
    }


def get_portfolio_summary():
    """Get current portfolio state"""
    closed_trades = [t for t in trade_log if t.get("status") == "SIMULATED_CLOSE"]
    open_trades = [t for t in trade_log if t.get("status") == "SIMULATED"]

    total_pnl = sum(t.get("pnl_usdc", 0) for t in closed_trades)

    return {
        "total_trades": len(trade_log),
        "open_positions": len(open_trades),
        "closed_positions": len(closed_trades),
        "total_pnl_usdc": round(total_pnl, 4),
        "trade_log": trade_log[-20:],
        "open_positions_detail": open_positions
    }
