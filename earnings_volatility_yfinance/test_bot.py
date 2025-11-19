"""Test script for Earnings Volatility Trading Bot (yfinance version)."""

import os
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv()

def test_config():
    """Test configuration loading."""
    logger.info("Testing configuration...")
    try:
        from .config import get_config
        config = get_config()
        logger.info("✓ Configuration loaded successfully")
        logger.info(f"  Alpaca Paper Trading: {config.alpaca.paper}")
        logger.info(f"  Supabase URL: {config.supabase.url}")
        logger.info(f"  Ticker list: {', '.join(config.ticker_list)}")
        logger.info(f"  Risk per trade: {config.trading.risk_per_trade_pct}%")
        logger.info(f"  IV Slope threshold: {config.trading.iv_slope_threshold}")
        logger.info(f"  Min volume: {config.trading.min_volume:,}")
        return True
    except Exception as e:
        logger.error(f"✗ Configuration error: {e}")
        return False

def test_database():
    """Test database connection."""
    logger.info("Testing database connection...")
    try:
        from .database import DatabaseService
        db = DatabaseService()
        # Try a simple query
        positions = db.get_open_positions()
        logger.info(f"✓ Database connection successful (found {len(positions)} open positions)")
        return True
    except Exception as e:
        logger.error(f"✗ Database error: {e}")
        logger.warning("  Make sure Supabase table 'earnings_signals' exists")
        return False

def test_data_service():
    """Test data service."""
    logger.info("Testing data service (yfinance)...")
    try:
        from .data_service import YahooDataService
        ds = YahooDataService()
        
        # Test with a single ticker
        test_ticker = "AAPL"
        logger.info(f"  Testing with {test_ticker}...")
        
        # Test market data
        logger.info("  Fetching market data...")
        market_data = ds.get_market_data(test_ticker, days=30)
        if market_data:
            logger.info(f"  ✓ Market data retrieved: ${market_data['current_price']:.2f}")
            logger.info(f"    30-day avg volume: {market_data['avg_volume_30d']:,.0f}")
        else:
            logger.warning("  ⚠ No market data returned")
        
        # Test earnings date
        logger.info("  Fetching earnings date...")
        earnings = ds.get_earnings_date(test_ticker)
        if earnings:
            logger.info(f"  ✓ Earnings date: {earnings['date']} ({earnings['time']})")
        else:
            logger.warning("  ⚠ No earnings date found")
        
        return True
    except Exception as e:
        logger.error(f"✗ Data service error: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False

def test_execution_service():
    """Test execution service (paper trading only)."""
    logger.info("Testing execution service...")
    try:
        from .execution_service import ExecutionService
        es = ExecutionService()
        
        equity = es.get_account_equity()
        logger.info(f"✓ Execution service connected (Account equity: ${equity:,.2f})")
        
        positions = es.get_open_positions()
        logger.info(f"  Open positions: {len(positions)}")
        
        return True
    except Exception as e:
        logger.error(f"✗ Execution service error: {e}")
        logger.warning("  Make sure Alpaca API credentials are correct")
        return False

def main():
    """Run all tests."""
    logger.info("=" * 80)
    logger.info("Earnings Volatility Trading Bot (yfinance) - Component Tests")
    logger.info("=" * 80)
    
    results = []
    
    results.append(("Configuration", test_config()))
    results.append(("Database", test_database()))
    results.append(("Data Service", test_data_service()))
    results.append(("Execution Service", test_execution_service()))
    
    logger.info("=" * 80)
    logger.info("Test Results Summary")
    logger.info("=" * 80)
    
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        logger.info(f"{status}: {name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        logger.info("\n✓ All tests passed!")
    else:
        logger.warning("\n⚠ Some tests failed. Check the errors above.")
        logger.info("\nNext steps:")
        logger.info("1. Run Supabase migration: migrations/001_create_earnings_signals.sql")
        logger.info("2. Verify all environment variables in .env file")
        logger.info("3. Check yfinance rate limits (may need to increase YFINANCE_DELAY_SECONDS)")

if __name__ == "__main__":
    main()

