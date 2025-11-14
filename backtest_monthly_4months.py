"""
Backtest Current Improved Anomaly Strategy - Monthly Breakdown (4 Months)
Runs separate backtests for each of the last 4 months
"""
import pandas as pd
from datetime import datetime, timedelta
from improved_anomaly_strategy import ImprovedAnomalyTradingStrategy
from config import Config


def run_monthly_backtest(stocks, position_size, month_num: int, end_date: datetime):
    """Run backtest for a specific month using fixed date ranges."""
    # Use fixed date ranges based on the successful 3-month backtest period
    # Going back 4 months from mid-August 2024 to mid-November 2024
    # Month 1: Oct 15 - Nov 13 (most recent)
    # Month 2: Sep 15 - Oct 14
    # Month 3: Aug 15 - Sep 14
    # Month 4: Jul 15 - Aug 14
    
    month_ranges = [
        {'start': '2024-10-01', 'end': '2024-10-31', 'name': 'October 2024'},
        {'start': '2024-09-01', 'end': '2024-09-30', 'name': 'September 2024'},
        {'start': '2024-08-01', 'end': '2024-08-31', 'name': 'August 2024'},
        {'start': '2024-07-01', 'end': '2024-07-31', 'name': 'July 2024'},
    ]
    
    month_info = month_ranges[month_num - 1]
    month_start = datetime.strptime(month_info['start'], '%Y-%m-%d')
    month_end_date = datetime.strptime(month_info['end'], '%Y-%m-%d')
    month_name = month_info['name']
    
    # Fetch data starting 30 days before the month to ensure we have enough
    # historical data for the 20-day lookback period
    data_start_date = month_start - timedelta(days=30)
    
    print(f'\n{"="*100}')
    print(f'{month_name.upper()} BACKTEST')
    print(f'{"="*100}')
    print(f'Backtest Period: {month_start.strftime("%Y-%m-%d")} to {month_end_date.strftime("%Y-%m-%d")}')
    print(f'Data Fetch Period: {data_start_date.strftime("%Y-%m-%d")} to {month_end_date.strftime("%Y-%m-%d")} (includes 30-day lookback)')
    print(f'Running backtest...')
    
    # Initialize strategy
    strategy = ImprovedAnomalyTradingStrategy(
        stocks=stocks,
        position_size=position_size,
        min_severity=1.0,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.05,
        min_risk_reward_ratio=1.5
    )
    # Set data fetch dates (includes lookback period)
    strategy.start_date = data_start_date.strftime('%Y-%m-%d')
    strategy.end_date = month_end_date.strftime('%Y-%m-%d')
    
    # Store the actual backtest period for filtering trades
    strategy.backtest_start_date = month_start
    strategy.backtest_end_date = month_end_date
    
    # Run backtest
    results = strategy.run_backtest()
    
    # Calculate win rate
    stocks_data = results['stocks']
    profitable = [s for s in stocks_data.values() if s['profit_loss'] > 0]
    win_rate = (len(profitable) / len(stocks_data) * 100) if len(stocks_data) > 0 else 0
    
    summary = results['summary']
    
    return {
        'month': month_name,
        'month_num': month_num,
        'start_date': month_start.strftime('%Y-%m-%d'),
        'end_date': month_end_date.strftime('%Y-%m-%d'),
        'days': (month_end_date - month_start).days,
        'return_pct': summary['overall_return_pct'],
        'win_rate_pct': win_rate,
        'total_trades': summary['total_trades'],
        'buy_trades': sum(s.get('buy_trades', 0) for s in stocks_data.values()),
        'sell_trades': sum(s.get('sell_trades', 0) for s in stocks_data.values()),
        'total_invested': summary['total_invested'],
        'total_value': summary['total_value'],
        'total_profit_loss': summary['total_profit_loss'],
        'profitable_stocks': len(profitable),
        'total_stocks': len(stocks_data),
        'stop_loss_triggers': summary.get('stop_loss_triggers', 0),
        'trailing_stop_triggers': summary.get('trailing_stop_triggers', 0),
        'overbought_sells': summary.get('overbought_sells', 0)
    }


