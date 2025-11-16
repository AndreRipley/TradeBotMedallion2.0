"""
Execute small batches via MCP Supabase execute_sql.
Reads batch files and provides SQL for execution.
"""
import glob
import os

def main():
    batch_files = sorted(glob.glob('small_batch_*_execute.sql'), key=lambda x: int(x.split('_')[2]))
    
    print(f"Found {len(batch_files)} small batch files")
    print(f"\nTo execute all batches:")
    print(f"1. Read each batch file")
    print(f"2. Execute via MCP Supabase execute_sql tool")
    print(f"\nBatch files ready:")
    for i, batch_file in enumerate(batch_files[:20], 1):
        size = os.path.getsize(batch_file)
        print(f"  {i}. {batch_file} ({size:,} bytes)")
    if len(batch_files) > 20:
        print(f"  ... and {len(batch_files) - 20} more batches")
    
    print(f"\nTotal batches to execute: {len(batch_files)}")
    print(f"Estimated time: ~{len(batch_files) * 2 / 60:.1f} minutes if executed sequentially")

if __name__ == '__main__':
    main()

