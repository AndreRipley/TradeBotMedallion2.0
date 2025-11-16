# Troubleshooting: Why Only 1 Trade?

## Possible Reasons for Low Trade Frequency

### 1. Strategy Selectivity (Most Likely)
The bot is designed to be selective:
- **Minimum Severity: 1.0** - Only trades significant anomalies
- **Anomaly Detection**: Requires statistical deviations (Z-score, RSI, price drops, etc.)
- **Not every minute**: Anomalies don't occur every minute

**This is NORMAL** - The strategy is designed to wait for good opportunities, not trade constantly.

### 2. Market Conditions
- If markets are stable (no big moves), fewer anomalies occur
- The bot waits for oversold conditions (price drops, RSI < 30, etc.)
- During trending markets, anomalies may be less frequent

### 3. Already Holding Positions
- Bot won't buy if already holding a stock
- If you have 1 position, it won't buy that stock again until sold

### 4. Insufficient Buying Power
- Check if you have enough cash for more trades
- Bot checks balance before each trade

### 5. Market Hours
- Bot only trades during market hours (9:30 AM - 4:00 PM ET, weekdays)
- No trades outside market hours

## How to Verify Bot is Working

### Check 1: Is Bot Running?
```bash
bash check_cloud_bot.sh
```

### Check 2: View Recent Logs
```bash
bash view_logs.sh
```

Look for:
- ✅ "Checking for anomalies every minute during market hours"
- ✅ "BUY SIGNAL detected" (when anomalies found)
- ✅ "HOLD" messages (normal - means no anomaly detected)
- ⚠️ "INSUFFICIENT BUYING POWER" (if cash issue)

### Check 3: Check Signal Detection
Look for logs showing:
- "Checking for anomalies..." (happens every minute)
- "No anomaly detected" or "Severity X below threshold" (normal)
- "BUY SIGNAL detected" (when trade happens)

## Expected Trade Frequency

**Normal behavior:**
- **0-5 trades per day** is normal for this strategy
- Strategy is selective by design
- More trades ≠ better returns
- Quality over quantity

**If you want more trades:**
1. Lower `min_severity` (currently 1.0)
2. Reduce anomaly detection thresholds
3. But this may reduce win rate

## What to Check in Logs

### Good Signs (Bot Working):
```
✅ Starting trading bot scheduler
✅ Monitoring stocks: AAPL, MSFT, GOOGL, ...
✅ Checking for anomalies every minute during market hours
✅ 🔍 Monitoring X positions for stop-loss/trailing stop...
```

### Potential Issues:
```
❌ INSUFFICIENT BUYING POWER
❌ Error fetching data for SYMBOL
❌ No quote data available
❌ Already have position (won't buy again)
```

## How to Increase Trade Frequency

### Option 1: Lower Severity Threshold
Edit `scheduler.py`:
```python
self.strategy = LiveAnomalyStrategy(
    min_severity=0.5,  # Lower from 1.0 to 0.5
    stop_loss_pct=0.05,
    trailing_stop_pct=0.05
)
```

### Option 2: Check Current Settings
The bot currently uses:
- `min_severity=1.0` (only trades significant anomalies)
- `stop_loss_pct=0.05` (5% stop-loss)
- `trailing_stop_pct=0.05` (5% trailing stop)

### Option 3: Verify Anomaly Detection
The bot checks for:
- Z-score < -2.0 (price 2+ std devs below mean)
- Price drop > 3%
- Gap down > 2%
- RSI < 30 (oversold)

These conditions don't occur every minute - they're relatively rare.

## Conclusion

**1 trade so far is likely NORMAL** if:
- ✅ Bot is running and checking every minute
- ✅ No errors in logs
- ✅ Markets are relatively stable
- ✅ You have buying power available

The strategy is designed to be selective. More trades will occur when:
- Markets become more volatile
- Anomalies are detected
- Existing positions are sold (freeing up capital)

## Next Steps

1. Check logs to confirm bot is checking signals: `bash view_logs.sh`
2. Verify no errors preventing trades
3. Check buying power is sufficient
4. Wait for more market volatility (more anomalies = more trades)

The bot is likely working correctly - it's just waiting for good opportunities!

