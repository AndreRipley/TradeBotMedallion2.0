# Quick Start Guide - Earnings Volatility Bot (yfinance)

## Setup Steps

### 1. Install Dependencies

```bash
cd earnings_volatility_yfinance
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
# Copy template
cp env_template.txt .env

# Edit .env with your credentials
# Use your existing Alpaca and Supabase credentials
```

### 3. Create Database Table

Run the migration in Supabase SQL Editor:

```sql
-- Copy contents from: migrations/001_create_earnings_signals.sql
```

Or use Supabase MCP:
```bash
# The migration file contains the SQL
```

### 4. Test Setup

```bash
cd /Users/andreripley/Desktop/TradeBot
PYTHONPATH=/Users/andreripley/Desktop/TradeBot python3 -m earnings_volatility_yfinance.test_bot
```

### 5. Run the Bot

```bash
cd /Users/andreripley/Desktop/TradeBot
PYTHONPATH=/Users/andreripley/Desktop/TradeBot python3 -m earnings_volatility_yfinance.main
```

## Important Notes

- **Start Small**: Default ticker list is only 5 tickers to avoid rate limits
- **Rate Limits**: yfinance has rate limits. Default delay is 2 seconds between requests
- **Timing**: Bot only executes during entry (3:45 PM ET) or exit (9:45 AM ET) windows
- **Paper Trading**: Uses Alpaca paper trading by default

## Configuration

Key settings in `.env`:

- `TICKER_LIST`: Start with 5-10 tickers, expand later
- `YFINANCE_DELAY_SECONDS`: Increase if you hit rate limits (default: 2.0)
- `IV_SLOPE_THRESHOLD`: Minimum IV slope (default: 0.05)
- `MIN_VOLUME`: Minimum volume threshold (default: 1,500,000)

## Troubleshooting

### Rate Limit Errors
- Increase `YFINANCE_DELAY_SECONDS` to 3.0 or higher
- Reduce `TICKER_LIST` size
- The bot has retry logic, but too many requests will still fail

### No Options Data
- Not all tickers have options available
- The bot will skip tickers without options chains

### Earnings Date Issues
- yfinance earnings dates may not always be accurate
- Verify manually if needed

## Next Steps

1. ✅ Test with small ticker list
2. ✅ Monitor logs for rate limit issues
3. ✅ Expand ticker list gradually
4. ✅ Schedule for entry/exit windows

