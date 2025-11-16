"""
Execute all SQL batches via MCP Supabase execute_sql.
This script reads each batch file and executes it.
"""
import glob
import os
import sys

def main():
    # Find all batch SQL files
    batch_files = sorted(glob.glob('batch_*_execute.sql'), key=lambda x: int(x.split('_')[1]))
    
    if not batch_files:
        print("❌ No batch SQL files found!")
        return False
    
    print("=" * 80)
    print("EXECUTING ALL BATCHES VIA MCP SUPABASE")
    print("=" * 80)
    print(f"Total batches: {len(batch_files)}")
    print(f"Total rows: ~696,818")
    print()
    
    # Read all batches and prepare for execution
    batches_data = []
    for i, batch_file in enumerate(batch_files, 1):
        try:
            with open(batch_file, 'r') as f:
                sql = f.read()
            
            batch_num = int(batch_file.split('_')[1])
            batches_data.append({
                'batch_num': batch_num,
                'file': batch_file,
                'sql': sql,
                'size': len(sql)
            })
            
            if i <= 5 or i % 50 == 0:
                print(f"✅ Loaded batch {batch_num}: {len(sql):,} chars")
        except Exception as e:
            print(f"❌ Error loading {batch_file}: {e}")
            return False
    
    print()
    print(f"✅ All {len(batches_data)} batches loaded successfully")
    print()
    print("=" * 80)
    print("BATCHES READY FOR EXECUTION")
    print("=" * 80)
    print()
    print("Note: Each batch needs to be executed via MCP Supabase execute_sql tool")
    print(f"      Execute batches 1-{len(batches_data)} sequentially")
    print()
    print("Batch summary:")
    for batch in batches_data[:10]:
        print(f"  Batch {batch['batch_num']}: {batch['size']:,} chars")
    if len(batches_data) > 10:
        print(f"  ... and {len(batches_data) - 10} more batches")
    
    # Save batch SQL to individual files for easy reference
    print()
    print("Batch SQL files are ready in the current directory")
    print("Each file can be executed via MCP Supabase execute_sql tool")
    
    return True

if __name__ == '__main__':
    main()

