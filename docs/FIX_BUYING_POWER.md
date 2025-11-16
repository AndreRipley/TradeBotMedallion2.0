# Fix Insufficient Buying Power Error

## Problem
Your Alpaca paper trading account doesn't have enough cash to execute trades.

Error: `insufficient buying power` or `code: 40310000`

## Solutions

### Option 1: Add Funds to Alpaca Paper Account (Recommended)

1. Go to Alpaca Dashboard: https://app.alpaca.markets/paper/dashboard/account
2. Click on "Account" or "Funding"
3. Look for "Add Funds" or "Deposit" button
4. Add funds (e.g., $10,000 - $50,000 for paper trading)
5. Funds are available immediately in paper trading

**Note:** Paper trading accounts start with $100,000 by default, but you may have used it all.

### Option 2: Reduce Position Size

If you don't want to add funds, reduce the position size:

**In Cloud Run:**
1. Go to Cloud Run console
2. Edit environment variable `POSITION_SIZE`
3. Change from `1000.0` to `500.0` or `250.0`
4. Redeploy

**In local .env file:**
```
POSITION_SIZE=500.0
```

### Option 3: Check Current Balance

The bot now logs your account balance before each trade attempt. Check logs to see:
- Current cash balance
- Buying power available
- Portfolio value

### Option 4: Wait for Positions to Close

If you have open positions, wait for them to be sold (via stop-loss, trailing stop, or sell signals). The proceeds will add to your buying power.

## How Much Capital Do You Need?

With 30 stocks and $1,000 per position:
- **Minimum:** $30,000 (one position per stock)
- **Recommended:** $50,000 - $100,000 (allows multiple positions)
- **Comfortable:** $100,000+ (allows for dynamic position sizing increases)

## Check Your Current Balance

The bot now automatically checks balance before trades and logs:
```
💰 Account Balance: $X cash, $Y buying power
```

If insufficient, you'll see:
```
⚠️  INSUFFICIENT BUYING POWER: Need $1000.00, have $500.00 available
```

## Quick Fix

**Easiest solution:** Add $50,000 to your Alpaca paper account:
1. https://app.alpaca.markets/paper/dashboard/account
2. Click "Add Funds"
3. Enter amount: $50,000
4. Submit

The bot will automatically detect the new balance on the next trade attempt.

