"""
Clean CSV file for Supabase import by converting float values to integers
for volume and trade_count columns.
"""
import pandas as pd

def clean_csv_for_supabase(input_file: str, output_file: str = None):
    """Clean CSV by converting volume and trade_count to integers."""
    if output_file is None:
        output_file = input_file.replace('.csv', '_cleaned.csv')
    
    print("=" * 80)
    print("CLEANING CSV FOR SUPABASE IMPORT")
    print("=" * 80)
    print(f"Input file: {input_file}")
    print(f"Output file: {output_file}")
    print()
    
    # Read CSV
    print("📖 Reading CSV...")
    df = pd.read_csv(input_file)
    print(f"✅ Loaded {len(df):,} rows")
    
    # Convert volume and trade_count to integers (remove .0)
    print()
    print("🔧 Cleaning data...")
    
    # Convert volume to int (handles NaN by filling with 0 or dropping)
    if 'Volume' in df.columns:
        df['Volume'] = df['Volume'].fillna(0).astype(int)
        print(f"✅ Converted Volume to integers")
    
    if 'volume' in df.columns:
        df['volume'] = df['volume'].fillna(0).astype(int)
        print(f"✅ Converted volume to integers")
    
    # Convert trade_count to int (handles NaN)
    if 'trade_count' in df.columns:
        # For trade_count, we'll keep NaN as None/null, but convert non-null values to int
        df['trade_count'] = df['trade_count'].apply(lambda x: int(x) if pd.notna(x) else None)
        print(f"✅ Converted trade_count to integers (preserving NULL values)")
    
    # Save cleaned CSV
    print()
    print("💾 Saving cleaned CSV...")
    df.to_csv(output_file, index=False)
    print(f"✅ Saved cleaned CSV: {output_file}")
    
    # Show sample of cleaned data
    print()
    print("=" * 80)
    print("SAMPLE OF CLEANED DATA")
    print("=" * 80)
    print(df.head(5).to_string())
    print()
    
    # Verify data types
    print("=" * 80)
    print("DATA TYPES")
    print("=" * 80)
    print(df.dtypes)
    print()
    
    print("✅ CSV cleaned successfully!")
    print(f"   Ready for Supabase import: {output_file}")
    
    return output_file

if __name__ == '__main__':
    input_file = 'all_100_stocks_30min_2years_alpaca_20251116.csv'
    clean_csv_for_supabase(input_file)

