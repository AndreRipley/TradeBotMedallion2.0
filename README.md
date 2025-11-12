# Trading Bot

A Python trading bot that automatically buys stocks at noon on days when the stock price has gone down (red days).

## Features

- ✅ Monitors multiple stocks simultaneously
- ✅ Detects "red days" (days when stock price decreased)
- ✅ Executes buy orders automatically at noon
- ✅ Supports paper trading (Alpaca) and live trading
- ✅ Configurable position sizing
- ✅ Comprehensive logging


## Requirements

- Python 3.8+
- Trading API account (Alpaca recommended for paper trading)
- Stock data API (Alpha Vantage - free tier available, or Yahoo Finance fallback)

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip3 install -r requirements.txt
# or: python3 -m pip install -r requirements.txt
```

3. Copy `env_template.txt` to `.env` and configure:
```bash
cp env_template.txt .env
```

4. Edit `.env` with your settings:
   - **STOCKS**: Comma-separated list of stock symbols to monitor
   - **ALPACA_API_KEY** & **ALPACA_SECRET_KEY**: For executing trades (get from https://alpaca.markets/)
   - **ALPHA_VANTAGE_API_KEY**: Optional, for stock data (get from https://www.alphavantage.co/support/#api-key)
   - **POSITION_SIZE**: Dollar amount to invest per stock per trade

## Usage

## Running the Bot

### Option 1: Run in Foreground (for testing)
```bash
python3 main.py
# Note: On macOS, use python3 instead of python
# Press Ctrl+C to stop
```

### Option 2: Run in Background (recommended for continuous operation)
```bash
# Start the bot in background
./start_bot.sh

# Check if bot is running
./check_bot.sh

# Stop the bot
./stop_bot.sh
```

### Option 3: Using screen/tmux (keeps running after terminal closes)
```bash
# Install screen (if not installed)
# macOS: brew install screen

# Start a screen session
screen -S trading_bot

# Run the bot
python3 main.py

# Detach: Press Ctrl+A then D
# Reattach: screen -r trading_bot
```

### Option 4: Run on a Cloud Server (best for 24/7 operation)
- Deploy to AWS EC2, Google Cloud, DigitalOcean, etc.
- Use a process manager like `systemd` or `supervisord`
- Or use a cloud function/serverless option

The bot will:
1. Check every minute if it's noon
2. At noon, check each configured stock to see if it's a "red day"
3. If it's a red day, execute a buy order for that stock
4. Log all activities to console and `trading_bot.log`

### Configuration

Edit `config.py` or `.env` to customize:

- **Stocks to monitor**: Set `STOCKS` environment variable
- **Trade time**: Default is `12:00` (noon), change `TRADE_TIME` in config
- **Position size**: Set `POSITION_SIZE` in dollars
- **Timezone**: Default is `America/New_York` (US market timezone)

## How It Works

1. **Red Day Detection**: Compares current stock price with previous day's closing price
2. **Scheduling**: Uses `schedule` library to trigger trades at noon daily
3. **Trading**: Executes market buy orders via Alpaca API (or simulates if no API key)

## API Setup

### Alpaca (Recommended for Paper Trading)

1. Sign up at https://alpaca.markets/
2. Get your API keys from the dashboard
3. Use paper trading URL: `https://paper-api.alpaca.markets`
4. Add keys to `.env`

### Alpha Vantage (Optional - Stock Data)

1. Get free API key from https://www.alphavantage.co/support/#api-key
2. Add to `.env` as `ALPHA_VANTAGE_API_KEY`
3. If not provided, bot will use Yahoo Finance (free, no API key needed)

## Safety Features

- Paper trading mode by default (Alpaca)
- Simulated orders if no API credentials provided
- Comprehensive error handling and logging
- Configurable position sizing

## Logging

Logs are written to:
- Console (INFO level and above)
- `trading_bot.log` file (all levels)

## Important Notes

⚠️ **DISCLAIMER**: This bot is for educational purposes. Always test with paper trading first. Trading involves risk of financial loss. Use at your own risk.

- **Cursor/IDE**: You can close Cursor - the bot runs independently as a Python process
- **Computer**: Your computer must stay on (or use a cloud server for 24/7 operation)
- **Terminal**: If running in foreground, keep terminal open. Use background mode or screen/tmux to avoid this
- The bot runs continuously - use `Ctrl+C` or `./stop_bot.sh` to stop
- Ensure your system clock is accurate
- Bot checks at noon in the configured timezone
- Only executes on trading days (when markets are open)

## Troubleshooting

- **"command not found: python"**: On macOS, use `python3` instead of `python`
- **No trades executing**: Check logs, verify API keys, ensure it's a trading day
- **API errors**: Verify API credentials and rate limits
- **Price data issues**: Check internet connection and API key validity

## License

MIT License - Use at your own risk.

