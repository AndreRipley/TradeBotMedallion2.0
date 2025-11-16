# Upload Top 50 Stocks Data to Supabase

## ✅ Table Created

The `stock_ohlc_30min` table has been successfully created in your Supabase database!

## 📊 Table Schema

```sql
stock_ohlc_30min
├── id (BIGSERIAL PRIMARY KEY)
├── symbol (VARCHAR) - Stock symbol (e.g., 'AAPL')
├── datetime (TIMESTAMPTZ) - Timestamp of the bar
├── date (DATE) - Date component
├── time (TIME) - Time component
├── open (DECIMAL) - Opening price
├── high (DECIMAL) - High price
├── low (DECIMAL) - Low price
├── close (DECIMAL) - Closing price
├── volume (BIGINT) - Trading volume
├── trade_count (BIGINT) - Number of trades (optional)
├── vwap (DECIMAL) - Volume-weighted average price (optional)
└── created_at (TIMESTAMPTZ) - Record creation timestamp
```

## 🚀 Upload Data

### Option 1: Using Python Script (Recommended)

1. **Ensure Supabase credentials are configured** in your `.env` file:
   ```bash
   SUPABASE_URL=https://your-project-id.supabase.co
   SUPABASE_KEY=your-anon-public-key-here
   ```

2. **Run the upload script**:
   ```bash
   python3 upload_to_supabase_batch.py top50_stocks_30min_1year_alpaca_20251115.csv
   ```

   The script will:
   - Read the CSV file (174,584 rows)
   - Upload in batches of 500 records
   - Show progress for each batch
   - Handle duplicate records gracefully

### Option 2: Using Supabase Dashboard

1. Go to your Supabase dashboard
2. Click "Table Editor" → `stock_ohlc_30min`
3. Click "Insert" → "Import CSV"
4. Upload `top50_stocks_30min_1year_alpaca_20251115.csv`
5. Map columns:
   - Symbol → symbol
   - Datetime → datetime
   - Date → date
   - Time → time
   - Open → open
   - High → high
   - Low → low
   - Close → close
   - Volume → volume
   - trade_count → trade_count (optional)
   - vwap → vwap (optional)

## 📈 Data Overview

- **Total Records**: 174,584 rows
- **Stocks**: 50 stocks (top 50 by market cap)
- **Date Range**: November 15, 2024 to November 14, 2025
- **Interval**: 30-minute bars
- **Market Hours Only**: 9:30 AM - 4:00 PM ET

## 🔍 Example Queries

### Get latest prices for all stocks:
```sql
SELECT DISTINCT ON (symbol)
    symbol, datetime, close as price, volume
FROM stock_ohlc_30min
ORDER BY symbol, datetime DESC;
```

### Get price statistics by stock:
```sql
SELECT 
    symbol,
    COUNT(*) as records,
    MIN(low) as min_price,
    MAX(high) as max_price,
    AVG(close) as avg_price,
    SUM(volume) as total_volume
FROM stock_ohlc_30min
GROUP BY symbol
ORDER BY symbol;
```

### Get AAPL data for a specific date:
```sql
SELECT *
FROM stock_ohlc_30min
WHERE symbol = 'AAPL'
  AND date = '2025-11-14'
ORDER BY time;
```

### Get daily price ranges:
```sql
SELECT 
    symbol,
    date,
    MIN(low) as daily_low,
    MAX(high) as daily_high,
    FIRST_VALUE(open) OVER (PARTITION BY symbol, date ORDER BY time) as daily_open,
    LAST_VALUE(close) OVER (PARTITION BY symbol, date ORDER BY time ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING) as daily_close
FROM stock_ohlc_30min
WHERE symbol = 'AAPL'
GROUP BY symbol, date
ORDER BY date DESC;
```

### Find stocks with highest volatility:
```sql
SELECT 
    symbol,
    AVG(high - low) as avg_range,
    STDDEV(close) as price_volatility,
    MAX(high) - MIN(low) as total_range
FROM stock_ohlc_30min
GROUP BY symbol
ORDER BY price_volatility DESC
LIMIT 10;
```

## 📊 Data Files

- **Combined CSV**: `top50_stocks_30min_1year_alpaca_20251115.csv` (174,584 rows)
- **Individual Stock Files**: `top50_stocks_30min_1year_alpaca_20251115/` directory (50 files)

## ⚠️ Notes

- **Duplicate Handling**: The table has a UNIQUE constraint on (symbol, datetime), so duplicate uploads will be skipped
- **Batch Upload**: The script uploads in batches of 500 to avoid timeouts
- **Rate Limiting**: Small delays between batches to avoid rate limits
- **Storage**: ~174k records × ~100 bytes = ~17 MB (well within free tier limits)

## 🔧 Troubleshooting

### "Supabase credentials not configured"
- Check `.env` file has `SUPABASE_URL` and `SUPABASE_KEY`
- Verify credentials are correct

### "Duplicate key error"
- This is normal - records already exist
- The script handles this gracefully

### "Timeout error"
- Reduce `BATCH_SIZE` in the script (default: 500)
- Check your internet connection
- Try uploading smaller chunks

### "RLS policy error"
- Verify RLS policies were created correctly
- Check Supabase dashboard → Authentication → Policies

## ✅ Next Steps

1. Upload the data using one of the methods above
2. Verify data in Supabase dashboard
3. Create dashboards or visualizations
4. Use for backtesting or analysis
5. Set up real-time updates if needed

