# Supabase Setup for Ticker Price Logging

## Overview

The bot logs all ticker price checks to Supabase for historical tracking and analysis. This includes:
- Signal detection price checks (every minute during market hours)
- Position monitoring price checks (every minute)
- Trade execution prices (buy/sell orders)

## Setup Steps

### 1. Create Supabase Project

1. Go to https://supabase.com/
2. Sign up or log in
3. Create a new project
4. Note your project URL and anon/public key

### 2. Create Database Table

Run this SQL in the Supabase SQL Editor:

```sql
-- Create ticker_prices table
CREATE TABLE IF NOT EXISTS ticker_prices (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    price DECIMAL(10, 2) NOT NULL,
    price_type VARCHAR(20) NOT NULL, -- 'close', 'ask', 'bid', 'intraday'
    source VARCHAR(20) NOT NULL, -- 'yfinance', 'alpaca', etc.
    volume BIGINT,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_ticker_prices_symbol ON ticker_prices(symbol);
CREATE INDEX IF NOT EXISTS idx_ticker_prices_timestamp ON ticker_prices(timestamp);
CREATE INDEX IF NOT EXISTS idx_ticker_prices_symbol_timestamp ON ticker_prices(symbol, timestamp DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE ticker_prices ENABLE ROW LEVEL SECURITY;

-- Create policy to allow inserts (adjust as needed for your security requirements)
CREATE POLICY "Allow inserts for authenticated users" ON ticker_prices
    FOR INSERT
    WITH CHECK (true);

-- Create policy to allow reads (adjust as needed)
CREATE POLICY "Allow reads for authenticated users" ON ticker_prices
    FOR SELECT
    USING (true);
```

### 3. Get Supabase Credentials

1. Go to your Supabase project dashboard
2. Click on "Settings" → "API"
3. Copy:
   - **Project URL** (e.g., `https://xxxxx.supabase.co`)
   - **anon/public key** (under "Project API keys")

### 4. Configure Environment Variables

**For Local Development:**
Add to your `.env` file:
```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-anon-public-key-here
```

**For Cloud Run Deployment:**
Add these environment variables in Cloud Run console:
- `SUPABASE_URL` = your project URL
- `SUPABASE_KEY` = your anon/public key

### 5. Install Dependencies

```bash
pip3 install supabase
```

Or update requirements:
```bash
pip3 install -r requirements.txt
```

## What Gets Logged

### Price Check Types

1. **Signal Check** (`price_type: 'close'`)
   - When: Every minute during market hours for anomaly detection
   - Price: Closing price from Yahoo Finance
   - Includes: Volume data

2. **Position Monitor** (`price_type: 'intraday'`)
   - When: Every minute for position monitoring
   - Price: Current intraday price (1-minute bars)
   - Includes: Volume data

3. **Trade Execution** (`price_type: 'ask'` or `'bid'`)
   - When: When executing buy/sell orders
   - Price: Ask price (buy) or bid price (sell) from Alpaca
   - Includes: Order details (dollar amount, shares)

## Database Schema

```sql
ticker_prices
├── id (BIGSERIAL PRIMARY KEY)
├── symbol (VARCHAR) - Stock symbol (e.g., 'AAPL')
├── price (DECIMAL) - Price at time of check
├── price_type (VARCHAR) - Type: 'close', 'ask', 'bid', 'intraday'
├── source (VARCHAR) - Data source: 'yfinance', 'alpaca'
├── volume (BIGINT) - Trading volume (optional)
├── timestamp (TIMESTAMPTZ) - When price was checked
└── created_at (TIMESTAMPTZ) - Record creation time
```

## Querying Data

### Example Queries

**Get latest price for a symbol:**
```sql
SELECT * FROM ticker_prices 
WHERE symbol = 'AAPL' 
ORDER BY timestamp DESC 
LIMIT 1;
```

**Get all prices for a symbol today:**
```sql
SELECT * FROM ticker_prices 
WHERE symbol = 'AAPL' 
AND timestamp::date = CURRENT_DATE
ORDER BY timestamp;
```

**Get price statistics:**
```sql
SELECT 
    symbol,
    COUNT(*) as checks,
    MIN(price) as min_price,
    MAX(price) as max_price,
    AVG(price) as avg_price
FROM ticker_prices
WHERE timestamp::date = CURRENT_DATE
GROUP BY symbol
ORDER BY checks DESC;
```

## Cost Considerations

- **Supabase Free Tier**: 
  - 500 MB database storage
  - 2 GB bandwidth
  - Unlimited API requests
  
- **Estimated Usage**:
  - ~30 stocks × 390 checks/day = ~11,700 records/day
  - ~350,000 records/month
  - ~50-100 MB storage/month (depending on data)
  
- **Free tier should be sufficient** for most use cases

## Troubleshooting

### "Supabase credentials not configured"
- Check that `SUPABASE_URL` and `SUPABASE_KEY` are set in environment variables
- Verify credentials are correct

### "Error initializing Supabase client"
- Check internet connection
- Verify Supabase project is active
- Check that `supabase-py` is installed: `pip3 install supabase`

### "Failed to log price"
- Check Supabase table exists
- Verify RLS policies allow inserts
- Check Supabase logs for errors

### Price logging is disabled
- If Supabase credentials are not set, logging gracefully fails
- Bot continues to function normally without Supabase logging
- Check logs for warnings about Supabase

## Security Notes

- Use **anon/public key** (not service_role key) for client-side access
- RLS policies control access - adjust as needed
- Consider adding authentication if exposing API publicly
- Never commit Supabase keys to git

## Monitoring

### View Logs in Supabase

1. Go to Supabase dashboard
2. Click "Table Editor" → `ticker_prices`
3. View real-time data

### Check Logging Status

The bot logs to console when Supabase is initialized:
- `✅ Supabase client initialized successfully` - Working
- `⚠️ Supabase credentials not configured` - Not configured
- `❌ Error initializing Supabase client` - Error occurred

## Optional: Real-time Subscriptions

You can subscribe to real-time price updates:

```python
from supabase import create_client

client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Subscribe to new price inserts
subscription = client.table('ticker_prices').on('INSERT', handle_new_price).subscribe()

def handle_new_price(payload):
    print(f"New price: {payload}")
```

## Next Steps

1. Set up Supabase project
2. Create database table
3. Add environment variables
4. Deploy bot with Supabase credentials
5. Monitor price logs in Supabase dashboard

