"""
Strategy Comparison Framework
Compares multiple trading strategies side-by-side using the same data and time period.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from live_anomaly_strategy import LiveAnomalyDetector, LivePositionTracker
from mean_reversion_strategy import MeanReversionStrategy

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class StrategyBase:
    """Base class for all trading strategies."""
    
    def __init__(self, name: str, position_size: float = 1000.0):
        self.name = name
        self.position_size = position_size
    
    def check_signals(self, symbol: str, data: pd.DataFrame, current_idx: int) -> Dict:
        """
        Check for trading signals.
        
        Args:
            symbol: Stock symbol
            data: Historical price data
            current_idx: Current index in data
            
        Returns:
            Dict with 'action' ('BUY', 'SELL', 'HOLD'), 'reason', etc.
        """
        raise NotImplementedError("Subclasses must implement check_signals")
    
    def get_position_size(self, symbol: str, base_size: float) -> float:
        """Get position size for a trade (can be overridden for dynamic sizing)."""
        return base_size


class CurrentAnomalyStrategy(StrategyBase):
    """Current Improved Anomaly Detection Strategy."""
    
    def __init__(self, position_size: float = 1000.0, min_severity: float = 1.0,
                 stop_loss_pct: float = 0.05, trailing_stop_pct: float = 0.05):
        super().__init__("Current Anomaly Strategy", position_size)
        self.min_severity = min_severity
        self.detector = LiveAnomalyDetector()
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop_pct = trailing_stop_pct
        self.stock_performance = {}  # For dynamic position sizing
    
    def get_position_size(self, symbol: str, base_size: float) -> float:
        """Get dynamic position size based on performance."""
        if symbol not in self.stock_performance:
            return base_size
        
        perf = self.stock_performance.get(symbol, {})
        wins = perf.get('wins', 0)
        losses = perf.get('losses', 0)
        total = wins + losses
        
        if total == 0:
            return base_size
        
        win_rate = wins / total
        
        if win_rate >= 0.6:
            return base_size * 1.2
        elif win_rate >= 0.5:
            return base_size
        elif win_rate >= 0.4:
            return base_size * 0.8
        else:
            return base_size * 0.6
    
    def check_signals(self, symbol: str, data: pd.DataFrame, current_idx: int) -> Dict:
        """Check signals using current anomaly detection."""
        # This is a simplified version for backtesting
        # In live trading, it uses LiveAnomalyDetector
        
        if len(data) < current_idx + 1 or current_idx < 20:
            return {'action': 'HOLD', 'reason': 'Insufficient data'}
        
        # Calculate indicators (simplified)
        historical = data.iloc[max(0, current_idx-20):current_idx]
        current = data.iloc[current_idx]
        
        mean_price = historical['Close'].mean()
        std_price = historical['Close'].std()
        current_price = current['Close']
        
        # Z-score
        z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
        
        # Price change
        if current_idx > 0:
            price_change_pct = ((current['Close'] - data.iloc[current_idx - 1]['Close']) / 
                              data.iloc[current_idx - 1]['Close']) * 100
        else:
            price_change_pct = 0
        
        # RSI (simplified)
        prices = data['Close'].iloc[:current_idx + 1]
        if len(prices) >= 14:
            delta = prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1] if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]) else 50
        else:
            current_rsi = 50
        
        # Gap
        if current_idx > 0:
            gap_pct = ((current['Open'] - data.iloc[current_idx - 1]['Close']) / 
                      data.iloc[current_idx - 1]['Close']) * 100
        else:
            gap_pct = 0
        
        # Calculate severity
        anomalies = []
        severity = 0
        
        # Buy signals
        if z_score < -2.0:
            anomalies.append('oversold')
            severity += abs(z_score)
        if price_change_pct < -3.0:
            anomalies.append('extreme_drop')
            severity += abs(price_change_pct) / 3
        if gap_pct < -2.0:
            anomalies.append('gap_down')
            severity += abs(gap_pct) / 2
        if current_rsi < 30:
            anomalies.append('rsi_oversold')
            severity += (30 - current_rsi) / 10
        
        # Sell signals
        if z_score > 2.0:
            anomalies.append('overbought')
            severity += abs(z_score)
        if price_change_pct > 3.0:
            anomalies.append('extreme_rise')
            severity += abs(price_change_pct) / 3
        if gap_pct > 2.0:
            anomalies.append('gap_up')
            severity += abs(gap_pct) / 2
        if current_rsi > 70:
            anomalies.append('rsi_overbought')
            severity += (current_rsi - 70) / 10
        
        # Determine signal type
        buy_signals = ['oversold', 'extreme_drop', 'gap_down', 'rsi_oversold']
        sell_signals = ['overbought', 'extreme_rise', 'gap_up', 'rsi_overbought']
        
        signal_type = None
        if any(signal in anomalies for signal in buy_signals):
            signal_type = 'BUY'
        if any(signal in anomalies for signal in sell_signals):
            if signal_type == 'BUY':
                signal_type = 'MIXED'
            else:
                signal_type = 'SELL'
        
        if not anomalies or severity < self.min_severity:
            return {'action': 'HOLD', 'reason': f'No anomaly or severity {severity:.2f} < {self.min_severity}'}
        
        if signal_type in ['BUY', 'MIXED']:
            return {
                'action': 'BUY',
                'reason': ', '.join(anomalies),
                'severity': severity,
                'anomaly_types': anomalies
            }
        elif signal_type == 'SELL':
            return {
                'action': 'SELL',
                'reason': ', '.join(anomalies),
                'severity': severity
            }
        
        return {'action': 'HOLD', 'reason': 'No clear signal'}


class StrategyComparator:
    """Compare multiple trading strategies."""
    
    def __init__(self, stocks: List[str], start_date: str, end_date: str, position_size: float = 1000.0):
        self.stocks = stocks
        self.start_date = start_date
        self.end_date = end_date
        self.position_size = position_size
        self.strategies = []
    
    def add_strategy(self, strategy: StrategyBase):
        """Add a strategy to compare."""
        self.strategies.append(strategy)
    
    def fetch_stock_data(self, symbol: str) -> pd.DataFrame:
        """Fetch historical stock data."""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=self.start_date, end=self.end_date, interval='1d')
            if data.empty:
                return pd.DataFrame()
            data = data.reset_index()
            data['Date'] = pd.to_datetime(data['Date'])
            return data
        except Exception as e:
            logger.warning(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def backtest_strategy(self, strategy: StrategyBase, symbol: str) -> Dict:
        """Backtest a single strategy on a single stock."""
        data = self.fetch_stock_data(symbol)
        if data.empty or len(data) < 20:
            return {
                'symbol': symbol,
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'total_invested': 0,
                'total_value': 0,
                'profit_loss': 0,
                'return_pct': 0
            }
        
        # Reset strategy positions for this stock (if MeanReversionStrategy)
        if hasattr(strategy, 'positions'):
            strategy.positions = {}
        
        trades = []
        total_invested = 0
        shares_owned = 0
        total_sold_value = 0
        
        # Check if this is MeanReversionStrategy (has complex exit logic)
        is_mean_reversion = hasattr(strategy, 'check_exit_conditions') and hasattr(strategy, 'calculate_indicators')
        
        # Track positions
        positions = {}  # symbol -> position info
        
        for i in range(20, len(data)):  # Start at 20 for indicators
            current_price = data.iloc[i]['Close']
            current_date = data.iloc[i]['Date']
            
            # Check for signals
            signal = strategy.check_signals(symbol, data, i)
            
            # Handle MeanReversionStrategy exits (complex logic)
            if is_mean_reversion and symbol in strategy.positions:
                position = strategy.positions[symbol]
                indicators = strategy.calculate_indicators(data, i)
                if indicators:
                    should_exit, reason, exit_pct = strategy.check_exit_conditions(symbol, indicators, position)
                    if should_exit:
                        shares_to_sell = shares_owned * exit_pct
                        sell_value = shares_to_sell * current_price
                        total_sold_value += sell_value
                        shares_owned -= shares_to_sell
                        
                        trades.append({
                            'date': current_date,
                            'type': 'SELL',
                            'reason': reason,
                            'price': current_price,
                            'shares': shares_to_sell,
                            'value': sell_value
                        })
                        
                        # Update position or remove if fully exited
                        if exit_pct >= 1.0:
                            del strategy.positions[symbol]
                            if symbol in positions:
                                del positions[symbol]
                        else:
                            position['shares'] = shares_owned
                            position['highest_price'] = max(position.get('highest_price', position['entry_price']), current_price)
                            if symbol in positions:
                                positions[symbol]['shares'] = shares_owned
                        continue
            
            # Standard position management for other strategies
            if not is_mean_reversion and symbol in positions:
                pos = positions[symbol]
                # Update trailing stop
                if hasattr(strategy, 'trailing_stop_pct') and current_price > pos['highest_price']:
                    pos['highest_price'] = current_price
                    pos['trailing_stop'] = current_price * (1 - strategy.trailing_stop_pct)
                
                # Check stop-loss
                if hasattr(strategy, 'stop_loss_pct') and current_price <= pos['stop_loss']:
                    sell_value = shares_owned * current_price
                    total_sold_value += sell_value
                    trades.append({
                        'date': current_date,
                        'type': 'SELL',
                        'reason': 'STOP_LOSS',
                        'price': current_price,
                        'shares': shares_owned,
                        'value': sell_value
                    })
                    shares_owned = 0
                    del positions[symbol]
                    continue
                
                # Check trailing stop
                if hasattr(strategy, 'trailing_stop_pct') and current_price <= pos['trailing_stop']:
                    sell_value = shares_owned * current_price
                    total_sold_value += sell_value
                    trades.append({
                        'date': current_date,
                        'type': 'SELL',
                        'reason': 'TRAILING_STOP',
                        'price': current_price,
                        'shares': shares_owned,
                        'value': sell_value
                    })
                    shares_owned = 0
                    del positions[symbol]
                    continue
            
            # Handle buy signals
            if signal['action'] == 'BUY' and symbol not in positions and (not is_mean_reversion or symbol not in strategy.positions):
                # MeanReversionStrategy calculates shares in signal
                if is_mean_reversion and 'shares' in signal:
                    shares_to_buy = signal['shares']
                    cost = shares_to_buy * current_price
                    
                    # Track position in strategy
                    strategy.positions[symbol] = {
                        'shares': shares_to_buy,
                        'entry_price': signal.get('entry_price', current_price),
                        'entry_date': current_date,
                        'atr_at_entry': signal.get('atr', current_price * 0.02),
                        'highest_price': current_price,
                        'tp1_hit': False
                    }
                    positions[symbol] = {'shares': shares_to_buy}
                else:
                    # Standard position sizing
                    position_size = strategy.get_position_size(symbol, self.position_size)
                    shares_to_buy = position_size / current_price
                    cost = shares_to_buy * current_price
                    
                    # Add position
                    positions[symbol] = {
                        'shares': shares_to_buy,
                        'entry_price': current_price,
                        'highest_price': current_price,
                        'stop_loss': current_price * (1 - getattr(strategy, 'stop_loss_pct', 0.05)),
                        'trailing_stop': current_price * (1 - getattr(strategy, 'trailing_stop_pct', 0.05))
                    }
                
                trades.append({
                    'date': current_date,
                    'type': 'BUY',
                    'reason': signal.get('reason', 'Signal'),
                    'price': current_price,
                    'shares': shares_to_buy,
                    'cost': cost,
                    'severity': signal.get('severity', 0)
                })
                
                shares_owned += shares_to_buy
                total_invested += cost
            
            # Handle sell signals (for non-MeanReversion strategies)
            elif not is_mean_reversion and signal['action'] == 'SELL' and symbol in positions:
                if signal.get('severity', 0) >= 3.0:  # Strong overbought
                    sell_value = shares_owned * current_price
                    total_sold_value += sell_value
                    trades.append({
                        'date': current_date,
                        'type': 'SELL',
                        'reason': signal.get('reason', 'OVERBOUGHT'),
                        'price': current_price,
                        'shares': shares_owned,
                        'value': sell_value
                    })
                    shares_owned = 0
                    del positions[symbol]
        
        # Calculate final value
        final_price = data.iloc[-1]['Close'] if len(data) > 0 else 0
        current_value = shares_owned * final_price
        total_value = total_sold_value + current_value
        
        profit_loss = total_value - total_invested
        return_pct = (profit_loss / total_invested * 100) if total_invested > 0 else 0
        
        buy_trades = len([t for t in trades if t['type'] == 'BUY'])
        sell_trades = len([t for t in trades if t['type'] == 'SELL'])
        
        return {
            'symbol': symbol,
            'total_trades': len(trades),
            'buy_trades': buy_trades,
            'sell_trades': sell_trades,
            'total_invested': round(total_invested, 2),
            'total_value': round(total_value, 2),
            'current_value': round(current_value, 2),
            'total_sold_value': round(total_sold_value, 2),
            'profit_loss': round(profit_loss, 2),
            'return_pct': round(return_pct, 2),
            'trades': trades
        }
    
    def compare_strategies(self) -> Dict:
        """Compare all strategies."""
        results = {}
        
        for strategy in self.strategies:
            print(f"\n{'='*80}")
            print(f"Backtesting: {strategy.name}")
            print(f"{'='*80}")
            
            strategy_results = {}
            total_invested = 0
            total_value = 0
            total_trades = 0
            total_buy_trades = 0
            total_sell_trades = 0
            
            for symbol in self.stocks:
                print(f"Testing {symbol}...", end=' ', flush=True)
                result = self.backtest_strategy(strategy, symbol)
                strategy_results[symbol] = result
                
                total_invested += result['total_invested']
                total_value += result['total_value']
                total_trades += result['total_trades']
                total_buy_trades += result['buy_trades']
                total_sell_trades += result['sell_trades']
                
                if result['total_trades'] > 0:
                    print(f"✅ {result['return_pct']:.2f}% return")
                else:
                    print("⏭️  No trades")
            
            total_profit_loss = total_value - total_invested
            overall_return = (total_profit_loss / total_invested * 100) if total_invested > 0 else 0
            
            # Calculate win rate
            profitable_stocks = [r for r in strategy_results.values() if r['profit_loss'] > 0]
            win_rate = (len(profitable_stocks) / len(self.stocks) * 100) if self.stocks else 0
            
            results[strategy.name] = {
                'stocks': strategy_results,
                'summary': {
                    'total_stocks': len(self.stocks),
                    'total_trades': total_trades,
                    'buy_trades': total_buy_trades,
                    'sell_trades': total_sell_trades,
                    'total_invested': round(total_invested, 2),
                    'total_value': round(total_value, 2),
                    'total_profit_loss': round(total_profit_loss, 2),
                    'overall_return_pct': round(overall_return, 2),
                    'win_rate': round(win_rate, 2),
                    'profitable_stocks': len(profitable_stocks)
                }
            }
        
        return results
    
    def print_comparison(self, results: Dict):
        """Print comparison table."""
        print("\n" + "="*100)
        print("STRATEGY COMPARISON RESULTS")
        print("="*100)
        
        print(f"\n{'Strategy':<30} {'Return %':<12} {'Win Rate %':<12} {'Trades':<10} {'Buy':<8} {'Sell':<8} {'Profit':<15} {'Profitable':<12}")
        print("-"*100)
        
        for strategy_name, data in results.items():
            summary = data['summary']
            print(f"{strategy_name:<30} "
                  f"{summary['overall_return_pct']:<11.2f}% "
                  f"{summary['win_rate']:<11.1f}% "
                  f"{summary['total_trades']:<10} "
                  f"{summary['buy_trades']:<8} "
                  f"{summary['sell_trades']:<8} "
                  f"${summary['total_profit_loss']:<14.2f} "
                  f"{summary['profitable_stocks']}/{summary['total_stocks']:<11}")
        
        print("\n" + "="*100)
        print("DETAILED BREAKDOWN BY STRATEGY")
        print("="*100)
        
        for strategy_name, data in results.items():
            print(f"\n{strategy_name}:")
            print("-" * 80)
            summary = data['summary']
            print(f"  Overall Return: {summary['overall_return_pct']:.2f}%")
            print(f"  Win Rate: {summary['win_rate']:.1f}% ({summary['profitable_stocks']}/{summary['total_stocks']} stocks)")
            print(f"  Total Trades: {summary['total_trades']} (Buy: {summary['buy_trades']}, Sell: {summary['sell_trades']})")
            print(f"  Total Invested: ${summary['total_invested']:,.2f}")
            print(f"  Total Value: ${summary['total_value']:,.2f}")
            print(f"  Profit/Loss: ${summary['total_profit_loss']:,.2f}")
            
            # Top 5 performers
            stock_returns = sorted(
                [(s, r['return_pct']) for s, r in data['stocks'].items() if r['total_invested'] > 0],
                key=lambda x: x[1],
                reverse=True
            )
            if stock_returns:
                print(f"\n  Top 5 Performers:")
                for symbol, ret in stock_returns[:5]:
                    print(f"    {symbol}: {ret:.2f}%")
        
        print("\n" + "="*100)


def main():
    """Main function - ready for new strategy input."""
    print("="*100)
    print("STRATEGY COMPARISON FRAMEWORK")
    print("="*100)
    print("\nThis script compares trading strategies side-by-side.")
    print("Add your new strategy below, then run the comparison.")
    print("\n" + "="*100)
    
    # Configuration
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN'
    ]
    
    # Backtest period (6 months)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)
    
    print(f"\nBacktest Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Stocks: {len(stocks)}")
    print(f"Position Size: $1000 per trade")
    
    # Initialize comparator
    comparator = StrategyComparator(
        stocks=stocks,
        start_date=start_date.strftime('%Y-%m-%d'),
        end_date=end_date.strftime('%Y-%m-%d'),
        position_size=1000.0
    )
    
    # Add current strategy
    current_strategy = CurrentAnomalyStrategy(
        position_size=1000.0,
        min_severity=1.0,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.05
    )
    comparator.add_strategy(current_strategy)
    
    # Add Mean-Reversion Strategy
    mean_reversion_strategy = MeanReversionStrategy(
        position_size=1000.0,
        equity=100000.0
    )
    comparator.add_strategy(mean_reversion_strategy)
    
    print("\n" + "="*100)
    print("READY TO ADD NEW STRATEGY")
    print("="*100)
    print("\nTo add your new strategy:")
    print("1. Create a class that inherits from StrategyBase")
    print("2. Implement the check_signals() method")
    print("3. Add it to the comparator using comparator.add_strategy(your_strategy)")
    print("\nThen run the comparison:")
    print("  results = comparator.compare_strategies()")
    print("  comparator.print_comparison(results)")
    print("\n" + "="*100)
    
    # Run comparison
    results = comparator.compare_strategies()
    comparator.print_comparison(results)
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Save detailed results
    for strategy_name, data in results.items():
        df_results = pd.DataFrame([
            {
                'Symbol': symbol,
                'Trades': result['total_trades'],
                'Buy_Trades': result['buy_trades'],
                'Sell_Trades': result['sell_trades'],
                'Invested': result['total_invested'],
                'Total_Value': result['total_value'],
                'Profit_Loss': result['profit_loss'],
                'Return_Pct': result['return_pct']
            }
            for symbol, result in data['stocks'].items()
        ])
        
        filename = f"strategy_comparison_{strategy_name.replace(' ', '_').lower()}_{timestamp}.csv"
        df_results.to_csv(filename, index=False)
        print(f"\n✅ Detailed results saved to {filename}")
    
    # Save comparison summary
    comparison_summary = []
    for strategy_name, data in results.items():
        summary = data['summary']
        comparison_summary.append({
            'Strategy': strategy_name,
            'Return_Pct': summary['overall_return_pct'],
            'Win_Rate_Pct': summary['win_rate'],
            'Total_Trades': summary['total_trades'],
            'Buy_Trades': summary['buy_trades'],
            'Sell_Trades': summary['sell_trades'],
            'Total_Invested': summary['total_invested'],
            'Total_Value': summary['total_value'],
            'Profit_Loss': summary['total_profit_loss'],
            'Profitable_Stocks': summary['profitable_stocks'],
            'Total_Stocks': summary['total_stocks']
        })
    
    df_comparison = pd.DataFrame(comparison_summary)
    comparison_file = f"strategy_comparison_summary_{timestamp}.csv"
    df_comparison.to_csv(comparison_file, index=False)
    print(f"✅ Comparison summary saved to {comparison_file}")


if __name__ == '__main__':
    main()

