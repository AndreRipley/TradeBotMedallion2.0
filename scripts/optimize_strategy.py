"""
Strategy optimizer to find the best trading strategy based on return percentage.
Tests various strategies and parameters to find optimal performance.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from itertools import product

logging.basicConfig(level=logging.WARNING)  # Reduce logging noise
logger = logging.getLogger(__name__)


class StrategyOptimizer:
    """Optimizes trading strategies to find best return percentage."""
    
    def __init__(self, stocks: List[str], position_size: float = 10.0):
        """
        Initialize optimizer.
        
        Args:
            stocks: List of stock symbols to test
            position_size: Dollar amount per trade
        """
        self.stocks = stocks
        self.position_size = position_size
        self.start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        self.stock_data_cache = {}
        
    def fetch_stock_data(self, symbol: str) -> pd.DataFrame:
        """Fetch and cache historical stock data."""
        if symbol not in self.stock_data_cache:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=self.start_date, end=self.end_date, interval='1d')
                if not data.empty:
                    data = data.reset_index()
                    data['Date'] = pd.to_datetime(data['Date'])
                    # Calculate additional metrics
                    data['Change'] = data['Close'].pct_change()
                    data['MA5'] = data['Close'].rolling(window=5).mean()
                    data['MA10'] = data['Close'].rolling(window=10).mean()
                    data['MA20'] = data['Close'].rolling(window=20).mean()
                    data['High_Low_Range'] = (data['High'] - data['Low']) / data['Close']
                    self.stock_data_cache[symbol] = data
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                return pd.DataFrame()
        return self.stock_data_cache.get(symbol, pd.DataFrame())
    
    def test_strategy(self, symbol: str, strategy_func, **params) -> Dict:
        """Test a single strategy on a stock."""
        data = self.fetch_stock_data(symbol)
        if data.empty or len(data) < 2:
            return {'total_trades': 0, 'total_invested': 0, 'current_value': 0, 
                   'profit_loss': 0, 'return_pct': 0}
        
        trades = []
        total_invested = 0
        shares_owned = 0
        
        for i in range(1, len(data)):
            current_date = data.iloc[i]['Date']
            current_price = data.iloc[i]['Close']
            previous_close = data.iloc[i-1]['Close']
            row_data = data.iloc[i]
            
            # Check if strategy says to buy
            should_buy = strategy_func(i, row_data, data, **params)
            
            if should_buy:
                shares_to_buy = self.position_size / current_price
                cost = shares_to_buy * current_price
                trades.append({
                    'date': current_date,
                    'price': current_price,
                    'shares': shares_to_buy,
                    'cost': cost
                })
                shares_owned += shares_to_buy
                total_invested += cost
        
        if len(data) > 0 and total_invested > 0:
            final_price = data.iloc[-1]['Close']
            current_value = shares_owned * final_price
            profit_loss = current_value - total_invested
            return_pct = (profit_loss / total_invested * 100)
            
            return {
                'total_trades': len(trades),
                'total_invested': round(total_invested, 2),
                'current_value': round(current_value, 2),
                'profit_loss': round(profit_loss, 2),
                'return_pct': round(return_pct, 2)
            }
        return {'total_trades': 0, 'total_invested': 0, 'current_value': 0, 
               'profit_loss': 0, 'return_pct': 0}
    
    def optimize_all_stocks(self) -> List[Dict]:
        """Test all strategies across all stocks and find best."""
        strategies = self._define_strategies()
        results = []
        
        print(f"Testing {len(strategies)} strategies across {len(self.stocks)} stocks...")
        print("This may take a few moments...\n")
        
        for idx, (strategy_name, strategy_func, params) in enumerate(strategies, 1):
            total_invested = 0
            total_value = 0
            total_trades = 0
            
            for symbol in self.stocks:
                result = self.test_strategy(symbol, strategy_func, **params)
                total_invested += result['total_invested']
                total_value += result['current_value']
                total_trades += result['total_trades']
            
            if total_invested > 0:
                profit_loss = total_value - total_invested
                return_pct = (profit_loss / total_invested * 100)
                
                results.append({
                    'strategy': strategy_name,
                    'params': params,
                    'total_invested': round(total_invested, 2),
                    'total_value': round(total_value, 2),
                    'profit_loss': round(profit_loss, 2),
                    'return_pct': round(return_pct, 2),
                    'total_trades': total_trades
                })
            
            if idx % 10 == 0:
                print(f"  Tested {idx}/{len(strategies)} strategies...")
        
        # Sort by return percentage
        results.sort(key=lambda x: x['return_pct'], reverse=True)
        return results
    
    def _define_strategies(self) -> List[Tuple]:
        """Define all strategies to test."""
        strategies = []
        
        # Strategy 1: Red day (baseline)
        def red_day_strategy(i, row, data, **kwargs):
            return row['Close'] < data.iloc[i-1]['Close']
        strategies.append(("Red Day", red_day_strategy, {}))
        
        # Strategy 2: Red day with minimum drop threshold
        for threshold in [0.01, 0.02, 0.03, 0.05]:  # 1%, 2%, 3%, 5% drops
            def red_day_threshold(i, row, data, threshold=threshold, **kwargs):
                prev_close = data.iloc[i-1]['Close']
                drop_pct = (prev_close - row['Close']) / prev_close
                return drop_pct >= threshold
            strategies.append((f"Red Day (>{threshold*100:.0f}% drop)", red_day_threshold, {'threshold': threshold}))
        
        # Strategy 3: Consecutive red days
        for consecutive in [2, 3]:
            def consecutive_red(i, row, data, consecutive=consecutive, **kwargs):
                if i < consecutive:
                    return False
                for j in range(consecutive):
                    if data.iloc[i-j]['Close'] >= data.iloc[i-j-1]['Close']:
                        return False
                return True
            strategies.append((f"{consecutive} Consecutive Red Days", consecutive_red, {'consecutive': consecutive}))
        
        # Strategy 4: Red day below moving average
        for ma_period in [5, 10, 20]:
            def red_below_ma(i, row, data, ma_period=ma_period, **kwargs):
                if pd.isna(row[f'MA{ma_period}']):
                    return False
                is_red = row['Close'] < data.iloc[i-1]['Close']
                below_ma = row['Close'] < row[f'MA{ma_period}']
                return is_red and below_ma
            strategies.append((f"Red Day Below MA{ma_period}", red_below_ma, {'ma_period': ma_period}))
        
        # Strategy 5: Large drop from recent high
        for lookback in [5, 10, 20]:
            for drop_pct in [0.03, 0.05, 0.10]:
                def drop_from_high(i, row, data, lookback=lookback, drop_pct=drop_pct, **kwargs):
                    if i < lookback:
                        return False
                    recent_high = data.iloc[i-lookback:i]['High'].max()
                    current_drop = (recent_high - row['Close']) / recent_high
                    return current_drop >= drop_pct
                strategies.append((f"{drop_pct*100:.0f}% Drop from {lookback}D High", drop_from_high, 
                                 {'lookback': lookback, 'drop_pct': drop_pct}))
        
        # Strategy 6: Red day with high volatility
        def red_high_volatility(i, row, data, **kwargs):
            is_red = row['Close'] < data.iloc[i-1]['Close']
            high_vol = row['High_Low_Range'] > data['High_Low_Range'].rolling(10).mean().iloc[i]
            return is_red and high_vol
        strategies.append(("Red Day + High Volatility", red_high_volatility, {}))
        
        # Strategy 7: Red day on specific days of week (Monday, Friday)
        for day_name, day_num in [("Monday", 0), ("Friday", 4)]:
            def red_specific_day(i, row, data, day_num=day_num, **kwargs):
                is_red = row['Close'] < data.iloc[i-1]['Close']
                is_day = row['Date'].weekday() == day_num
                return is_red and is_day
            strategies.append((f"Red Day on {day_name}", red_specific_day, {'day_num': day_num}))
        
        # Strategy 8: Red day after green day (reversal)
        def red_after_green(i, row, data, **kwargs):
            if i < 2:
                return False
            prev_was_green = data.iloc[i-1]['Close'] > data.iloc[i-2]['Close']
            current_is_red = row['Close'] < data.iloc[i-1]['Close']
            return prev_was_green and current_is_red
        strategies.append(("Red Day After Green Day", red_after_green, {}))
        
        # Strategy 9: Red day with volume spike
        def red_volume_spike(i, row, data, **kwargs):
            if i < 10:
                return False
            is_red = row['Close'] < data.iloc[i-1]['Close']
            avg_volume = data.iloc[i-10:i]['Volume'].mean()
            volume_spike = row['Volume'] > avg_volume * 1.5
            return is_red and volume_spike
        strategies.append(("Red Day + Volume Spike", red_volume_spike, {}))
        
        # Strategy 10: Multiple red days in a week
        def multiple_red_week(i, row, data, **kwargs):
            if i < 5:
                return False
            week_data = data.iloc[max(0, i-5):i+1]
            red_count = sum(week_data.iloc[j]['Close'] < week_data.iloc[j-1]['Close'] 
                          for j in range(1, len(week_data)))
            return red_count >= 3 and row['Close'] < data.iloc[i-1]['Close']
        strategies.append(("Red Day in Weak Week", multiple_red_week, {}))
        
        return strategies
    
    def print_top_strategies(self, results: List[Dict], top_n: int = 20):
        """Print top performing strategies."""
        print("\n" + "="*100)
        print(f"TOP {top_n} STRATEGIES BY RETURN PERCENTAGE")
        print("="*100)
        print(f"\n{'Rank':<6} {'Strategy':<40} {'Return %':<12} {'Invested':<12} {'Profit':<12} {'Trades':<8}")
        print("-"*100)
        
        for idx, result in enumerate(results[:top_n], 1):
            print(f"{idx:<6} {result['strategy']:<40} {result['return_pct']:<11.2f}% "
                  f"${result['total_invested']:<11.2f} ${result['profit_loss']:<11.2f} "
                  f"{result['total_trades']:<8}")
        
        print("\n" + "="*100)
        print("BEST STRATEGY DETAILS")
        print("="*100)
        best = results[0]
        print(f"\nStrategy: {best['strategy']}")
        print(f"Parameters: {best['params']}")
        print(f"Return Percentage: {best['return_pct']:.2f}%")
        print(f"Total Invested: ${best['total_invested']:.2f}")
        print(f"Current Value: ${best['total_value']:.2f}")
        print(f"Profit/Loss: ${best['profit_loss']:.2f}")
        print(f"Total Trades: {best['total_trades']}")
        
        # Show breakdown by stock for best strategy
        print("\n" + "-"*100)
        print("BREAKDOWN BY STOCK (Best Strategy)")
        print("-"*100)
        print(f"{'Stock':<8} {'Trades':<8} {'Invested':<12} {'Value':<12} {'P/L':<12} {'Return %':<10}")
        print("-"*100)
        
        # Find the best strategy function
        strategies = self._define_strategies()
        best_strategy_info = next((s for s in strategies if s[0] == best['strategy']), None)
        
        if best_strategy_info:
            strategy_func = best_strategy_info[1]
            params = best['params']
            
            for symbol in self.stocks:
                result = self.test_strategy(symbol, strategy_func, **params)
                print(f"{symbol:<8} {result['total_trades']:<8} ${result['total_invested']:<11.2f} "
                      f"${result['current_value']:<11.2f} ${result['profit_loss']:<11.2f} "
                      f"{result['return_pct']:<9.2f}%")


def main():
    """Main function to optimize strategies."""
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    position_size = 10.0
    
    optimizer = StrategyOptimizer(stocks=stocks, position_size=position_size)
    results = optimizer.optimize_all_stocks()
    
    optimizer.print_top_strategies(results, top_n=20)
    
    # Save results
    df_results = pd.DataFrame(results)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"strategy_optimization_{timestamp}.csv"
    df_results.to_csv(output_file, index=False)
    print(f"\n✅ All results saved to {output_file}")


if __name__ == '__main__':
    main()

