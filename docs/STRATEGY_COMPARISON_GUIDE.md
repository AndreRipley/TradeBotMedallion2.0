# Strategy Comparison Guide

## Overview

The `compare_strategies.py` script allows you to test new trading strategies against the current Improved Anomaly Detection Strategy using the same historical data and time period.

## How to Add Your New Strategy

### Step 1: Create Your Strategy Class

Create a class that inherits from `StrategyBase`:

```python
class YourNewStrategy(StrategyBase):
    """Your new strategy description."""
    
    def __init__(self, position_size: float = 1000.0, **your_params):
        super().__init__("Your Strategy Name", position_size)
        # Initialize your strategy parameters
        self.your_param = your_params.get('your_param', default_value)
    
    def check_signals(self, symbol: str, data: pd.DataFrame, current_idx: int) -> Dict:
        """
        Implement your trading logic here.
        
        Args:
            symbol: Stock symbol
            data: Historical price data (DataFrame with Date, Open, High, Low, Close, Volume)
            current_idx: Current index in data (0-based)
            
        Returns:
            Dict with:
            - 'action': 'BUY', 'SELL', or 'HOLD'
            - 'reason': String explaining the signal
            - Any other relevant info (severity, confidence, etc.)
        """
        # Your strategy logic here
        # Access data: data.iloc[current_idx]['Close'], etc.
        
        # Example:
        current_price = data.iloc[current_idx]['Close']
        
        # Your conditions here
        if your_buy_condition:
            return {'action': 'BUY', 'reason': 'Your buy reason'}
        elif your_sell_condition:
            return {'action': 'SELL', 'reason': 'Your sell reason'}
        else:
            return {'action': 'HOLD', 'reason': 'No signal'}
    
    def get_position_size(self, symbol: str, base_size: float) -> float:
        """Optional: Override for custom position sizing."""
        return base_size  # Or implement your sizing logic
```

### Step 2: Add to Comparison Script

In `compare_strategies.py`, add your strategy:

```python
# After line ~480, add:
your_new_strategy = YourNewStrategy(
    position_size=1000.0,
    your_param=value
)
comparator.add_strategy(your_new_strategy)
```

### Step 3: Run Comparison

```bash
python3 compare_strategies.py
```

## What Gets Compared

The comparison tests both strategies on:
- **Same stocks**: 30 stocks by default
- **Same time period**: 6 months (configurable)
- **Same position size**: $1000 per trade (configurable)

And compares:
- **Overall Return %**: Total return across all stocks
- **Win Rate %**: Percentage of profitable stocks
- **Total Trades**: Number of buy/sell trades
- **Profit/Loss**: Total dollar profit/loss
- **Per-stock performance**: Detailed breakdown

## Example: Adding a Simple Strategy

```python
class MomentumStrategy(StrategyBase):
    """Buy on strong momentum, sell on reversal."""
    
    def __init__(self, position_size: float = 1000.0, lookback: int = 5):
        super().__init__("Momentum Strategy", position_size)
        self.lookback = lookback
    
    def check_signals(self, symbol: str, data: pd.DataFrame, current_idx: int) -> Dict:
        if current_idx < self.lookback:
            return {'action': 'HOLD', 'reason': 'Insufficient data'}
        
        current_price = data.iloc[current_idx]['Close']
        past_price = data.iloc[current_idx - self.lookback]['Close']
        
        momentum_pct = ((current_price - past_price) / past_price) * 100
        
        if momentum_pct > 5:  # Strong upward momentum
            return {'action': 'BUY', 'reason': f'Momentum {momentum_pct:.2f}%'}
        elif momentum_pct < -5:  # Strong downward momentum
            return {'action': 'SELL', 'reason': f'Reversal {momentum_pct:.2f}%'}
        else:
            return {'action': 'HOLD', 'reason': 'No momentum'}
```

## Strategy Requirements

Your strategy class must:

1. **Inherit from StrategyBase**
2. **Implement `check_signals()` method** that returns a Dict with:
   - `'action'`: 'BUY', 'SELL', or 'HOLD'
   - `'reason'`: String explaining the signal
3. **Optionally override `get_position_size()`** for custom sizing

## Data Available in check_signals()

The `data` DataFrame contains:
- `Date`: Timestamp
- `Open`: Opening price
- `High`: Highest price
- `Low`: Lowest price
- `Close`: Closing price
- `Volume`: Trading volume

Access with: `data.iloc[current_idx]['Close']`, etc.

## Stop-Loss and Trailing Stop

The comparison framework automatically applies:
- **Stop-loss**: 5% below entry (if strategy has `stop_loss_pct` attribute)
- **Trailing stop**: 5% below highest price (if strategy has `trailing_stop_pct` attribute)

If your strategy doesn't define these, they default to 5%.

## Output

The script generates:
1. **Console output**: Comparison table and detailed breakdown
2. **CSV files**: 
   - `strategy_comparison_[strategy_name]_[timestamp].csv` - Per-stock results
   - `strategy_comparison_summary_[timestamp].csv` - Overall comparison

## Tips

- **Keep it simple**: Start with basic conditions, then refine
- **Use same data**: The framework ensures both strategies use identical data
- **Test thoroughly**: Run multiple time periods to verify consistency
- **Compare metrics**: Look at return %, win rate, and trade frequency

## Ready to Add Your Strategy?

Share your strategy details and I'll help you implement it in the comparison framework!



