# Earnings Calendar API Setup

## Overview

Instead of checking each ticker individually for earnings (slow and rate-limited), you can use an **earnings calendar API** to get all earnings for today/tomorrow in one call.

## Benefits

- ✅ **Much faster**: 1 API call vs. N calls (one per ticker)
- ✅ **Avoids rate limits**: Fewer requests to yfinance
- ✅ **More reliable**: Dedicated earnings calendar APIs are more accurate
- ✅ **Includes BMO/AMC**: Better time detection than yfinance

## Setup: API Ninjas (Free)

### Step 1: Get API Key

1. Go to https://api-ninjas.com/api/earningscalendar
2. Click "Get API Key" (free signup)
3. Copy your API key

### Step 2: Add to `.env`

Add this line to your `.env` file:

```bash
API_NINJAS_KEY=your_api_key_here
```

### Step 3: Use the Enhanced Bot

Run the calendar-enabled version:

```bash
python3 -m earnings_volatility_yfinance.main_calendar
```

Or import it:

```python
from earnings_volatility_yfinance.main_calendar import EarningsVolatilityBotCalendar

bot = EarningsVolatilityBotCalendar(use_calendar_api=True)
bot.run_scan()
```

## How It Works

### Old Method (Per-Ticker Scanning)
```
For each ticker in watchlist:
    1. Check earnings date (yfinance call)
    2. If earnings today/tomorrow → analyze IV/RV
    3. If passes filters → trade

Time: ~2-5 seconds per ticker
```

### New Method (Calendar API)
```
1. Fetch ALL earnings for today/tomorrow (1 API call)
2. Filter to tickers in watchlist
3. For each relevant ticker → analyze IV/RV
4. If passes filters → trade

Time: ~1 second + analysis time
```

## Example Output

```
Using earnings calendar API for efficient scanning...
Found 45 total earnings from calendar API
Filtered to 3 earnings in watchlist
Analyzing NVDA (earnings: 2024-11-21 AMC)
Analyzing AMD (earnings: 2024-11-22 BMO)
Analyzing TSLA (earnings: 2024-11-21 AMC)
Found 2 valid signals after filtering
```

## Fallback Behavior

If `API_NINJAS_KEY` is not set, the bot automatically falls back to per-ticker scanning:

```
API_NINJAS_KEY not set, falling back to per-ticker scanning
Scanning 5 tickers individually for earnings
```

## Alternative APIs

If you prefer a different provider, modify `data_service_calendar.py`:

- **Polygon.io**: Already implemented in `earnings_volatility` version
- **Financial Data API**: Requires subscription
- **EarningsWhispers**: Paid service

## Testing

Test the calendar API directly:

```python
from earnings_volatility_yfinance.data_service_calendar import EarningsCalendarService
from datetime import datetime

service = EarningsCalendarService(api_key="your_key")
earnings = service.get_earnings_for_date(datetime.now())
print(f"Found {len(earnings)} earnings today")
```

