"""
Upload all 100 stocks (2 years) data to Supabase using MCP Supabase tools.
Uses execute_sql for bulk inserts in batches.
"""
import pandas as pd
import sys
import os
from datetime import datetime

def generate_insert_sql_batch(df_batch):
    """Generate SQL INSERT statement for a batch of rows."""
    values = []
    for _, row in df_batch.iterrows():
        symbol = str(row['Symbol']).upper().replace("'", "''")
        datetime_str = pd.to_datetime(row['Datetime']).isoformat()
        date_str = str(row['Date'])
        time_str = str(row['Time'])
        open_val = float(row['Open'])
        high_val = float(row['High'])
        low_val = float(row['Low'])
        close_val = float(row['Close'])
        volume_val = int(row['Volume'])
        
        trade_count_val = f", {int(row['trade_count'])}" if 'trade_count' in row and pd.notna(row.get('trade_count')) else ", NULL"
        vwap_val = f", {float(row['vwap'])}" if 'vwap' in row and pd.notna(row.get('vwap')) else ", NULL"
        
        values.append(
            f"('{symbol}', '{datetime_str}'::timestamptz, '{date_str}'::date, "
            f"'{time_str}'::time, {open_val}, {high_val}, {low_val}, {close_val}, "
            f"{volume_val}{trade_count_val}{vwap_val})"
        )
    
    sql = f"""
INSERT INTO stock_ohlc_30min (symbol, datetime, date, time, open, high, low, close, volume, trade_count, vwap)
VALUES {', '.join(values)}
ON CONFLICT (symbol, datetime) DO NOTHING;
"""
    return sql


def upload_via_mcp(csv_file: str, batch_size: int = 1000):
    """Upload CSV to Supabase using MCP execute_sql."""
    print("=" * 80)
    print("UPLOADING TO SUPABASE VIA MCP")
    print("=" * 80)
    print(f"File: {csv_file}")
    print(f"Table: stock_ohlc_30min")
    print(f"Batch Size: {batch_size}")
    print()
    
    # Read CSV
    print("📖 Reading CSV...")
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df):,} rows")
    
    # Convert datetime
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    
    # Prepare batches
    total_batches = (len(df) + batch_size - 1) // batch_size
    print(f"📤 Preparing {total_batches} SQL batches...")
    print()
    print("⚠️  Note: This will use MCP Supabase execute_sql")
    print("   For 696k rows, this may take 30-60 minutes")
    print()
    
    # Import MCP function
    try:
        # Try to use MCP Supabase execute_sql
        # Note: This is a placeholder - actual MCP integration would be different
        print("📝 To upload via MCP, you would need to:")
        print("   1. Use mcp_supabase_execute_sql tool")
        print("   2. Generate SQL INSERT statements in batches")
        print("   3. Execute each batch")
        print()
        print("   However, for 696k rows, it's recommended to:")
        print("   - Use Python Supabase client (faster)")
        print("   - Or use Supabase dashboard CSV import")
        print()
        print("   To use Python client:")
        print("   1. Add SUPABASE_URL and SUPABASE_KEY to .env")
        print(f"   2. Run: python3 upload_all_100_to_supabase.py {csv_file}")
        print()
        
        return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'all_100_stocks_30min_2years_alpaca_20251116.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)
    
    upload_via_mcp(csv_file)

