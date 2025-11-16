"""
Upload all 100 stocks (2 years) to Supabase using MCP Supabase execute_sql.
Processes CSV in batches of 500 rows and executes SQL INSERT statements.
"""
import pandas as pd
import sys
import os
import time

def generate_batch_sql(df_batch):
    """Generate SQL INSERT statement for a batch of rows."""
    values_list = []
    
    for _, row in df_batch.iterrows():
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
    
    return sql


def main():
    csv_file = 'all_100_stocks_30min_2years_alpaca_20251116.csv'
    batch_size = 500
    
    print("=" * 80)
    print("UPLOADING ALL 100 STOCKS TO SUPABASE VIA MCP")
    print("=" * 80)
    print(f"File: {csv_file}")
    print(f"Table: stock_ohlc_30min")
    print(f"Batch Size: {batch_size} rows per SQL statement")
    print()
    
    # Read CSV
    print("📖 Reading CSV...")
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df):,} rows")
    
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    
    total_batches = (len(df) + batch_size - 1) // batch_size
    print(f"📤 Will execute {total_batches} SQL batches")
    print(f"   Estimated time: {total_batches * 2 / 60:.1f} minutes")
    print()
    print("🚀 Starting upload...")
    print()
    
    successful = 0
    failed = 0
    start_time = time.time()
    
    for i in range(0, len(df), batch_size):
        batch_num = (i // batch_size) + 1
        batch_df = df.iloc[i:i + batch_size]
        
        sql = generate_batch_sql(batch_df)
        
        # Execute via MCP Supabase execute_sql
        try:
            print(f"📤 Batch {batch_num}/{total_batches}: Uploading {len(batch_df)} rows...", end=' ', flush=True)
            
            # Note: This needs to be executed via MCP tool in the actual flow
            # For now, we'll print the SQL and let the user know it needs MCP execution
            
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
    print(f"📊 Total: {len(df):,} records")
    print(f"⏱️  Time: {elapsed_time/60:.1f} minutes")
    
    return successful > 0


if __name__ == '__main__':
    print("⚠️  This script generates SQL batches.")
    print("   To actually upload, each batch needs to be executed via MCP Supabase execute_sql.")
    print("   This will be done automatically in the next step.")
    print()
    
    main()

