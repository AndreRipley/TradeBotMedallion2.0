"""
Fetch last 20 stocks (31-50) from top 50 at 30-minute intervals for the past 2 years using Alpaca API.
"""
import pandas as pd
from datetime import datetime, timedelta
import pytz
from config import Config
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Last 20 stocks from top 50 (stocks 31-50)
LAST_20_STOCKS = [
    'ACN', 'NKE', 'LIN', 'DHR', 'VZ', 'TXN', 'PM', 'NEE', 'HON', 'UPS',
    'QCOM', 'RTX', 'BMY', 'AMGN', 'SPGI', 'DE', 'LOW', 'INTU', 'BKNG', 'SBUX'
]

# Import the fetch function from the main script
def fetch_stock_alpaca_1year(symbol: str, data_client, start_date, end_date):
    """Fetch 1 year of 30-minute data for a single stock."""
    try:
        from alpaca.data.requests import StockBarsRequest
        from alpaca.data.timeframe import TimeFrame
        
        print(f"   📡 Fetching {symbol}...", end=' ', flush=True)
        
        request_params = StockBarsRequest(
            symbol_or_symbols=[symbol],
            timeframe=TimeFrame.Minute,
            start=start_date.date(),
            end=end_date.date()
        )
        
        bars = data_client.get_stock_bars(request_params)
        
        if not bars or not hasattr(bars, 'data') or symbol not in bars.data:
            print(f"❌ No data")
            return None
        
        df = bars.df
        
        if df.empty:
            print(f"❌ Empty")
            return None
        
        if 'symbol' in df.index.names:
            df = df.loc[symbol]
        
        df = df.reset_index()
        
        if 'timestamp' in df.columns:
            df['Datetime'] = pd.to_datetime(df['timestamp'])
        elif len(df.index) > 0 and isinstance(df.index, pd.DatetimeIndex):
            df['Datetime'] = df.index
        else:
            datetime_cols = [col for col in df.columns if 'time' in col.lower() or 'date' in col.lower()]
            if datetime_cols:
                df['Datetime'] = pd.to_datetime(df[datetime_cols[0]])
            else:
                print(f"❌ No timestamp column")
                return None
        
        df = df.set_index('Datetime')
        
        df_resampled = df.resample('30min').agg({
            'open': 'first',
            'high': 'max',
            'low': 'min',
            'close': 'last',
            'volume': 'sum',
            'trade_count': 'sum' if 'trade_count' in df.columns else 'first',
            'vwap': 'mean' if 'vwap' in df.columns else 'first'
        }).dropna()
        
        df = df_resampled.reset_index()
        
        if 'Datetime' not in df.columns:
            if 'timestamp' in df.columns:
                df['Datetime'] = pd.to_datetime(df['timestamp'])
            else:
                df['Datetime'] = df.index if isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df.index)
        
        if not pd.api.types.is_datetime64_any_dtype(df['Datetime']):
            df['Datetime'] = pd.to_datetime(df['Datetime'])
        
        et_tz = pytz.timezone('America/New_York')
        if df['Datetime'].dt.tz is None:
            df['Datetime'] = df['Datetime'].dt.tz_localize('UTC')
        df['Datetime'] = df['Datetime'].dt.tz_convert(et_tz)
        
        df['Date'] = df['Datetime'].dt.date
        df['Time'] = df['Datetime'].dt.time
        
        market_open = pd.Timestamp('09:30').time()
        market_close = pd.Timestamp('16:00').time()
        
        filtered_data = df[
            (df['Time'] >= market_open) & 
            (df['Time'] <= market_close)
        ].copy()
        
        if filtered_data.empty:
            print(f"❌ No market hours data")
            return None
        
        filtered_data = filtered_data.sort_values('Datetime')
        
        filtered_data = filtered_data.rename(columns={
            'open': 'Open',
            'high': 'High',
            'low': 'Low',
            'close': 'Close',
            'volume': 'Volume'
        })
        
        filtered_data['Symbol'] = symbol
        
        print(f"✅ {len(filtered_data)} data points")
        return filtered_data
        
    except Exception as e:
        print(f"❌ Error: {str(e)[:50]}")
        return None