def main():
    """Run monthly backtests for the last 4 months."""
    # Use the full 30-stock list from default configuration
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN'
    ]
    
    # Use the same position size as the live bot
    position_size = Config.POSITION_SIZE
    
    print('='*100)
    print('CURRENT STRATEGY - MONTHLY BACKTEST (4 MONTHS)')
    print('='*100)
    print(f'\nStrategy: Improved Anomaly Buy+Sell Strategy')
    print(f'Features: Stop-losses (5%), Trailing stops (5%), Dynamic position sizing')
    print(f'Stocks: {len(stocks)} stocks')
    print(f'Position Size: ${position_size:.2f} per trade')
    print(f'Minimum Severity: 1.0')
    print(f'\nRunning 4 separate monthly backtests...')
    
    end_date = datetime.now()
    all_results = []
    
    # Run backtest for each of the last 4 months
    for month_num in range(1, 5):
        result = run_monthly_backtest(stocks, position_size, month_num, end_date)
        all_results.append(result)
        
        # Display monthly results
        print(f'\n📊 {result["month"]} Results:')
        print(f'  Period: {result["start_date"]} to {result["end_date"]} ({result["days"]} days)')
        print(f'  Return: {result["return_pct"]:.2f}%')
        print(f'  Win Rate: {result["win_rate_pct"]:.1f}% ({result["profitable_stocks"]}/{result["total_stocks"]} stocks)')
        print(f'  Total Trades: {result["total_trades"]:,} ({result["buy_trades"]:,} buys, {result["sell_trades"]:,} sells)')
        print(f'  Total Invested: ${result["total_invested"]:,.2f}')
        print(f'  Total Value: ${result["total_value"]:,.2f}')
        print(f'  Total Profit/Loss: ${result["total_profit_loss"]:,.2f}')
        print(f'  Stop-Loss Triggers: {result["stop_loss_triggers"]}')
        print(f'  Trailing Stop Triggers: {result["trailing_stop_triggers"]}')
        print(f'  Overbought Sells: {result["overbought_sells"]}')
    
    # Display comparison table
    print('\n' + '='*100)
    print('MONTHLY COMPARISON TABLE')
    print('='*100)
    
    print(f'\n{"Month":<10} {"Period":<25} {"Return %":<12} {"Win Rate %":<12} {"Trades":<10} {"Profit":<15} {"Stop-L":<8} {"Trail":<8} {"Profitable":<12}')
    print('-'*130)
    
    for result in all_results:
        period_str = f"{result['start_date']} to {result['end_date']}"
        print(f"{result['month']:<10} {period_str:<25} "
              f"{result['return_pct']:<11.2f}% {result['win_rate_pct']:<11.1f}% "
              f"{result['total_trades']:<10} ${result['total_profit_loss']:<14.2f} "
              f"{result['stop_loss_triggers']:<8} {result['trailing_stop_triggers']:<8} "
              f"{result['profitable_stocks']}/{result['total_stocks']:<11}")
    
    # Calculate cumulative performance
    print('\n' + '='*100)
    print('CUMULATIVE PERFORMANCE')
    print('='*100)
    
    cumulative_invested = 0
    cumulative_value = 0
    cumulative_trades = 0
    
    print(f'\n{"Month":<10} {"Cumulative Return %":<20} {"Cumulative Profit":<20} {"Cumulative Trades":<20}')
    print('-'*70)
    
    for i, result in enumerate(all_results, 1):
        cumulative_invested += result['total_invested']
        cumulative_value += result['total_value']
        cumulative_trades += result['total_trades']
        
        cumulative_profit = cumulative_value - cumulative_invested
        cumulative_return = (cumulative_profit / cumulative_invested * 100) if cumulative_invested > 0 else 0
        
        print(f"{result['month']:<10} {cumulative_return:<19.2f}% ${cumulative_profit:<19.2f} {cumulative_trades:<20}")
    
    # Summary statistics
    print('\n' + '='*100)
    print('SUMMARY STATISTICS')
    print('='*100)
    
    returns = [r['return_pct'] for r in all_results]
    win_rates = [r['win_rate_pct'] for r in all_results]
    trades = [r['total_trades'] for r in all_results]
    
    print(f'\n📈 Return Statistics:')
    print(f'  Best Month: {max(all_results, key=lambda x: x["return_pct"])["month"]} ({max(returns):.2f}%)')
    print(f'  Worst Month: {min(all_results, key=lambda x: x["return_pct"])["month"]} ({min(returns):.2f}%)')
    print(f'  Average Monthly Return: {sum(returns)/len(returns):.2f}%')
    print(f'  Total 4-Month Return: {cumulative_return:.2f}%')
    
    print(f'\n📊 Win Rate Statistics:')
    print(f'  Best Month: {max(all_results, key=lambda x: x["win_rate_pct"])["month"]} ({max(win_rates):.1f}%)')
    print(f'  Worst Month: {min(all_results, key=lambda x: x["win_rate_pct"])["month"]} ({min(win_rates):.1f}%)')
    print(f'  Average Win Rate: {sum(win_rates)/len(win_rates):.1f}%')
    
    print(f'\n🔄 Trading Activity:')
    print(f'  Most Active Month: {max(all_results, key=lambda x: x["total_trades"])["month"]} ({max(trades):,} trades)')
    print(f'  Least Active Month: {min(all_results, key=lambda x: x["total_trades"])["month"]} ({min(trades):,} trades)')
    print(f'  Average Monthly Trades: {sum(trades)/len(trades):.0f}')
    print(f'  Total Trades (4 months): {sum(trades):,}')
    
    print(f'\n🛡️  Risk Management:')
    total_stop_losses = sum(r['stop_loss_triggers'] for r in all_results)
    total_trailing_stops = sum(r['trailing_stop_triggers'] for r in all_results)
    total_overbought = sum(r['overbought_sells'] for r in all_results)
    print(f'  Total Stop-Loss Triggers: {total_stop_losses}')
    print(f'  Total Trailing Stop Triggers: {total_trailing_stops}')
    print(f'  Total Overbought Sells: {total_overbought}')
    
    # Save results to CSV
    df = pd.DataFrame(all_results)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"current_strategy_monthly_4months_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f'\n✅ Results saved to {output_file}')
    
    print('\n' + '='*100)


if __name__ == '__main__':
    main()

