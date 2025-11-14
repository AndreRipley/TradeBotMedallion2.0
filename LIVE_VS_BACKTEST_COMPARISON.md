# Live Bot vs Backtest: Detailed Comparison

## Overview
This document compares the **live trading bot** (currently running) with the **backtest implementation** to highlight key differences in timing, execution, and behavior.

---

## 1. TIMING & FREQUENCY

### Live Bot
- **Check Frequency**: Every **1 minute** during market hours (9:30 AM - 4:00 PM ET)
- **Signal Checks**: Every minute
- **Position Monitoring**: Every minute (integrated with signal checks)
- **Runs**: Continuously, 24/7 (checks market hours every minute)
- **Execution Time**: Real-time, whenever signal detected

### Backtest
- **Check Frequency**: Once per **trading day** (daily bars)
- **Signal Checks**: Once per day (at end of day)
- **Position Monitoring**: Once per day (same time as signal checks)
- **Runs**: Processes historical data sequentially, day by day
- **Execution Time**: Simulated at ~3:45 PM (market hours) for each day

**Key Difference**: Live bot checks **390 times per day** (6.5 hours × 60 minutes), backtest checks **once per day**.

---

## 2. DATA SOURCE & PRICE DETECTION

### Live Bot
- **Data Source**: Yahoo Finance API (real-time)
- **Price Used**: 
  - **Anomaly Detection**: Last available closing price (from daily data)
  - **Position Monitoring**: Current intraday price (1-minute bars)
  - **Trade Execution**: Real-time market price via Alpaca API (ask_price for buys, bid_price for sells)
- **Data Fetch**: Fetches last 30 days of daily data for anomaly detection
- **Current Price**: Uses most recent 1-minute bar for position monitoring

### Backtest
- **Data Source**: Yahoo Finance historical data
- **Price Used**:
  - **Anomaly Detection**: Closing price of the day
  - **Trade Execution**: Simulated execution price (~3:45 PM)
    - Recent dates (<60 days): Fetches intraday 5-minute data, uses price closest to 3:45 PM
    - Historical dates (>60 days): Simulated price (Close × 0.998 if upper half, Close if lower half)
- **Data Fetch**: Fetches full historical period at once
- **Current Price**: Uses daily OHLCV data

**Key Difference**: Live bot uses **real-time prices**, backtest uses **historical closing prices** with simulated execution.

---

## 3. SIGNAL DETECTION

### Live Bot
```python
# Process:
1. Fetch last 30 days of daily data
2. Use LAST data point as "current" (most recent close)
3. Calculate 20-day lookback from previous 20 days
4. Detect anomalies using most recent close
5. Check if severity >= 1.0
6. Return BUY/SELL/HOLD signal
```

**Timing**: Uses yesterday's close (most recent available daily data)

### Backtest
```python
# Process:
1. Fetch full historical period
2. Loop through each day sequentially
3. For each day:
   - Use that day's closing price
   - Calculate 20-day lookback from previous 20 days
   - Detect anomalies using that day's close
   - Check if severity >= 1.0
   - Execute trade if conditions met
```

**Timing**: Uses each day's actual closing price as it processes historically

