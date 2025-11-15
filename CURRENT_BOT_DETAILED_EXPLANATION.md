# Current Live Bot: Detailed Explanation

## Overview
The live trading bot is an **automated anomaly detection system** that monitors 30 stocks and executes trades based on statistical anomalies. It runs continuously, checking every minute during market hours and executing real trades through the Alpaca API.

---

## 1. OPERATION SCHEDULE

### When It Runs
- **Frequency**: Every **1 minute** during market hours
- **Market Hours**: 9:30 AM - 4:00 PM ET (Eastern Time)
- **Days**: Monday through Friday (weekdays only)
- **Status**: Runs 24/7 (checks market hours every minute)

### What Happens Each Minute
1. **Signal Detection**: Checks all 30 stocks for trading signals
2. **Position Monitoring**: Monitors existing positions for stop-loss/trailing stop triggers
3. **Trade Execution**: Executes buy/sell orders if signals detected

---

## 2. STOCKS MONITORED

### Default Portfolio (30 Stocks)
**Technology (11 stocks)**:
- AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, ADBE, CSCO, NFLX, ACN

**Finance (3 stocks)**:
- V, JPM, MA

**Healthcare (7 stocks)**:
- UNH, JNJ, LLY, MRK, ABBV, ABT, TMO

**Consumer (4 stocks)**:
- WMT, PG, COST, MCD

**Energy (2 stocks)**:
- XOM, CVX

**Industrial (2 stocks)**:
- HD, AVGO

**Other (1 stock)**:
- PEP

**Total**: 30 diversified stocks across multiple sectors

---

## 3. SIGNAL DETECTION PROCESS

