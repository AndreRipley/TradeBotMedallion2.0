#!/usr/bin/env python3
"""
Monitor and display backtest results when complete.
"""
import time
import os
import glob

def check_backtest_complete():
    """Check if backtest has completed."""
    # Look for the results CSV file
    csv_files = glob.glob('anomaly_backtest_top200_*.csv')
    if csv_files:
        latest = max(csv_files, key=os.path.getmtime)
        return latest
    return None

def monitor_backtest():
    """Monitor backtest progress."""
    print("Monitoring backtest progress...")
    print("Press Ctrl+C to stop monitoring\n")
    
    start_time = time.time()
    last_stock_count = 0
    
    while True:
        try:
            # Check log file
            if os.path.exists('top200_results.log'):
                with open('top200_results.log', 'r') as f:
                    lines = f.readlines()
                    fetch_lines = [l for l in lines if 'Fetching data for' in l]
                    current_stock_count = len(fetch_lines)
                    
                    if current_stock_count > last_stock_count:
                        progress = (current_stock_count / 200) * 100
                        elapsed = time.time() - start_time
                        print(f"Progress: {current_stock_count}/200 stocks ({progress:.1f}%) - {elapsed:.0f}s elapsed")
                        last_stock_count = current_stock_count
                    
                    # Check if complete
                    if 'SUMMARY RESULTS' in ''.join(lines[-50:]):
                        print("\n✅ Backtest complete!")
                        return True
            
            # Check for results file
            result_file = check_backtest_complete()
            if result_file:
                print(f"\n✅ Backtest complete! Results in: {result_file}")
                return True
            
            time.sleep(5)
            
        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            return False

if __name__ == '__main__':
    monitor_backtest()

