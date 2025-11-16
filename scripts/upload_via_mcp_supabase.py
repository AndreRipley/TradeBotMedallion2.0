"""
Upload all 100 stocks data to Supabase using MCP Supabase tools.
This script uses the MCP Supabase integration to upload data via SQL.
"""
import pandas as pd
import sys
import os
from datetime import datetime

# Try to import MCP Supabase tools
try:
    # This would be available if MCP is configured
    # We'll use execute_sql for bulk inserts
    pass
except ImportError:
    pass


def upload_via_sql_batches(csv_file: str):
    """
    Upload CSV data to Supabase using SQL INSERT statements via MCP.
    This approach uses execute_sql for bulk inserts.
    """
    print("=" * 80)
    print("UPLOADING TO SUPABASE VIA MCP")
    print("=" * 80)
    print(f"File: {csv_file}")
    print(f"Table: stock_ohlc_30min")
    print()
    
    # Read CSV
    print("📖 Reading CSV...")
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df):,} rows")
    
    # Prepare data
    print("🔄 Preparing data for SQL insert...")
    
    # Convert datetime to ISO format
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    
    # Group into batches for SQL INSERT
    batch_size = 1000
    total_batches = (len(df) + batch_size - 1) // batch_size
    
    print(f"📤 Preparing {total_batches} SQL batches...")
    print()
    print("⚠️  Note: This script requires MCP Supabase integration.")
    print("   For large datasets, it's recommended to:")
    print("   1. Use the Python Supabase client (faster)")
    print("   2. Or use Supabase dashboard CSV import")
    print()
    print("   To use Python client, configure SUPABASE_URL and SUPABASE_KEY")
    print("   in your .env file, then run:")
    print(f"   python3 upload_all_100_to_supabase.py {csv_file}")
    print()
    
    # Show sample of what would be inserted
    print("Sample data (first 3 rows):")
    print(df[['Symbol', 'Datetime', 'Close', 'Volume']].head(3).to_string(index=False))
    print()
    
    return False


if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'all_100_stocks_30min_2years_alpaca_20251116.csv'
    
    if not os.path.exists(csv_file):
        print(f"❌ File not found: {csv_file}")
        sys.exit(1)
    
    upload_via_sql_batches(csv_file)

