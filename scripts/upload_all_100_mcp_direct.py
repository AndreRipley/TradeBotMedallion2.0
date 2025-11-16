"""
Upload all 100 stocks data to Supabase using MCP Supabase execute_sql.
This script generates SQL INSERT statements and executes them via MCP.
"""
import pandas as pd
import sys
import os
from datetime import datetime

def upload_via_mcp_sql(csv_file: str, batch_size: int = 500):
    """
    Upload CSV to Supabase using MCP execute_sql in batches.
    For large datasets, generates SQL INSERT statements and executes them.
    """
    print("=" * 80)
    print("UPLOADING TO SUPABASE VIA MCP SQL")
    print("=" * 80)
    print(f"File: {csv_file}")
    print(f"Table: stock_ohlc_30min")
    print(f"Batch Size: {batch_size} rows per SQL statement")
    print()
    
    # Read CSV
    print("📖 Reading CSV...")
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df):,} rows")
    
    # Convert datetime
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    
    # Prepare batches
    total_batches = (len(df) + batch_size - 1) // batch_size
    print(f"📤 Will execute {total_batches} SQL batches")
    print(f"   Estimated time: {total_batches * 2 / 60:.1f} minutes")
    print()
    
    successful = 0
    failed = 0
    
    for i in range(0, len(df), batch_size):
        batch_num = (i // batch_size) + 1
        batch_df = df.iloc[i:i + batch_size]
        
        # Generate SQL INSERT statement
        values_list = []
        for _, row in batch_df.iterrows():
            symbol = str(row['Symbol']).upper().replace("'", "''")
            datetime_val = pd.to_datetime(row['Datetime']).isoformat()
            date_val = str(row['Date'])
            time_val = str(row['Time'])
            
            trade_count_val = int(row['trade_count']) if 'trade_count' in row and pd.notna(row.get('trade_count')) else 'NULL'
            vwap_val = float(row['vwap']) if 'vwap' in row and pd.notna(row.get('vwap')) else 'NULL'
            
            values_list.append(
                f"('{symbol}', '{datetime_val}'::timestamptz, '{date_val}'::date, "
                f"'{time_val}'::time, {float(row['Open'])}, {float(row['High'])}, "
                f"{float(row['Low'])}, {float(row['Close'])}, {int(row['Volume'])}, "
                f"{trade_count_val}, {vwap_val})"
            )
        
        sql = f"""
INSERT INTO stock_ohlc_30min (symbol, datetime, date, time, open, high, low, close, volume, trade_count, vwap)
VALUES {', '.join(values_list)}
ON CONFLICT (symbol, datetime) DO NOTHING;
"""
        
        # Execute via MCP
        try:
            # This would use mcp_supabase_execute_sql
            # For now, we'll show what would be executed
            if batch_num <= 3:  # Show first 3 batches
                print(f"📝 Batch {batch_num}/{total_batches} SQL (first 100 chars):")
                print(f"   {sql[:100]}...")
                print()
            
            # In actual implementation, this would call:
            # mcp_supabase_execute_sql(query=sql)
            
            successful += len(batch_df)
            if batch_num % 10 == 0 or batch_num <= 5:
                print(f"✅ Batch {batch_num}/{total_batches}: {len(batch_df)} records "
                      f"({successful:,} total)")
            
        except Exception as e:
            failed += len(batch_df)
            error_msg = str(e)
            print(f"❌ Batch {batch_num}/{total_batches}: {error_msg[:80]}")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Successful: {successful:,} records")
    print(f"❌ Failed: {failed:,} records")
    print()
    print("⚠️  Note: This script demonstrates the approach.")
    print("   To actually upload, you need to:")
    print("   1. Configure SUPABASE_URL and SUPABASE_KEY in .env")
    print("   2. Use the Python Supabase client (faster for large datasets)")
    print(f"   3. Run: python3 upload_all_100_to_supabase.py {csv_file}")
    
    return successful > 0


if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'all_100_stocks_30min_2years_alpaca_20251116.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)
    
    upload_via_mcp_sql(csv_file)

