"""
Show when buy and sell trades occurred during the backtest
"""
import pandas as pd
from datetime import datetime, timedelta
from improved_anomaly_strategy import ImprovedAnomalyTradingStrategy
from config import Config

def show_trades_for_period(stocks, position_size, start_date, end_date, period_name):
    """Show trades for a specific period."""
    print(f'\n{"="*100}')
    print(f'{period_name.upper()} - TRADE DATES')
    print(f'{"="*100}')
    
    strategy = ImprovedAnomalyTradingStrategy(
        stocks=stocks,
        position_size=position_size,
        min_severity=1.0,
        stop_loss_pct=0.05,
        trailing_stop_pct=0.05,
        min_risk_reward_ratio=1.5
    )
    strategy.start_date = start_date
    strategy.end_date = end_date
    
    all_trades = []
    
    for symbol in stocks:
        symbol = symbol.strip().upper()
        result = strategy.backtest_strategy(symbol)
        trades = result.get('trades', [])
        
        for trade in trades:
            trade['symbol'] = symbol
            all_trades.append(trade)
    
    if not all_trades:
        print(f'No trades found for {period_name}')
        return
    
    # Convert to DataFrame for easier analysis
    df = pd.DataFrame(all_trades)
    df['date'] = pd.to_datetime(df['date'])
    
    # Group by date and type
    print(f'\n📊 Trade Summary by Date:')
    print(f'{"Date":<12} {"BUY":<8} {"SELL":<8} {"Total":<8}')
    print('-' * 40)
    
    daily_summary = df.groupby(['date', 'type']).size().unstack(fill_value=0)
    for date in sorted(daily_summary.index):
        buy_count = daily_summary.loc[date, 'BUY'] if 'BUY' in daily_summary.columns else 0
        sell_count = daily_summary.loc[date, 'SELL'] if 'SELL' in daily_summary.columns else 0
        total = buy_count + sell_count
        print(f'{date.strftime("%Y-%m-%d"):<12} {buy_count:<8} {sell_count:<8} {total:<8}')
    
    # Show first 20 trades
    print(f'\n📈 First 20 Trades:')
    print(f'{"Date":<12} {"Symbol":<8} {"Type":<8} {"Reason":<20} {"Price":<10}')
    print('-' * 70)
    
    df_sorted = df.sort_values('date')
    for idx, trade in df_sorted.head(20).iterrows():
        reason = trade.get('reason', '')
        if not reason:
            reason = trade.get('anomaly_types', 'N/A')
        if isinstance(reason, str):
            reason = reason[:18]
        else:
            reason = 'N/A'
        print(f'{trade["date"].strftime("%Y-%m-%d"):<12} {trade["symbol"]:<8} {trade["type"]:<8} {reason:<20} ${trade["price"]:<9.2f}')
    
    # Monthly breakdown
    print(f'\n📅 Monthly Breakdown:')
    df['month'] = df['date'].dt.to_period('M')
    monthly = df.groupby(['month', 'type']).size().unstack(fill_value=0)
    print(f'{"Month":<12} {"BUY":<8} {"SELL":<8} {"Total":<8}')
    print('-' * 40)
    for month in sorted(monthly.index):
        buy_count = monthly.loc[month, 'BUY'] if 'BUY' in monthly.columns else 0
        sell_count = monthly.loc[month, 'SELL'] if 'SELL' in monthly.columns else 0
        total = buy_count + sell_count
        print(f'{str(month):<12} {buy_count:<8} {sell_count:<8} {total:<8}')

def main():
    """Show trade dates for the 4-month backtest period."""
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN'
    ]
    
    position_size = Config.POSITION_SIZE
    
    # July 2024
    show_trades_for_period(
        stocks, position_size,
        '2024-06-01', '2024-07-31',
        'July 2024'
    )
    
    # August 2024
    show_trades_for_period(
        stocks, position_size,
        '2024-07-01', '2024-08-31',
        'August 2024'
    )
    
    # September 2024
    show_trades_for_period(
        stocks, position_size,
        '2024-08-01', '2024-09-30',
        'September 2024'
    )
    
    # October 2024
    show_trades_for_period(
        stocks, position_size,
        '2024-09-01', '2024-10-31',
        'October 2024'
    )

if __name__ == '__main__':
    main()

