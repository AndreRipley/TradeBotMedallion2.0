# Trading Bot - Improved Anomaly Detection Strategy

An automated trading bot that uses statistical anomaly detection to identify and capitalize on oversold and overbought conditions in the stock market. The bot implements a sophisticated strategy with risk management features including stop-losses, trailing stops, and dynamic position sizing.

## Strategy Overview

The bot uses an **Improved Anomaly Buy+Sell Strategy** that:

- **Detects statistical anomalies** in real-time using multiple technical indicators
- **Trades on oversold conditions** (buy signals) and **overbought conditions** (sell signals)
- **Manages risk** with stop-losses and trailing stops
- **Adapts position sizing** based on stock performance
- **Monitors continuously** during market hours for trading opportunities

## Features

- ✅ **Real-time anomaly detection** using Z-scores, RSI, price action, and volume analysis
- ✅ **Continuous monitoring** - checks all stocks every minute during market hours
- ✅ **Risk management** - 5% stop-loss and 5% trailing stop on all positions
- ✅ **Dynamic position sizing** - increases size for winners, decreases for losers
- ✅ **Multiple positions per stock** - can accumulate positions with independent risk management
- ✅ **Position monitoring** - checks open positions every minute for stop-loss triggers
- ✅ **30 diversified stocks** by default (across 7 sectors)
- ✅ **Paper trading support** via Alpaca API
- ✅ **Cloud deployed** - runs 24/7 on Google Cloud Run with health check endpoint
- ✅ **Comprehensive logging** and error handling

## Strategy Details

### Anomaly Detection

The bot detects anomalies using multiple indicators:

**Buy Signals (Oversold Conditions):**
- Z-score < -2.0 (price 2+ standard deviations below 20-day mean)
- Price drop > 3% in a day
- Gap down > 2% from previous close
- RSI < 30 (oversold)

**Sell Signals (Overbought Conditions):**
- Z-score > 2.0 (price 2+ standard deviations above mean)
- Price rise > 3% in a day
- Gap up > 2% from previous close
- RSI > 70 (overbought)

### Trading Logic

1. **Severity Threshold**: Only trades anomalies with severity ≥ 1.0
2. **Multiple Positions**: Can buy same stock multiple times (each tracked independently)
3. **Account Balance**: Checks buying power before each trade
4. **Risk Management**: Stop-losses and trailing stops protect capital
5. **Independent Stops**: Each position has its own stop-loss and trailing stop

### Risk Management

- **Stop-Loss**: 5% below entry price (fixed protection)
- **Trailing Stop**: 5% below highest price reached (locks in gains)
- **Position Monitoring**: Checks every minute during market hours
- **Dynamic Sizing**: Adjusts position size based on win rate:
  - Win rate ≥ 60%: +20% position size
  - Win rate 50-60%: Normal size
  - Win rate 40-50%: -20% position size
  - Win rate < 40%: -40% position size

## Requirements

- Python 3.8+
- Trading API account (Alpaca recommended for paper trading)
- Stock data API (Alpha Vantage - optional, Yahoo Finance fallback available)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip3 install -r requirements.txt
```

3. Copy `env_template.txt` to `.env` and configure:
```bash
cp env_template.txt .env
```

4. Edit `.env` with your settings:
   - **STOCKS**: Comma-separated list of stock symbols (default: 30 stocks)
   - **ALPACA_API_KEY** & **ALPACA_SECRET_KEY**: For executing trades (get from https://alpaca.markets/)
   - **ALPACA_BASE_URL**: `https://paper-api.alpaca.markets` for paper trading
   - **ALPHA_VANTAGE_API_KEY**: Optional, for stock data
   - **POSITION_SIZE**: Dollar amount per stock (default: $1000.0)
   - **TIMEZONE**: Market timezone (default: `America/New_York`)

## Usage

### Running Locally

**Foreground (for testing):**
```bash
python3 main.py
# Press Ctrl+C to stop
```

**Background:**
```bash
./start_bot.sh    # Start bot
./check_bot.sh    # Check status
./stop_bot.sh     # Stop bot
```

### Cloud Deployment (Recommended for 24/7 Operation)

**Currently Deployed**: The bot is configured and ready for Google Cloud Run deployment.

**Deploy to Google Cloud Run:**

```bash
bash deploy_fix_permissions.sh
```

**What Gets Deployed:**
- Docker containerized application
- HTTP health check endpoint (`/health` and `/` on port 8080)
- Runs continuously with `min-instances=1` (24/7 operation)
- Environment variables configured via Cloud Run console
- Automatic logging to Cloud Run logs