### Data Collection
- **Source**: Yahoo Finance API
- **Data Fetched**: Last 30 days of daily OHLCV data
- **Lookback Period**: 20 days (for statistical calculations)
- **Current Price**: Uses most recent closing price (yesterday's close)

### Anomaly Detection Indicators

#### 1. **Price Anomalies (Z-Score)**
- **Oversold**: Price >2 standard deviations below 20-day mean
  - Severity: `abs(z_score)`
  - Signal: **BUY**
  
- **Overbought**: Price >2 standard deviations above 20-day mean
  - Severity: `abs(z_score)`
  - Signal: **SELL**

#### 2. **Price Movement Anomalies**
- **Extreme Drop**: Daily price drop >3%
  - Severity: `abs(price_change_pct) / 3`
  - Signal: **BUY**
  
- **Extreme Rise**: Daily price rise >3%
  - Severity: `abs(price_change_pct) / 3`
  - Signal: **SELL**

#### 3. **Gap Anomalies**
- **Gap Down**: Open price >2% below previous close
  - Severity: `abs(gap_pct) / 2`
  - Signal: **BUY**
  
- **Gap Up**: Open price >2% above previous close
  - Severity: `abs(gap_pct) / 2`
  - Signal: **SELL**

#### 4. **RSI (Relative Strength Index)**
- **Oversold**: RSI <30 (14-period)
  - Severity: `(30 - rsi) / 10`
  - Signal: **BUY**
  
- **Overbought**: RSI >70 (14-period)
  - Severity: `(rsi - 70) / 10`
  - Signal: **SELL**

#### 5. **Volume Anomalies**
- **Volume Spike**: Current volume >2x 20-day average
  - Severity: `+1` (adds to total severity)
  - Signal: Enhances other signals

### Severity Calculation
- **Total Severity**: Sum of all detected anomaly severities
- **Minimum Threshold**: Severity ≥ 1.0 required to trade
- **Example**: 
  - Z-score: -2.5 → Severity: 2.5
  - Volume spike: +1 → Total: 3.5
  - **Result**: BUY signal (severity 3.5 ≥ 1.0)

### Signal Types
- **BUY**: One or more buy signals detected
- **SELL**: One or more sell signals detected
- **MIXED**: Both buy and sell signals detected (treated as BUY)
- **HOLD**: No anomaly or severity too low

---

## 4. TRADE EXECUTION

### Buy Orders

#### Process:
1. **Signal Detected**: BUY signal with severity ≥ 1.0
2. **Position Size Calculation**: Dynamic sizing based on stock performance
3. **Buying Power Check**: Verifies sufficient funds
4. **Price Fetch**: Gets current ask_price from Alpaca
5. **Shares Calculation**: `int(dollar_amount / ask_price)` (rounded down)
6. **Order Submission**: Market order via Alpaca API
7. **Position Tracking**: Adds to position tracker

#### Position Sizing (Dynamic)
**Base Size**: $1,000 per trade (configurable)

**Performance-Based Adjustment**:
- **Win Rate ≥ 60%**: $1,200 (20% increase)
- **Win Rate 50-60%**: $1,000 (normal)
- **Win Rate 40-50%**: $800 (20% decrease)
- **Win Rate < 40%**: $600 (40% decrease)

**Example**:
- Stock with 70% win rate → $1,200 position
- Stock with 30% win rate → $600 position

#### Multiple Positions
- **Can buy same stock multiple times**
- Each buy tracked as separate logical position
- Alpaca combines them into one physical position (averages entry price)
- Each logical position has independent stop-loss/trailing stop

### Sell Orders

#### Three Types of Sells:

1. **Stop-Loss Trigger**
   - **Condition**: Price drops 5% below entry price
   - **Action**: Sell entire position immediately
   - **Purpose**: Limit losses

2. **Trailing Stop Trigger**
   - **Condition**: Price drops 5% below highest price reached
   - **Action**: Sell entire position
   - **Purpose**: Lock in profits as price rises

3. **Overbought Signal**
   - **Condition**: Severity ≥ 3.0 AND have position
   - **Action**: Sell entire position
   - **Purpose**: Take profit on strong overbought signals

#### Sell Process:
1. **Signal Detected**: Stop-loss, trailing stop, or overbought
2. **Price Fetch**: Gets current bid_price from Alpaca
3. **Shares**: Sells all shares (Alpaca limitation)
4. **Order Submission**: Market order via Alpaca API
5. **Profit Calculation**: Calculates profit for each logical position
6. **Position Removal**: Removes all positions from tracker
7. **Performance Update**: Updates win/loss tracking

---

## 5. RISK MANAGEMENT

### Stop-Loss
- **Percentage**: 5% below entry price
- **Example**: Buy at $100 → Stop-loss at $95
- **Check Frequency**: Every minute
- **Trigger**: If price ≤ stop-loss price → SELL immediately

### Trailing Stop
- **Percentage**: 5% below highest price
- **Behavior**: Moves up as price rises, never moves down
- **Example**: 
  - Buy at $100 → Trailing stop at $95
  - Price rises to $120 → Trailing stop moves to $114
  - Price drops to $114 → SELL (locks in $14 profit)
- **Check Frequency**: Every minute
- **Trigger**: If price ≤ trailing stop price → SELL

### Position Limits
- **Per Stock**: Can hold multiple positions (tracked separately)
- **Total Capital**: Limited by Alpaca account buying power
- **Validation**: Checks buying power before each buy

---

## 6. POSITION TRACKING

### Data Structure
```python
positions = {
    'NVDA': [
        {
            'shares': 10.0,
            'entry_price': 100.0,
            'entry_date': datetime(...),
            'highest_price': 120.0,
            'stop_loss_price': 95.0,
            'trailing_stop_price': 114.0
        },
        {
            'shares': 5.0,
            'entry_price': 110.0,
            ...
        }
    ],
    'AAPL': [...]
}
```

### Position Management
- **Multiple Positions**: Can track multiple buys per stock
- **Independent Stops**: Each position has its own stop-loss/trailing stop
- **Alpaca Integration**: Syncs with Alpaca's actual positions
- **Profit Tracking**: Calculates profit separately for each position

---

## 7. PERFORMANCE TRACKING

### Metrics Tracked
- **Wins**: Number of profitable trades per stock
- **Losses**: Number of losing trades per stock
- **Win Rate**: `wins / (wins + losses)`

### Usage
- **Position Sizing**: Adjusts position size based on win rate
- **Learning**: Bot learns which stocks perform better
- **Adaptation**: Increases size on winners, decreases on losers

---

## 8. ORDER EXECUTION DETAILS

### Buy Orders
- **Order Type**: Market order
- **Time in Force**: DAY (expires at market close)
- **Price**: Uses `ask_price` (what you pay)
- **Shares**: Rounded down to nearest integer
- **Execution**: Immediate (market order)

### Sell Orders
- **Order Type**: Market order
- **Time in Force**: DAY (expires at market close)
- **Price**: Uses `bid_price` (what you receive)
- **Shares**: All shares in position (Alpaca limitation)
- **Execution**: Immediate (market order)

### Price Sources
- **Anomaly Detection**: Yahoo Finance (yesterday's close)
- **Position Monitoring**: Yahoo Finance (1-minute bars)
- **Trade Execution**: Alpaca API (real-time bid/ask)

---

## 9. LOGGING & MONITORING

### Log Levels
- **INFO**: Normal operations, trades executed
- **WARNING**: Stop-loss/trailing stop triggers, insufficient buying power
- **ERROR**: Failed orders, API errors

### What Gets Logged
- **BUY Signals**: Symbol, reason, severity, anomaly types, position size
- **SELL Signals**: Symbol, reason, entry price, current price, profit/loss
- **Position Monitoring**: Number of positions, stop-loss/trailing stop triggers
- **Account Balance**: Cash, buying power (before/after trades)
- **Errors**: Detailed error messages with solutions

### Log File
- **Location**: `trading_bot.log` (configurable)
- **Format**: Timestamp, logger name, level, message

---

## 10. ERROR HANDLING

### Insufficient Buying Power
- **Detection**: Checks before each buy
- **Response**: Logs warning, skips trade
- **Solutions Provided**: 
  1. Add funds to Alpaca account
  2. Reduce POSITION_SIZE
  3. Wait for existing positions to be sold

### API Errors
- **Alpaca Errors**: Logged with error codes
- **Yahoo Finance Errors**: Logged, skips that stock
- **Network Errors**: Logged, retries next minute

### Data Issues
- **Missing Data**: Skips stock if data unavailable
- **Insufficient History**: Requires 20+ days of data
- **Invalid Symbols**: Logged, skipped

---

## 11. CONFIGURATION

### Environment Variables
- **STOCKS**: Comma-separated list of stock symbols
- **ALPACA_API_KEY**: Alpaca API key
- **ALPACA_SECRET_KEY**: Alpaca secret key
- **ALPACA_BASE_URL**: Alpaca API URL (default: paper trading)
- **POSITION_SIZE**: Dollar amount per trade (default: $1,000)
- **TIMEZONE**: Timezone for market hours (default: America/New_York)
- **LOG_LEVEL**: Logging level (default: INFO)
- **LOG_FILE**: Log file path (default: trading_bot.log)

### Strategy Parameters
- **Min Severity**: 1.0 (minimum anomaly severity to trade)
- **Stop-Loss**: 5% (below entry price)
- **Trailing Stop**: 5% (below highest price)
- **Lookback Period**: 20 days (for statistical calculations)
- **RSI Period**: 14 days

---

## 12. EXAMPLE WORKFLOW

### Minute-by-Minute Example

**9:30 AM - Market Opens**
```
1. Check market hours → Yes, market is open
2. Loop through 30 stocks:
   - AAPL: No anomaly → HOLD
   - NVDA: Z-score -2.3, RSI 28 → BUY signal (severity 2.8)
   - MSFT: No anomaly → HOLD
   ...
3. Execute NVDA buy:
   - Position size: $1,000 (no history yet)
   - Ask price: $120.50
   - Shares: 8 shares ($964 invested)
   - Order submitted to Alpaca
   - Position tracked: 8 shares @ $120.50
```

**9:31 AM - One Minute Later**
```
1. Check NVDA position:
   - Current price: $121.00
   - Stop-loss: $114.48 (5% below $120.50)
   - Trailing stop: $114.48 (starts 5% below entry)
   - No triggers → Continue holding
2. Check for new signals → None
```

**10:15 AM - Price Rises**
```
1. Check NVDA position:
   - Current price: $130.00
   - Highest price: $130.00 (updated)
   - Trailing stop: $123.50 (moved up to 5% below $130)
   - No triggers → Continue holding
```

**10:16 AM - Price Drops**
```
1. Check NVDA position:
   - Current price: $123.00
   - Trailing stop: $123.50
   - Trigger: $123.00 ≤ $123.50 → SELL
2. Execute sell:
   - Bid price: $123.00
   - Shares: 8 shares
   - Profit: ($123.00 - $120.50) × 8 = $20.00
   - Order submitted to Alpaca
   - Position removed from tracker
   - Performance updated: 1 win for NVDA
```

**11:00 AM - New Signal**
```
1. NVDA drops again:
   - Z-score: -2.1, Gap down: -2.5%
   - Severity: 2.1 + 1.25 = 3.35
   - BUY signal detected
2. Execute buy:
   - Position size: $1,200 (70% win rate from previous trade)
   - Ask price: $115.00
   - Shares: 10 shares ($1,150 invested)
   - New position tracked: 10 shares @ $115.00
```

---

## 13. KEY FEATURES

### ✅ What It Does
- ✅ Monitors 30 stocks continuously
- ✅ Detects statistical anomalies (oversold/overbought)
- ✅ Executes real trades via Alpaca API
- ✅ Manages risk with stop-losses and trailing stops
- ✅ Supports multiple positions per stock
- ✅ Adjusts position sizes based on performance
- ✅ Runs 24/7 (checks every minute during market hours)
- ✅ Comprehensive logging and error handling

### ❌ What It Doesn't Do
- ❌ Trade outside market hours
- ❌ Trade on weekends/holidays
- ❌ Use limit orders (only market orders)
- ❌ Partial position sells (Alpaca limitation)
- ❌ Short selling (only long positions)
- ❌ Options or derivatives trading
- ❌ Portfolio rebalancing
- ❌ Tax optimization

---

## 14. STRATEGY PHILOSOPHY

### Mean Reversion Focus
- **Buy**: When stocks are oversold (below normal range)
- **Sell**: When stocks recover or become overbought
- **Assumption**: Prices tend to revert to mean

### Risk Management First
- **Stop-Losses**: Limit losses to 5% per trade
- **Trailing Stops**: Lock in profits as prices rise
- **Position Sizing**: Reduce size on losing stocks

### Adaptive Learning
- **Performance Tracking**: Learns which stocks perform better
- **Dynamic Sizing**: Increases size on winners, decreases on losers
- **Continuous Improvement**: Adapts to market conditions

---

## SUMMARY

The live bot is a **fully automated trading system** that:
1. **Monitors** 30 stocks every minute during market hours
2. **Detects** statistical anomalies using multiple indicators
3. **Executes** real trades through Alpaca API
4. **Manages** risk with stop-losses and trailing stops
5. **Adapts** position sizes based on performance
6. **Tracks** multiple positions per stock independently
7. **Logs** all activity for monitoring and debugging

It's designed to capture **mean reversion opportunities** while **limiting downside risk** through strict risk management rules.

