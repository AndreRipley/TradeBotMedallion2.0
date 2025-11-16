"""
Upload top 50 stocks historical data to Supabase.
Creates a new table for historical OHLC data and uploads all records.
"""
import pandas as pd
import logging
from datetime import datetime
from config import Config
from supabase_logger import get_supabase_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Table name for historical OHLC data
TABLE_NAME = 'stock_ohlc_30min'


def create_table_sql():
    """Return SQL to create the historical OHLC table."""
    return f"""
-- Create stock_ohlc_30min table for historical 30-minute OHLC data
CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    datetime TIMESTAMPTZ NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    open DECIMAL(10, 2) NOT NULL,
    high DECIMAL(10, 2) NOT NULL,
    low DECIMAL(10, 2) NOT NULL,
    close DECIMAL(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    trade_count BIGINT,
    vwap DECIMAL(10, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(symbol, datetime)
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_symbol ON {TABLE_NAME}(symbol);
CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_datetime ON {TABLE_NAME}(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_symbol_datetime ON {TABLE_NAME}(symbol, datetime DESC);
CREATE INDEX IF NOT EXISTS idx_{TABLE_NAME}_date ON {TABLE_NAME}(date);

-- Enable Row Level Security (RLS)
ALTER TABLE {TABLE_NAME} ENABLE ROW LEVEL SECURITY;

-- Create policy to allow inserts
CREATE POLICY "Allow inserts for {TABLE_NAME}" ON {TABLE_NAME}
    FOR INSERT
    WITH CHECK (true);

-- Create policy to allow reads
CREATE POLICY "Allow reads for {TABLE_NAME}" ON {TABLE_NAME}
    FOR SELECT
    USING (true);
"""