def main():
    if not Config.ALPACA_API_KEY or not Config.ALPACA_SECRET_KEY:
        print("❌ Alpaca API credentials not configured!")
        return None
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=730)  # 2 years
    
    print("=" * 80)
    print("FETCHING LAST 20 STOCKS (31-50) FROM TOP 50 (30-MINUTE INTERVALS) - 2 YEARS")
    print("Using: Alpaca API")
    print("=" * 80)
    print(f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"Interval: 30 minutes")
    print(f"Market Hours: 9:30 AM - 4:00 PM ET")
    print(f"Stocks: {len(LAST_20_STOCKS)} stocks")
    print(f"Stocks: {', '.join(LAST_20_STOCKS)}")
    print()
    
    try:
        from alpaca.data.historical import StockHistoricalDataClient
        
        data_client = StockHistoricalDataClient(
            api_key=Config.ALPACA_API_KEY,
            secret_key=Config.ALPACA_SECRET_KEY
        )
        
        print("📡 Fetching data from Alpaca API...")
        print()
        
        all_data = []
        successful = []
        failed = []
        
        for i, symbol in enumerate(LAST_20_STOCKS, 1):
            print(f"[{i}/{len(LAST_20_STOCKS)}] {symbol}:", end=' ')
            
            data = fetch_stock_alpaca_1year(symbol, data_client, start_date, end_date)
            
            if data is not None:
                all_data.append(data)
                successful.append(symbol)
            else:
                failed.append(symbol)
        
        if not all_data:
            print("\n❌ No data fetched for any stocks")
            return None
        
        print()
        print("=" * 80)
        print("COMBINING DATA")
        print("=" * 80)
        
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df = combined_df.sort_values(['Symbol', 'Datetime'])
        
        print(f"✅ Combined {len(combined_df)} total data points")
        
        print()
        print("=" * 80)
        print("FETCH SUMMARY")
        print("=" * 80)
        print(f"✅ Successful: {len(successful)} stocks")
        print(f"❌ Failed: {len(failed)} stocks")
        
        if successful:
            print(f"\n✅ Successfully fetched: {', '.join(successful)}")
        
        if failed:
            print(f"\n❌ Failed: {', '.join(failed)}")
        
        print()
        print("=" * 80)
        print("DATA STATISTICS BY STOCK")
        print("=" * 80)
        
        stats_list = []
        for symbol in successful:
            stock_data = combined_df[combined_df['Symbol'] == symbol]
            if not stock_data.empty:
                stats_list.append({
                    'Symbol': symbol,
                    'Data Points': len(stock_data),
                    'Date Range': f"{stock_data['Date'].min()} to {stock_data['Date'].max()}",
                    'Trading Days': stock_data['Date'].nunique(),
                    'Avg Price': f"${stock_data['Close'].mean():.2f}",
                    'High': f"${stock_data['High'].max():.2f}",
                    'Low': f"${stock_data['Low'].min():.2f}",
                    'Total Volume': f"{int(stock_data['Volume'].sum()):,}"
                })
        
        stats_df = pd.DataFrame(stats_list)
        print(stats_df.to_string(index=False))
        
        output_file = f"last20_top50_30min_2years_alpaca_{end_date.strftime('%Y%m%d')}.csv"
        combined_df.to_csv(output_file, index=False)
        print()
        print(f"✅ Combined data saved to: {output_file}")
        print(f"   Total rows: {len(combined_df):,}")
        
        return combined_df
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == '__main__':
    data = main()
    
    if data is not None:
        print()
        print("=" * 80)
        print("✅ Data fetch complete!")
        print("=" * 80)
    else:
        print()
        print("❌ Failed to fetch data")

