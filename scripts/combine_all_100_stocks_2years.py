"""
Combine all 2-year stock data files into one CSV with all 100 stocks.
"""
import pandas as pd
import glob
import os
from datetime import datetime

def combine_all_2year_data():
    """Combine all 2-year CSV files into one."""
    
    print("=" * 80)
    print("COMBINING ALL 100 STOCKS - 2 YEARS DATA")
    print("=" * 80)
    print()
    
    # Find all 2-year CSV files (excluding the full files if they exist)
    pattern = "*2years_alpaca*.csv"
    files = glob.glob(pattern)
    
    # Exclude the full combined files if they exist, but include all batch files
    files = [f for f in files if 'all_100_stocks' not in f]
    
    # Sort files to ensure consistent order
    files = sorted(files)
    
    if not files:
        print("❌ No 2-year CSV files found!")
        return None
    
    print(f"📁 Found {len(files)} CSV files to combine:")
    for f in sorted(files):
        print(f"   - {f}")
    print()
    
    # Read and combine all files
    print("📖 Reading CSV files...")
    all_dataframes = []
    
    for file in sorted(files):
        try:
            df = pd.read_csv(file)
            print(f"   ✅ {file}: {len(df):,} rows, {df['Symbol'].nunique()} stocks")
            all_dataframes.append(df)
        except Exception as e:
            print(f"   ❌ Error reading {file}: {e}")
            continue
    
    if not all_dataframes:
        print("❌ No data to combine!")
        return None
    
    print()
    print("🔄 Combining data...")
    combined_df = pd.concat(all_dataframes, ignore_index=True)
    
    print(f"   Total rows before deduplication: {len(combined_df):,}")
    
    # Remove duplicates (in case any stocks appear in multiple files)
    # Based on Symbol and Datetime
    initial_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=['Symbol', 'Datetime'], keep='first')
    duplicates_removed = initial_count - len(combined_df)
    
    if duplicates_removed > 0:
        print(f"   Removed {duplicates_removed:,} duplicate rows")
    
    # Sort by Symbol and Datetime
    combined_df = combined_df.sort_values(['Symbol', 'Datetime'])
    
    print(f"   Total rows after deduplication: {len(combined_df):,}")
    print()
    
    # Get unique stocks
    unique_stocks = combined_df['Symbol'].unique()
    num_stocks = len(unique_stocks)
    
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Total Stocks: {num_stocks}")
    print(f"✅ Total Data Points: {len(combined_df):,}")
    print(f"✅ Date Range: {combined_df['Date'].min()} to {combined_df['Date'].max()}")
    print(f"✅ Trading Days: {combined_df['Date'].nunique()}")
    print()
    
    # Show stocks by group
    print("📊 Stocks by group:")
    
    # Top 50 stocks (from the original list)
    top50_list = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'V', 'UNH',
        'XOM', 'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX',
        'MRK', 'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT',
        'ACN', 'NKE', 'LIN', 'DHR', 'VZ', 'TXN', 'PM', 'NEE', 'HON', 'UPS',
        'QCOM', 'RTX', 'BMY', 'AMGN', 'SPGI', 'DE', 'LOW', 'INTU', 'BKNG', 'SBUX'
    ]
    
    stocks_51_100_list = [
        'GE', 'AXP', 'AMAT', 'ADI', 'ISRG', 'MU', 'BLK', 'TJX', 'C', 'LMT',
        'SCHW', 'MDT', 'GILD', 'CI', 'ZTS', 'CME', 'ADP', 'ITW', 'EQIX', 'ETN',
        'WM', 'KLAC', 'APH', 'CDNS', 'SNPS', 'FTNT', 'NXPI', 'MCHP', 'CRWD', 'ANSS',
        'CTAS', 'FAST', 'PAYX', 'NDAQ', 'CPRT', 'ODFL', 'TTD', 'FDS', 'BR', 'ROL',
        'POOL', 'WST', 'ZBRA', 'VRSK', 'EXPD', 'CHRW', 'JBHT', 'CSGP', 'RBC', 'TECH'
    ]
    
    top50_in_data = [s for s in top50_list if s in unique_stocks]
    stocks_51_100_in_data = [s for s in stocks_51_100_list if s in unique_stocks]
    
    print(f"   Top 50 stocks: {len(top50_in_data)}/{len(top50_list)}")
    print(f"   Stocks 51-100: {len(stocks_51_100_in_data)}/{len(stocks_51_100_list)}")
    print()
    
    # Check for missing stocks
    all_expected = set(top50_list + stocks_51_100_list)
    missing = all_expected - set(unique_stocks)
    
    if missing:
        print(f"⚠️  Missing stocks ({len(missing)}): {', '.join(sorted(missing))}")
        print()
    
    # Statistics by stock
    print("=" * 80)
    print("DATA STATISTICS BY STOCK")
    print("=" * 80)
    
    stats_list = []
    for symbol in sorted(unique_stocks):
        stock_data = combined_df[combined_df['Symbol'] == symbol]
        if not stock_data.empty:
            stats_list.append({
                'Symbol': symbol,
                'Data Points': len(stock_data),
                'Date Range': f"{stock_data['Date'].min()} to {stock_data['Date'].max()}",
                'Trading Days': stock_data['Date'].nunique(),
                'Avg Price': f"${stock_data['Close'].mean():.2f}",
                'High': f"${stock_data['High'].max():.2f}",
                'Low': f"${stock_data['Low'].min():.2f}",
                'Total Volume': f"{int(stock_data['Volume'].sum()):,}"
            })
    
    stats_df = pd.DataFrame(stats_list)
    print(stats_df.to_string(index=False))
    
    # Save combined file
    output_file = f"all_100_stocks_30min_2years_alpaca_{datetime.now().strftime('%Y%m%d')}.csv"
    combined_df.to_csv(output_file, index=False)
    
    print()
    print("=" * 80)
    print("✅ COMBINED FILE CREATED")
    print("=" * 80)
    print(f"📄 File: {output_file}")
    print(f"   Total rows: {len(combined_df):,}")
    print(f"   Total stocks: {num_stocks}")
    print(f"   File size: {os.path.getsize(output_file) / (1024*1024):.1f} MB")
    print()
    
    return combined_df


if __name__ == '__main__':
    df = combine_all_2year_data()
    
    if df is not None:
        print("=" * 80)
        print("✅ All done!")
        print("=" * 80)
    else:
        print()
        print("❌ Failed to combine files")