def upload_csv_to_supabase(csv_file: str, batch_size: int = 1000):
    """
    Upload CSV file to Supabase in batches.
    
    Args:
        csv_file: Path to CSV file
        batch_size: Number of records to upload per batch
    """
    client = get_supabase_client()
    
    if client is None:
        logger.error("❌ Supabase client not initialized. Check credentials.")
        return False
    
    print("=" * 80)
    print("UPLOADING HISTORICAL DATA TO SUPABASE")
    print("=" * 80)
    print(f"CSV File: {csv_file}")
    print(f"Table: {TABLE_NAME}")
    print(f"Batch Size: {batch_size}")
    print()
    
    # Read CSV file
    print("📖 Reading CSV file...")
    try:
        df = pd.read_csv(csv_file)
        print(f"✅ Loaded {len(df):,} rows from CSV")
    except Exception as e:
        logger.error(f"❌ Error reading CSV file: {e}")
        return False
    
    # Check required columns
    required_cols = ['Symbol', 'Datetime', 'Date', 'Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        logger.error(f"❌ Missing required columns: {missing_cols}")
        return False
    
    # Prepare data for upload
    print("🔄 Preparing data for upload...")
    
    # Convert datetime strings to ISO format
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    
    # Prepare records
    records = []
    for _, row in df.iterrows():
        record = {
            'symbol': str(row['Symbol']).upper(),
            'datetime': row['Datetime'].isoformat(),
            'date': str(row['Date']),
            'time': str(row['Time']),
            'open': float(row['Open']),
            'high': float(row['High']),
            'low': float(row['Low']),
            'close': float(row['Close']),
            'volume': int(row['Volume'])
        }
        
        # Add optional fields if they exist
        if 'trade_count' in df.columns and pd.notna(row.get('trade_count')):
            record['trade_count'] = int(row['trade_count'])
        if 'vwap' in df.columns and pd.notna(row.get('vwap')):
            record['vwap'] = float(row['vwap'])
        
        records.append(record)
    
    print(f"✅ Prepared {len(records):,} records")
    
    # Upload in batches
    total_batches = (len(records) + batch_size - 1) // batch_size
    print(f"📤 Uploading {total_batches} batches...")
    print()
    
    successful = 0
    failed = 0
    
    for i in range(0, len(records), batch_size):
        batch_num = (i // batch_size) + 1
        batch = records[i:i + batch_size]
        
        try:
            # Insert batch
            response = client.table(TABLE_NAME).insert(batch).execute()
            
            if response.data:
                successful += len(batch)
                print(f"✅ Batch {batch_num}/{total_batches}: Uploaded {len(batch)} records "
                      f"({successful:,} total)")
            else:
                failed += len(batch)
                logger.warning(f"⚠️  Batch {batch_num}/{total_batches}: Failed to upload")
                
        except Exception as e:
            failed += len(batch)
            error_msg = str(e)
            # Check if it's a duplicate key error (record already exists)
            if 'duplicate key' in error_msg.lower() or 'unique constraint' in error_msg.lower():
                print(f"⚠️  Batch {batch_num}/{total_batches}: Some records already exist (skipping duplicates)")
            else:
                logger.error(f"❌ Batch {batch_num}/{total_batches}: Error - {error_msg[:100]}")
    
    # Summary
    print()
    print("=" * 80)
    print("UPLOAD SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully uploaded: {successful:,} records")
    print(f"❌ Failed: {failed:,} records")
    print(f"📊 Total processed: {len(records):,} records")
    
    if successful > 0:
        print()
        print("✅ Upload complete!")
        print(f"   View data in Supabase dashboard: Table '{TABLE_NAME}'")
        return True
    else:
        print()
        print("❌ Upload failed. Check errors above.")
        return False


def create_table_if_not_exists():
    """Create the table if it doesn't exist."""
    client = get_supabase_client()
    
    if client is None:
        logger.error("❌ Supabase client not initialized. Check credentials.")
        return False
    
    print("=" * 80)
    print("CREATING SUPABASE TABLE")
    print("=" * 80)
    print(f"Table: {TABLE_NAME}")
    print()
    print("⚠️  Note: You need to run the SQL manually in Supabase SQL Editor.")
    print("   The SQL is printed below:")
    print()
    print("-" * 80)
    print(create_table_sql())
    print("-" * 80)
    print()
    print("📝 Steps:")
    print("   1. Go to your Supabase dashboard")
    print("   2. Click 'SQL Editor'")
    print("   3. Copy and paste the SQL above")
    print("   4. Click 'Run'")
    print("   5. Then run this script again to upload data")
    print()
    
    return False


def create_table_via_mcp():
    """Try to create table via Supabase MCP if available."""
    try:
        from mcp_supabase_apply_migration import mcp_supabase_apply_migration
        
        sql = create_table_sql()
        # Extract just the CREATE TABLE and index statements
        # Remove comments and policy statements for migration
        migration_sql = """
-- Create stock_ohlc_30min table for historical 30-minute OHLC data
CREATE TABLE IF NOT EXISTS stock_ohlc_30min (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    datetime TIMESTAMPTZ NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    open DECIMAL(10, 2) NOT NULL,
    high DECIMAL(10, 2) NOT NULL,
    low DECIMAL(10, 2) NOT NULL,
    close DECIMAL(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    trade_count BIGINT,
    vwap DECIMAL(10, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(symbol, datetime)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_stock_ohlc_30min_symbol ON stock_ohlc_30min(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_ohlc_30min_datetime ON stock_ohlc_30min(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_stock_ohlc_30min_symbol_datetime ON stock_ohlc_30min(symbol, datetime DESC);
CREATE INDEX IF NOT EXISTS idx_stock_ohlc_30min_date ON stock_ohlc_30min(date);

-- Enable RLS
ALTER TABLE stock_ohlc_30min ENABLE ROW LEVEL SECURITY;

-- Create policies
CREATE POLICY "Allow inserts for stock_ohlc_30min" ON stock_ohlc_30min
    FOR INSERT
    WITH CHECK (true);

CREATE POLICY "Allow reads for stock_ohlc_30min" ON stock_ohlc_30min
    FOR SELECT
    USING (true);
"""
        
        # Note: This would require MCP Supabase integration
        # For now, we'll just print the SQL
        return False
    except ImportError:
        return False


def main():
    """Main function to upload data."""
    import sys
    import os
    
    # Check if CSV file is provided
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        # Default to the combined file
        csv_file = 'top50_stocks_30min_1year_alpaca_20251115.csv'
    
    # Check if file exists
    if not os.path.exists(csv_file):
        print(f"❌ CSV file not found: {csv_file}")
        print()
        print("Available CSV files:")
        for f in os.listdir('.'):
            if f.endswith('.csv') and '30min' in f:
                print(f"   - {f}")
        return
    
    # Check Supabase credentials
    if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
        print("❌ Supabase credentials not configured!")
        print("   Please set SUPABASE_URL and SUPABASE_KEY in .env or environment variables")
        print()
        print("📝 SQL to create table (run in Supabase SQL Editor):")
        print("-" * 80)
        print(create_table_sql())
        print("-" * 80)
        return
    
    # Show table creation SQL first
    print()
    print("📝 SQL to create table (if not already created):")
    print("-" * 80)
    print(create_table_sql())
    print("-" * 80)
    print()
    
    # Try to upload (will handle errors if table doesn't exist)
    print("🚀 Starting upload...")
    print()
    success = upload_csv_to_supabase(csv_file)
    
    if success:
        print()
        print("=" * 80)
        print("✅ DATA UPLOAD COMPLETE!")
        print("=" * 80)
        print()
        print("📊 Next steps:")
        print(f"   1. View data in Supabase dashboard: Table '{TABLE_NAME}'")
        print("   2. Query data using SQL Editor")
        print("   3. Create dashboards or visualizations")
        print()
        print("Example queries:")
        print(f"   SELECT * FROM {TABLE_NAME} WHERE symbol = 'AAPL' ORDER BY datetime DESC LIMIT 10;")
        print(f"   SELECT symbol, COUNT(*) as records FROM {TABLE_NAME} GROUP BY symbol;")
        print(f"   SELECT symbol, MIN(low) as min_price, MAX(high) as max_price, AVG(close) as avg_price")
        print(f"   FROM {TABLE_NAME} GROUP BY symbol ORDER BY symbol;")
    else:
        print()
        print("❌ Upload failed. Please check:")
        print("   1. Table exists in Supabase (run SQL above if needed)")
        print("   2. Supabase credentials are correct")
        print("   3. RLS policies allow inserts")


if __name__ == '__main__':
    main()

