"""Test script to run full scan and show execution flow."""

import sys
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv('.env')

from earnings_volatility_yfinance.config import get_config
from earnings_volatility_yfinance.database import DatabaseService
from earnings_volatility_yfinance.data_service import YahooDataService
from earnings_volatility_yfinance.analysis_engine import AnalysisEngine
from earnings_volatility_yfinance.execution_service import ExecutionService
from loguru import logger

# Configure logging
logger.remove()
logger.add(lambda msg: print(msg, end=''), format="{message}")

def main():
    """Run full scan simulation."""
    print("=" * 80)
    print("Earnings Volatility Trading Bot - Full Scan Simulation")
    print("=" * 80)
    
    config = get_config()
    database = DatabaseService()
    data_service = YahooDataService()
    analysis_engine = AnalysisEngine(data_service)
    execution_service = ExecutionService()
    
    print(f"\nTicker List: {', '.join(config.ticker_list)}")
    print(f"Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("\n" + "=" * 80)
    print("STEP 1: Scanning for Earnings")
    print("=" * 80)
    
    valid_signals = []
    all_results = []
    
    for ticker in config.ticker_list:
        print(f"\n{ticker}:")
        try:
            passed, metrics, rejection_reason = analysis_engine.analyze_ticker(ticker)
            
            if metrics:
                # Log to database
                record_id = database.log_signal(
                    ticker=ticker,
                    earnings_date=metrics["earnings_date"],
                    earnings_time=metrics["earnings_time"],
                    iv_slope=metrics["iv_slope"],
                    iv_rv_ratio=metrics["iv_rv_ratio"],
                    volume_30d=int(metrics["avg_volume_30d"]),
                    front_month_expiry=metrics["front_month_expiry"],
                    back_month_expiry=metrics["back_month_expiry"],
                    front_month_strike=metrics["front_month_strike"],
                    back_month_strike=metrics["back_month_strike"],
                    option_type=metrics["option_type"],
                    rejection_reason=rejection_reason
                )
                
                if record_id:
                    metrics["record_id"] = record_id
            
            if passed and metrics:
                valid_signals.append(metrics)
                print(f"  ✓ PASSED - Ready to trade!")
            else:
                print(f"  ✗ REJECTED: {rejection_reason}")
            
            all_results.append({
                "ticker": ticker,
                "passed": passed,
                "rejection_reason": rejection_reason,
                "metrics": metrics
            })
            
        except Exception as e:
            print(f"  ✗ ERROR: {str(e)[:60]}")
            all_results.append({
                "ticker": ticker,
                "passed": False,
                "rejection_reason": f"Error: {str(e)[:60]}",
                "metrics": None
            })
    
    print("\n" + "=" * 80)
    print("STEP 2: Summary of Results")
    print("=" * 80)
    
    print(f"\nTotal Tickers Scanned: {len(config.ticker_list)}")
    print(f"Valid Signals Found: {len(valid_signals)}")
    print(f"Rejected: {len(all_results) - len(valid_signals)}")
    
    if valid_signals:
        print("\n" + "=" * 80)
        print("STEP 3: Valid Trading Signals")
        print("=" * 80)
        
        for signal in valid_signals:
            ticker = signal["ticker"]
            print(f"\n{ticker}:")
            print(f"  Earnings: {signal['earnings_date'].date() if hasattr(signal['earnings_date'], 'date') else signal['earnings_date']} ({signal['earnings_time']})")
            print(f"  Current Price: ${signal['current_price']:.2f}")
            print(f"  IV Slope: {signal['iv_slope']:.4f}")
            print(f"  IV/RV Ratio: {signal['iv_rv_ratio']:.4f}")
            print(f"  Volume (30d avg): {signal['avg_volume_30d']:,.0f}")
            print(f"  Front Month: {signal['front_month_expiry'].date()} @ ${signal['front_month_strike']:.2f}")
            print(f"  Back Month: {signal['back_month_expiry'].date()} @ ${signal['back_month_strike']:.2f}")
            print(f"  Option Type: {signal['option_type'].upper()}")
            
            # Calculate estimated entry price
            front_mid = (signal["front_month_bid"] + signal["front_month_ask"]) / 2
            back_mid = (signal["back_month_bid"] + signal["back_month_ask"]) / 2
            net_price = front_mid - back_mid
            print(f"  Estimated Entry Price: ${net_price:.2f} per contract")
            
            # Calculate position size
            equity = execution_service.get_account_equity()
            risk_amount = equity * (config.trading.risk_per_trade_pct / 100.0)
            quantity = int(risk_amount / abs(net_price)) if net_price != 0 else 0
            print(f"  Estimated Position Size: {quantity} contracts (Risk: ${risk_amount:.2f})")
    
    print("\n" + "=" * 80)
    print("STEP 4: Rejection Summary")
    print("=" * 80)
    
    rejected = [r for r in all_results if not r["passed"]]
    if rejected:
        for r in rejected:
            print(f"\n{r['ticker']}: {r['rejection_reason']}")
    else:
        print("\nNo rejections (all passed or errors)")
    
    print("\n" + "=" * 80)
    print("Scan Complete")
    print("=" * 80)
    
    if valid_signals:
        print(f"\n🎯 {len(valid_signals)} ticker(s) ready for trading!")
        print("Note: Actual execution would occur during entry window (3:45 PM - 4:00 PM ET)")
    else:
        print("\n⚠️  No valid trading signals found.")
        print("Reasons could be:")
        print("  - No earnings today/tomorrow")
        print("  - Failed volume filter")
        print("  - Failed IV slope filter")
        print("  - Failed IV/RV ratio filter")
        print("  - No options data available")

if __name__ == "__main__":
    main()

