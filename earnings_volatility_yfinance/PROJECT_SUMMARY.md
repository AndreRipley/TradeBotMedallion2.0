# Earnings Volatility Trading Bot (yfinance) - Project Summary

## ✅ Implementation Complete

A complete automated trading bot rebuilt to use **yfinance** (Yahoo Finance) for all market data instead of Polygon.io.

## 📁 Project Structure

```
earnings_volatility_yfinance/
├── Core Modules
│   ├── config.py              ✅ Configuration with ticker list
│   ├── data_service.py        ✅ Yahoo Finance data (yfinance + tenacity)
│   ├── analysis_engine.py     ✅ RV calculation & filtering
│   ├── execution_service.py   ✅ Alpaca calendar spread execution
│   ├── database.py           ✅ Supabase operations
│   └── main.py               ✅ Main orchestrator
│
├── Testing
│   └── test_bot.py           ✅ Component test script
│
├── Database
│   └── migrations/
│       └── 001_create_earnings_signals.sql ✅ Supabase schema
│
└── Documentation
    ├── README.md
    ├── QUICK_START.md
    └── PROJECT_SUMMARY.md
```

## 🎯 Key Features

### Data Source: yfinance
- ✅ Price history for RV calculation
- ✅ Volume data for liquidity filter
- ✅ Options chains for IV data
- ✅ Earnings calendar

### Rate Limiting
- ✅ `tenacity` library for retry logic
- ✅ Exponential backoff (up to 5 attempts)
- ✅ Configurable delay between requests (default: 2 seconds)
- ✅ Custom `YFRateLimitError` exception handling

### Strategy Implementation
- ✅ Entry: 15 minutes before market close (3:45 PM ET)
- ✅ Exit: 15 minutes after market open (9:45 AM ET)
- ✅ Long Calendar Spread execution
- ✅ All three filters implemented:
  1. IV Term Structure Slope > 0.05
  2. Volume > 1,500,000
  3. IV/RV Ratio > 1.2

## 📊 Filtering Logic

### Step 1: Volume Check (Fastest)
- Fetches 30-day market data
- Checks average volume against threshold
- Rejects immediately if fails

### Step 2: Earnings Date Check
- Fetches earnings date from yfinance
- Verifies earnings is today (AMC) or tomorrow (BMO)
- Rejects if not in window

### Step 3: IV/RV & Slope Check (Slowest)
- Calculates Realized Volatility from price history
- Fetches option chains for front and back month
- Finds ATM strikes
- Calculates IV slope and IV/RV ratio
- Rejects if thresholds not met

## 🔧 Technical Implementation

### IV Calculation
- Finds ATM option by minimizing `abs(strike - current_price)`
- Handles yfinance option chain dataframe structure
- Extracts IV from various possible column names

### Date Parsing
- Handles multiple earnings date formats
- Converts to UTC for consistency
- Handles timezone conversion carefully

### Calendar Spread Execution
- Two-leg order (Alpaca doesn't support native calendar spreads)
- Sequential execution: Buy back month → Sell front month
- Cancels back leg if front leg fails

## 📝 Configuration

### Environment Variables
- `ALPACA_KEY`, `ALPACA_SECRET`: Trading execution
- `SUPABASE_URL`, `SUPABASE_KEY`: Database logging
- `TICKER_LIST`: Comma-separated ticker list (start small!)
- `YFINANCE_DELAY_SECONDS`: Rate limiting delay (default: 2.0)
- `IV_SLOPE_THRESHOLD`: Minimum IV slope (default: 0.05)
- `MIN_VOLUME`: Minimum volume (default: 1,500,000)
- `MIN_IV_RV_RATIO`: Minimum IV/RV ratio (default: 1.2)

### Default Ticker List
Start with: `["AAPL", "TSLA", "AMD", "NVDA", "META"]`

Expand gradually to avoid rate limits.

## 🚀 Quick Start

1. **Install**: `pip install -r requirements.txt`
2. **Configure**: Copy `env_template.txt` to `.env` and fill in credentials
3. **Database**: Run migration SQL in Supabase
4. **Test**: `python -m earnings_volatility_yfinance.test_bot`
5. **Run**: `python -m earnings_volatility_yfinance.main`

## ⚠️ Important Notes

### Rate Limiting
- yfinance has rate limits
- Default 2-second delay between requests
- Increase `YFINANCE_DELAY_SECONDS` if you hit limits
- Start with small ticker list (5-10 tickers)

### Options Data
- Not all tickers have options available
- Bot will skip tickers without option chains
- Some expirations may not be available

### Earnings Dates
- yfinance earnings dates may not always be accurate
- Bot checks for today (AMC) or tomorrow (BMO)
- Verify manually if needed

## 📈 Strategy Execution

### Entry Window (3:45 PM - 4:00 PM ET)
1. Scans ticker list
2. Checks each ticker's filters
3. Executes calendar spreads on qualifying stocks
4. Logs all signals to database

### Exit Window (9:45 AM - 10:00 AM ET)
1. Checks open positions
2. Closes positions that have reached exit time
3. Calculates P&L
4. Updates database

## 🔍 Logging

Clear rejection reasons for each ticker:
- `"Rejected AAPL: Volume 500k < 1.5M"`
- `"Rejected TSLA: IV Slope 0.03 <= threshold 0.05"`
- `"Rejected AMD: IV/RV Ratio 1.1 < threshold 1.2"`

All logs written to: `logs/earnings_volatility_yfinance_YYYY-MM-DD.log`

## ✨ Differences from Polygon.io Version

1. **Data Source**: yfinance instead of Polygon.io
2. **Rate Limiting**: Aggressive retry logic with tenacity
3. **Ticker List**: Predefined list instead of earnings-driven scan
4. **Table Name**: `earnings_signals` instead of `earnings_trades`
5. **IV Calculation**: Finds ATM from dataframe instead of API response

## 🎯 Status

**Ready for testing!** All components implemented with:
- ✅ yfinance integration
- ✅ Retry logic and rate limiting
- ✅ Complete filtering pipeline
- ✅ Calendar spread execution
- ✅ Database logging
- ✅ Comprehensive error handling

