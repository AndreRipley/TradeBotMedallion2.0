"""
Fetch Apple (AAPL) stock prices at 30-minute intervals for the past week.
Only includes prices during market hours (9:30 AM - 4:00 PM ET).
"""
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import pytz

def fetch_aapl_30min_week():
    """Fetch AAPL prices at 30-minute intervals for the past week."""
    
    # Get date range (past 7 days)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=7)
    
    print("=" * 80)
    print("FETCHING AAPL STOCK PRICES (30-MINUTE INTERVALS)")
    print("=" * 80)
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Interval: 30 minutes")
    print(f"Market Hours: 9:30 AM - 4:00 PM ET")
    print()
    
    # Fetch intraday data
    ticker = yf.Ticker("AAPL")
    
    # Try to fetch 30-minute data for the past week
    # Note: yfinance may have limitations on historical intraday data
    try:
        # Fetch 30-minute interval data
        data = ticker.history(
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='30m'
        )
        
        if data.empty:
            print("⚠️  No data returned. Trying alternative method...")
            # Try fetching last 5 days with 30m interval
            data = ticker.history(period='5d', interval='30m')
        
        if data.empty:
            print("❌ Could not fetch 30-minute interval data.")
            print("   Yahoo Finance may not provide 30-minute data for this period.")
            print("   Trying 1-hour intervals instead...")
            data = ticker.history(period='5d', interval='1h')
            
            if data.empty:
                print("❌ Could not fetch intraday data.")
                return None
        
        # Reset index to get Datetime as a column
        data = data.reset_index()
        
        # Filter for market hours (9:30 AM - 4:00 PM ET)
        # Convert to ET timezone
        et_tz = pytz.timezone('America/New_York')
        
        # Ensure Datetime column is timezone-aware
        if 'Datetime' in data.columns:
            if data['Datetime'].dt.tz is None:
                # Assume UTC if no timezone
                data['Datetime'] = pd.to_datetime(data['Datetime']).dt.tz_localize('UTC')
            # Convert to ET
            data['Datetime'] = data['Datetime'].dt.tz_convert(et_tz)
            data['Time'] = data['Datetime'].dt.time
            data['Date'] = data['Datetime'].dt.date
        else:
            # If index is datetime
            if data.index.tz is None:
                data.index = pd.to_datetime(data.index).tz_localize('UTC')
            data.index = data.index.tz_convert(et_tz)
            data['Time'] = data.index.time
            data['Date'] = data.index.date
            data['Datetime'] = data.index
        
        # Filter for market hours (9:30 AM - 4:00 PM)
        market_open = pd.Timestamp('09:30').time()
        market_close = pd.Timestamp('16:00').time()
        
        # Filter data
        filtered_data = data[
            (data['Time'] >= market_open) & 
            (data['Time'] <= market_close)
        ].copy()
        
        if filtered_data.empty:
            print("⚠️  No data found for market hours.")
            print("   Showing all available data:")
            filtered_data = data.copy()
        
        # Sort by datetime
        filtered_data = filtered_data.sort_values('Datetime')
        
        # Display results
        print(f"✅ Found {len(filtered_data)} data points")
        print()
        print("=" * 80)
        print("AAPL PRICE DATA (30-MINUTE INTERVALS)")
        print("=" * 80)
        print()
        
        # Group by date
        for date, group in filtered_data.groupby('Date'):
            print(f"\n📅 {date} ({pd.Timestamp(date).strftime('%A')})")
            print("-" * 80)
            print(f"{'Time (ET)':<12} {'Open':<10} {'High':<10} {'Low':<10} {'Close':<10} {'Volume':<15}")
            print("-" * 80)
            
            for _, row in group.iterrows():
                time_str = row['Time'].strftime('%H:%M')
                print(f"{time_str:<12} ${row['Open']:<9.2f} ${row['High']:<9.2f} "
                      f"${row['Low']:<9.2f} ${row['Close']:<9.2f} {int(row['Volume']):<15,}")
        
        # Summary statistics
        print()
        print("=" * 80)
        print("SUMMARY STATISTICS")
        print("=" * 80)
        print(f"Total Data Points: {len(filtered_data)}")
        print(f"Date Range: {filtered_data['Date'].min()} to {filtered_data['Date'].max()}")
        print(f"Trading Days: {filtered_data['Date'].nunique()}")
        print(f"Average Price: ${filtered_data['Close'].mean():.2f}")
        print(f"High Price: ${filtered_data['High'].max():.2f}")
        print(f"Low Price: ${filtered_data['Low'].min():.2f}")
        print(f"Price Range: ${filtered_data['High'].max() - filtered_data['Low'].min():.2f}")
        print(f"Total Volume: {int(filtered_data['Volume'].sum()):,}")
        
        # Save to CSV
        output_file = f"aapl_30min_{start_date.strftime('%Y%m%d')}_to_{end_date.strftime('%Y%m%d')}.csv"
        filtered_data.to_csv(output_file, index=False)
        print()
        print(f"✅ Data saved to: {output_file}")
        
        return filtered_data
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    data = fetch_aapl_30min_week()
    
    if data is not None:
        print()
        print("=" * 80)
        print("✅ Data fetch complete!")
        print("=" * 80)

