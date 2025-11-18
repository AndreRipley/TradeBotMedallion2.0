# Automated Trade Execution

## Overview

The bot now includes **automated trade execution** based on RSI alerts. When an alert is generated, the bot automatically executes buy orders and manages positions with take-profit and max-holding exit rules.

## How It Works

### 1. Alert Generation
- Bot monitors 40 stocks every 5 minutes
- Detects RSI cross-under events (RSI < 28)
- Creates alerts in the database

### 2. Buy Order Execution
- **When**: 5 minutes after alert is generated (next 5-minute candle)
- **What**: Market buy order via Alpaca API
- **Size**: $1000 per position (configurable via `POSITION_SIZE`)
- **Checks**:
  - Sufficient buying power
  - No existing position in symbol
  - Valid price quote available

### 3. Position Management
- Tracks positions via Alpaca API
- Monitors exit conditions every update cycle (5 minutes)

### 4. Exit Conditions
- **Take Profit**: +3% gain (configurable)
- **Max Holding**: 20 calendar days (configurable)
- **Execution**: Market sell order when condition met

## Configuration

### Environment Variables

Set in Cloud Run:

```bash
# Enable/disable trading
TRADING_ENABLED=true  # Set to false to disable

# Position size per trade
POSITION_SIZE=1000.0  # Dollar amount per position

# Alpaca API credentials (already set)
ALPACA_API_KEY=your_key
ALPACA_SECRET_KEY=your_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets
```

### Alert Rules (in config.yaml)

```yaml
alert:
  take_profit_pct: 3.0  # 3% take profit
  max_holding_days: 20   # 20 calendar days
```

## Trade Flow

```
1. RSI crosses below 28
   ↓
2. Alert created (status: "pending")
   ↓
3. Wait 5 minutes (next candle)
   ↓
4. Execute buy order
   ↓
5. Alert status → "triggered"
   ↓
6. Monitor position every 5 minutes
   ↓
7. Check exit conditions:
   - Price >= entry * 1.03? → SELL (take profit)
   - Days held >= 20? → SELL (max holding)
   ↓
8. Execute sell order
   ↓
9. Alert status → "expired"
```

## Safety Features

1. **Position Check**: Won't buy if position already exists
2. **Buying Power Check**: Validates sufficient funds before buying
3. **Price Validation**: Confirms valid quote before executing
4. **Error Handling**: Logs errors, doesn't crash on failures
5. **Trading Toggle**: Can disable via `TRADING_ENABLED=false`

## Monitoring

### Logs to Watch

```
✅ BUY ORDER EXECUTED: X shares of SYMBOL at ~$PRICE ($AMOUNT total)
Order ID: xxx-xxx-xxx
💰 Updated Balance: $XXXX buying power remaining

✅ SELL ORDER EXECUTED: X shares of SYMBOL at ~$PRICE ($AMOUNT proceeds, Reason: take_profit)
Order ID: xxx-xxx-xxx
```

### Database

Check alerts table:
```sql
SELECT symbol, ts, rsi_value, price, status FROM alerts ORDER BY ts DESC;
```

- `pending`: Alert created, waiting for buy
- `triggered`: Buy executed, position open
- `expired`: Sell executed, position closed

## Current Status

✅ **Automated trading enabled**
- Buy orders: Execute 5 minutes after alert
- Sell orders: Execute when take profit or max holding reached
- Position tracking: Via Alpaca API
- Safety checks: All enabled

## Important Notes

1. **Paper Trading**: Currently using Alpaca paper trading (safe for testing)
2. **Position Size**: Default $1000 per position
3. **Market Orders**: Uses market orders (immediate execution)
4. **No Stop Loss**: Only take profit and max holding exits
5. **Single Position**: Won't buy if position already exists

## Disabling Trading

To disable automated trading without redeploying:

1. Go to Cloud Run console
2. Edit service → Variables & Secrets
3. Set `TRADING_ENABLED=false`
4. Deploy new revision

The bot will continue monitoring and generating alerts but won't execute trades.

