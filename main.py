import os
import threading
import time
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from agent import run_agent_cycle, get_portfolio_summary
from myx_client import get_all_prices

app = FastAPI(title="MemePerp AI Agent")

if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")

agent_running = False
agent_thread = None
last_cycle_result = {}

def agent_loop():
    global last_cycle_result
    while agent_running:
        try:
            result = run_agent_cycle()
            last_cycle_result = result
        except Exception as e:
            last_cycle_result = {"error": str(e)}
        time.sleep(60)

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    with open("templates/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/agent/start")
async def start_agent():
    global agent_running, agent_thread
    if agent_running:
        return {"status": "already running"}
    agent_running = True
    agent_thread = threading.Thread(target=agent_loop, daemon=True)
    agent_thread.start()
    return {"status": "Agent started"}

@app.post("/agent/stop")
async def stop_agent():
    global agent_running
    agent_running = False
    return {"status": "Agent stopped"}

@app.post("/agent/run-once")
async def run_once():
    global last_cycle_result
    result = run_agent_cycle()
    last_cycle_result = result
    return result

@app.get("/agent/status")
async def agent_status():
    return {"running": agent_running, "last_cycle": last_cycle_result}

@app.get("/portfolio")
async def portfolio():
    return get_portfolio_summary()

@app.get("/markets")
async def markets():
    prices = get_all_prices()
    return {"markets": prices}

@app.get("/trending")
async def trending():
    from fourmeme_scanner import get_trending_tokens
    tokens = get_trending_tokens(limit=6)
    return {"tokens": tokens}

@app.get("/myx-transaction/{ticker}/{direction}")
async def build_transaction(ticker: str, direction: str):
    from myx_client import get_market_price, simulate_order
    from wallet_monitor import generate_myx_trade_link
    market = get_market_price(ticker)
    if not market:
        return {"error": "Market not found"}
    is_long = direction.upper() == "LONG"
    order = simulate_order(
        ticker=ticker,
        is_long=is_long,
        collateral=10,
        leverage=2,
        entry_price=float(market["last_price"])
    )
    order["trade_link"] = generate_myx_trade_link(ticker, direction.upper(), 2)
    order["raw_transaction"] = {
        "contract": "MYX_Router_BNBChain",
        "function": "createIncreaseOrderWithTpSl",
        "params": {
            "pairIndex": ticker,
            "tradeType": 0,
            "collateral": "10000000000000000000",
            "openPrice": str(int(float(market["last_price"]) * 1e30)),
            "isLong": is_long,
            "sizeAmount": str(int(order["size_amount"] * 1e18)),
            "tpPrice": str(int(order["tp_price"] * 1e30)),
            "slPrice": str(int(order["sl_price"] * 1e30)),
            "maxSlippage": "30",
            "paymentType": 0,
            "networkFeeAmount": "1000000000000000"
        }
    }
    return order

@app.get("/wallet/{address}")
async def monitor_wallet(address: str):
    from wallet_monitor import get_wallet_myx_positions
    return get_wallet_myx_positions(address)

@app.get("/risk-check")
async def risk_check():
    from wallet_monitor import analyze_wallet_risk
    from agent import open_positions
    result = analyze_wallet_risk("simulated", open_positions)
    return result

@app.get("/trade-link/{ticker}/{direction}")
async def trade_link(ticker: str, direction: str):
    from wallet_monitor import generate_myx_trade_link
    link = generate_myx_trade_link(ticker, direction.upper(), 2)
    return {"ticker": ticker, "direction": direction.upper(), "link": link}

@app.get("/meme-scores")
async def meme_scores():
    from agent import scan_and_score_memes
    scores = scan_and_score_memes()
    return {"scores": scores}
