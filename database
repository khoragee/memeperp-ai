import sqlite3
import json
import os
from datetime import datetime

DB_PATH = "memeperp.db"

def init_db():
    """Initialize the database and create tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id TEXT PRIMARY KEY,
            ticker TEXT,
            direction TEXT,
            status TEXT,
            entry_price REAL,
            current_price REAL,
            size_amount REAL,
            collateral_usdc REAL,
            leverage INTEGER,
            tp_price REAL,
            sl_price REAL,
            pnl_usdc REAL,
            pnl_percent REAL,
            analysis TEXT,
            created_at TEXT,
            closed_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()

def save_trade(order: dict):
    """Save a new trade to database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO trades 
        (id, ticker, direction, status, entry_price, current_price, 
         size_amount, collateral_usdc, leverage, tp_price, sl_price,
         pnl_usdc, pnl_percent, analysis, created_at, closed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        order.get("id"),
        order.get("ticker"),
        order.get("direction"),
        order.get("status", "SIMULATED"),
        order.get("entry_price", 0),
        order.get("current_price", 0),
        order.get("size_amount", 0),
        order.get("collateral_usdc", 10),
        order.get("leverage", 2),
        order.get("tp_price", 0),
        order.get("sl_price", 0),
        order.get("pnl_usdc", 0),
        order.get("pnl_percent", 0),
        json.dumps(order.get("analysis", {})),
        order.get("created_at", datetime.now().isoformat()),
        order.get("closed_at", None)
    ))
    conn.commit()
    conn.close()

def update_trade(trade_id: str, updates: dict):
    """Update a trade in database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE trades SET
            status = ?,
            current_price = ?,
            pnl_usdc = ?,
            pnl_percent = ?,
            closed_at = ?
        WHERE id = ?
    ''', (
        updates.get("status"),
        updates.get("current_price", 0),
        updates.get("pnl_usdc", 0),
        updates.get("pnl_percent", 0),
        updates.get("closed_at", datetime.now().isoformat()),
        trade_id
    ))
    conn.commit()
    conn.close()

def get_open_positions():
    """Get all open positions from database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM trades WHERE status = "SIMULATED"')
    rows = c.fetchall()
    conn.close()
    
    positions = []
    for row in rows:
        positions.append({
            "id": row[0],
            "ticker": row[1],
            "direction": row[2],
            "status": row[3],
            "entry_price": row[4],
            "current_price": row[5],
            "size_amount": row[6],
            "collateral_usdc": row[7],
            "leverage": row[8],
            "tp_price": row[9],
            "sl_price": row[10],
            "pnl_usdc": row[11],
            "pnl_percent": row[12],
            "analysis": json.loads(row[13]) if row[13] else {},
            "created_at": row[14],
            "closed_at": row[15]
        })
    return positions

def get_all_trades():
    """Get all trades from database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT * FROM trades ORDER BY created_at DESC LIMIT 50')
    rows = c.fetchall()
    conn.close()
    
    trades = []
    for row in rows:
        trades.append({
            "id": row[0],
            "ticker": row[1],
            "direction": row[2],
            "status": row[3],
            "entry_price": row[4],
            "current_price": row[5],
            "size_amount": row[6],
            "collateral_usdc": row[7],
            "leverage": row[8],
            "tp_price": row[9],
            "sl_price": row[10],
            "pnl_usdc": row[11],
            "pnl_percent": row[12],
            "analysis": json.loads(row[13]) if row[13] else {},
            "created_at": row[14],
            "closed_at": row[15]
        })
    return trades

def get_portfolio_stats():
    """Get portfolio statistics from database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('SELECT COUNT(*) FROM trades')
    total = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM trades WHERE status = "SIMULATED"')
    open_count = c.fetchone()[0]
    
    c.execute('SELECT COUNT(*) FROM trades WHERE status = "SIMULATED_CLOSE"')
    closed_count = c.fetchone()[0]
    
    c.execute('SELECT SUM(pnl_usdc) FROM trades WHERE status = "SIMULATED_CLOSE"')
    total_pnl = c.fetchone()[0] or 0
    
    conn.close()
    
    return {
        "total_trades": total,
        "open_positions": open_count,
        "closed_positions": closed_count,
        "total_pnl_usdc": round(total_pnl, 4)
    }
