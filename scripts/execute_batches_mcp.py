"""
Helper script to execute SQL batches via MCP Supabase execute_sql.
This script reads SQL files and prints instructions for MCP execution.
"""
import glob
import os

def main():
    batch_files = sorted(glob.glob('batch_*_execute.sql'), key=lambda x: int(x.split('_')[1]))
    
    print(f"Found {len(batch_files)} batch SQL files")
    print(f"\nTo execute via MCP Supabase execute_sql:")
    print(f"1. Read each batch file")
    print(f"2. Execute via mcp_supabase_execute_sql tool")
    print(f"\nBatch files:")
    for i, batch_file in enumerate(batch_files[:10], 1):
        size = os.path.getsize(batch_file)
        print(f"  {i}. {batch_file} ({size:,} bytes)")
    if len(batch_files) > 10:
        print(f"  ... and {len(batch_files) - 10} more")

if __name__ == '__main__':
    main()

