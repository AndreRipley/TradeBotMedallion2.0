"""
Backtest Current Improved Anomaly Strategy for 3 Months
Uses the same configuration as the live trading bot
"""
import pandas as pd
from datetime import datetime, timedelta
from improved_anomaly_strategy import ImprovedAnomalyTradingStrategy
from config import Config


def main():
    """Run 3-month backtest of current strategy."""
    # Use the full 30-stock list from default configuration
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN'
    ]
    
    # Use the same position size as the live bot
    position_size = Config.POSITION_SIZE
    
    print('='*100)
    print('CURRENT STRATEGY - 3 MONTH BACKTEST')
    print('='*100)
    print(f'\nStrategy: Improved Anomaly Buy+Sell Strategy')
    print(f'Features: Stop-losses (5%), Trailing stops (5%), Dynamic position sizing')
    print(f'Stocks: {len(stocks)} stocks')
    print(f'Position Size: ${position_size:.2f} per trade')
    print(f'Minimum Severity: 1.0')
    print(f'Period: 3 months (90 days)')
    print(f'Execution: Market hours (near close ~3:45 PM) - Realistic intraday pricing')
    
    # Calculate dates
    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)
    
    print(f'\nBacktest Period: {start_date.strftime("%Y-%m-%d")} to {end_date.strftime("%Y-%m-%d")}')
    print(f'Stocks: {len(stocks)} stocks ({", ".join(stocks[:10])}... and {len(stocks)-10} more)')
    print('\n' + '='*100)
    print('Running backtest...')
    print('='*100)
    
    # Initialize strategy with current bot settings
    strategy = ImprovedAnomalyTradingStrategy(
        stocks=stocks,
        position_size=position_size,
        min_severity=1.0,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.05,
        min_risk_reward_ratio=1.5
    )
    strategy.start_date = start_date.strftime('%Y-%m-%d')
    strategy.end_date = end_date.strftime('%Y-%m-%d')
    
    # Run backtest
    results = strategy.run_backtest()
    
    # Calculate win rate
    stocks_data = results['stocks']
    profitable = [s for s in stocks_data.values() if s['profit_loss'] > 0]
    win_rate = (len(profitable) / len(stocks_data) * 100) if len(stocks_data) > 0 else 0
    
    summary = results['summary']
    
    # Display results
    print('\n' + '='*100)
    print('BACKTEST RESULTS - 3 MONTHS')
    print('='*100)
    
    print(f'\n📊 Overall Performance:')
    print(f'  Return: {summary["overall_return_pct"]:.2f}%')
    print(f'  Win Rate: {win_rate:.1f}% ({len(profitable)}/{len(stocks_data)} stocks profitable)')
    print(f'  Total Trades: {summary["total_trades"]:,}')
    print(f'  Buy Trades: {sum(s.get("buy_trades", 0) for s in stocks_data.values()):,}')
    print(f'  Sell Trades: {sum(s.get("sell_trades", 0) for s in stocks_data.values()):,}')
    
    print(f'\n💰 Financial Summary:')
    print(f'  Total Invested: ${summary["total_invested"]:,.2f}')
    print(f'  Total Value: ${summary["total_value"]:,.2f}')
    print(f'  Total Profit/Loss: ${summary["total_profit_loss"]:,.2f}')
    
    # Calculate annualized return
    annualized = ((1 + summary["overall_return_pct"]/100) ** (365/90) - 1) * 100
    print(f'  Annualized Return: {annualized:.2f}%')
    
    print(f'\n🛡️  Risk Management:')
    print(f'  Stop-Loss Triggers: {summary.get("stop_loss_triggers", 0)}')
    print(f'  Trailing Stop Triggers: {summary.get("trailing_stop_triggers", 0)}')
    print(f'  Overbought Sells: {summary.get("overbought_sells", 0)}')
    
    # Top performers
    if stocks_data:
        sorted_stocks = sorted(stocks_data.items(), key=lambda x: x[1]['profit_loss'], reverse=True)
        print(f'\n📈 Top 10 Performers:')
        for i, (symbol, data) in enumerate(sorted_stocks[:10], 1):
            profit_pct = (data['profit_loss'] / data['total_invested'] * 100) if data['total_invested'] > 0 else 0
            print(f'  {i}. {symbol}: ${data["profit_loss"]:.2f} ({profit_pct:.2f}%)')
        
        print(f'\n📉 Bottom 10 Performers:')
        for i, (symbol, data) in enumerate(sorted_stocks[-10:], 1):
            profit_pct = (data['profit_loss'] / data['total_invested'] * 100) if data['total_invested'] > 0 else 0
            print(f'  {i}. {symbol}: ${data["profit_loss"]:.2f} ({profit_pct:.2f}%)')
    
    # Save results to CSV
    result_data = {
        'period': '3 Months',
        'days': 90,
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
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
        'overbought_sells': summary.get('overbought_sells', 0),
        'annualized_return_pct': annualized
    }
    
    df = pd.DataFrame([result_data])
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"current_strategy_3month_{timestamp}.csv"
    df.to_csv(output_file, index=False)
    print(f'\n✅ Results saved to {output_file}')
    
    print('\n' + '='*100)


if __name__ == '__main__':
    main()

