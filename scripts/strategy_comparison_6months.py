"""
Comprehensive Strategy Comparison - 50 Stocks, 6 Months
Tests all strategies on the same 50 stocks over 6 months period.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import logging
from anomaly_strategy import AnomalyDetector, AnomalyTradingStrategy
from statistical_arbitrage_strategy import StatisticalArbitrageDetector, StatisticalArbitrageStrategy

logging.basicConfig(level=logging.WARNING)  # Reduce logging
logger = logging.getLogger(__name__)


class RedDayStrategy:
    """Basic Red Day Strategy - Buy on red days only."""
    
    def __init__(self, stocks: List[str], position_size: float = 10.0):
        self.stocks = stocks
        self.position_size = position_size
        self.start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')  # 6 months
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
                'buy_trades': len(trades),
                'sell_trades': 0,
                'total_invested': round(total_invested, 2),
                'current_value': round(current_value, 2),
                'total_value': round(current_value, 2),
                'profit_loss': round(profit_loss, 2),
                'return_pct': round(return_pct, 2),
                'trades': trades
            }
        else:
            return {
                'symbol': symbol,
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'total_invested': 0,
                'current_value': 0,
                'total_value': 0,
                'profit_loss': 0,
                'return_pct': 0,
                'trades': []
            }
    
    def run_backtest(self) -> Dict:
        """Run backtest for all stocks."""
        results = {}
        for symbol in self.stocks:
            symbol = symbol.strip().upper()
            result = self.backtest_strategy(symbol)
            results[symbol] = result
        
        total_invested = sum(r['total_invested'] for r in results.values())
        total_value = sum(r['total_value'] for r in results.values())
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


def run_all_strategies_comparison():
    """Run all strategies on 50 stocks over 6 months."""
    # Top 50 stocks
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN',
        'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE', 'CMCSA',
        'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI', 'INTU'
    ]
    
    print('='*100)
    print('COMPREHENSIVE STRATEGY COMPARISON - 50 STOCKS, 6 MONTHS')
    print('='*100)
    start_date_str = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    end_date_str = datetime.now().strftime('%Y-%m-%d')
    print(f'\nTesting {len(stocks)} stocks over 6 months period')
    print(f'Period: {start_date_str} to {end_date_str}')
    
    all_results = {}
    
    # 1. Red Day Strategy
    print('\n[1/4] Testing Red Day Strategy...')
    red_day = RedDayStrategy(stocks=stocks, position_size=10.0)
    red_day_results = red_day.run_backtest()
    all_results['Red Day'] = red_day_results
    
    # 2. Anomaly Detection (Buy Only)
    print('[2/4] Testing Anomaly Detection (Buy Only)...')
    anomaly_buy_only = AnomalyTradingStrategy(stocks=stocks, position_size=10.0, min_severity=1.0)
    anomaly_buy_only.start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    anomaly_buy_only.end_date = datetime.now().strftime('%Y-%m-%d')
    anomaly_buy_results = anomaly_buy_only.run_backtest()
    all_results['Anomaly Detection (Buy Only)'] = anomaly_buy_results
    
    # 3. Anomaly Detection (Buy + Sell)
    print('[3/4] Testing Anomaly Detection (Buy + Sell)...')
    anomaly_buy_sell = AnomalyTradingStrategy(stocks=stocks, position_size=10.0, min_severity=1.0)
    anomaly_buy_sell.start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    anomaly_buy_sell.end_date = datetime.now().strftime('%Y-%m-%d')
    anomaly_buy_sell_results = anomaly_buy_sell.run_backtest()
    all_results['Anomaly Detection (Buy + Sell)'] = anomaly_buy_sell_results
    
    # 4. Statistical Arbitrage
    print('[4/4] Testing Statistical Arbitrage...')
    stat_arb = StatisticalArbitrageStrategy(stocks=stocks, position_size=10.0, min_severity=1.5)
    stat_arb.start_date = (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d')
    stat_arb.end_date = datetime.now().strftime('%Y-%m-%d')
    stat_arb_results = stat_arb.run_backtest()
    all_results['Statistical Arbitrage'] = stat_arb_results
    
    # Calculate win rates
    print('\n' + '='*100)
    print('RESULTS COMPARISON - 50 STOCKS, 6 MONTHS')
    print('='*100)
    
    comparison_data = []
    
    for strategy_name, results in all_results.items():
        summary = results['summary']
        stocks_data = results['stocks']
        
        profitable = [s for s in stocks_data.values() if s['profit_loss'] > 0]
        win_rate = (len(profitable) / len(stocks_data) * 100) if len(stocks_data) > 0 else 0
        
        comparison_data.append({
            'Strategy': strategy_name,
            'Return %': summary['overall_return_pct'],
            'Win Rate %': round(win_rate, 1),
            'Total Trades': summary['total_trades'],
            'Total Invested': summary['total_invested'],
            'Total Profit': summary['total_profit_loss'],
            'Profitable Stocks': len(profitable),
            'Total Stocks': len(stocks_data)
        })
    
    df = pd.DataFrame(comparison_data)
    
    print(f'\n{"Strategy":<35} {"Return %":<12} {"Win Rate %":<12} {"Trades":<10} {"Profit":<15} {"Profitable":<12}')
    print('-'*120)
    
    for _, row in df.iterrows():
        strategy = row['Strategy']
        return_pct = row['Return %']
        win_rate = row['Win Rate %']
        trades = int(row['Total Trades'])
        profit = row['Total Profit']
        profitable = f"{int(row['Profitable Stocks'])}/{int(row['Total Stocks'])}"
        print(f"{strategy:<35} {return_pct:<11.2f}% {win_rate:<11.1f}% {trades:<10} ${profit:<14.2f} {profitable:<12}")
    
    # Save results
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"strategy_comparison_50stocks_6months_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f'\n✅ Results saved to {output_file}')
    
    # Detailed breakdown
    print(f'\n\n📊 DETAILED BREAKDOWN:')
    print('-'*100)
    
    for strategy_name, results in all_results.items():
        summary = results['summary']
        stocks_data = results['stocks']
        profitable = [s for s in stocks_data.values() if s['profit_loss'] > 0]
        
        print(f'\n{strategy_name}:')
        overall_return = summary['overall_return_pct']
        print(f'  Return: {overall_return:.2f}%')
        win_rate_pct = len(profitable)/len(stocks_data)*100
        print(f'  Win Rate: {len(profitable)}/{len(stocks_data)} ({win_rate_pct:.1f}%)')
        print(f'  Total Trades: {summary["total_trades"]:,}')
        total_invested = summary['total_invested']
        print(f'  Total Invested: ${total_invested:,.2f}')
        total_profit = summary['total_profit_loss']
        print(f'  Total Profit: ${total_profit:,.2f}')
        
        if len(profitable) > 0:
            avg_return = np.mean([s['return_pct'] for s in profitable])
            print(f'  Avg Return (Profitable): {avg_return:.2f}%')
        
        losing_stocks = [s for s in stocks_data.values() if s['profit_loss'] < 0]
        if len(losing_stocks) > 0:
            avg_loss = np.mean([s['return_pct'] for s in losing_stocks])
            print(f'  Avg Return (Losing): {avg_loss:.2f}%')
    
    return df


if __name__ == '__main__':
    results_df = run_all_strategies_comparison()