**After Deployment:**
1. Set environment variables in Cloud Run console (see `CLOUD_RUN_ENV_VARS.md`)
2. Bot starts automatically and runs continuously
3. Monitor via Cloud Run logs or use `view_logs.sh` script

See `QUICK_DEPLOY.md`, `GCP_DEPLOYMENT.md` and `CLOUD_RUN_ENV_VARS.md` for detailed instructions.

## How It Works

### Trading Schedule

- **Signal Detection**: Every 1 minute during market hours (9:30 AM - 4:00 PM ET, weekdays)
- **Position Monitoring**: Every 1 minute during market hours
- **Stocks Monitored**: 30 stocks by default (configurable)

### Trading Process

1. **Every Minute During Market Hours:**
   - Fetches recent price data for all monitored stocks
   - Calculates technical indicators (Z-score, RSI, volume, gaps)
   - Detects anomalies and calculates severity scores
   - Executes trades if severity ≥ 1.0 and conditions are met
   - Checks existing positions for stop-loss/trailing stop triggers

2. **Buy Signal Execution:**
   - Checks account balance and buying power
   - Calculates dynamic position size based on stock performance
   - Executes buy order via Alpaca API (uses ask_price)
   - Creates new logical position with independent stop-loss and trailing stop
   - Tracks position separately (supports multiple positions per stock)
   - Alpaca combines positions physically, but bot tracks them independently

3. **Sell Signal Execution (3 types):**
   - **Stop-Loss**: Price drops 5% below entry → SELL entire position
   - **Trailing Stop**: Price drops 5% below highest → SELL entire position
   - **Overbought**: Severity ≥ 3.0 with position → SELL entire position
   - Executes sell order via Alpaca API (uses bid_price)
   - Calculates profit/loss for each logical position
   - Updates performance tracking (wins/losses per stock)

4. **Position Monitoring:**
   - Checks current price every minute (using 1-minute bars from Yahoo Finance)
   - Updates trailing stop independently for each position if price increases
   - Executes sell if any position's stop-loss or trailing stop triggered
   - Sells entire Alpaca position (all logical positions) when any trigger fires
   - Protects capital from rapid declines

## Default Stock List

The bot monitors 30 diversified stocks by default:

**Technology (11):** AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, ADBE, CSCO, NFLX, ACN  
**Finance (3):** V, JPM, MA  
**Healthcare (7):** UNH, JNJ, LLY, MRK, ABBV, ABT, TMO  
**Consumer (4):** WMT, PG, COST, MCD  
**Energy (2):** XOM, CVX  
**Industrial (2):** HD, AVGO  
**Consumer Staples (1):** PEP

See `STOCK_LISTS.md` for 20-stock and 50-stock alternatives.

## Configuration

### Environment Variables

- **STOCKS**: Comma-separated stock symbols (no spaces)
- **POSITION_SIZE**: Dollar amount per stock (default: 1000.0)
- **TIMEZONE**: Market timezone (default: America/New_York)
- **LOG_LEVEL**: DEBUG, INFO, WARNING, ERROR (default: INFO)

### Strategy Parameters

Configured in `scheduler.py`:
- `min_severity`: 1.0 (minimum anomaly severity to trade)
- `stop_loss_pct`: 0.05 (5% stop-loss)
- `trailing_stop_pct`: 0.05 (5% trailing stop)

## API Setup

### Alpaca (Required for Trading)

1. Sign up at https://alpaca.markets/
2. Get your API keys from the dashboard
3. Use paper trading URL: `https://paper-api.alpaca.markets`
4. Add keys to `.env` or Cloud Run environment variables

### Alpha Vantage (Optional)

1. Get free API key from https://www.alphavantage.co/support/#api-key
2. Add to `.env` as `ALPHA_VANTAGE_API_KEY`
3. If not provided, bot uses Yahoo Finance (free, no API key needed)

## Monitoring & Logs

### View Logs

**Local:**
```bash
tail -f trading_bot.log
```

**Cloud Run:**
```bash
bash view_logs.sh          # View recent logs
bash stream_logs.sh         # Stream logs (polling)
bash check_cloud_bot.sh     # Check bot status
```

**Browser:**
- Go to Google Cloud Console → Cloud Run → trading-bot → LOGS tab

### What to Look For

