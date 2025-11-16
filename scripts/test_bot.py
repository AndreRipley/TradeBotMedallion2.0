"""
Test script to verify the trading bot components work correctly.
"""
import logging
from stock_data import StockDataFetcher
from trader import Trader
from config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_stock_data():
    """Test stock data fetching."""
    logger.info("Testing stock data fetcher...")
    fetcher = StockDataFetcher()
    
    test_symbol = "AAPL"
    is_red = fetcher.is_red_day(test_symbol)
    
    if is_red is not None:
        logger.info(f"✅ Stock data fetcher working. {test_symbol} is {'red' if is_red else 'green'} day.")
    else:
        logger.warning(f"⚠️  Could not fetch data for {test_symbol}. Check API keys or internet connection.")


def test_trader():
    """Test trader (will simulate if no API keys)."""
    logger.info("Testing trader...")
    trader = Trader()
    
    test_symbol = "AAPL"
    # Use a larger amount for testing (enough to buy at least 1 share)
    success = trader.buy_stock(test_symbol, 500.0)
    
    if success:
        logger.info(f"✅ Trader working (simulated or real order executed).")
    else:
        logger.warning(f"⚠️  Trader test failed.")


def main():
    """Run all tests."""
    logger.info("=" * 60)
    logger.info("Running Trading Bot Tests")
    logger.info("=" * 60)
    
    logger.info(f"\nConfiguration:")
    logger.info(f"  Stocks: {Config.STOCKS}")
    logger.info(f"  Position Size: ${Config.POSITION_SIZE}")
    logger.info(f"  Trade Time: {Config.TRADE_TIME}")
    
    logger.info("\n" + "-" * 60)
    test_stock_data()
    
    logger.info("\n" + "-" * 60)
    test_trader()
    
    logger.info("\n" + "=" * 60)
    logger.info("Tests complete!")
    logger.info("=" * 60)


if __name__ == '__main__':
    main()

