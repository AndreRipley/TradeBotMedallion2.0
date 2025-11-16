"""
Analyze Anomaly Buy+Sell Strategy Trade Patterns
Understanding why win rate is high but return is low
"""
import pandas as pd
import numpy as np
from anomaly_strategy import AnomalyTradingStrategy
from datetime import datetime, timedelta

def analyze_trade_patterns():
    """Analyze trade patterns to understand win rate vs return discrepancy."""
    # Top 50 stocks
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN',
        'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE', 'CMCSA',
        'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI', 'INTU'
    ]
    
    print('='*100)
    print('ANALYZING ANOMALY BUY+SELL STRATEGY TRADE PATTERNS')
    print('='*100)
    print('Understanding why win rate is 90% but return is only 3.34%\n')
    
    strategy = AnomalyTradingStrategy(stocks=stocks, position_size=10.0, min_severity=1.0)
    strategy.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
    strategy.end_date = datetime.now().strftime('%Y-%m-%d')
    
    results = strategy.run_backtest()
    
    # Analyze trade patterns
    all_buy_trades = []
    all_sell_trades = []
    trade_pairs = []  # Match buys with sells
    
    for symbol, data in results['stocks'].items():
        trades = data['trades']
        buys = [t for t in trades if t['type'] == 'BUY']
        sells = [t for t in trades if t['type'] == 'SELL']
        
        all_buy_trades.extend(buys)
        all_sell_trades.extend(sells)
        
        # Try to match buys with sells (FIFO)
        buy_queue = []
        for trade in trades:
            if trade['type'] == 'BUY':
                buy_queue.append({
                    'date': trade['date'],
                    'price': trade['price'],
                    'shares': trade['shares'],
                    'cost': trade['cost']
                })
            elif trade['type'] == 'SELL':
                if buy_queue:
                    # Match with oldest buy
                    buy = buy_queue.pop(0)
                    profit = (trade['price'] - buy['price']) * trade['shares']
                    profit_pct = ((trade['price'] - buy['price']) / buy['price']) * 100
                    trade_pairs.append({
                        'symbol': symbol,
                        'buy_date': buy['date'],
                        'sell_date': trade['date'],
                        'buy_price': buy['price'],
                        'sell_price': trade['price'],
                        'shares': trade['shares'],
                        'profit': profit,
                        'profit_pct': profit_pct,
                        'hold_days': (datetime.strptime(trade['date'], '%Y-%m-%d') - 
                                     datetime.strptime(buy['date'], '%Y-%m-%d')).days
                    })
    
    # Calculate statistics
    print('\n📊 TRADE STATISTICS:')
    print('-'*100)
    print(f"Total Buy Trades: {len(all_buy_trades):,}")
    print(f"Total Sell Trades: {len(all_sell_trades):,}")
    print(f"Matched Trade Pairs: {len(trade_pairs):,}")
    print(f"Unmatched Buys: {len(all_buy_trades) - len(trade_pairs):,}")
    
    if trade_pairs:
        df_pairs = pd.DataFrame(trade_pairs)
        
        # Profit analysis
        profitable_trades = df_pairs[df_pairs['profit'] > 0]
        losing_trades = df_pairs[df_pairs['profit'] < 0]
        
        print(f"\n💰 PROFIT ANALYSIS:")
        print('-'*100)
        print(f"Profitable Trades: {len(profitable_trades):,} ({len(profitable_trades)/len(df_pairs)*100:.1f}%)")
        print(f"Losing Trades: {len(losing_trades):,} ({len(losing_trades)/len(df_pairs)*100:.1f}%)")
        
        if len(profitable_trades) > 0:
            print(f"\nAverage Profit per Winning Trade: ${profitable_trades['profit'].mean():.2f}")
            print(f"Average Return % per Winning Trade: {profitable_trades['profit_pct'].mean():.2f}%")
            print(f"Median Profit per Winning Trade: ${profitable_trades['profit'].median():.2f}")
            print(f"Median Return % per Winning Trade: {profitable_trades['profit_pct'].median():.2f}%")
            print(f"Max Profit: ${profitable_trades['profit'].max():.2f} ({profitable_trades.loc[profitable_trades['profit'].idxmax(), 'profit_pct']:.2f}%)")
        
        if len(losing_trades) > 0:
            print(f"\nAverage Loss per Losing Trade: ${losing_trades['profit'].mean():.2f}")
            print(f"Average Return % per Losing Trade: {losing_trades['profit_pct'].mean():.2f}%")
            print(f"Median Loss per Losing Trade: ${losing_trades['profit'].median():.2f}")
            print(f"Median Return % per Losing Trade: {losing_trades['profit_pct'].median():.2f}%")
            print(f"Max Loss: ${losing_trades['profit'].min():.2f} ({losing_trades.loc[losing_trades['profit'].idxmin(), 'profit_pct']:.2f}%)")
        
        # Hold time analysis
        print(f"\n⏱️  HOLD TIME ANALYSIS:")
        print('-'*100)
        print(f"Average Hold Time: {df_pairs['hold_days'].mean():.1f} days")
        print(f"Median Hold Time: {df_pairs['hold_days'].median():.1f} days")
        print(f"Min Hold Time: {df_pairs['hold_days'].min()} days")
        print(f"Max Hold Time: {df_pairs['hold_days'].max()} days")
        
        if len(profitable_trades) > 0:
            print(f"\nAverage Hold Time (Winners): {profitable_trades['hold_days'].mean():.1f} days")
        if len(losing_trades) > 0:
            print(f"Average Hold Time (Losers): {losing_trades['hold_days'].mean():.1f} days")
        
        # Profit distribution
        print(f"\n📈 PROFIT DISTRIBUTION:")
        print('-'*100)
        print(f"Total Profit from All Trades: ${df_pairs['profit'].sum():.2f}")
        print(f"Total Profit from Winners: ${profitable_trades['profit'].sum():.2f}")
        print(f"Total Loss from Losers: ${losing_trades['profit'].sum():.2f}")
        
        # Small wins vs large losses
        small_wins = profitable_trades[profitable_trades['profit'] < 1.0]
        large_wins = profitable_trades[profitable_trades['profit'] >= 5.0]
        large_losses = losing_trades[abs(losing_trades['profit']) >= 5.0]
        
        print(f"\n🔍 WIN/LOSS BREAKDOWN:")
        print('-'*100)
        print(f"Small Wins (< $1): {len(small_wins):,} trades, Total: ${small_wins['profit'].sum():.2f}")
        print(f"Large Wins (>= $5): {len(large_wins):,} trades, Total: ${large_wins['profit'].sum():.2f}")
        print(f"Large Losses (<= -$5): {len(large_losses):,} trades, Total: ${large_losses['profit'].sum():.2f}")
        
        # Early exit analysis
        early_exits = df_pairs[df_pairs['hold_days'] <= 5]
        late_exits = df_pairs[df_pairs['hold_days'] > 20]
        
        print(f"\n🚪 EXIT TIMING ANALYSIS:")
        print('-'*100)
        if len(early_exits) > 0:
            early_profitable = early_exits[early_exits['profit'] > 0]
            print(f"Early Exits (<= 5 days): {len(early_exits):,} trades")
            print(f"  • Profitable: {len(early_profitable):,} ({len(early_profitable)/len(early_exits)*100:.1f}%)")
            print(f"  • Average Profit: ${early_exits['profit'].mean():.2f}")
            print(f"  • Total Profit: ${early_exits['profit'].sum():.2f}")
        
        if len(late_exits) > 0:
            late_profitable = late_exits[late_exits['profit'] > 0]
            print(f"\nLate Exits (> 20 days): {len(late_exits):,} trades")
            print(f"  • Profitable: {len(late_profitable):,} ({len(late_profitable)/len(late_exits)*100:.1f}%)")
            print(f"  • Average Profit: ${late_exits['profit'].mean():.2f}")
            print(f"  • Total Profit: ${late_exits['profit'].sum():.2f}")
    
    # Stock-level analysis
    print(f"\n📊 STOCK-LEVEL ANALYSIS:")
    print('-'*100)
    stock_stats = []
    for symbol, data in results['stocks'].items():
        if data['total_trades'] > 0:
            stock_stats.append({
                'Symbol': symbol,
                'Total_Trades': data['total_trades'],
                'Buy_Trades': data.get('buy_trades', 0),
                'Sell_Trades': data.get('sell_trades', 0),
                'Invested': data['total_invested'],
                'Total_Value': data.get('total_value', data['current_value']),
                'Profit': data['profit_loss'],
                'Return_Pct': data['return_pct'],
                'Shares_Remaining': data.get('shares_owned', 0)
            })
    
    df_stocks = pd.DataFrame(stock_stats)
    df_stocks = df_stocks.sort_values('Return_Pct', ascending=False)
    
    print(f"\nTop 10 Performers:")
    print(f"{'Symbol':<8} {'Return %':<12} {'Profit':<12} {'Trades':<8} {'Sell/Buy':<10}")
    print('-'*60)
    for _, row in df_stocks.head(10).iterrows():
        sell_buy_ratio = row['Sell_Trades'] / row['Buy_Trades'] if row['Buy_Trades'] > 0 else 0
        print(f"{row['Symbol']:<8} {row['Return_Pct']:<11.2f}% ${row['Profit']:<11.2f} {row['Total_Trades']:<8} {sell_buy_ratio:.2f}")
    
    print(f"\nBottom 10 Performers:")
    print(f"{'Symbol':<8} {'Return %':<12} {'Profit':<12} {'Trades':<8} {'Sell/Buy':<10}")
    print('-'*60)
    for _, row in df_stocks.tail(10).iterrows():
        sell_buy_ratio = row['Sell_Trades'] / row['Buy_Trades'] if row['Buy_Trades'] > 0 else 0
        print(f"{row['Symbol']:<8} {row['Return_Pct']:<11.2f}% ${row['Profit']:<11.2f} {row['Total_Trades']:<8} {sell_buy_ratio:.2f}")
    
    # Key insights
    print(f"\n💡 KEY INSIGHTS:")
    print('='*100)
    print("""
    WHY HIGH WIN RATE BUT LOW RETURN?
    
    1. EARLY PROFIT TAKING:
       • Strategy sells on overbought signals (RSI > 70, price spikes)
       • This cuts winners short, taking small profits instead of letting them run
       • Many small wins (< $1) but few large wins
    
    2. HOLDING LOSERS:
       • Strategy only sells on overbought signals
       • If a stock doesn't become overbought after buying, it holds the position
       • Losing positions may not trigger sell signals, leading to larger losses
    
    3. WIN RATE vs RETURN MISMATCH:
       • Win rate measures: How many stocks ended profitable?
       • Return measures: How much money was made/lost?
       • High win rate (90%) means most stocks were profitable
       • Low return (3.34%) means profits were small relative to losses
    
    4. THE PROBLEM:
       • Taking profits too early (cutting winners)
       • Not cutting losses quickly enough (letting losers run)
       • Classic "cutting winners, letting losers run" pattern
    """)


if __name__ == '__main__':
    analyze_trade_patterns()

