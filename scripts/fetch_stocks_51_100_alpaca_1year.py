"""
Fetch stocks 51-100 by market cap at 30-minute intervals for the past 1 year using Alpaca API.
Only includes prices during market hours (9:30 AM - 4:00 PM ET).
"""
import pandas as pd
from datetime import datetime, timedelta
import pytz
from config import Config
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Stocks 51-100 by market cap (as of 2025)
STOCKS_51_100 = [
    'GE', 'AXP', 'AMAT', 'ADI', 'ISRG', 'MU', 'BLK', 'TJX', 'C', 'LMT',
    'SCHW', 'MDT', 'GILD', 'CI', 'ZTS', 'CME', 'ADP', 'ITW', 'EQIX', 'ETN',
    'WM', 'KLAC', 'APH', 'CDNS', 'SNPS', 'FTNT', 'NXPI', 'MCHP', 'CRWD', 'ANSS',
    'CTAS', 'FAST', 'PAYX', 'NDAQ', 'CPRT', 'ODFL', 'TTD', 'FDS', 'BR', 'ROL',
    'POOL', 'WST', 'ZBRA', 'VRSK', 'EXPD', 'CHRW', 'JBHT', 'CSGP', 'RBC', 'TECH'
]


def fetch_stock_alpaca_1year(symbol: str, data_client, start_date, end_date):
    """Fetch 1 year of 30-minute data for a single stock."""
    try:
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        
        print(f"   📡 Fetching {symbol}...", end=' ', flush=True)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Minute,  # 1-minute intervals (will resample)
            start=start_date.date(),
            end=end_date.date()
        )
        
        bars = data_client.get_stock_bars(request_params)
        
        if not bars or not hasattr(bars, 'data') or symbol not in bars.data:
            print(f"❌ No data")
            return None
        
        # Use the DataFrame directly
        df = bars.df
        
        if df.empty:
            print(f"❌ Empty")
            return None
        
        # Filter for symbol (in case multiple symbols)
        if 'symbol' in df.index.names:
            df = df.loc[symbol]
        
        # Reset index to get timestamp as column
        df = df.reset_index()
        
        # Find the timestamp column
        if 'timestamp' in df.columns:
            df['Datetime'] = pd.to_datetime(df['timestamp'])
        elif len(df.index) > 0 and isinstance(df.index, pd.DatetimeIndex):
            df['Datetime'] = df.index
        else:
            datetime_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
            if datetime_cols:
                df['Datetime'] = pd.to_datetime(df[datetime_cols[0]])
            else:
                print(f"❌ No timestamp column")
                return None
        
        # Set Datetime as index for resampling
        df = df.set_index('Datetime')
        
        # Resample 1-minute data to 30-minute intervals
        df_resampled = df.resample('30min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'trade_count': 'sum' if 'trade_count' in df.columns else 'first',
            'vwap': 'mean' if 'vwap' in df.columns else 'first'
        }).dropna()
        
        df = df_resampled.reset_index()
        
        # Ensure Datetime is datetime type
        if 'Datetime' not in df.columns:
            if 'timestamp' in df.columns:
                df['Datetime'] = pd.to_datetime(df['timestamp'])
            else:
                df['Datetime'] = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df.index)
        
        if not pd.api.types.is_datetime64_any_dtype(df['Datetime']):
            df['Datetime'] = pd.to_datetime(df['Datetime'])
        
        # Convert to ET timezone
        et_tz = pytz.timezone('America/New_York')
        if df['Datetime'].dt.tz is None:
            df['Datetime'] = df['Datetime'].dt.tz_localize('UTC')
        df['Datetime'] = df['Datetime'].dt.tz_convert(et_tz)
        
        # Extract date and time
        df['Date'] = df['Datetime'].dt.date
        df['Time'] = df['Datetime'].dt.time
        
        # Filter for market hours (9:30 AM - 4:00 PM ET)
        market_open = pd.Timestamp('09:30').time()
        market_close = pd.Timestamp('16:00').time()
        
        filtered_data = df[
            (df['Time'] >= market_open) & 
            (df['Time'] <= market_close)
        ].copy()
        
        if filtered_data.empty:
            print(f"❌ No market hours data")
            return None
        
        # Sort by datetime
        filtered_data = filtered_data.sort_values('Datetime')
        
        # Rename columns to match expected format
        filtered_data = filtered_data.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        # Add symbol column
        filtered_data['Symbol'] = symbol
        
        print(f"✅ {len(filtered_data)} data points")
        return filtered_data
        
    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}")
        return None


