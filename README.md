# ⚡ MemePerp AI — Autonomous Perp Trading Agent

> An autonomous AI trading agent that monitors MYX Finance perpetual markets on BNB Chain, analyzes meme token sentiment from four.meme, and generates trading signals using multi-model AI consensus.

![MemePerp AI Dashboard](https://img.shields.io/badge/MYX%20Finance-BNB%20Chain-f7931a?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-LLaMA%203.1-purple?style=for-the-badge)

---

## 🚀 What It Does

MemePerp AI is a fully autonomous trading agent built for the Four.meme AI Sprint hackathon. It:

1. **Monitors all 37 MYX Finance perpetual markets** in real-time via the MYX API
2. **Runs multi-model AI consensus** — 3 LLMs (LLaMA 3.1, Gemma 2, Mixtral) vote on LONG/SHORT decisions
3. **Scans four.meme / BSC trending tokens** and scores them 1-10 for trading potential
4. **Monitors wallet risk** — tracks open positions, calculates liquidation distance, and alerts on high-risk positions
5. **Generates MYX trade links** — one-click deep links to execute signals directly on MYX Finance
6. **Runs autonomously** — agent cycles every 60 seconds with auto risk checks

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                  MemePerp AI Agent                  │
├──────────────┬──────────────────┬───────────────────┤
│  MYX Finance │   Groq LLMs      │  four.meme / BSC  │
│  REST API    │   (3 Models)     │  GeckoTerminal    │
│  37 Markets  │   Multi-Vote     │  Trending Tokens  │
└──────┬───────┴────────┬─────────┴──────────┬────────┘
       │                │                    │
       ▼                ▼                    ▼
┌─────────────────────────────────────────────────────┐
│              FastAPI Backend                        │
│  /markets  /agent/run  /risk-check  /meme-scores   │
└─────────────────────────┬───────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────┐
│           Live Trading Dashboard (HTML/JS)          │
│  Portfolio · Positions · AI Decisions · Trade Log  │
└─────────────────────────────────────────────────────┘
```

---

## 🤖 Multi-Model AI Consensus

Instead of relying on a single AI model, MemePerp AI runs each market through **3 different LLMs simultaneously**:

| Model | Provider | Role |
|-------|----------|------|
| LLaMA 3.1 8B | Groq | Primary analysis |
| Gemma 2 9B | Groq | Second opinion |
| Mixtral 8x7B | Groq | Tiebreaker |

A trade is only executed when **2/3 models agree**. This reduces false signals and increases decision reliability.

---

## 📊 Features

- **Live MYX Markets** — Real-time prices for all 37 perpetual pairs on BNB Chain
- **Autonomous Agent** — Runs every 60 seconds, analyzing markets and managing positions
- **Meme Token Scanner** — Fetches trending BSC tokens and scores them with AI
- **Wallet Monitor** — Enter any BNB address to check balance and on-chain activity
- **Risk Engine** — Calculates liquidation distance per position and triggers alerts
- **Trade Links** — One-click links to execute any signal directly on MYX Finance
- **Paper Trading** — Full simulation mode with PnL tracking, no real funds required

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, Uvicorn |
| AI/LLM | Groq API (LLaMA 3.1, Gemma 2, Mixtral) |
| Market Data | MYX Finance REST API |
| Meme Data | GeckoTerminal API (BSC pools) |
| On-chain | BscScan API |
| Frontend | Vanilla HTML/CSS/JS |
| Hosting | Railway (free tier) |

---

## ⚙️ Setup & Run

### Prerequisites
- Python 3.10+
- Groq API key (free at https://console.groq.com)

### Installation

```bash
git clone https://github.com/khoragee/memeperp-ai
cd memeperp-ai
pip install -r requirements.txt
```

### Configuration

Create a `.env` file:
```env
GROQ_API_KEY=your_groq_api_key_here
```

### Run

```bash
python -m uvicorn main:app --reload
```

Open `http://localhost:8000` in your browser.

---

## 📁 Project Structure

```
memeperp-ai/
├── main.py              # FastAPI app + API endpoints
├── agent.py             # AI trading agent + multi-model consensus
├── myx_client.py        # MYX Finance API integration
├── fourmeme_scanner.py  # four.meme / BSC token scanner
├── wallet_monitor.py    # Wallet monitoring + risk engine
├── templates/
│   └── index.html       # Trading dashboard UI
├── static/              # Static assets
├── .env                 # API keys (not committed)
└── requirements.txt     # Python dependencies
```

---

## 🔮 Future Roadmap

- [ ] Real on-chain trade execution via MYX Router contract
- [ ] Telegram bot integration for trade alerts
- [ ] Twitter/X sentiment analysis for meme tokens
- [ ] Multi-wallet portfolio tracking
- [ ] Backtesting engine

---

## 👥 Team

Built for the **Four.meme AI Sprint Hackathon** — April 2026

---

*MemePerp AI is for educational and demonstration purposes. Always do your own research before trading.*
