"""
Generate smaller SQL batches that can be executed via MCP Supabase execute_sql.
Splits the CSV into batches of 100 rows each (small enough for MCP).
"""
import pandas as pd
import glob
import os

def generate_small_batches_from_csv(csv_file: str, batch_size: int = 100):
    """Generate smaller SQL batches from CSV that can be executed via MCP."""
    print("=" * 80)
    print("GENERATING SMALL BATCHES FOR MCP EXECUTION")
    print("=" * 80)
    print(f"CSV File: {csv_file}")
    print(f"Batch Size: {batch_size} rows per batch")
    print()
    
    # Read CSV
    print("📖 Reading CSV...")
    df = pd.read_csv(csv_file)
    print(f"✅ Loaded {len(df):,} rows")
    
    df['Datetime'] = pd.to_datetime(df['Datetime'])
    
    total_batches = (len(df) + batch_size - 1) // batch_size
    print(f"📤 Will generate {total_batches} small batches")
    print()
    
    print("🚀 Generating batches...")
    
    for i in range(0, len(df), batch_size):
        batch_num = (i // batch_size) + 1
        batch_df = df.iloc[i:i + batch_size]
        
        # Generate SQL for this batch
        values_list = []
        for _, row in batch_df.iterrows():
            symbol = str(row['Symbol']).upper().replace("'", "''")
            dt = pd.to_datetime(row['Datetime'])
            if dt.tz is None:
                dt = dt.tz_localize('America/New_York')
            dt_utc = dt.tz_convert('UTC')
            datetime_val = dt_utc.isoformat()
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
        
        # Save to file
        output_file = f'small_batch_{batch_num}_execute.sql'
        with open(output_file, 'w') as f:
            f.write(sql.strip())
        
        if batch_num % 100 == 0 or batch_num <= 10:
            print(f"✅ Generated batch {batch_num}/{total_batches}: {len(batch_df)} rows ({len(sql):,} chars)")
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Generated {total_batches} small batch SQL files")
    print(f"   Files: small_batch_1_execute.sql through small_batch_{total_batches}_execute.sql")
    print(f"   Each batch: ~{batch_size} rows, suitable for MCP execution")
    print()
    print("Next: Execute each small batch via MCP Supabase execute_sql tool")
    
    return total_batches

if __name__ == '__main__':
    csv_file = 'all_100_stocks_30min_2years_alpaca_20251116.csv'
    generate_small_batches_from_csv(csv_file, batch_size=100)

