"""
Upload CSV data directly to Supabase using Python client.
More efficient than executing large SQL batches.
"""
import pandas as pd
import time
from datetime import datetime
from supabase import create_client, Client
from config import Config

def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    supabase_url = Config.SUPABASE_URL
    supabase_key = Config.SUPABASE_KEY
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not configured! Set SUPABASE_URL and SUPABASE_KEY environment variables.")
    
    return create_client(supabase_url, supabase_key)

def upload_csv_to_supabase(csv_file: str, batch_size: int = 1000):
    """Upload CSV data to Supabase in batches."""
    print("=" * 80)
    print("UPLOADING CSV DATA TO SUPABASE")
    print("=" * 80)
    print(f"File: {csv_file}")
    print(f"Table: stock_ohlc_30min")
    print(f"Batch size: {batch_size} rows")
    print()
    
    # Read CSV
    print("📖 Reading CSV...")
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df):,} rows")
    
    # Convert Datetime to proper format
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    
    # Initialize Supabase client
    try:
        supabase = get_supabase_client()
        print("✅ Supabase client initialized")
    except Exception as e:
        print(f"❌ Error initializing Supabase client: {e}")
        return False
    
    print()
    print("🚀 Starting upload...")
    print()
    
    total_batches = (len(df) + batch_size - 1) // batch_size
    successful_rows = 0
    failed_batches = 0
    start_time = time.time()
    
    # Upload in batches
    for i in range(0, len(df), batch_size):
        batch_num = (i // batch_size) + 1
        batch_df = df.iloc[i:i + batch_size]
        
        # Prepare data for Supabase
        records = []
        for _, row in batch_df.iterrows():
            dt = pd.to_datetime(row['Datetime'])
            if dt.tz is None:
                dt = dt.tz_localize('America/New_York')
            dt_utc = dt.tz_convert('UTC')
            
            record = {
                'symbol': str(row['Symbol']).upper(),
                'datetime': dt_utc.isoformat(),
                'date': str(row['Date']),
                'time': str(row['Time']),
                'open': float(row['Open']),
                'high': float(row['High']),
                'low': float(row['Low']),
                'close': float(row['Close']),
                'volume': int(row['Volume']),
            }
            
            # Add optional fields if they exist
            if 'trade_count' in row and pd.notna(row['trade_count']):
                record['trade_count'] = int(row['trade_count'])
            if 'vwap' in row and pd.notna(row['vwap']):
                record['vwap'] = float(row['vwap'])
            
            records.append(record)
        
        # Insert batch
        try:
            result = supabase.table('stock_ohlc_30min').insert(records).execute()
            
            if result.data:
                successful_rows += len(records)
                elapsed = time.time() - start_time
                rate = successful_rows / elapsed if elapsed > 0 else 0
                remaining = (len(df) - successful_rows) / rate if rate > 0 else 0
                
                print(f"✅ Batch {batch_num}/{total_batches}: Uploaded {len(records)} rows "
                      f"({successful_rows:,}/{len(df):,} total, ETA: {remaining/60:.1f} min)")
            else:
                failed_batches += 1
                print(f"❌ Batch {batch_num}/{total_batches}: Failed (no data returned)")
                
        except Exception as e:
            failed_batches += 1
            error_msg = str(e)[:200]
            print(f"❌ Batch {batch_num}/{total_batches}: Failed - {error_msg}")
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    elapsed_time = time.time() - start_time
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Successful rows: {successful_rows:,}")
    print(f"❌ Failed batches: {failed_batches}")
    print(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
    print()
    
    if failed_batches == 0:
        print("✅ All data uploaded successfully!")
    else:
        print("⚠️  Some batches failed. Please check errors above.")
    
    return successful_rows > 0

if __name__ == '__main__':
    csv_file = 'all_100_stocks_30min_2years_alpaca_20251116.csv'
    upload_csv_to_supabase(csv_file, batch_size=1000)

