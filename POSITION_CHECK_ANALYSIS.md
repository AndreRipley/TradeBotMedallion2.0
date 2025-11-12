# Analysis: Position Check Frequency

## Current Setup
- **Signal Checks**: Every 1 minute (for new opportunities)
- **Position Monitoring**: Every 5 minutes (for stop-loss/trailing stop)

## The Problem

### Risk Management Gap
With 5% stop-loss and trailing stop:
- **5 minutes is too long** for risk management
- Stocks can drop 5%+ in **seconds** during volatility
- A $100 stock could drop to $90 before you check (10% loss vs 5% target)

### Real-World Scenario
```
10:00 AM - Buy META at $600 (stop-loss at $570)
10:01 AM - Price drops to $580 (no check yet)
10:02 AM - Price drops to $560 (no check yet)
10:03 AM - Price drops to $550 (no check yet)
10:04 AM - Price drops to $540 (no check yet)
10:05 AM - FINALLY checks, sells at $540 (10% loss instead of 5%)
```

## Why This Matters

### Stop-Loss Purpose
- **Limit losses** to 5%
- **Protect capital** from rapid declines
- **Risk management** is critical

### Current Gap
- Checking every 5 minutes means you could lose **more than intended**
- In volatile markets, 5 minutes = significant price movement
- Defeats the purpose of stop-loss protection

## Recommended Solution

### Option 1: Check Positions Every Minute (Best)
Since you're already checking signals every minute, **also check positions**:
- No extra API calls (already fetching price data)
- Better risk management
- Catches stop-loss triggers faster

### Option 2: Check Positions Every 2 Minutes (Compromise)
- Balance between risk and API calls
- Still much better than 5 minutes
- Reasonable for most scenarios

### Option 3: Check Positions Every 30 Seconds (Aggressive)
- Maximum protection
- More API calls
- May be overkill for most stocks

## Recommendation

**Check positions every 1 minute** because:
1. ✅ Already checking signals every minute
2. ✅ Can combine checks (no extra overhead)
3. ✅ Better risk management
4. ✅ Catches stop-loss triggers quickly
5. ✅ Minimal additional cost

## Implementation

The bot should check positions **during the same loop** that checks signals, since it's already fetching price data for each stock.