def fetch_stocks_51_100_alpaca_1year():
    """Fetch 1 year of 30-minute data for stocks 51-100."""
    
    # Check if Alpaca credentials are configured
    if not Config.ALPACA_API_KEY or not Config.ALPACA_SECRET_KEY:
        print("❌ Alpaca API credentials not configured!")
        print("   Please set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env or environment variables")
        return None
    
    # Get date range (3 years from most recent market day)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    print("=" * 80)
    print("FETCHING STOCKS 51-100 BY MARKET CAP (30-MINUTE INTERVALS) - 2 YEARS")
    print("Using: Alpaca API")
    print("=" * 80)
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Interval: 30 minutes")
    print(f"Market Hours: 9:30 AM - 4:00 PM ET")
    print(f"Stocks: {len(STOCKS_51_100)} stocks")
    print()
    
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        
        # Initialize Alpaca data client
        data_client = StockHistoricalDataClient(
            api_key=Config.ALPACA_API_KEY,
            secret_key=Config.ALPACA_SECRET_KEY
        )
        
        print("📡 Fetching data from Alpaca API...")
        print("   (This will take several minutes for 50 stocks)...")
        print()
        
        all_data = []
        successful = []
        failed = []
        
        for i, symbol in enumerate(STOCKS_51_100, 1):
            print(f"[{i}/{len(STOCKS_51_100)}] {symbol}:", end=' ')
            
            data = fetch_stock_alpaca_1year(symbol, data_client, start_date, end_date)
            
            if data is not None:
                all_data.append(data)
                successful.append(symbol)
            else:
                failed.append(symbol)
        
        if not all_data:
            print("\n❌ No data fetched for any stocks")
            return None
        
        # Combine all data
        print()
        print("=" * 80)
        print("COMBINING DATA")
        print("=" * 80)
        print(f"Combining data from {len(all_data)} stocks...")
        
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Sort by symbol and datetime
        combined_df = combined_df.sort_values(['Symbol', 'Datetime'])
        
        print(f"✅ Combined {len(combined_df)} total data points")
        
        # Display summary
        print()
        print("=" * 80)
        print("FETCH SUMMARY")
        print("=" * 80)
        print(f"✅ Successful: {len(successful)} stocks")
        print(f"❌ Failed: {len(failed)} stocks")
        
        if successful:
            print(f"\n✅ Successfully fetched:")
            for i, sym in enumerate(successful, 1):
                print(f"   {i:2d}. {sym}", end='  ')
                if i % 5 == 0:
                    print()
            if len(successful) % 5 != 0:
                print()
        
        if failed:
            print(f"\n❌ Failed to fetch:")
            for sym in failed:
                print(f"   - {sym}")
        
        # Statistics by stock
        print()
        print("=" * 80)
        print("DATA STATISTICS BY STOCK")
        print("=" * 80)
        
        stats_list = []
        for symbol in successful:
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
        
        # Save combined data
        output_file = f"stocks_51_100_30min_2years_alpaca_{end_date.strftime('%Y%m%d')}.csv"
        combined_df.to_csv(output_file, index=False)
        print()
        print(f"✅ Combined data saved to: {output_file}")
        print(f"   Total rows: {len(combined_df):,}")
        
        # Also save individual files per stock
        output_dir = f"stocks_51_100_30min_2years_alpaca_{end_date.strftime('%Y%m%d')}"
        os.makedirs(output_dir, exist_ok=True)
        
        print()
        print(f"📁 Saving individual stock files to: {output_dir}/")
        
        for symbol in successful:
            stock_data = combined_df[combined_df['Symbol'] == symbol]
            if not stock_data.empty:
                stock_file = os.path.join(output_dir, f"{symbol}_30min_1year.csv")
                stock_data.to_csv(stock_file, index=False)
        
        print(f"✅ Saved {len(successful)} individual stock files")
        
        return combined_df
        
    except ImportError:
        print("❌ alpaca-py not installed!")
        print("   Install with: pip install alpaca-py")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    data = fetch_stocks_51_100_alpaca_1year()
    
    if data is not None:
        print()
        print("=" * 80)
        print("✅ Data fetch complete!")
        print("=" * 80)
    else:
        print()
        print("❌ Failed to fetch data. Please check:")
        print("   1. Alpaca API credentials are configured")
        print("   2. alpaca-py is installed: pip install alpaca-py")
        print("   3. Your Alpaca account has data access")

