"""
Backtesting script for the red day trading strategy.
Simulates buying stocks at noon on red days over the last 3 months.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Backtester:
    """Backtests the red day trading strategy."""
    
    def __init__(self, stocks: List[str], position_size: float = 10.0):
        """
        Initialize backtester.
        
        Args:
            stocks: List of stock symbols to backtest
            position_size: Dollar amount per trade (default: $10)
        """
        self.stocks = stocks
        self.position_size = position_size
        self.start_date = (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d')
        self.end_date = datetime.now().strftime('%Y-%m-%d')
        
    def is_red_day(self, current_price: float, previous_close: float) -> bool:
        """
        Check if it's a red day (price went down).
        
        Args:
            current_price: Current day's price
            previous_close: Previous day's closing price
            
        Returns:
            True if red day, False otherwise
        """
        return current_price < previous_close
    
    def fetch_stock_data(self, symbol: str) -> pd.DataFrame:
        """Fetch historical stock data."""
        try:
            logger.info(f"Fetching data for {symbol}...")
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=self.start_date, end=self.end_date, interval='1d')
            
            if data.empty:
                logger.warning(f"No data found for {symbol}")
                return pd.DataFrame()
            
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def simulate_trading(self, symbol: str, data: pd.DataFrame, strategy: str = 'red_day') -> Dict:
        """
        Simulate trading strategy for a stock.
        
        Args:
            symbol: Stock symbol
            data: Historical price data
            strategy: 'red_day', 'green_day', or 'every_day'
            
        Returns:
            Dictionary with trading results
        """
        if data.empty or len(data) < 2:
            return {
                'symbol': symbol,
                'total_trades': 0,
                'total_invested': 0,
                'current_value': 0,
                'profit_loss': 0,
                'return_pct': 0,
                'trades': []
            }
        
        # Reset index to have date as column
        data = data.reset_index()
        data['Date'] = pd.to_datetime(data['Date'])
        
        trades = []
        total_invested = 0
        shares_owned = 0
        last_price = None
        
        # Iterate through each trading day
        for i in range(1, len(data)):
            current_date = data.iloc[i]['Date']
            current_price = data.iloc[i]['Close']
            previous_close = data.iloc[i-1]['Close']
            
            # Determine if we should buy based on strategy
            should_buy = False
            if strategy == 'every_day':
                # Buy every market day
                should_buy = True
            elif strategy == 'red_day':
                # Only buy on red days (price went down)
                is_red = self.is_red_day(current_price, previous_close)
                should_buy = is_red
            elif strategy == 'green_day':
                # Only buy on green days (price went up)
                is_green = current_price > previous_close
                should_buy = is_green
            
            if should_buy:
                # Execute buy order
                shares_to_buy = self.position_size / current_price
                cost = shares_to_buy * current_price
                
                trades.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'price': round(current_price, 2),
                    'shares': round(shares_to_buy, 4),
                    'cost': round(cost, 2),
                    'type': 'BUY'
                })
                
                shares_owned += shares_to_buy
                total_invested += cost
                last_price = current_price
        
        # Calculate final value (using last available price)
        if len(data) > 0:
            final_price = data.iloc[-1]['Close']
            current_value = shares_owned * final_price
            profit_loss = current_value - total_invested
            return_pct = (profit_loss / total_invested * 100) if total_invested > 0 else 0
            
            return {
                'symbol': symbol,
                'total_trades': len(trades),
                'total_invested': round(total_invested, 2),
                'shares_owned': round(shares_owned, 4),
                'final_price': round(final_price, 2),
                'current_value': round(current_value, 2),
                'profit_loss': round(profit_loss, 2),
                'return_pct': round(return_pct, 2),
                'trades': trades
            }
        else:
            return {
                'symbol': symbol,
                'total_trades': 0,
                'total_invested': 0,
                'current_value': 0,
                'profit_loss': 0,
                'return_pct': 0,
                'trades': []
            }
    
    def run_backtest(self, strategy: str = 'red_day') -> Dict:
        """
        Run backtest for all stocks.
        
        Args:
            strategy: 'red_day', 'green_day', or 'every_day'
        """
        strategy_names = {
            'red_day': 'Red Day Strategy',
            'green_day': 'Green Day Strategy',
            'every_day': 'Buy Every Day Strategy'
        }
        strategy_name = strategy_names.get(strategy, 'Red Day Strategy')
        logger.info(f"Starting backtest ({strategy_name}) from {self.start_date} to {self.end_date}")
        logger.info(f"Position size: ${self.position_size} per trade")
        logger.info(f"Stocks: {', '.join(self.stocks)}")
        
        results = {}
        total_invested_all = 0
        total_value_all = 0
        
        for symbol in self.stocks:
            symbol = symbol.strip().upper()
            data = self.fetch_stock_data(symbol)
            result = self.simulate_trading(symbol, data, strategy=strategy)
            results[symbol] = result
            
            total_invested_all += result['total_invested']
            total_value_all += result['current_value']
        
        # Calculate overall statistics
        total_profit_loss = total_value_all - total_invested_all
        overall_return_pct = (total_profit_loss / total_invested_all * 100) if total_invested_all > 0 else 0
        
        return {
            'strategy': strategy_name,
            'strategy_key': strategy,
            'period': f"{self.start_date} to {self.end_date}",
            'position_size': self.position_size,
            'stocks': results,
            'summary': {
                'total_invested': round(total_invested_all, 2),
                'total_value': round(total_value_all, 2),
                'total_profit_loss': round(total_profit_loss, 2),
                'overall_return_pct': round(overall_return_pct, 2),
                'total_trades': sum(r['total_trades'] for r in results.values())
            }
        }
    
    def print_results(self, results: Dict):
        """Print formatted backtest results."""
        print("\n" + "="*80)
        print(f"BACKTEST RESULTS - {results['strategy']}")
        print("="*80)
        print(f"\nPeriod: {results['period']}")
        print(f"Position Size: ${results['position_size']} per trade")
        print(f"\n{'Stock':<8} {'Trades':<8} {'Invested':<12} {'Value':<12} {'P/L':<12} {'Return %':<10}")
        print("-"*80)
        
        for symbol, data in results['stocks'].items():
            print(f"{symbol:<8} {data['total_trades']:<8} ${data['total_invested']:<11.2f} "
                  f"${data['current_value']:<11.2f} ${data['profit_loss']:<11.2f} "
                  f"{data['return_pct']:<9.2f}%")
        
        print("-"*80)
        summary = results['summary']
        print(f"{'TOTAL':<8} {summary['total_trades']:<8} ${summary['total_invested']:<11.2f} "
              f"${summary['total_value']:<11.2f} ${summary['total_profit_loss']:<11.2f} "
              f"{summary['overall_return_pct']:<9.2f}%")
        
        print("\n" + "="*80)
        print("DETAILED BREAKDOWN BY STOCK")
        print("="*80)
        
        for symbol, data in results['stocks'].items():
            if data['total_trades'] > 0:
                print(f"\n{symbol}:")
                print(f"  Total Trades: {data['total_trades']}")
                print(f"  Total Invested: ${data['total_invested']:.2f}")
                print(f"  Shares Owned: {data['shares_owned']:.4f}")
                print(f"  Final Price: ${data['final_price']:.2f}")
                print(f"  Current Value: ${data['current_value']:.2f}")
                print(f"  Profit/Loss: ${data['profit_loss']:.2f} ({data['return_pct']:.2f}%)")
                
                # Show first 5 trades
                if len(data['trades']) > 0:
                    print(f"  Sample Trades (showing first 5):")
                    for trade in data['trades'][:5]:
                        print(f"    {trade['date']}: BUY {trade['shares']:.4f} shares @ ${trade['price']:.2f} (${trade['cost']:.2f})")
                    if len(data['trades']) > 5:
                        print(f"    ... and {len(data['trades']) - 5} more trades")


def compare_strategies(red_day_results: Dict, green_day_results: Dict, every_day_results: Dict):
    """Compare and print results from all three strategies."""
    print("\n" + "="*80)
    print("STRATEGY COMPARISON - ALL THREE STRATEGIES")
    print("="*80)
    
    print(f"\n{'Metric':<25} {'Red Day':<18} {'Green Day':<18} {'Buy Every Day':<18} {'Best':<10}")
    print("-"*80)
    
    # Compare totals
    red_summary = red_day_results['summary']
    green_summary = green_day_results['summary']
    every_summary = every_day_results['summary']
    
    # Find best return
    returns = {
        'Red Day': red_summary['overall_return_pct'],
        'Green Day': green_summary['overall_return_pct'],
        'Buy Every Day': every_summary['overall_return_pct']
    }
    best_return = max(returns, key=returns.get)
    
    print(f"{'Total Invested':<25} ${red_summary['total_invested']:<17.2f} ${green_summary['total_invested']:<17.2f} ${every_summary['total_invested']:<17.2f}")
    print(f"{'Current Value':<25} ${red_summary['total_value']:<17.2f} ${green_summary['total_value']:<17.2f} ${every_summary['total_value']:<17.2f}")
    print(f"{'Profit/Loss':<25} ${red_summary['total_profit_loss']:<17.2f} ${green_summary['total_profit_loss']:<17.2f} ${every_summary['total_profit_loss']:<17.2f}")
    print(f"{'Return %':<25} {red_summary['overall_return_pct']:<17.2f}% {green_summary['overall_return_pct']:<17.2f}% {every_summary['overall_return_pct']:<17.2f}% {best_return:<10}")
    print(f"{'Total Trades':<25} {red_summary['total_trades']:<17} {green_summary['total_trades']:<17} {every_summary['total_trades']:<17}")
    
    print("\n" + "="*80)
    print("BREAKDOWN BY STOCK - COMPARISON")
    print("="*80)
    print(f"\n{'Stock':<8} {'Strategy':<20} {'Trades':<8} {'Invested':<12} {'Value':<12} {'P/L':<12} {'Return %':<10}")
    print("-"*80)
    
    for symbol in red_day_results['stocks'].keys():
        red_data = red_day_results['stocks'][symbol]
        green_data = green_day_results['stocks'][symbol]
        every_data = every_day_results['stocks'][symbol]
        
        print(f"{symbol:<8} {'Red Day':<20} {red_data['total_trades']:<8} ${red_data['total_invested']:<11.2f} "
              f"${red_data['current_value']:<11.2f} ${red_data['profit_loss']:<11.2f} {red_data['return_pct']:<9.2f}%")
        print(f"{'':<8} {'Green Day':<20} {green_data['total_trades']:<8} ${green_data['total_invested']:<11.2f} "
              f"${green_data['current_value']:<11.2f} ${green_data['profit_loss']:<11.2f} {green_data['return_pct']:<9.2f}%")
        print(f"{'':<8} {'Buy Every Day':<20} {every_data['total_trades']:<8} ${every_data['total_invested']:<11.2f} "
              f"${every_data['current_value']:<11.2f} ${every_data['profit_loss']:<11.2f} {every_data['return_pct']:<9.2f}%")
        print()


def main():
    """Main function to run backtest."""
    # Default stocks from config
    stocks = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
    position_size = 10.0  # $10 per trade as requested
    
    backtester = Backtester(stocks=stocks, position_size=position_size)
    
    # Run red day strategy
    print("\n" + "="*80)
    print("RUNNING RED DAY STRATEGY BACKTEST")
    print("="*80)
    red_day_results = backtester.run_backtest(strategy='red_day')
    backtester.print_results(red_day_results)
    
    # Run green day strategy
    print("\n" + "="*80)
    print("RUNNING GREEN DAY STRATEGY BACKTEST")
    print("="*80)
    green_day_results = backtester.run_backtest(strategy='green_day')
    backtester.print_results(green_day_results)
    
    # Run buy every day strategy
    print("\n" + "="*80)
    print("RUNNING BUY EVERY DAY STRATEGY BACKTEST")
    print("="*80)
    every_day_results = backtester.run_backtest(strategy='every_day')
    backtester.print_results(every_day_results)
    
    # Compare all strategies
    compare_strategies(red_day_results, green_day_results, every_day_results)
    
    # Save results to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Combine all results
    all_results = []
    for results_dict in [red_day_results, green_day_results, every_day_results]:
        for symbol, data in results_dict['stocks'].items():
            all_results.append({
                'Symbol': symbol,
                'Strategy': results_dict['strategy'],
                'Trades': data['total_trades'],
                'Invested': data['total_invested'],
                'Current_Value': data['current_value'],
                'Profit_Loss': data['profit_loss'],
                'Return_Pct': data['return_pct']
            })
    
    df_combined = pd.DataFrame(all_results)
    output_file = f"backtest_comparison_{timestamp}.csv"
    df_combined.to_csv(output_file, index=False)
    print(f"\n✅ Comparison results saved to {output_file}")


if __name__ == '__main__':
    main()