**Key Difference**: Live bot uses **most recent available data** (yesterday's close), backtest uses **each day's actual close** as it processes.

---

## 4. TRADE EXECUTION

### Live Bot
- **Execution Method**: Real Alpaca API orders (market orders)
- **Price**: 
  - **Buy**: Uses `ask_price` (what you pay)
  - **Sell**: Uses `bid_price` (what you receive)
- **Timing**: Executes immediately when signal detected (any time during market hours)
- **Order Type**: Market order (`TimeInForce.DAY`)
- **Shares**: Calculated as `int(dollar_amount / current_price)` (rounded down)
- **Validation**: Checks buying power before executing
- **Position Tracking**: Gets actual shares/entry price from Alpaca after execution

### Backtest
- **Execution Method**: Simulated trades
- **Price**: 
  - **Buy**: Uses simulated execution price (~3:45 PM)
  - **Sell**: Uses simulated execution price (~3:45 PM)
- **Timing**: Simulated at ~3:45 PM for each day
- **Order Type**: Assumes perfect execution at simulated price
- **Shares**: Calculated as `dollar_amount / execution_price` (exact, not rounded)
- **Validation**: No buying power checks (assumes infinite capital)
- **Position Tracking**: Tracks positions internally in code

**Key Difference**: Live bot executes **real trades** with **bid/ask spread**, backtest assumes **perfect execution** at simulated prices.

---

## 5. POSITION MANAGEMENT

### Live Bot
- **Position Tracking**: Uses `LivePositionTracker` class
- **Stop-Loss Check**: Every minute using current intraday price
- **Trailing Stop Check**: Every minute using current intraday price
- **Price Source**: 1-minute bars from Yahoo Finance
- **Update Frequency**: Every minute
- **Position Limit**: Only **1 position per stock** (won't buy if already have position)

### Backtest
- **Position Tracking**: Uses `Position` class objects in a list
- **Stop-Loss Check**: Once per day using execution price
- **Trailing Stop Check**: Once per day using execution price
- **Price Source**: Daily OHLCV data
- **Update Frequency**: Once per day
- **Position Limit**: Can hold **multiple positions per stock** (each managed independently)

**Key Difference**: Live bot allows **1 position per stock**, backtest allows **multiple positions per stock**.

---

## 6. BUY SIGNAL HANDLING

### Live Bot
```python
if signal['action'] == 'BUY':
    # Check if already have position
    if position_tracker.has_position(symbol):
        return HOLD  # Won't buy if already have position
    
    # Execute buy order
    trader.buy_stock(symbol, position_size)
    # Track position after execution
    position_tracker.add_position(symbol, shares, entry_price)
```

**Behavior**: Only buys if **no existing position**

### Backtest
```python
if signal_type in ['BUY', 'MIXED']:
    # No check for existing positions
    # Can buy multiple times for same stock
    new_position = Position(shares, entry_price, ...)
    positions.append(new_position)  # Adds to list
```

**Behavior**: Can buy **multiple times** for same stock (each position tracked separately)

**Key Difference**: Live bot prevents multiple positions, backtest allows them.

---

## 7. SELL SIGNAL HANDLING

### Live Bot
```python
# Two types of sells:

1. Stop-Loss/Trailing Stop:
   - Checks every minute
   - Uses current intraday price
   - Sells entire position

2. Overbought Signal:
   - Only if severity >= 3.0 AND have position
   - Sells entire position (not partial)
```

**Behavior**: Sells **entire position** when triggered

### Backtest
```python
# Three types of sells:

1. Stop-Loss:
   - Checks once per day
   - Uses execution price
   - Sells entire position

2. Trailing Stop:
   - Checks once per day
   - Uses execution price
   - Sells entire position

3. Overbought Signal:
   - Only if severity >= 3.0 AND have positions
   - Sells 25% of smallest position (partial sell)
```

**Behavior**: Can do **partial sells** on overbought signals

**Key Difference**: Live bot sells **entire position**, backtest can do **partial sells**.

---

## 8. POSITION SIZING

### Live Bot
- **Base Size**: $1,000 per trade (from Config.POSITION_SIZE)
- **Dynamic Sizing**: Based on stock's win rate
  - Win rate ≥ 60%: $1,200 (20% increase)
  - Win rate 50-60%: $1,000 (normal)
  - Win rate 40-50%: $800 (20% decrease)
  - Win rate < 40%: $600 (40% decrease)
- **Shares Calculation**: `int(dollar_amount / ask_price)` (rounded down)
- **Actual Investment**: May be slightly less than intended due to rounding

### Backtest
- **Base Size**: $1,000 per trade
- **Dynamic Sizing**: Same logic as live bot
- **Shares Calculation**: `dollar_amount / execution_price` (exact, not rounded)
- **Actual Investment**: Exactly matches intended amount

**Key Difference**: Live bot rounds shares down (may invest slightly less), backtest uses exact calculations.

---

## 9. RISK MANAGEMENT

### Live Bot
- **Stop-Loss**: 5% below entry price
- **Trailing Stop**: 5% below highest price
- **Check Frequency**: Every minute
- **Price Used**: Current intraday price (1-minute bars)
- **Execution**: Real market order at current price

### Backtest
- **Stop-Loss**: 5% below entry price
- **Trailing Stop**: 5% below highest price
- **Check Frequency**: Once per day
- **Price Used**: Simulated execution price (~3:45 PM)
- **Execution**: Simulated at execution price

**Key Difference**: Live bot checks **every minute** with **real prices**, backtest checks **once per day** with **simulated prices**.

---

## 10. CAPITAL CONSTRAINTS

### Live Bot
- **Buying Power Check**: Yes, checks before every buy
- **Error Handling**: Logs warning if insufficient buying power
- **Reality**: Limited by actual account balance
- **Multiple Positions**: Limited by total buying power

### Backtest
- **Buying Power Check**: No (assumes infinite capital)
- **Error Handling**: None needed
- **Reality**: Unlimited capital assumption
- **Multiple Positions**: No limit

**Key Difference**: Live bot is **capital constrained**, backtest has **unlimited capital**.

---

## 11. ORDER EXECUTION REALITY

### Live Bot
- **Slippage**: Real slippage (bid/ask spread)
- **Execution Delay**: Network latency + order processing time
- **Fill Price**: May differ from expected price
- **Partial Fills**: Possible (though rare with market orders)
- **Order Rejection**: Possible (insufficient buying power, market closed, etc.)

### Backtest
- **Slippage**: Simulated (0.2% for upper half of range)
- **Execution Delay**: None (instant)
- **Fill Price**: Exact simulated price
- **Partial Fills**: Not simulated
- **Order Rejection**: Not simulated

**Key Difference**: Live bot faces **real execution challenges**, backtest assumes **perfect execution**.

---

## 12. DATA FRESHNESS

### Live Bot
- **Anomaly Detection**: Uses yesterday's close (most recent daily data)
- **Position Monitoring**: Uses current 1-minute bar (real-time)
- **Data Lag**: ~1 day for anomaly detection, real-time for monitoring

### Backtest
- **Anomaly Detection**: Uses each day's actual close
- **Position Monitoring**: Uses each day's execution price
- **Data Lag**: None (historical data is complete)

**Key Difference**: Live bot uses **slightly stale data** for signals, backtest uses **complete historical data**.

---

## SUMMARY TABLE

| Aspect | Live Bot | Backtest |
|--------|----------|----------|
| **Check Frequency** | Every 1 minute | Once per day |
| **Signal Detection** | Yesterday's close | Each day's actual close |
| **Execution Price** | Real bid/ask | Simulated ~3:45 PM |
| **Position Limit** | 1 per stock | Multiple per stock |
| **Sell Behavior** | Entire position | Can be partial |
| **Capital** | Limited | Unlimited |
| **Slippage** | Real bid/ask spread | Simulated 0.2% |
| **Order Execution** | Real API calls | Simulated |
| **Position Monitoring** | Every minute | Once per day |
| **Data Freshness** | ~1 day lag | Complete historical |

---

## KEY IMPLICATIONS

### Why Backtest Returns May Differ from Live Trading:

1. **Timing**: Backtest checks once per day, live bot checks every minute
   - Live bot may catch signals earlier or miss them entirely
   
2. **Execution Price**: Backtest uses simulated prices, live bot uses real bid/ask
   - Live bot pays more (ask) and receives less (bid) than backtest assumes
   
3. **Position Limits**: Live bot only allows 1 position per stock
   - Backtest can accumulate multiple positions, amplifying returns
   
4. **Capital Constraints**: Live bot limited by buying power
   - Backtest can take unlimited positions
   
5. **Slippage**: Live bot faces real slippage
   - Backtest assumes near-perfect execution
   
6. **Data Lag**: Live bot uses yesterday's close for signals
   - May miss intraday opportunities that backtest catches

### Expected Differences:

- **Live bot returns** may be **lower** than backtest due to:
  - Bid/ask spread costs
  - Real slippage
  - Capital constraints
  - Single position limit
  - Data lag

- **Live bot returns** may be **higher** than backtest due to:
  - More frequent checks (may catch opportunities earlier)
  - Real-time position monitoring (faster stop-loss execution)

---

## CONCLUSION

The backtest provides a **theoretical upper bound** of what the strategy could achieve with perfect execution and unlimited capital. The live bot operates with **real-world constraints** including bid/ask spreads, capital limits, and execution delays.

**Expected Performance Gap**: Live bot returns are likely to be **10-30% lower** than backtest returns due to execution costs and constraints, though the strategy logic remains the same.

