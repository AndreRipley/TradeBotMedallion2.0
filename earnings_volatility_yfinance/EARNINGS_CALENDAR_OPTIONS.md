# Earnings Calendar API Options

## Current Limitation

**yfinance does NOT have a global earnings calendar endpoint**. It only provides earnings data per individual ticker, which means:
- ❌ Must check each ticker individually
- ❌ Slow (2+ seconds per ticker)
- ❌ Rate limit issues with large lists

## Alternative APIs with Earnings Calendars

### Option 1: API Ninjas Earnings Calendar (FREE)

**Endpoint**: `https://api.api-ninjas.com/v1/earningscalendar`

**Features**:
- Free tier available
- Query by date to get all earnings for that date
- Returns ticker, date, and time (BMO/AMC)

**Example**:
```python
import requests

def get_earnings_calendar(date):
    url = "https://api.api-ninjas.com/v1/earningscalendar"
    params = {"date": date.strftime("%Y-%m-%d")}
    headers = {"X-Api-Key": "YOUR_API_KEY"}  # Free API key
    
    response = requests.get(url, params=params, headers=headers)
    return response.json()
```

**Get API Key**: https://api-ninjas.com/api/earningscalendar

### Option 2: Polygon.io Earnings Endpoint

**Endpoint**: `/v2/reference/earnings` (if available in your plan)

**Features**:
- Returns all tickers with earnings for date range
- Includes BMO/AMC information
- May require specific subscription tier

**Status**: Already implemented in `earnings_volatility` version (not yfinance version)

### Option 3: Financial Data API

**Endpoint**: Various endpoints for earnings calendar

**Features**:
- Upcoming earnings announcements
- Historical earnings data
- May require subscription

### Option 4: EarningsWhispers API

**Endpoint**: Custom API (paid)

**Features**:
- Comprehensive earnings calendar
- BMO/AMC detection
- Requires paid subscription

## Recommended Solution: API Ninjas

**Why API Ninjas?**
- ✅ Free tier available
- ✅ Simple API
- ✅ Returns all tickers for a date
- ✅ Includes BMO/AMC info

**Implementation**:
```python
def get_upcoming_earnings_calendar(target_date, days_ahead=1):
    """Get all earnings for date range using API Ninjas."""
    earnings_list = []
    
    for i in range(days_ahead + 1):
        date = target_date + timedelta(days=i)
        # Call API Ninjas endpoint
        # Parse results
        # Add to earnings_list
    
    return earnings_list
```

This would replace the need to check each ticker individually!

