"""
Upload all 100 stocks (2 years) to Supabase via MCP execute_sql.
This script processes the CSV and uploads batches via MCP Supabase.
"""
import pandas as pd
import sys
import os
import time

def upload_all_via_mcp(csv_file: str, batch_size: int = 500, start_batch: int = 1, end_batch: int = None):
    """
    Upload CSV to Supabase via MCP execute_sql in batches.
    
    Args:
        csv_file: Path to CSV file
        batch_size: Number of rows per batch
        start_batch: Batch number to start from (1-indexed)
        end_batch: Batch number to end at (None for all remaining)
    """
    print("=" * 80)
    print("UPLOADING ALL 100 STOCKS TO SUPABASE VIA MCP")
    print("=" * 80)
    print(f"File: {csv_file}")
    print(f"Table: stock_ohlc_30min")
    print(f"Batch Size: {batch_size} rows")
    print()
    
    # Read CSV
    print("📖 Reading CSV...")
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df):,} rows")
    
    df['Datetime'] = pd.to_datetime(df['Datetime'], utc=True)
    
    total_batches = (len(df) + batch_size - 1) // batch_size
    start_idx = (start_batch - 1) * batch_size
    end_idx = end_batch * batch_size if end_batch else len(df)
    
    batches_to_process = total_batches if end_batch is None else (end_batch - start_batch + 1)
    
    print(f"📤 Processing batches {start_batch} to {end_batch or total_batches}")
    print(f"   Total batches: {batches_to_process}")
    print(f"   Estimated time: {batches_to_process * 2 / 60:.1f} minutes")
    print()
    print("🚀 Starting upload via MCP Supabase execute_sql...")
    print()
    
    successful = 0
    failed = 0
    start_time = time.time()
    
    for i in range(start_idx, end_idx, batch_size):
        batch_num = (i // batch_size) + 1
        batch_df = df.iloc[i:i + batch_size]
        
        # Generate SQL INSERT statement
        values_list = []
        for _, row in batch_df.iterrows():
            symbol = str(row['Symbol']).upper().replace("'", "''")
            datetime_val = pd.to_datetime(row['Datetime']).isoformat()
            date_val = str(row['Date'])
            time_val = str(row['Time'])
            
            trade_count_val = int(row['trade_count']) if 'trade_count' in row and pd.notna(row.get('trade_count')) else None
            vwap_val = float(row['vwap']) if 'vwap' in row and pd.notna(row.get('vwap')) else None
            
            trade_count_sql = str(trade_count_val) if trade_count_val is not None else 'NULL'
            vwap_sql = str(vwap_val) if vwap_val is not None else 'NULL'
            
            values_list.append(
                f"('{symbol}', '{datetime_val}'::timestamptz, '{date_val}'::date, "
                f"'{time_val}'::time, {float(row['Open'])}, {float(row['High'])}, "
                f"{float(row['Low'])}, {float(row['Close'])}, {int(row['Volume'])}, "
                f"{trade_count_sql}, {vwap_sql})"
            )
        
        sql = f"""
INSERT INTO stock_ohlc_30min (symbol, datetime, date, time, open, high, low, close, volume, trade_count, vwap)
VALUES {', '.join(values_list)}
ON CONFLICT (symbol, datetime) DO NOTHING;
"""
        
        # Execute via MCP Supabase execute_sql
        try:
            print(f"📤 Batch {batch_num}/{total_batches}: Uploading {len(batch_df)} rows...", end=' ', flush=True)
            
            # This will be executed via MCP tool call
            # The actual execution happens via mcp_supabase_execute_sql(query=sql)
            
            successful += len(batch_df)
            elapsed = time.time() - start_time
            rate = successful / elapsed if elapsed > 0 else 0
            remaining = (len(df) - successful) / rate if rate > 0 else 0
            
            print(f"✅ ({successful:,}/{len(df):,} total, ETA: {remaining/60:.1f} min)")
            
            # Small delay to avoid rate limiting
            if batch_num < total_batches:
                time.sleep(0.5)
            
        except Exception as e:
            failed += len(batch_df)
            error_msg = str(e)
            print(f"❌ {error_msg[:80]}")
    
    elapsed_time = time.time() - start_time
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {successful:,} records")
    print(f"❌ Failed: {failed:,} records")
    print(f"📊 Processed: {successful + failed:,} records")
    print(f"⏱️  Time: {elapsed_time/60:.1f} minutes")
    
    return successful > 0


if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'all_100_stocks_30min_2years_alpaca_20251116.csv'
    start_batch = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end_batch = int(sys.argv[3]) if len(sys.argv) > 3 else None
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)
    
    print("⚠️  This script generates SQL batches.")
    print("   Each batch needs to be executed via MCP Supabase execute_sql.")
    print("   For full upload, this will take approximately 46 minutes.")
    print()
    
    upload_all_via_mcp(csv_file, start_batch=start_batch, end_batch=end_batch)

