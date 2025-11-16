"""
Advanced Strategy Optimizer - Comprehensive search for the absolute best strategy.
Tests hundreds of strategy combinations including multi-factor strategies.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Callable
import logging
from itertools import product

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class AdvancedStrategyOptimizer:
    """Advanced optimizer testing comprehensive strategy combinations."""
    
    def __init__(self, stocks: List[str], position_size: float = 10.0):
        self.stocks = stocks
        self.position_size = position_size
        self.start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        self.stock_data_cache = {}
        
    def fetch_stock_data(self, symbol: str) -> pd.DataFrame:
        """Fetch and cache historical stock data with advanced indicators."""
        if symbol not in self.stock_data_cache:
            try:
                ticker = yf.Ticker(symbol)
                data = ticker.history(start=self.start_date, end=self.end_date, interval='1d')
                if not data.empty:
                    data = data.reset_index()
                    data['Date'] = pd.to_datetime(data['Date'])
                    
                    # Basic metrics
                    data['Change'] = data['Close'].pct_change()
                    data['Change_Abs'] = abs(data['Change'])
                    
                    # Moving averages
                    for period in [3, 5, 10, 20, 50]:
                        data[f'MA{period}'] = data['Close'].rolling(window=period).mean()
                        data[f'EMA{period}'] = data['Close'].ewm(span=period, adjust=False).mean()
                    
                    # Volatility metrics
                    data['High_Low_Range'] = (data['High'] - data['Low']) / data['Close']
                    data['Volatility'] = data['Change'].rolling(window=10).std()
                    data['ATR'] = self._calculate_atr(data, 14)
                    
                    # Price position metrics
                    for period in [5, 10, 20]:
                        data[f'High_{period}'] = data['High'].rolling(window=period).max()
                        data[f'Low_{period}'] = data['Low'].rolling(window=period).min()
                        data[f'Price_Position_{period}'] = (data['Close'] - data[f'Low_{period}']) / (data[f'High_{period}'] - data[f'Low_{period}'])
                    
                    # Volume metrics
                    data['Volume_MA'] = data['Volume'].rolling(window=10).mean()
                    data['Volume_Ratio'] = data['Volume'] / data['Volume_MA']
                    
                    # RSI-like momentum
                    data['RSI'] = self._calculate_rsi(data['Close'], 14)
                    
                    # Trend strength
                    for period in [5, 10, 20]:
                        data[f'Trend_{period}'] = (data['Close'] - data[f'MA{period}']) / data[f'MA{period}']
                    
                    self.stock_data_cache[symbol] = data
            except Exception as e:
                logger.error(f"Error fetching {symbol}: {e}")
                return pd.DataFrame()
        return self.stock_data_cache.get(symbol, pd.DataFrame())
    
    def _calculate_atr(self, data: pd.DataFrame, period: int) -> pd.Series:
        """Calculate Average True Range."""
        high_low = data['High'] - data['Low']
        high_close = abs(data['High'] - data['Close'].shift())
        low_close = abs(data['Low'] - data['Close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=period).mean()
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def test_strategy(self, symbol: str, strategy_func: Callable, **params) -> Dict:
        """Test a single strategy on a stock."""
        data = self.fetch_stock_data(symbol)
        if data.empty or len(data) < 50:  # Need enough data for indicators
            return {'total_trades': 0, 'total_invested': 0, 'current_value': 0, 
                   'profit_loss': 0, 'return_pct': 0, 'max_drawdown': 0}
        
        trades = []
        total_invested = 0
        shares_owned = 0
        portfolio_value = []
        
        # Start after indicators stabilize, but not too late
        start_idx = max(20, len(data) // 20)  # Reduced from 50 to capture more trades
        for i in range(start_idx, len(data)):
            current_date = data.iloc[i]['Date']
            current_price = data.iloc[i]['Close']
            row_data = data.iloc[i]
            
            # Check if strategy says to buy
            try:
                should_buy = strategy_func(i, row_data, data, **params)
            except:
                should_buy = False
            
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
            
            # Track portfolio value
            if shares_owned > 0:
                current_value = shares_owned * current_price
                portfolio_value.append(current_value)
        
        if len(data) > 0 and total_invested > 0:
            final_price = data.iloc[-1]['Close']
            current_value = shares_owned * final_price
            profit_loss = current_value - total_invested
            return_pct = (profit_loss / total_invested * 100)
            
            # Calculate max drawdown
            max_drawdown = 0
            if len(portfolio_value) > 1:
                peak = portfolio_value[0]
                for val in portfolio_value:
                    if val > peak:
                        peak = val
                    drawdown = (peak - val) / peak if peak > 0 else 0
                    max_drawdown = max(max_drawdown, drawdown)
            
            return {
                'total_trades': len(trades),
                'total_invested': round(total_invested, 2),
                'current_value': round(current_value, 2),
                'profit_loss': round(profit_loss, 2),
                'return_pct': round(return_pct, 2),
                'max_drawdown': round(max_drawdown * 100, 2)
            }
        return {'total_trades': 0, 'total_invested': 0, 'current_value': 0, 
               'profit_loss': 0, 'return_pct': 0, 'max_drawdown': 0}
    
    def optimize_all_stocks(self) -> List[Dict]:
        """Test all strategies across all stocks."""
        strategies = self._define_comprehensive_strategies()
        results = []
        
        total_strategies = len(strategies)
        print(f"Testing {total_strategies} advanced strategies across {len(self.stocks)} stocks...")
        print("This will take several minutes. Please wait...\n")
        
        for idx, (strategy_name, strategy_func, params) in enumerate(strategies, 1):
            stock_results = []
            total_invested = 0
            total_value = 0
            total_trades = 0
            max_dd = 0
            
            for symbol in self.stocks:
                result = self.test_strategy(symbol, strategy_func, **params)
                stock_results.append(result)
                total_invested += result['total_invested']
                total_value += result['current_value']
                total_trades += result['total_trades']
                max_dd = max(max_dd, result.get('max_drawdown', 0))
            
            if total_invested > 0:
                profit_loss = total_value - total_invested
                return_pct = (profit_loss / total_invested * 100)
                
                # Calculate consistency (std dev of returns across stocks)
                stock_returns = [r['return_pct'] for r in stock_results if r['total_invested'] > 0]
                consistency = np.std(stock_returns) if len(stock_returns) > 1 else 100
                
                # Risk-adjusted return (simple Sharpe-like)
                risk_adjusted = return_pct / (max_dd + 1) if max_dd > 0 else return_pct
                
                # Composite score: balances return, consistency, and reasonable trade count
                # Penalize too few trades (< 10) and too many trades (> 200)
                trade_penalty = 1.0
                if total_trades < 10:
                    trade_penalty = 0.5  # Penalize strategies with very few trades
                elif total_trades > 200:
                    trade_penalty = 0.8  # Slight penalty for too many trades
                
                # Composite score: return * consistency_factor * trade_factor
                consistency_factor = max(0.5, 1.0 - (consistency / 50))  # Lower consistency is better
                composite_score = return_pct * consistency_factor * trade_penalty
                
                results.append({
                    'strategy': strategy_name,
                    'params': params,
                    'total_invested': round(total_invested, 2),
                    'total_value': round(total_value, 2),
                    'profit_loss': round(profit_loss, 2),
                    'return_pct': round(return_pct, 2),
                    'total_trades': total_trades,
                    'max_drawdown': round(max_dd, 2),
                    'consistency': round(consistency, 2),
                    'risk_adjusted': round(risk_adjusted, 2),
                    'composite_score': round(composite_score, 2),
                    'stock_results': stock_results
                })
            
            if idx % 20 == 0:
                print(f"  Progress: {idx}/{total_strategies} strategies tested ({idx*100//total_strategies}%)...")
        
        # Filter and sort: prioritize return percentage for strategies with reasonable trade counts
        # Keep strategies with at least 10 trades OR very high returns
        results = [r for r in results if r['total_trades'] >= 10 or r['return_pct'] > 5]
        # Sort by return percentage first (most important), then composite score, then consistency
        results.sort(key=lambda x: (-x['return_pct'], -x['composite_score'], x['consistency']))
        return results
    
    def _define_comprehensive_strategies(self) -> List[Tuple]:
        """Define comprehensive strategies including multi-factor combinations."""
        strategies = []
        
        # === SINGLE FACTOR STRATEGIES ===
        
        # Consecutive red days (various counts)
        for consecutive in [2, 3, 4, 5]:
            def consecutive_red(i, row, data, consecutive=consecutive, **kwargs):
                if i < consecutive:
                    return False
                for j in range(consecutive):
                    if data.iloc[i-j]['Close'] >= data.iloc[i-j-1]['Close']:
                        return False
                return True
            strategies.append((f"{consecutive} Consecutive Red Days", consecutive_red, {'consecutive': consecutive}))
        
        # Red day with minimum drop
        for threshold in [0.005, 0.01, 0.015, 0.02, 0.03, 0.05]:
            def red_threshold(i, row, data, threshold=threshold, **kwargs):
                prev_close = data.iloc[i-1]['Close']
                drop_pct = (prev_close - row['Close']) / prev_close
                return drop_pct >= threshold
            strategies.append((f"Red Day (>{threshold*100:.1f}% drop)", red_threshold, {'threshold': threshold}))
        
        # Drop from recent high
        for lookback in [3, 5, 7, 10, 14, 20]:
            for drop_pct in [0.02, 0.03, 0.05, 0.07, 0.10]:
                def drop_from_high(i, row, data, lookback=lookback, drop_pct=drop_pct, **kwargs):
                    if i < lookback:
                        return False
                    recent_high = data.iloc[i-lookback:i]['High'].max()
                    current_drop = (recent_high - row['Close']) / recent_high
                    return current_drop >= drop_pct
                strategies.append((f"{drop_pct*100:.0f}% Drop from {lookback}D High", drop_from_high, 
                                 {'lookback': lookback, 'drop_pct': drop_pct}))
        
        # Below moving average
        for ma_period in [5, 10, 20, 50]:
            for drop_pct in [0, 0.01, 0.02, 0.03]:
                def below_ma(i, row, data, ma_period=ma_period, drop_pct=drop_pct, **kwargs):
                    if pd.isna(row[f'MA{ma_period}']):
                        return False
                    is_red = row['Close'] < data.iloc[i-1]['Close']
                    below_ma = row['Close'] <= row[f'MA{ma_period}'] * (1 - drop_pct)
                    return is_red and below_ma
                strategies.append((f"Red Day {drop_pct*100:.0f}% Below MA{ma_period}", below_ma, 
                                 {'ma_period': ma_period, 'drop_pct': drop_pct}))
        
        # RSI oversold
        for rsi_threshold in [20, 25, 30, 35]:
            def rsi_oversold(i, row, data, rsi_threshold=rsi_threshold, **kwargs):
                if pd.isna(row['RSI']):
                    return False
                is_red = row['Close'] < data.iloc[i-1]['Close']
                oversold = row['RSI'] < rsi_threshold
                return is_red and oversold
            strategies.append((f"Red Day + RSI < {rsi_threshold}", rsi_oversold, {'rsi_threshold': rsi_threshold}))
        
        # Price position (near support)
        for period in [10, 20]:
            for position in [0.1, 0.15, 0.2, 0.25]:
                def near_support(i, row, data, period=period, position=position, **kwargs):
                    if pd.isna(row[f'Price_Position_{period}']):
                        return False
                    is_red = row['Close'] < data.iloc[i-1]['Close']
                    near_low = row[f'Price_Position_{period}'] <= position
                    return is_red and near_low
                strategies.append((f"Red Day + Price Position <{position*100:.0f}% ({period}D)", near_support,
                                 {'period': period, 'position': position}))
        
        # === MULTI-FACTOR STRATEGIES ===
        
        # Consecutive red + volume spike
        for consecutive in [2, 3]:
            for volume_mult in [1.2, 1.5, 2.0]:
                def red_vol(i, row, data, consecutive=consecutive, volume_mult=volume_mult, **kwargs):
                    if i < consecutive:
                        return False
                    # Check consecutive red
                    for j in range(consecutive):
                        if data.iloc[i-j]['Close'] >= data.iloc[i-j-1]['Close']:
                            return False
                    # Check volume
                    avg_vol = data.iloc[i-10:i]['Volume'].mean() if i >= 10 else row['Volume']
                    return row['Volume'] > avg_vol * volume_mult
                strategies.append((f"{consecutive} Red Days + {volume_mult}x Volume", red_vol,
                                 {'consecutive': consecutive, 'volume_mult': volume_mult}))
        
        # Consecutive red + drop threshold
        for consecutive in [2, 3]:
            for drop_threshold in [0.01, 0.02, 0.03]:
                def red_drop(i, row, data, consecutive=consecutive, drop_threshold=drop_threshold, **kwargs):
                    if i < consecutive:
                        return False
                    # Check consecutive red
                    for j in range(consecutive):
                        if data.iloc[i-j]['Close'] >= data.iloc[i-j-1]['Close']:
                            return False
                    # Check total drop
                    start_price = data.iloc[i-consecutive]['Close']
                    total_drop = (start_price - row['Close']) / start_price
                    return total_drop >= drop_threshold
                strategies.append((f"{consecutive} Red Days + {drop_threshold*100:.0f}% Total Drop", red_drop,
                                 {'consecutive': consecutive, 'drop_threshold': drop_threshold}))
        
        # Consecutive red + below MA
        for consecutive in [2, 3]:
            for ma_period in [5, 10, 20]:
                def red_ma(i, row, data, consecutive=consecutive, ma_period=ma_period, **kwargs):
                    if i < consecutive or pd.isna(row[f'MA{ma_period}']):
                        return False
                    # Check consecutive red
                    for j in range(consecutive):
                        if data.iloc[i-j]['Close'] >= data.iloc[i-j-1]['Close']:
                            return False
                    return row['Close'] < row[f'MA{ma_period}']
                strategies.append((f"{consecutive} Red Days + Below MA{ma_period}", red_ma,
                                 {'consecutive': consecutive, 'ma_period': ma_period}))
        
        # Drop from high + volume confirmation
        for lookback in [5, 10]:
            for drop_pct in [0.03, 0.05]:
                for volume_mult in [1.2, 1.5]:
                    def drop_vol(i, row, data, lookback=lookback, drop_pct=drop_pct, volume_mult=volume_mult, **kwargs):
                        if i < lookback:
                            return False
                        recent_high = data.iloc[i-lookback:i]['High'].max()
                        current_drop = (recent_high - row['Close']) / recent_high
                        avg_vol = data.iloc[i-10:i]['Volume'].mean() if i >= 10 else row['Volume']
                        return current_drop >= drop_pct and row['Volume'] > avg_vol * volume_mult
                    strategies.append((f"{drop_pct*100:.0f}% Drop ({lookback}D) + {volume_mult}x Vol", drop_vol,
                                     {'lookback': lookback, 'drop_pct': drop_pct, 'volume_mult': volume_mult}))
        
        # Consecutive red + RSI oversold
        for consecutive in [2, 3]:
            for rsi_threshold in [25, 30]:
                def red_rsi(i, row, data, consecutive=consecutive, rsi_threshold=rsi_threshold, **kwargs):
                    if i < consecutive or pd.isna(row['RSI']):
                        return False
                    # Check consecutive red
                    for j in range(consecutive):
                        if data.iloc[i-j]['Close'] >= data.iloc[i-j-1]['Close']:
                            return False
                    return row['RSI'] < rsi_threshold
                strategies.append((f"{consecutive} Red Days + RSI < {rsi_threshold}", red_rsi,
                                 {'consecutive': consecutive, 'rsi_threshold': rsi_threshold}))
        
        # Triple combo: Consecutive red + Below MA + Volume
        for consecutive in [2, 3]:
            for ma_period in [10, 20]:
                def triple_combo(i, row, data, consecutive=consecutive, ma_period=ma_period, **kwargs):
                    if i < consecutive or pd.isna(row[f'MA{ma_period}']):
                        return False
                    # Consecutive red
                    for j in range(consecutive):
                        if data.iloc[i-j]['Close'] >= data.iloc[i-j-1]['Close']:
                            return False
                    # Below MA
                    below_ma = row['Close'] < row[f'MA{ma_period}']
                    # Volume spike
                    avg_vol = data.iloc[i-10:i]['Volume'].mean() if i >= 10 else row['Volume']
                    vol_spike = row['Volume'] > avg_vol * 1.3
                    return below_ma and vol_spike
                strategies.append((f"{consecutive} Red + Below MA{ma_period} + Vol", triple_combo,
                                 {'consecutive': consecutive, 'ma_period': ma_period}))
        
        # Consecutive red + Price near support
        for consecutive in [2, 3]:
            for position in [0.15, 0.2]:
                def red_support(i, row, data, consecutive=consecutive, position=position, **kwargs):
                    if i < consecutive or pd.isna(row['Price_Position_20']):
                        return False
                    # Consecutive red
                    for j in range(consecutive):
                        if data.iloc[i-j]['Close'] >= data.iloc[i-j-1]['Close']:
                            return False
                    return row['Price_Position_20'] <= position
                strategies.append((f"{consecutive} Red Days + Near Support ({position*100:.0f}%)", red_support,
                                 {'consecutive': consecutive, 'position': position}))
        
        # Advanced: Mean reversion after extreme drop
        for lookback in [5, 10]:
            for extreme_drop in [0.05, 0.07, 0.10]:
                def mean_reversion(i, row, data, lookback=lookback, extreme_drop=extreme_drop, **kwargs):
                    if i < lookback:
                        return False
                    # Check if recent drop was extreme
                    start_price = data.iloc[i-lookback]['Close']
                    recent_drop = (start_price - row['Close']) / start_price
                    # Current day should be red
                    is_red = row['Close'] < data.iloc[i-1]['Close']
                    return recent_drop >= extreme_drop and is_red
                strategies.append((f"Mean Reversion: {extreme_drop*100:.0f}% Drop ({lookback}D)", mean_reversion,
                                 {'lookback': lookback, 'extreme_drop': extreme_drop}))
        
        print(f"Generated {len(strategies)} strategies to test")
        return strategies
    
    def print_top_strategies(self, results: List[Dict], top_n: int = 30):
        """Print top performing strategies with detailed metrics."""
        print("\n" + "="*120)
        print(f"TOP {top_n} STRATEGIES - RANKED BY RETURN PERCENTAGE (with consistency filter)")
        print("="*120)
        print(f"\n{'Rank':<6} {'Strategy':<50} {'Return %':<12} {'Composite':<12} {'Consistency':<12} {'Max DD %':<10} {'Trades':<8}")
        print("-"*120)
        
        for idx, result in enumerate(results[:top_n], 1):
            print(f"{idx:<6} {result['strategy']:<50} {result['return_pct']:<11.2f}% "
                  f"{result['composite_score']:<11.2f} {result['consistency']:<11.2f} "
                  f"{result['max_drawdown']:<9.2f}% {result['total_trades']:<8}")
        
        print("\n" + "="*120)
        print("🏆 ABSOLUTE BEST STRATEGY")
        print("="*120)
        best = results[0]
        print(f"\nStrategy Name: {best['strategy']}")
        print(f"Parameters: {best['params']}")
        print(f"\nPerformance Metrics:")
        print(f"  Return Percentage: {best['return_pct']:.2f}%")
        print(f"  Composite Score: {best['composite_score']:.2f}")
        print(f"  Risk-Adjusted Return: {best['risk_adjusted']:.2f}")
        print(f"  Consistency (Lower = Better): {best['consistency']:.2f}%")
        print(f"  Maximum Drawdown: {best['max_drawdown']:.2f}%")
        print(f"  Total Invested: ${best['total_invested']:.2f}")
        print(f"  Current Value: ${best['total_value']:.2f}")
        print(f"  Profit/Loss: ${best['profit_loss']:.2f}")
        print(f"  Total Trades: {best['total_trades']}")
        
        # Show breakdown by stock
        print("\n" + "-"*120)
        print("BREAKDOWN BY STOCK (Best Strategy)")
        print("-"*120)
        print(f"{'Stock':<8} {'Trades':<8} {'Invested':<12} {'Value':<12} {'P/L':<12} {'Return %':<10} {'Max DD %':<10}")
        print("-"*120)
        
        best_strategy_info = None
        strategies = self._define_comprehensive_strategies()
        for s in strategies:
            if s[0] == best['strategy']:
                best_strategy_info = s
                break
        
        if best_strategy_info:
            strategy_func = best_strategy_info[1]
            params = best['params']
            
            for symbol in self.stocks:
                result = self.test_strategy(symbol, strategy_func, **params)
                print(f"{symbol:<8} {result['total_trades']:<8} ${result['total_invested']:<11.2f} "
                      f"${result['current_value']:<11.2f} ${result['profit_loss']:<11.2f} "
                      f"{result['return_pct']:<9.2f}% {result.get('max_drawdown', 0):<9.2f}%")


def main():
    """Main function to optimize strategies."""
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    position_size = 10.0
    
    print("="*120)
    print("ADVANCED STRATEGY OPTIMIZER")
    print("Searching for the absolute best strategy with consistent returns...")
    print("="*120)
    
    optimizer = AdvancedStrategyOptimizer(stocks=stocks, position_size=position_size)
    results = optimizer.optimize_all_stocks()
    
    optimizer.print_top_strategies(results, top_n=30)
    
    # Save results
    df_results = pd.DataFrame([
        {
            'strategy': r['strategy'],
            'return_pct': r['return_pct'],
            'risk_adjusted': r['risk_adjusted'],
            'consistency': r['consistency'],
            'max_drawdown': r['max_drawdown'],
            'total_invested': r['total_invested'],
            'profit_loss': r['profit_loss'],
            'total_trades': r['total_trades']
        }
        for r in results
    ])
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"advanced_strategy_optimization_{timestamp}.csv"
    df_results.to_csv(output_file, index=False)
    print(f"\n✅ All results saved to {output_file}")


if __name__ == '__main__':
    main()

