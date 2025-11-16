"""
Upload all 100 stocks (2 years) to Supabase using Supabase Python client.
Reads SQL batch files and executes them efficiently.
"""
import os
import glob
import time
from supabase import create_client, Client
from config import Config

def get_supabase_client() -> Client:
    """Initialize and return Supabase client."""
    supabase_url = Config.SUPABASE_URL
    supabase_key = Config.SUPABASE_KEY
    
    if not supabase_url or not supabase_key:
        raise ValueError("Supabase credentials not configured! Set SUPABASE_URL and SUPABASE_KEY environment variables.")
    
    return create_client(supabase_url, supabase_key)

def execute_sql_batch(supabase: Client, sql: str) -> bool:
    """Execute a SQL batch using Supabase RPC or direct SQL execution."""
    try:
        # Supabase Python client doesn't have direct SQL execution
        # We need to use the REST API or parse SQL and use table.insert()
        # For now, we'll use a workaround: parse the INSERT statement
        
        # Actually, Supabase doesn't support arbitrary SQL execution via Python client
        # We need to use the REST API directly or use a different approach
        
        # Alternative: Use Supabase's REST API with PostgREST
        import requests
        
        # Extract the SQL and execute via REST API
        # This requires the service_role key for SQL execution
        response = requests.post(
            f"{Config.SUPABASE_URL}/rest/v1/rpc/exec_sql",
            headers={
                "apikey": Config.SUPABASE_KEY,
                "Authorization": f"Bearer {Config.SUPABASE_KEY}",
                "Content-Type": "application/json"
            },
            json={"query": sql}
        )
        
        if response.status_code in [200, 201, 204]:
            return True
        else:
            print(f"   Error: {response.status_code} - {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"   Exception: {str(e)[:200]}")
        return False

def main():
    print("=" * 80)
    print("UPLOADING ALL 100 STOCKS TO SUPABASE")
    print("=" * 80)
    print()
    
    # Check Supabase credentials
    if not Config.SUPABASE_URL or not Config.SUPABASE_KEY:
        print("❌ Supabase credentials not configured!")
        print("   Set SUPABASE_URL and SUPABASE_KEY environment variables.")
        print()
        print("   Alternatively, execute SQL batches manually via Supabase SQL Editor:")
        print("   1. Open Supabase Dashboard")
        print("   2. Go to SQL Editor")
        print("   3. Copy and paste each batch_*_execute.sql file")
        print("   4. Execute (349 batches total)")
        return False
    
    # Find all batch SQL files
    batch_files = sorted(glob.glob('batch_*_execute.sql'), key=lambda x: int(x.split('_')[1]))
    
    if not batch_files:
        print("❌ No batch SQL files found!")
        print("   Run upload_to_supabase_batch.py first to generate SQL files.")
        return False
    
    print(f"📁 Found {len(batch_files)} batch SQL files")
    print()
    
    # Initialize Supabase client
    try:
        supabase = get_supabase_client()
        print("✅ Supabase client initialized")
    except Exception as e:
        print(f"❌ Error initializing Supabase client: {e}")
        return False
    
    print()
    print("🚀 Starting upload...")
    print("   Note: Supabase Python client doesn't support direct SQL execution.")
    print("   This script will attempt to use REST API, but manual execution")
    print("   via Supabase SQL Editor may be required.")
    print()
    
    successful = 0
    failed = 0
    start_time = time.time()
    
    # Execute batches
    for i, batch_file in enumerate(batch_files, 1):
        batch_num = int(batch_file.split('_')[1])
        
        # Read SQL
        with open(batch_file, 'r') as f:
            sql = f.read()
        
        # Execute SQL
        if execute_sql_batch(supabase, sql):
            successful += 1
            elapsed = time.time() - start_time
            rate = successful / elapsed if elapsed > 0 else 0
            remaining = (len(batch_files) - successful) / rate if rate > 0 else 0
            
            print(f"✅ Batch {batch_num}/{len(batch_files)}: Uploaded successfully "
                  f"({successful}/{len(batch_files)} total, ETA: {remaining/60:.1f} min)")
        else:
            failed += 1
            print(f"❌ Batch {batch_num}/{len(batch_files)}: Failed")
        
        # Small delay to avoid rate limiting
        time.sleep(0.1)
    
    elapsed_time = time.time() - start_time
    
    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"✅ Successful batches: {successful}")
    print(f"❌ Failed batches: {failed}")
    print(f"⏱️  Total time: {elapsed_time/60:.1f} minutes")
    print()
    
    if failed > 0:
        print("⚠️  Some batches failed. You may need to execute them manually")
        print("   via Supabase SQL Editor or check your Supabase configuration.")
    
    return successful > 0

if __name__ == '__main__':
    main()
