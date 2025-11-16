"""
Backtest Red Day Strategy for 1 Year on 50 Stocks
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import logging

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class RedDayStrategy:
    """Basic Red Day Strategy - Buy on red days only."""
    
    def __init__(self, stocks: List[str], position_size: float = 10.0):
        self.stocks = stocks
        self.position_size = position_size
        self.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')  # 1 year
        self.end_date = datetime.now().strftime('%Y-%m-%d')
    
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
    
    def is_red_day(self, current_price: float, previous_close: float) -> bool:
        """Check if it's a red day (price dropped)."""
        return current_price < previous_close
    
    def backtest_strategy(self, symbol: str) -> Dict:
        """Backtest red day strategy."""
        data = self.fetch_stock_data(symbol)
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
        
        trades = []
        total_invested = 0
        shares_owned = 0
        
        for i in range(1, len(data)):
            current_price = data.iloc[i]['Close']
            previous_close = data.iloc[i-1]['Close']
            
            if self.is_red_day(current_price, previous_close):
                # Buy on red day
                shares_to_buy = self.position_size / current_price
                cost = shares_to_buy * current_price
                
                trades.append({
                    'date': data.iloc[i]['Date'].strftime('%Y-%m-%d'),
                    'type': 'BUY',
                    'price': round(current_price, 2),
                    'shares': round(shares_to_buy, 4),
                    'cost': round(cost, 2)
                })
                
                shares_owned += shares_to_buy
                total_invested += cost
        
        # Calculate final value
        if len(data) > 0 and total_invested > 0:
            final_price = data.iloc[-1]['Close']
            current_value = shares_owned * final_price
            profit_loss = current_value - total_invested
            return_pct = (profit_loss / total_invested * 100)
            
            return {
                'symbol': symbol,
                'total_trades': len(trades),
                'total_invested': round(total_invested, 2),
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
    
    def run_backtest(self) -> Dict:
        """Run backtest for all stocks."""
        results = {}
        for i, symbol in enumerate(self.stocks, 1):
            symbol = symbol.strip().upper()
            print(f"Processing {symbol} ({i}/{len(self.stocks)})...", end='\r')
            result = self.backtest_strategy(symbol)
            results[symbol] = result
        
        print()  # New line after progress
        
        total_invested = sum(r['total_invested'] for r in results.values())
        total_value = sum(r['current_value'] for r in results.values())
        total_profit = total_value - total_invested
        overall_return = (total_profit / total_invested * 100) if total_invested > 0 else 0
        
        return {
            'period': f"{self.start_date} to {self.end_date}",
            'stocks': results,
            'summary': {
                'total_invested': round(total_invested, 2),
                'total_value': round(total_value, 2),
                'total_profit_loss': round(total_profit, 2),
                'overall_return_pct': round(overall_return, 2),
                'total_trades': sum(r['total_trades'] for r in results.values())
            }
        }


def main():
    """Main function to run 1-year Red Day backtest."""
    # Top 50 stocks
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN',
        'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE', 'CMCSA',
        'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI', 'INTU'
    ]
    
    print('='*100)
    print('RED DAY STRATEGY BACKTEST - 50 STOCKS, 1 YEAR')
    print('='*100)
    start_date_str = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    end_date_str = datetime.now().strftime('%Y-%m-%d')
    print(f'\nTesting {len(stocks)} stocks over 1 year period')
    print(f'Period: {start_date_str} to {end_date_str}')
    print(f'Position Size: $10 per trade\n')
    
    # Run backtest
    red_day = RedDayStrategy(stocks=stocks, position_size=10.0)
    results = red_day.run_backtest()
    
    # Calculate win rate
    stocks_data = results['stocks']
    profitable = [s for s in stocks_data.values() if s['profit_loss'] > 0]
    win_rate = (len(profitable) / len(stocks_data) * 100) if len(stocks_data) > 0 else 0
    
    # Print results
    print('\n' + '='*100)
    print('RESULTS SUMMARY')
    print('='*100)
    summary = results['summary']
    print(f"Period: {results['period']}")
    print(f"Total Stocks: {len(stocks_data)}")
    print(f"Total Trades: {summary['total_trades']:,}")
    print(f"Total Invested: ${summary['total_invested']:,.2f}")
    print(f"Total Value: ${summary['total_value']:,.2f}")
    print(f"Total Profit/Loss: ${summary['total_profit_loss']:,.2f}")
    print(f"Overall Return: {summary['overall_return_pct']:.2f}%")
    print(f"Win Rate: {len(profitable)}/{len(stocks_data)} ({win_rate:.1f}%)")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"redday_backtest_50stocks_1year_{timestamp}.csv"
    
    results_list = []
    for symbol, data in stocks_data.items():
        results_list.append({
            'Symbol': symbol,
            'Trades': data['total_trades'],
            'Invested': data['total_invested'],
            'Current_Value': data['current_value'],
            'Profit_Loss': data['profit_loss'],
            'Return_Pct': data['return_pct']
        })
    
    df = pd.DataFrame(results_list)
    df.to_csv(output_file, index=False)
    print(f'\n✅ Results saved to {output_file}')
    
    # Top and bottom performers
    print('\n' + '='*100)
    print('TOP 10 PERFORMERS')
    print('='*100)
    top_performers = sorted(stocks_data.items(), key=lambda x: x[1]['return_pct'], reverse=True)[:10]
    print(f"{'Symbol':<8} {'Trades':<8} {'Return %':<12} {'Profit':<15}")
    print('-'*50)
    for symbol, data in top_performers:
        print(f"{symbol:<8} {data['total_trades']:<8} {data['return_pct']:<11.2f}% ${data['profit_loss']:<14.2f}")
    
    print('\n' + '='*100)
    print('BOTTOM 10 PERFORMERS')
    print('='*100)
    bottom_performers = sorted(stocks_data.items(), key=lambda x: x[1]['return_pct'])[:10]
    print(f"{'Symbol':<8} {'Trades':<8} {'Return %':<12} {'Profit':<15}")
    print('-'*50)
    for symbol, data in bottom_performers:
        print(f"{symbol:<8} {data['total_trades']:<8} {data['return_pct']:<11.2f}% ${data['profit_loss']:<14.2f}")


if __name__ == '__main__':
    main()

