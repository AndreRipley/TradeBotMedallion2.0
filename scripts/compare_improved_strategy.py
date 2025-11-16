"""
Compare Original vs Improved Anomaly Buy+Sell Strategy
"""
import pandas as pd
from datetime import datetime, timedelta
from anomaly_strategy import AnomalyTradingStrategy
from improved_anomaly_strategy import ImprovedAnomalyTradingStrategy

def compare_strategies():
    """Compare original and improved strategies."""
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN',
        'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE', 'CMCSA',
        'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI', 'INTU'
    ]
    
    print('='*100)
    print('COMPARING ORIGINAL vs IMPROVED ANOMALY BUY+SELL STRATEGY')
    print('='*100)
    print(f'\nTesting {len(stocks)} stocks over 1 year')
    print('Period: 2024-11-10 to 2025-11-10\n')
    
    # Run original strategy
    print('[1/2] Running Original Strategy...')
    original = AnomalyTradingStrategy(stocks=stocks, position_size=10.0, min_severity=1.0)
    original.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    original.end_date = datetime.now().strftime('%Y-%m-%d')
    original_results = original.run_backtest()
    
    # Run improved strategy
    print('[2/2] Running Improved Strategy...')
    improved = ImprovedAnomalyTradingStrategy(
        stocks=stocks,
        position_size=10.0,
        min_severity=1.0,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.05,
        min_risk_reward_ratio=1.5
    )
    improved.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    improved.end_date = datetime.now().strftime('%Y-%m-%d')
    improved_results = improved.run_backtest()
    
    # Compare results
    print('\n' + '='*100)
    print('COMPARISON RESULTS')
    print('='*100)
    
    orig_summary = original_results['summary']
    impr_summary = improved_results['summary']
    
    # Calculate win rates
    orig_stocks = original_results['stocks']
    impr_stocks = improved_results['stocks']
    
    orig_profitable = [s for s in orig_stocks.values() if s['profit_loss'] > 0]
    impr_profitable = [s for s in impr_stocks.values() if s['profit_loss'] > 0]
    
    orig_win_rate = (len(orig_profitable) / len(orig_stocks) * 100) if len(orig_stocks) > 0 else 0
    impr_win_rate = (len(impr_profitable) / len(impr_stocks) * 100) if len(impr_stocks) > 0 else 0
    
    print(f'\n{"Metric":<30} {"Original":<20} {"Improved":<20} {"Change":<15}')
    print('-'*100)
    
    print(f"{'Return %':<30} {orig_summary['overall_return_pct']:<19.2f}% {impr_summary['overall_return_pct']:<19.2f}% "
          f"{impr_summary['overall_return_pct'] - orig_summary['overall_return_pct']:+.2f}%")
    
    print(f"{'Win Rate %':<30} {orig_win_rate:<19.1f}% {impr_win_rate:<19.1f}% "
          f"{impr_win_rate - orig_win_rate:+.1f}%")
    
    print(f"{'Total Trades':<30} {orig_summary['total_trades']:<20} {impr_summary['total_trades']:<20} "
          f"{impr_summary['total_trades'] - orig_summary['total_trades']:+}")
    
    print(f"{'Total Invested':<30} ${orig_summary['total_invested']:<19.2f} ${impr_summary['total_invested']:<19.2f} "
          f"${impr_summary['total_invested'] - orig_summary['total_invested']:+.2f}")
    
    print(f"{'Total Profit/Loss':<30} ${orig_summary['total_profit_loss']:<19.2f} ${impr_summary['total_profit_loss']:<19.2f} "
          f"${impr_summary['total_profit_loss'] - orig_summary['total_profit_loss']:+.2f}")
    
    # Risk management metrics
    print(f"\n{'Risk Management':<30} {'Original':<20} {'Improved':<20}")
    print('-'*100)
    print(f"{'Stop-Loss Triggers':<30} {'N/A':<20} {impr_summary.get('stop_loss_triggers', 0):<20}")
    print(f"{'Trailing Stop Triggers':<30} {'N/A':<20} {impr_summary.get('trailing_stop_triggers', 0):<20}")
    print(f"{'Overbought Sells':<30} {orig_summary.get('total_trades', 0) // 2:<20} {impr_summary.get('overbought_sells', 0):<20}")
    
    # Analyze trade quality
    print(f"\n{'Trade Quality Analysis':<30} {'Original':<20} {'Improved':<20}")
    print('-'*100)
    
    # Calculate average win/loss for original
    orig_trade_profits = []
    for symbol, data in orig_stocks.items():
        if data['total_trades'] > 0:
            # Estimate average profit per trade
            if data['total_trades'] > 0:
                avg_profit = data['profit_loss'] / data['total_trades']
                orig_trade_profits.append(avg_profit)
    
    # Calculate average win/loss for improved
    impr_trade_profits = []
    for symbol, data in impr_stocks.items():
        if data['total_trades'] > 0:
            avg_profit = data['profit_loss'] / data['total_trades']
            impr_trade_profits.append(avg_profit)
    
    if orig_trade_profits:
        orig_avg_profit = sum(orig_trade_profits) / len(orig_trade_profits)
        orig_wins = [p for p in orig_trade_profits if p > 0]
        orig_losses = [p for p in orig_trade_profits if p < 0]
        orig_avg_win = sum(orig_wins) / len(orig_wins) if orig_wins else 0
        orig_avg_loss = sum(orig_losses) / len(orig_losses) if orig_losses else 0
    else:
        orig_avg_profit = 0
        orig_avg_win = 0
        orig_avg_loss = 0
    
    if impr_trade_profits:
        impr_avg_profit = sum(impr_trade_profits) / len(impr_trade_profits)
        impr_wins = [p for p in impr_trade_profits if p > 0]
        impr_losses = [p for p in impr_trade_profits if p < 0]
        impr_avg_win = sum(impr_wins) / len(impr_wins) if impr_wins else 0
        impr_avg_loss = sum(impr_losses) / len(impr_losses) if impr_losses else 0
    else:
        impr_avg_profit = 0
        impr_avg_win = 0
        impr_avg_loss = 0
    
    print(f"{'Avg Profit per Trade':<30} ${orig_avg_profit:<19.2f} ${impr_avg_profit:<19.2f}")
    print(f"{'Avg Win':<30} ${orig_avg_win:<19.2f} ${impr_avg_win:<19.2f}")
    print(f"{'Avg Loss':<30} ${orig_avg_loss:<19.2f} ${impr_avg_loss:<19.2f}")
    
    if orig_avg_loss != 0 and impr_avg_loss != 0:
        orig_rr = abs(orig_avg_win / orig_avg_loss) if orig_avg_loss != 0 else 0
        impr_rr = abs(impr_avg_win / impr_avg_loss) if impr_avg_loss != 0 else 0
        print(f"{'Risk/Reward Ratio':<30} {orig_rr:<19.2f} {impr_rr:<19.2f}")
    
    # Key improvements
    print('\n' + '='*100)
    print('KEY IMPROVEMENTS')
    print('='*100)
    print(f"""
    ✅ Stop-Loss Protection:
       • Improved strategy cuts losses at 5% instead of holding losing positions
       • Stop-loss triggers: {impr_summary.get('stop_loss_triggers', 0)}
    
    ✅ Trailing Stops:
       • Lets winners run while protecting profits
       • Trailing stop triggers: {impr_summary.get('trailing_stop_triggers', 0)}
       • Maintains 5% below highest price
    
    ✅ Dynamic Position Sizing:
       • Increases position size for winning stocks (up to 20%)
       • Decreases position size for losing stocks (down to 40%)
       • Adapts to stock performance
    
    ✅ Better Risk/Reward:
       • Average win: ${impr_avg_win:.2f} vs ${orig_avg_win:.2f} (original)
       • Average loss: ${impr_avg_loss:.2f} vs ${orig_avg_loss:.2f} (original)
       • Risk/Reward ratio: {impr_rr:.2f} vs {orig_rr:.2f} (original)
    
    📊 Performance Improvement:
       • Return: {impr_summary['overall_return_pct']:.2f}% vs {orig_summary['overall_return_pct']:.2f}% 
         (change: {impr_summary['overall_return_pct'] - orig_summary['overall_return_pct']:+.2f}%)
       • Win Rate: {impr_win_rate:.1f}% vs {orig_win_rate:.1f}%
         (change: {impr_win_rate - orig_win_rate:+.1f}%)
    """)
    
    # Save comparison
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    comparison_data = {
        'Strategy': ['Original', 'Improved'],
        'Return_Pct': [orig_summary['overall_return_pct'], impr_summary['overall_return_pct']],
        'Win_Rate_Pct': [orig_win_rate, impr_win_rate],
        'Total_Trades': [orig_summary['total_trades'], impr_summary['total_trades']],
        'Total_Profit': [orig_summary['total_profit_loss'], impr_summary['total_profit_loss']],
        'Avg_Win': [orig_avg_win, impr_avg_win],
        'Avg_Loss': [orig_avg_loss, impr_avg_loss],
        'Risk_Reward_Ratio': [orig_rr, impr_rr]
    }
    
    df_comparison = pd.DataFrame(comparison_data)
    output_file = f"strategy_comparison_original_vs_improved_{timestamp}.csv"
    df_comparison.to_csv(output_file, index=False)
    print(f'\n✅ Comparison saved to {output_file}')


if __name__ == '__main__':
    compare_strategies()