- `🟢 BUY SIGNAL detected` - Anomaly detected, trade executed
- `🔴 SELL SIGNAL detected` - Overbought condition or stop-loss triggered
- `🔍 Monitoring X positions` - Position monitoring active
- `💰 Account Balance` - Buying power check before trades
- `⚠️ INSUFFICIENT BUYING POWER` - Need to add funds

## Safety Features

- **Paper trading mode** by default (Alpaca)
- **Account balance checking** before trades
- **Stop-losses** limit downside risk
- **Trailing stops** protect profits
- **Dynamic position sizing** reduces risk on losing stocks
- **Comprehensive error handling** and logging
- **Simulated orders** if no API credentials provided

## Expected Performance

- **Trade Frequency**: 0-5 trades per day (strategy is selective)
- **Win Rate**: Varies by market conditions
- **Risk Management**: Stop-losses limit losses to 5% per position
- **Capital Utilization**: Monitors 30 stocks, trades when opportunities arise

The strategy prioritizes **quality over quantity** - waiting for significant anomalies rather than trading constantly.

## Troubleshooting

### Low Trade Frequency

This is **normal** - the strategy is selective:
- Only trades anomalies with severity ≥ 1.0
- Requires specific conditions (oversold/overbought)
- Can buy same stock multiple times (multiple positions supported)
- See `TROUBLESHOOTING_LOW_TRADES.md` for details

### Insufficient Buying Power

- Add funds to Alpaca paper account: https://app.alpaca.markets/paper/dashboard/account
- Or reduce `POSITION_SIZE` in environment variables
- See `FIX_BUYING_POWER.md` for solutions

### Other Issues

- **"command not found: python"**: Use `python3` on macOS
- **No trades executing**: Check logs, verify API keys, ensure market hours
- **API errors**: Verify credentials and rate limits
- **Price data issues**: Check internet connection

## Cloud Deployment Status

✅ **Ready for Deployment**: The bot is fully configured for Google Cloud Run

**Deployment Features:**
- ✅ Docker containerized (`Dockerfile` included)
- ✅ HTTP health check endpoint (`/health` and `/` on port 8080)
- ✅ Cloud Run compatible (handles PORT environment variable)
- ✅ Continuous operation (`min-instances=1` keeps it running 24/7)
- ✅ Environment variable configuration via Cloud Run console
- ✅ Comprehensive logging to Cloud Run logs

**Deployment Scripts:**
- `deploy_fix_permissions.sh` - Full deployment with permission fixes (recommended)
- `deploy_gcp.sh` - Standard deployment script
- `deploy_automated.sh` - Automated deployment with project creation

**Quick Deploy:**
```bash
bash deploy_fix_permissions.sh
```

Then set environment variables in Cloud Run console (see `CLOUD_RUN_ENV_VARS.md`).

## Important Notes

⚠️ **DISCLAIMER**: This bot is for educational purposes. Always test with paper trading first. Trading involves risk of financial loss. Use at your own risk.

- **Cloud Deployment**: Bot runs 24/7 on Cloud Run (no computer needed)
- **Market Hours**: Only trades 9:30 AM - 4:00 PM ET on weekdays
- **Selective Trading**: Low trade frequency is intentional - strategy waits for good opportunities
- **Risk Management**: Stop-losses and trailing stops protect capital
- **Multiple Positions**: Can hold multiple positions per stock with independent risk management
- **Health Check**: HTTP endpoint on port 8080 for Cloud Run health checks

## Documentation

**Deployment:**
- `QUICK_DEPLOY.md` - Quick deployment guide ⭐
- `CLOUD_RUN_ENV_VARS.md` - Environment variables guide
- `GCP_DEPLOYMENT.md` - Detailed Google Cloud deployment instructions
- `deploy_fix_permissions.sh` - Deployment script (recommended)

**Understanding the Bot:**
- `CURRENT_BOT_DETAILED_EXPLANATION.md` - Complete explanation of current bot behavior
- `LIVE_VS_BACKTEST_COMPARISON.md` - Differences between live bot and backtest
- `MULTIPLE_POSITIONS_EXPLANATION.md` - How multiple positions work

**Troubleshooting:**
- `TROUBLESHOOTING_LOW_TRADES.md` - Why trade frequency is low
- `FIX_BUYING_POWER.md` - Resolving insufficient buying power
- `POSITION_CHECK_ANALYSIS.md` - Position monitoring frequency analysis

**Configuration:**
- `STOCK_LISTS.md` - Stock list options (20, 30, 50 stocks)
- `STRATEGY_COMPARISON_GUIDE.md` - How to add new strategies

## License

MIT License - Use at your own risk.
