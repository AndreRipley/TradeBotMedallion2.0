# How Earnings Are Checked

## Overview

The bot checks earnings dates using **yfinance** (Yahoo Finance) for each ticker in the predefined list. It only trades stocks with earnings **today (AMC)** or **tomorrow (BMO)**.

## Earnings Check Flow

### Step 1: Fetch Earnings Date (`data_service.py::get_earnings_date()`)

For each ticker, the bot:

1. **Creates yfinance Ticker object**
   ```python
   stock = yf.Ticker(ticker)
   info = stock.info
   ```

2. **Tries multiple fields in `info` dictionary**
   - Checks in order: `earningsDate`, `earningsTimestamp`, `earningsTimestampStart`
   - Handles multiple formats:
     - **Unix timestamp** (int/float): Converts using `datetime.fromtimestamp()`
     - **String date** (YYYY-MM-DD): Parses using `datetime.strptime()`
     - **List**: Takes first element if it's a list

3. **Fallback: Check `earningsCalendar`**
   - If `info` doesn't have earnings date, tries `stock.calendar`
   - Calendar is a **dict** with key `"Earnings Date"` containing a list of dates
   - Gets the first (next) earnings date from the list
   - Converts `datetime.date` to `datetime` using `datetime.combine()`

4. **Default Time**
   - yfinance doesn't always provide BMO/AMC info
   - **Defaults to "AMC"** (After Market Close)
   - This is a limitation - you may want to enhance with other sources

### Step 2: Validate Earnings Window (`analysis_engine.py::analyze_ticker()`)

After fetching earnings date, the bot checks:

```python
# Check if earnings is today (AMC) or tomorrow (BMO)
today = datetime.now().date()
tomorrow = (datetime.now() + timedelta(days=1)).date()

earnings_date_only = earnings_date.date()

if earnings_date_only not in [today, tomorrow]:
    # REJECT - earnings not in trading window
    return False, None, "Earnings date not today or tomorrow"
```

**Logic**:
- ✅ **Today (AMC)**: Earnings after market close today → Trade today before close
- ✅ **Tomorrow (BMO)**: Earnings before market open tomorrow → Trade today before close
- ❌ **Any other date**: Rejected (not in trading window)

## Code Flow Diagram

```
For each ticker in TICKER_LIST:
    │
    ├─> get_earnings_date(ticker)
    │   │
    │   ├─> Method 1: Check info fields
    │   │   ├─> info["earningsDate"]
    │   │   ├─> info["earningsTimestamp"]
    │   │   └─> info["earningsTimestampStart"]
    │   │       └─> Parse date (timestamp/string/list)
    │   │
    │   └─> Method 2: Check calendar (if Method 1 fails)
    │       └─> stock.calendar["Earnings Date"][0]
    │           └─> Convert date to datetime
    │
    ├─> Check: earnings_date in [today, tomorrow]?
    │   │
    │   ├─> YES → Continue to IV/RV checks
    │   │
    │   └─> NO → REJECT ("Earnings date not today or tomorrow")
    │
    └─> Continue with other filters...
```

## Example

**Scenario**: Today is Tuesday, Nov 19, 2024

**Ticker: AAPL**
1. `get_earnings_date("AAPL")` 
   - Checks `info["earningsTimestamp"]` → `1761854400` (Unix timestamp)
   - Parses: `2025-10-30` (future date)
   - Check: `2025-10-30` in `[2024-11-19, 2024-11-20]`? ❌ **NO**
2. **Result**: REJECT ("Earnings date 2025-10-30 not today or tomorrow")

**Ticker: TSLA** (if earnings were tomorrow)
1. `get_earnings_date("TSLA")` → Returns `{"date": 2024-11-20, "time": "AMC"}`
2. Check: `2024-11-20` in `[2024-11-19, 2024-11-20]`? ✅ **YES**
3. **Result**: Continue analysis (earnings tomorrow BMO)

## Implementation Details

### Date Parsing (`data_service.py`)

The bot handles multiple yfinance date formats:

**Method 1: Info Dictionary**
```python
# Check multiple fields
earnings_fields = ["earningsDate", "earningsTimestamp", "earningsTimestampStart"]

for field in earnings_fields:
    if field in info and info[field]:
        # Parse timestamp or string
        if isinstance(value, (int, float)):
            earnings_date = datetime.fromtimestamp(value)
        elif isinstance(value, str):
            earnings_date = datetime.strptime(value, "%Y-%m-%d")
```

**Method 2: Calendar Dictionary**
```python
calendar = stock.calendar  # Returns dict, not DataFrame!

if isinstance(calendar, dict) and "Earnings Date" in calendar:
    earnings_dates = calendar["Earnings Date"]  # List of datetime.date objects
    first_date = earnings_dates[0]
    earnings_date = datetime.combine(first_date, datetime.min.time())
```

### Timezone Handling

- Earnings dates are converted to date-only (no time)
- Comparison uses `datetime.now().date()` for consistency
- Timezone conversion handled carefully to avoid errors

### BMO vs AMC Detection

**Current Implementation**:
- Defaults to "AMC" (After Market Close)
- yfinance doesn't reliably provide BMO/AMC info

**Enhancement Options**:
- Check `info.get("earningsCallTimestampStart")` for time hints
- Use `info.get("isEarningsDateEstimate")` to verify accuracy
- Parse from earnings announcement text
- Use third-party earnings calendar API

## Rate Limiting

Each earnings check includes:
- **2-second delay** before request (`YFINANCE_DELAY_SECONDS`)
- **Retry logic** with exponential backoff (up to 5 attempts)
- **Error handling** for rate limit errors

## Limitations

1. **yfinance Data Quality**:
   - Earnings dates may not always be accurate
   - BMO/AMC detection is limited (defaults to AMC)
   - Some tickers may not have earnings data
   - Dates may be estimates (`isEarningsDateEstimate`)

2. **Date Window**:
   - Only checks today and tomorrow
   - Misses earnings further out (by design - strategy requirement)

3. **No Pre-filtering**:
   - Checks every ticker in list (no pre-filter by earnings date)
   - Could be optimized by pre-fetching earnings calendar

## Optimization Opportunities

1. **Pre-fetch Earnings Calendar**:
   ```python
   # Fetch all earnings dates first
   # Filter ticker list to only those with earnings today/tomorrow
   # Then run full analysis
   ```

2. **Cache Earnings Dates**:
   - Store earnings dates in database
   - Update daily instead of checking every run

3. **Enhanced BMO/AMC Detection**:
   - Check `earningsCallTimestampStart` for time hints
   - Use multiple sources
   - Parse earnings announcement times

## Summary

**How earnings are checked**:
1. ✅ Fetch from yfinance `info` fields (`earningsTimestamp`, `earningsDate`, etc.)
2. ✅ Fallback to `calendar["Earnings Date"]` if info fails
3. ✅ Parse date (handles timestamps, strings, dates)
4. ✅ Validate: earnings date is today or tomorrow
5. ✅ Default to "AMC" if time not available
6. ✅ Reject if earnings not in window

**Key Point**: The bot only trades stocks with earnings **today (AMC)** or **tomorrow (BMO)** - this is the core strategy requirement.

**Note**: yfinance earnings dates may be estimates or future dates. The bot will only trade if the date matches today or tomorrow.
