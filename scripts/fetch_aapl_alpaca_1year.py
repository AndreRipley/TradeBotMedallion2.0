"""
Fetch Apple (AAPL) stock prices at 30-minute intervals for the past 1 year using Alpaca API.
Only includes prices during market hours (9:30 AM - 4:00 PM ET).
"""
import pandas as pd
from datetime import datetime, timedelta
import pytz
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def fetch_aapl_alpaca_1year():
    """Fetch AAPL prices at 30-minute intervals for the past 1 year using Alpaca."""
    
    # Check if Alpaca credentials are configured
    if not Config.ALPACA_API_KEY or not Config.ALPACA_SECRET_KEY:
        print("❌ Alpaca API credentials not configured!")
        print("   Please set ALPACA_API_KEY and ALPACA_SECRET_KEY in .env or environment variables")
        return None
    
    # Get date range (1 year from most recent market day)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print("=" * 80)
    print("FETCHING AAPL STOCK PRICES (30-MINUTE INTERVALS) - 1 YEAR")
    print("Using: Alpaca API")
    print("=" * 80)
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Interval: 30 minutes")
    print(f"Market Hours: 9:30 AM - 4:00 PM ET")
    print()
    
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        
        # Initialize Alpaca data client
        data_client = StockHistoricalDataClient(
            api_key=Config.ALPACA_API_KEY,
            secret_key=Config.ALPACA_SECRET_KEY
        )
        
        print("📡 Fetching data from Alpaca API...")
        print("   (This may take a minute for 1 year of data)...")
        
        # Fetch 1-minute bars for AAPL (Alpaca limitation - will resample to 30min)
        # Alpaca requires dates in ISO format
        print("   Note: Fetching 1-minute data, will resample to 30-minute intervals...")
        
        request_params = StockBarsRequest(
            symbol_or_symbols=["AAPL"],
            timeframe=TimeFrame.Minute,  # 1-minute intervals (will resample)
            start=start_date.date(),
            end=end_date.date()
        )
        
        bars = data_client.get_stock_bars(request_params)
        
        # Check if data was returned
        if not bars or not hasattr(bars, 'data') or 'AAPL' not in bars.data:
            print("❌ No data returned from Alpaca")
            if hasattr(bars, 'data'):
                print(f"   Available symbols: {list(bars.data.keys())}")
            return None
        
        # Use the DataFrame directly (easier than iterating bars)
        df = bars.df
        
        if df.empty:
            print("❌ Empty DataFrame returned")
            return None
        
        # Filter for AAPL (in case multiple symbols)
        if 'symbol' in df.index.names:
            df = df.loc['AAPL']
        
        print(f"✅ Fetched {len(df)} 1-minute bars from Alpaca")
        print(f"   Resampling to 30-minute intervals...")
        
        # The DataFrame from Alpaca has MultiIndex (symbol, timestamp)
        # Reset index to get timestamp as column
        df = df.reset_index()
        
        # Check what columns we have
        print(f"   DataFrame columns after reset: {list(df.columns)}")
        
        # Find the timestamp column (could be 'timestamp' or in index)
        if 'timestamp' in df.columns:
            df['Datetime'] = pd.to_datetime(df['timestamp'])
        elif len(df.index) > 0 and isinstance(df.index, pd.DatetimeIndex):
            df['Datetime'] = df.index
        else:
            # Check if there's a datetime column already
            datetime_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
            if datetime_cols:
                df['Datetime'] = pd.to_datetime(df[datetime_cols[0]])
            else:
                print(f"   Available columns: {list(df.columns)}")
                raise ValueError("Could not find timestamp column")
        
        # Set Datetime as index for resampling
        df = df.set_index('Datetime')
        
        # Resample 1-minute data to 30-minute intervals
        # Use OHLC aggregation: Open=first, High=max, Low=min, Close=last, Volume=sum
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
        
        print(f"✅ Resampled to {len(df)} 30-minute intervals")
        
        if df.empty:
            print("❌ No data in DataFrame")
            return None
        
        # After reset_index(), Datetime is already a column (from the index)
        # Just ensure it's a datetime type
        if 'Datetime' not in df.columns:
            # If Datetime is not a column, check for timestamp
            if 'timestamp' in df.columns:
                df['Datetime'] = pd.to_datetime(df['timestamp'])
            else:
                # Use index if it's datetime
                df['Datetime'] = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df.index)
        
        # Ensure Datetime is datetime type
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
        
        # Remove timestamp column if it exists (we're using Datetime now)
        if 'timestamp' in df.columns:
            df = df.drop(columns=['timestamp'])
        
        # Filter for market hours (9:30 AM - 4:00 PM ET)
        market_open = pd.Timestamp('09:30').time()
        market_close = pd.Timestamp('16:00').time()
        
        filtered_data = df[
            (df['Time'] >= market_open) & 
            (df['Time'] <= market_close)
        ].copy()
        
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
        
        # Display results
        print()
        print("=" * 80)
        print("AAPL PRICE DATA SUMMARY")
        print("=" * 80)
        print(f"✅ Found {len(filtered_data)} data points")
        print(f"Date Range: {filtered_data['Date'].min()} to {filtered_data['Date'].max()}")
        print(f"Trading Days: {filtered_data['Date'].nunique()}")
        print(f"Average Data Points Per Day: {len(filtered_data) / filtered_data['Date'].nunique():.1f}")
        
        print()
        print("=" * 80)
        print("PRICE STATISTICS")
        print("=" * 80)
        print(f"Average Price: ${filtered_data['Close'].mean():.2f}")
        print(f"High Price: ${filtered_data['High'].max():.2f}")
        print(f"Low Price: ${filtered_data['Low'].min():.2f}")
        print(f"Price Range: ${filtered_data['High'].max() - filtered_data['Low'].min():.2f}")
        print(f"Total Volume: {int(filtered_data['Volume'].sum()):,}")
        
        # Show sample of data
        print()
        print("=" * 80)
        print("SAMPLE DATA (First 20 rows)")
        print("=" * 80)
        
        display_cols = ['Datetime', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']
        print(filtered_data[display_cols].head(20).to_string(index=False))
        
        # Show data by date (sample)
        print()
        print("=" * 80)
        print("DATA BY DATE (Sample - First 5 days)")
        print("=" * 80)
        
        for i, (date, group) in enumerate(filtered_data.groupby('Date')):
            if i >= 5:
                break
            print(f"\n📅 {date} ({pd.Timestamp(date).strftime('%A')}) - {len(group)} data points")
            print("-" * 80)
            print(f"{'Time (ET)':<12} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<15}")
            print("-" * 80)
            for _, row in group.head(5).iterrows():
                time_str = row['Time'].strftime('%H:%M')
                print(f"{time_str:<12} ${row['Open']:<9.2f} ${row['High']:<9.2f} "
                      f"${row['Low']:<9.2f} ${row['Close']:<9.2f} {int(row['Volume']):<15,}")
            if len(group) > 5:
                print(f"... and {len(group) - 5} more intervals")
        
        # Save to CSV
        output_file = f"aapl_30min_1year_alpaca_{end_date.strftime('%Y%m%d')}.csv"
        
        # Prepare data for CSV (select relevant columns)
        csv_data = filtered_data[['Datetime', 'Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']].copy()
        csv_data['Datetime'] = csv_data['Datetime'].dt.strftime('%Y-%m-%d %H:%M:%S %Z')
        csv_data['Time'] = csv_data['Time'].astype(str)
        csv_data['Date'] = csv_data['Date'].astype(str)
        
        csv_data.to_csv(output_file, index=False)
        print()
        print(f"✅ Data saved to: {output_file}")
        print(f"   Total rows: {len(filtered_data)}")
        
        return filtered_data
        
    except ImportError:
        print("❌ alpaca-py not installed!")
        print("   Install with: pip install alpaca-py")
        return None
    except Exception as e:
        print(f"❌ Error fetching data from Alpaca: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    data = fetch_aapl_alpaca_1year()
    
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

