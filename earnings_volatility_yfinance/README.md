# Earnings Volatility Trading Bot (yfinance version)

An automated trading bot implementing an "Earnings Volatility Selling" strategy using Long Calendar Spreads, powered by Yahoo Finance (yfinance) for all market data.

## Strategy Overview

The bot scans a predefined list of liquid tickers for earnings announcements and executes Long Calendar Spreads when specific volatility conditions are met:

- **Entry**: 15 minutes before market close (3:45 PM ET)
- **Exit**: 15 minutes after market open next day (9:45 AM ET)
- **Structure**: Long Calendar Spread (Sell front-month, Buy back-month ATM options)

## Filtering Criteria

All of the following conditions must be met for a trade:

1. **IV Term Structure Slope (Backwardation)**: Front month IV must be > 0.05 higher than back month IV
2. **Liquidity**: 30-day average volume > 1,500,000
3. **IV/RV Ratio**: Current implied volatility must be > 1.2x realized volatility

## Key Features

- **yfinance Integration**: All data from Yahoo Finance (no Polygon.io needed)
- **Aggressive Rate Limiting**: Built-in retry logic with exponential backoff using `tenacity`
- **Predefined Ticker List**: Start with small list to avoid rate limits
- **Comprehensive Logging**: Clear "why rejected" messages for each ticker

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file:

```bash
# Alpaca API Configuration
ALPACA_KEY=your_alpaca_api_key
ALPACA_SECRET=your_alpaca_secret
ALPACA_PAPER=true

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Trading Configuration (Optional)
RISK_PER_TRADE_PCT=5.0
IV_SLOPE_THRESHOLD=0.05
MIN_VOLUME=1500000
MIN_IV_RV_RATIO=1.2
TICKER_LIST=AAPL,TSLA,AMD,NVDA,META  # Start small!
YFINANCE_DELAY_SECONDS=2.0
```

### 3. Set Up Database

Run the migration in Supabase:

```sql
-- Copy contents from: migrations/001_create_earnings_signals.sql
```

### 4. Run the Bot

```bash
python -m earnings_volatility_yfinance.main
```

## Rate Limiting

The bot includes aggressive rate limiting:

- **Default delay**: 2 seconds between yfinance requests
- **Retry logic**: Up to 5 attempts with exponential backoff
- **Custom exception handling**: Detects rate limit errors and retries

Adjust `YFINANCE_DELAY_SECONDS` in `.env` if you hit rate limits.

## Ticker List

Start with a small list (5-10 tickers) to avoid rate limits:

```bash
TICKER_LIST=AAPL,TSLA,AMD,NVDA,META
```

Once stable, you can expand to S&P 500 or other lists.

## Logging

Logs are written to `logs/earnings_volatility_yfinance_YYYY-MM-DD.log` with:
- Clear rejection reasons for each ticker
- Execution details
- Error handling

## Important Notes

- **Rate Limits**: yfinance has rate limits. The bot handles this with retries and delays.
- **Options Data**: Not all tickers have options data available. The bot will skip these.
- **Earnings Dates**: yfinance earnings dates may not always be accurate. Verify manually if needed.
- **Paper Trading**: Uses Alpaca paper trading by default.

## Architecture

```
earnings_volatility_yfinance/
├── config.py              # Configuration & env vars
├── data_service.py        # Yahoo Finance data (yfinance)
├── analysis_engine.py     # Metrics & filtering
├── execution_service.py   # Alpaca trading
├── database.py           # Supabase operations
└── main.py               # Main orchestrator
```

## License

See main project license.

