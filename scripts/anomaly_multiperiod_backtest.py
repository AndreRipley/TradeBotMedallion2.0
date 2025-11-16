"""
Anomaly Buy+Sell Strategy - Multiple Time Periods Comparison
Tests the strategy over 1 month, 3 months, 6 months, and 1 year
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
import logging
from anomaly_strategy import AnomalyDetector, AnomalyTradingStrategy

logging.basicConfig(level=logging.WARNING)  # Reduce logging
logger = logging.getLogger(__name__)


def run_anomaly_backtest_for_period(stocks: List[str], days: int, period_name: str):
    """Run Anomaly Buy+Sell backtest for a specific period."""
    print(f"\n[{period_name}] Running backtest for {days} days ({days/30:.1f} months)...")
    
    strategy = AnomalyTradingStrategy(stocks=stocks, position_size=10.0, min_severity=1.0)
    strategy.start_date = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')
    strategy.end_date = datetime.now().strftime('%Y-%m-%d')
    
    results = strategy.run_backtest()
    
    # Calculate win rate
    stocks_data = results['stocks']
    profitable = [s for s in stocks_data.values() if s['profit_loss'] > 0]
    win_rate = (len(profitable) / len(stocks_data) * 100) if len(stocks_data) > 0 else 0
    
    summary = results['summary']
    
    return {
        'period': period_name,
        'days': days,
        'start_date': strategy.start_date,
        'end_date': strategy.end_date,
        'return_pct': summary['overall_return_pct'],
        'win_rate_pct': win_rate,
        'total_trades': summary['total_trades'],
        'buy_trades': sum(s.get('buy_trades', 0) for s in stocks_data.values()),
        'sell_trades': sum(s.get('sell_trades', 0) for s in stocks_data.values()),
        'total_invested': summary['total_invested'],
        'total_value': summary['total_value'],
        'total_profit_loss': summary['total_profit_loss'],
        'profitable_stocks': len(profitable),
        'total_stocks': len(stocks_data)
    }


def main():
    """Run Anomaly Buy+Sell strategy for multiple time periods."""
    # Top 50 stocks
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN',
        'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE', 'CMCSA',
        'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI', 'INTU'
    ]
    
    print('='*100)
    print('ANOMALY BUY+SELL STRATEGY - MULTIPLE TIME PERIODS COMPARISON')
    print('='*100)
    print(f'\nTesting {len(stocks)} stocks over different time periods')
    print('Strategy: Anomaly Detection with Buy + Sell signals')
    print('Position Size: $10 per trade')
    print('Minimum Severity: 1.0\n')
    
    # Run backtests for different periods
    periods = [
        (30, '1 Month'),
        (90, '3 Months'),
        (180, '6 Months'),
        (365, '1 Year')
    ]
    
    all_results = []
    for days, period_name in periods:
        result = run_anomaly_backtest_for_period(stocks, days, period_name)
        all_results.append(result)
    
    # Display comparison table
    print('\n' + '='*100)
    print('RESULTS COMPARISON - ANOMALY BUY+SELL STRATEGY')
    print('='*100)
    
    print(f'\n{"Period":<15} {"Days":<8} {"Return %":<12} {"Win Rate %":<12} {"Trades":<10} {"Buy":<8} {"Sell":<8} {"Profit":<15} {"Profitable":<12}')
    print('-'*120)
    
    for result in all_results:
        print(f"{result['period']:<15} {result['days']:<8} "
              f"{result['return_pct']:<11.2f}% {result['win_rate_pct']:<11.1f}% "
              f"{result['total_trades']:<10} {result['buy_trades']:<8} {result['sell_trades']:<8} "
              f"${result['total_profit_loss']:<14.2f} "
              f"{result['profitable_stocks']}/{result['total_stocks']:<11}")
    
    # Detailed breakdown
    print('\n' + '='*100)
    print('DETAILED BREAKDOWN BY PERIOD')
    print('='*100)
    
    for result in all_results:
        print(f"\n{result['period']} ({result['days']} days):")
        print(f"  Period: {result['start_date']} to {result['end_date']}")
        print(f"  Return: {result['return_pct']:.2f}%")
        print(f"  Win Rate: {result['win_rate_pct']:.1f}% ({result['profitable_stocks']}/{result['total_stocks']} stocks)")
        print(f"  Total Trades: {result['total_trades']:,} ({result['buy_trades']:,} buys, {result['sell_trades']:,} sells)")
        print(f"  Total Invested: ${result['total_invested']:,.2f}")
        print(f"  Total Value: ${result['total_value']:,.2f}")
        print(f"  Total Profit/Loss: ${result['total_profit_loss']:,.2f}")
        
        # Calculate annualized return
        if result['days'] > 0:
            annualized = ((1 + result['return_pct']/100) ** (365/result['days']) - 1) * 100
            print(f"  Annualized Return: {annualized:.2f}%")
    
    # Save results to CSV
    df = pd.DataFrame(all_results)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"anomaly_buysell_multiperiod_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f'\n✅ Results saved to {output_file}')
    
    # Key insights
    print('\n' + '='*100)
    print('KEY INSIGHTS')
    print('='*100)
    
    if len(all_results) >= 2:
        print(f"\n📈 Return Progression:")
        for i, result in enumerate(all_results):
            if i == 0:
                print(f"  {result['period']}: {result['return_pct']:.2f}%")
            else:
                prev_return = all_results[i-1]['return_pct']
                change = result['return_pct'] - prev_return
                print(f"  {result['period']}: {result['return_pct']:.2f}% (change: {change:+.2f}%)")
        
        print(f"\n📊 Win Rate Progression:")
        for i, result in enumerate(all_results):
            if i == 0:
                print(f"  {result['period']}: {result['win_rate_pct']:.1f}%")
            else:
                prev_wr = all_results[i-1]['win_rate_pct']
                change = result['win_rate_pct'] - prev_wr
                print(f"  {result['period']}: {result['win_rate_pct']:.1f}% (change: {change:+.1f}%)")
        
        print(f"\n💡 Observations:")
        print(f"  • Shortest period (1 month): {all_results[0]['return_pct']:.2f}% return")
        print(f"  • Longest period (1 year): {all_results[-1]['return_pct']:.2f}% return")
        print(f"  • Best period: {max(all_results, key=lambda x: x['return_pct'])['period']} ({max(all_results, key=lambda x: x['return_pct'])['return_pct']:.2f}%)")
        print(f"  • Highest win rate: {max(all_results, key=lambda x: x['win_rate_pct'])['period']} ({max(all_results, key=lambda x: x['win_rate_pct'])['win_rate_pct']:.1f}%)")


if __name__ == '__main__':
    main()

