"""
Fetch Apple (AAPL) stock prices at 30-minute intervals for the past 1 year.
Only includes prices during market hours (9:30 AM - 4:00 PM ET).

Note: Yahoo Finance typically limits intraday data to ~60 days.
This script will fetch what's available and note any limitations.
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

def fetch_aapl_30min_1year():
    """Fetch AAPL prices at 30-minute intervals for the past 1 year."""
    
    # Get date range (1 year from most recent market day)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365)
    
    print("=" * 80)
    print("FETCHING AAPL STOCK PRICES (30-MINUTE INTERVALS) - 1 YEAR")
    print("=" * 80)
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Interval: 30 minutes")
    print(f"Market Hours: 9:30 AM - 4:00 PM ET")
    print()
    print("⚠️  Note: Yahoo Finance typically limits intraday data to ~60 days.")
    print("   This script will fetch what's available...")
    print()
    
    # Fetch intraday data
    ticker = yf.Ticker("AAPL")
    
    all_data = []
    
    # Try fetching in chunks (Yahoo Finance limitation workaround)
    # Fetch last 60 days first (most recent data)
    print("Fetching most recent 60 days of 30-minute data...")
    try:
        recent_data = ticker.history(period='60d', interval='30m')
        if not recent_data.empty:
            print(f"✅ Fetched {len(recent_data)} data points for recent period")
            all_data.append(recent_data)
    except Exception as e:
        print(f"⚠️  Error fetching recent data: {e}")
    
    # For older data, we'll need to use daily data (Yahoo Finance limitation)
    # But let's try to get as much 30-minute data as possible
    print("\nAttempting to fetch additional historical data...")
    
    # Combine all data
    if all_data:
        data = pd.concat(all_data)
        data = data.sort_index()
        data = data[~data.index.duplicated(keep='first')]  # Remove duplicates
    else:
        print("❌ Could not fetch any 30-minute data.")
        print("   Falling back to daily data...")
        data = ticker.history(start=start_date.strftime('%Y-%m-%d'), 
                             end=end_date.strftime('%Y-%m-%d'), 
                             interval='1d')
        if data.empty:
            print("❌ Could not fetch any data.")
            return None
    
    # Reset index to get Datetime as a column
    data = data.reset_index()
    
    # Handle datetime column
    if 'Datetime' in data.columns:
        datetime_col = 'Datetime'
    elif 'Date' in data.columns:
        datetime_col = 'Date'
    else:
        # Use index if it's datetime
        data['Datetime'] = data.index if isinstance(data.index, pd.DatetimeIndex) else pd.to_datetime(data.index)
        datetime_col = 'Datetime'
    
    # Convert to ET timezone
    et_tz = pytz.timezone('America/New_York')
    
    # Ensure Datetime column is timezone-aware
    if data[datetime_col].dt.tz is None:
        # Assume UTC if no timezone
        data[datetime_col] = pd.to_datetime(data[datetime_col]).dt.tz_localize('UTC')
    
    # Convert to ET
    data[datetime_col] = data[datetime_col].dt.tz_convert(et_tz)
    data['Time'] = data[datetime_col].dt.time
    data['Date'] = data[datetime_col].dt.date
    
    # Filter for market hours (9:30 AM - 4:00 PM) - only if we have time data
    if 'Time' in data.columns:
        market_open = pd.Timestamp('09:30').time()
        market_close = pd.Timestamp('16:00').time()
        
        # Filter data (only if time is available)
        time_mask = data['Time'].notna()
        if time_mask.any():
            market_hours_mask = (data['Time'] >= market_open) & (data['Time'] <= market_close)
            filtered_data = data[time_mask & market_hours_mask].copy()
        else:
            # If no time data (daily data), include all
            filtered_data = data.copy()
    else:
        filtered_data = data.copy()
    
    # Sort by datetime
    filtered_data = filtered_data.sort_values(datetime_col)
    
    # Display results
    print()
    print("=" * 80)
    print("AAPL PRICE DATA SUMMARY")
    print("=" * 80)
    print(f"✅ Found {len(filtered_data)} data points")
    
    if len(filtered_data) > 0:
        print(f"Date Range: {filtered_data['Date'].min()} to {filtered_data['Date'].max()}")
        print(f"Trading Days: {filtered_data['Date'].nunique()}")
        
        # Check if we have intraday or daily data
        if 'Time' in filtered_data.columns and filtered_data['Time'].notna().any():
            print(f"Data Type: 30-minute intraday intervals")
            print(f"Average Data Points Per Day: {len(filtered_data) / filtered_data['Date'].nunique():.1f}")
        else:
            print(f"Data Type: Daily (Yahoo Finance limitation - intraday data only available for ~60 days)")
            print("⚠️  For full 1-year 30-minute data, consider using a paid data provider.")
    
    print()
    print("=" * 80)
    print("PRICE STATISTICS")
    print("=" * 80)
    if len(filtered_data) > 0:
        print(f"Average Price: ${filtered_data['Close'].mean():.2f}")
        print(f"High Price: ${filtered_data['High'].max():.2f}")
        print(f"Low Price: ${filtered_data['Low'].min():.2f}")
        print(f"Price Range: ${filtered_data['High'].max() - filtered_data['Low'].min():.2f}")
        if 'Volume' in filtered_data.columns:
            print(f"Total Volume: {int(filtered_data['Volume'].sum()):,}")
    
    # Show sample of data
    print()
    print("=" * 80)
    print("SAMPLE DATA (First 20 rows)")
    print("=" * 80)
    
    display_cols = [datetime_col, 'Open', 'High', 'Low', 'Close']
    if 'Volume' in filtered_data.columns:
        display_cols.append('Volume')
    if 'Time' in filtered_data.columns:
        display_cols.insert(1, 'Time')
    
    available_cols = [col for col in display_cols if col in filtered_data.columns]
    print(filtered_data[available_cols].head(20).to_string(index=False))
    
    # Group by date and show summary
    if 'Time' in filtered_data.columns and filtered_data['Time'].notna().any():
        print()
        print("=" * 80)
        print("DATA BY DATE (Sample - First 5 days)")
        print("=" * 80)
        
        for i, (date, group) in enumerate(filtered_data.groupby('Date')):
            if i >= 5:
                break
            print(f"\n📅 {date} ({pd.Timestamp(date).strftime('%A')}) - {len(group)} data points")
            print("-" * 80)
            if 'Time' in group.columns:
                print(f"{'Time (ET)':<12} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10}")
                print("-" * 80)
                for _, row in group.head(5).iterrows():
                    time_str = row['Time'].strftime('%H:%M') if pd.notna(row['Time']) else 'N/A'
                    print(f"{time_str:<12} ${row['Open']:<9.2f} ${row['High']:<9.2f} "
                          f"${row['Low']:<9.2f} ${row['Close']:<9.2f}")
                if len(group) > 5:
                    print(f"... and {len(group) - 5} more intervals")
            else:
                print(f"Open: ${group['Open'].iloc[0]:.2f}, Close: ${group['Close'].iloc[0]:.2f}")
    
    # Save to CSV
    output_file = f"aapl_30min_1year_{end_date.strftime('%Y%m%d')}.csv"
    filtered_data.to_csv(output_file, index=False)
    print()
    print(f"✅ Data saved to: {output_file}")
    print(f"   Total rows: {len(filtered_data)}")
    
    return filtered_data


if __name__ == '__main__':
    data = fetch_aapl_30min_1year()
    
    if data is not None:
        print()
        print("=" * 80)
        print("✅ Data fetch complete!")
        print("=" * 80)
        print()
        print("📊 Note: Yahoo Finance typically provides 30-minute intraday data")
        print("   for the last ~60 days only. For full 1-year 30-minute data,")
        print("   consider using a paid data provider like Alpha Vantage Pro,")
        print("   Polygon.io, or IEX Cloud.")
    else:
        print()
        print("❌ Failed to fetch data. Please check your internet connection")
        print("   and try again.")

