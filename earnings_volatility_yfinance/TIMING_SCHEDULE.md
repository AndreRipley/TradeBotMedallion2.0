# Earnings Volatility Bot - Timing Schedule

## Overview

The bot operates during specific time windows to execute the earnings volatility strategy. All times are in **Eastern Time (ET)**.

---

## Market Hours

- **Market Open**: 9:30 AM ET
- **Market Close**: 4:00 PM ET
- **Trading Days**: Monday - Friday (closed on weekends and holidays)

---

## Entry Window: Open New Positions

**Time**: **3:45 PM - 4:00 PM ET** (15 minutes before market close)

**What Happens**:
1. ✅ Bot scans for stocks with earnings:
   - **Today (AMC)** - After Market Close today
   - **Tomorrow (BMO)** - Before Market Open tomorrow
2. ✅ Applies filters:
   - Volume check (30-day avg > 1.5M)
   - IV Term Structure Slope (Front Month IV > Back Month IV by >0.05)
   - IV/RV Ratio (IV/RV > 1.2)
3. ✅ Executes **Long Calendar Spreads** for qualifying signals
4. ✅ Logs all signals (both passed and rejected) to database

**Strategy Rationale**: 
- Enter positions just before market close
- Capture high IV before earnings announcement
- Minimize time decay exposure

---

## Exit Window: Close Positions

**Time**: **9:45 AM - 10:00 AM ET** (15 minutes after market open next trading day)

**What Happens**:
1. ✅ Bot identifies positions opened the previous day
2. ✅ Closes calendar spreads to capture IV crush
3. ✅ Calculates P&L and updates database

**Strategy Rationale**:
- Exit shortly after market open
- Capture IV crush from earnings announcement
- Avoid prolonged exposure to time decay

---

## Outside Trading Windows

**When**: All other times during market hours (9:30 AM - 3:45 PM ET, 10:00 AM - 4:00 PM ET)

**What Happens**:
- ⏸️ Bot waits and does NOT execute trades
- 📊 Can still scan and log signals for monitoring (if manually triggered)
- ⏰ Shows countdown to next entry/exit window

---

## Daily Schedule Example

### Monday
- **9:45 AM - 10:00 AM ET**: Exit positions from Friday
- **3:45 PM - 4:00 PM ET**: Enter new positions (for Monday AMC or Tuesday BMO earnings)

### Tuesday
- **9:45 AM - 10:00 AM ET**: Exit positions from Monday
- **3:45 PM - 4:00 PM ET**: Enter new positions (for Tuesday AMC or Wednesday BMO earnings)

### Wednesday
- **9:45 AM - 10:00 AM ET**: Exit positions from Tuesday
- **3:45 PM - 4:00 PM ET**: Enter new positions (for Wednesday AMC or Thursday BMO earnings)

### Thursday
- **9:45 AM - 10:00 AM ET**: Exit positions from Wednesday
- **3:45 PM - 4:00 PM ET**: Enter new positions (for Thursday AMC or Friday BMO earnings)

### Friday
- **9:45 AM - 10:00 AM ET**: Exit positions from Thursday
- **3:45 PM - 4:00 PM ET**: Enter new positions (for Friday AMC or Monday BMO earnings)

---

## Configuration

Timing can be adjusted via environment variables in `.env`:

```bash
# Entry timing (minutes before market close)
ENTRY_MINUTES_BEFORE_CLOSE=15

# Exit timing (minutes after market open)
EXIT_MINUTES_AFTER_OPEN=15
```

---

## Current Status Check

To see current timing status, run:

```bash
python3 -m earnings_volatility_yfinance.main_calendar
```

The bot will show:
- Current time
- Whether it's in entry/exit window
- Time until next window
- Market status (open/closed)

---

## Important Notes

1. **Weekend Handling**: Bot skips weekends automatically
2. **Holiday Handling**: Bot checks if market is open before executing
3. **Timezone**: All times are Eastern Time (ET) - automatically handles EST/EDT
4. **Precision**: Entry/exit windows are exact (not approximate)
5. **Multiple Runs**: Bot can be run multiple times during windows - it will check if trades already executed

---

## Example Output

```
================================================================================
Earnings Volatility Trading Bot (yfinance + Calendar API) - Starting Scan
================================================================================
Current time: 2025-11-19 15:45:00 EST
Ticker list: AAPL, TSLA, AMD, NVDA, META
Using calendar API: True
✓ In ENTRY window: 15:45:00 - 16:00:00 ET
Scanning for earnings and executing new positions...
Using earnings calendar API for efficient scanning...
Found 3 total earnings from calendar API
Filtered to 1 earnings in watchlist
Analyzing NVDA (earnings: 2025-11-19 AMC)
✓ NVDA passed all filters: Slope=0.0823, IV/RV=1.45, Vol=2,450,000
Found 1 valid signals after filtering
Executing 1 trades (slots available: 5)
✓ Executed NVDA: Order sim-back-NVDA-..., Entry $7.50, Qty 1
Execution complete: 1/1 trades successful
================================================================================
Scan Complete
================================================================================
```

