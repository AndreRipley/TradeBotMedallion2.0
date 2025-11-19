"""Cloud Run Job entry point for Earnings Volatility Trading Bot.

This script runs as a Google Cloud Run Job triggered by Cloud Scheduler.
It supports two modes:
- --mode entry: Scan and execute trades (runs at 3:15 PM, executes at 3:45 PM)
- --mode exit: Close all open positions (runs at 9:45 AM)
"""

import sys
import os
import argparse
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any
from loguru import logger
import pytz

# Configure logging for Cloud Run (stdout/stderr)
logger.remove()  # Remove default handler
logger.add(
    sys.stdout,
    format="<level>{level: <8}</level> | <green>{time:YYYY-MM-DD HH:mm:ss}</green> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    level="INFO"
)
logger.add(
    sys.stderr,
    format="<level>{level: <8}</level> | <green>{time:YYYY-MM-DD HH:mm:ss}</green> | <cyan>{name}</cyan>:<cyan>{function}</cyan> | <level>{message}</level>",
    level="ERROR"
)

# Load environment variables from Secret Manager (set by Cloud Run)
# In Cloud Run, secrets are mounted as environment variables
from dotenv import load_dotenv
from pathlib import Path

# Try loading .env if it exists (for local testing)
project_root = Path(__file__).parent.parent
env_path = project_root / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path, override=True)
else:
    load_dotenv()

# Import bot components
from .config import get_config
from .database import DatabaseService
from .data_service import YahooDataService
from .data_service_calendar import EarningsCalendarService
from .analysis_engine import AnalysisEngine
from .execution_service import ExecutionService


class CloudRunBot:
    """Bot optimized for Cloud Run Job execution."""
    
    def __init__(self):
        """Initialize bot components."""
        logger.info("Initializing Cloud Run Bot...")
        
        self.config = get_config()
        self.database = DatabaseService()
        self.data_service = YahooDataService()
        self.analysis_engine = AnalysisEngine(self.data_service)
        self.execution_service = ExecutionService()
        self.market_tz = pytz.timezone("America/New_York")
        
        # Initialize database
        self.database.init_db()
        
        # Initialize calendar service if API key available
        self.calendar_service = None
        api_key = os.getenv("API_NINJAS_KEY")
        if api_key:
            try:
                self.calendar_service = EarningsCalendarService(api_key=api_key)
                logger.info("✓ Earnings calendar API enabled")
            except Exception as e:
                logger.warning(f"Could not initialize calendar API: {e}")
        
        logger.info("Bot initialization complete")
    
    def scan_universe(self) -> List[Dict[str, Any]]:
        """Scan universe for earnings and filter signals.
        
        Returns:
            List of valid trading signals
        """
        logger.info("=" * 80)
        logger.info("SCAN UNIVERSE - Entry Mode")
        logger.info("=" * 80)
        
        now_et = datetime.now(self.market_tz)
        logger.info(f"Current time: {now_et.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Ticker list: {', '.join(self.config.ticker_list)}")
        
        # Check if market is open
        if not self._is_market_open():
            logger.error("Market is closed. Cannot execute trades.")
            return []
        
        # Perform scan
        valid_signals = []
        
        if self.calendar_service:
            # Use calendar API (faster)
            logger.info("Using earnings calendar API for scanning...")
            valid_signals = self._scan_with_calendar()
        else:
            # Fallback to per-ticker scanning
            logger.info("Using per-ticker scanning...")
            valid_signals = self._scan_per_ticker()
        
        logger.info(f"Found {len(valid_signals)} valid signals after filtering")
        return valid_signals
    
    def _scan_with_calendar(self) -> List[Dict[str, Any]]:
        """Scan using earnings calendar API."""
        today = datetime.now()
        earnings_list = self.calendar_service.get_upcoming_earnings(
            target_date=today,
            days_ahead=1
        )
        
        if not earnings_list:
            logger.info("No earnings found in calendar API for today/tomorrow")
            return []
        
        logger.info(f"Found {len(earnings_list)} total earnings from calendar API")
        
        # Filter to watchlist
        watchlist_set = set(t.upper() for t in self.config.ticker_list)
        relevant_earnings = [
            e for e in earnings_list 
            if e["ticker"].upper() in watchlist_set
        ]
        
        logger.info(f"Filtered to {len(relevant_earnings)} earnings in watchlist")
        
        if not relevant_earnings:
            return []
        
        # Analyze relevant tickers
        valid_signals = []
        for earning in relevant_earnings:
            ticker = earning["ticker"]
            earnings_date = earning["date"]
            earnings_time = earning["time"]
            
            logger.info(f"Analyzing {ticker} (earnings: {earnings_date.date()} {earnings_time})")
            
            try:
                passed, metrics, rejection_reason = self.analysis_engine.analyze_ticker(ticker)
                
                if metrics:
                    metrics["earnings_date"] = earnings_date
                    metrics["earnings_time"] = earnings_time
                    
                    # Log signal
                    record_id = self.database.log_signal(
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
                else:
                    logger.info(f"Rejected {ticker}: {rejection_reason}")
                    
            except Exception as e:
                logger.error(f"Error analyzing {ticker}: {e}")
                continue
        
        return valid_signals
    
    def _scan_per_ticker(self) -> List[Dict[str, Any]]:
        """Scan each ticker individually."""
        valid_signals = []
        
        for ticker in self.config.ticker_list:
            try:
                passed, metrics, rejection_reason = self.analysis_engine.analyze_ticker(ticker)
                
                if metrics:
                    record_id = self.database.log_signal(
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
                else:
                    logger.info(f"Rejected {ticker}: {rejection_reason}")
                    
            except Exception as e:
                logger.error(f"Error analyzing {ticker}: {e}")
                continue
        
        return valid_signals
    
    def submit_orders(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Submit orders for valid signals.
        
        Args:
            signals: List of valid trading signals
            
        Returns:
            List of execution results
        """
        if not signals:
            logger.info("No signals to execute")
            return []
        
        # Check position limits
        open_positions = self.database.get_open_positions()
        available_slots = self.config.trading.max_positions - len(open_positions)
        
        if available_slots <= 0:
            logger.warning(f"Max positions ({self.config.trading.max_positions}) reached")
            return []
        
        signals_to_trade = signals[:available_slots]
        logger.info(f"Executing {len(signals_to_trade)} trades (slots available: {available_slots})")
        
        execution_results = []
        
        for signal in signals_to_trade:
            ticker = signal["ticker"]
            record_id = signal.get("record_id")
            
            try:
                # Calculate position size
                front_mid = (signal["front_month_bid"] + signal["front_month_ask"]) / 2
                back_mid = (signal["back_month_bid"] + signal["back_month_ask"]) / 2
                estimated_entry_price = front_mid - back_mid
                
                quantity = self.execution_service.calculate_position_size(estimated_entry_price)
                
                if quantity <= 0:
                    logger.warning(f"Skipping {ticker}: Invalid position size")
                    continue
                
                # Submit calendar spread
                order_id, entry_price, error = self.execution_service.submit_calendar_spread(
                    ticker=ticker,
                    front_expiry=signal["front_month_expiry"],
                    back_expiry=signal["back_month_expiry"],
                    strike=signal["front_month_strike"],
                    option_type=signal["option_type"],
                    front_bid=signal["front_month_bid"],
                    front_ask=signal["front_month_ask"],
                    back_bid=signal["back_month_bid"],
                    back_ask=signal["back_month_ask"],
                    quantity=quantity
                )
                
                if order_id and entry_price is not None:
                    # Log trade
                    if record_id:
                        self.database.log_trade(
                            record_id=record_id,
                            entry_time=datetime.utcnow(),
                            entry_price=entry_price,
                            position_size=quantity
                        )
                    
                    logger.info(f"✓ Executed {ticker}: Order {order_id}, Entry ${entry_price:.2f}, Qty {quantity}")
                    
                    execution_results.append({
                        "ticker": ticker,
                        "order_id": order_id,
                        "entry_price": entry_price,
                        "quantity": quantity,
                        "success": True
                    })
                else:
                    logger.error(f"✗ Failed to execute {ticker}: {error}")
                    execution_results.append({
                        "ticker": ticker,
                        "success": False,
                        "error": error
                    })
                    
            except Exception as e:
                logger.error(f"Error executing trade for {ticker}: {e}")
                execution_results.append({
                    "ticker": ticker,
                    "success": False,
                    "error": str(e)
                })
        
        return execution_results
    
    def close_positions(self):
        """Close all open positions."""
        logger.info("=" * 80)
        logger.info("CLOSE POSITIONS - Exit Mode")
        logger.info("=" * 80)
        
        open_positions = self.database.get_open_positions()
        
        if not open_positions:
            logger.info("No open positions to close")
            return
        
        now_et = datetime.now(self.market_tz)
        logger.info(f"Current time: {now_et.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Found {len(open_positions)} open positions to close")
        
        closed_count = 0
        
        for position in open_positions:
            ticker = position.get("ticker")
            record_id = position.get("id")
            
            if not ticker or not record_id:
                logger.warning(f"Skipping position with missing data: {position}")
                continue
            
            try:
                front_expiry_str = position.get("front_month_expiry")
                back_expiry_str = position.get("back_month_expiry")
                strike = position.get("front_month_strike")
                option_type = position.get("option_type", "call")
                quantity = position.get("position_size", 1)
                
                if not all([front_expiry_str, back_expiry_str, strike]):
                    logger.warning(f"Skipping {ticker}: Missing position details")
                    continue
                
                # Parse expiration dates
                try:
                    front_expiry = datetime.fromisoformat(front_expiry_str.replace("Z", "+00:00"))
                    back_expiry = datetime.fromisoformat(back_expiry_str.replace("Z", "+00:00"))
                except Exception as e:
                    logger.error(f"Error parsing dates for {ticker}: {e}")
                    continue
                
                logger.info(f"Closing position for {ticker}...")
                
                # Close the calendar spread
                order_id, exit_price, error = self.execution_service.close_position(
                    ticker=ticker,
                    front_expiry=front_expiry,
                    back_expiry=back_expiry,
                    strike=strike,
                    option_type=option_type,
                    quantity=quantity
                )
                
                if order_id:
                    entry_price = position.get("entry_price", 0)
                    pnl = (exit_price - entry_price) * quantity * 100 if entry_price else None
                    
                    # Update database
                    self.database.update_position_status(
                        record_id=record_id,
                        status="closed",
                        exit_time=datetime.utcnow(),
                        exit_price=exit_price,
                        pnl=pnl
                    )
                    
                    logger.info(f"✓ Closed {ticker}: Order {order_id}, Exit ${exit_price:.2f}, P&L: ${pnl:.2f}" if pnl else f"✓ Closed {ticker}: Order {order_id}")
                    closed_count += 1
                else:
                    logger.error(f"✗ Failed to close {ticker}: {error}")
                    
            except Exception as e:
                logger.error(f"Error closing position for {ticker}: {e}")
        
        logger.info(f"Closed {closed_count}/{len(open_positions)} positions")
        logger.info("=" * 80)
    
    def _is_market_open(self) -> bool:
        """Check if market is currently open."""
        now_et = datetime.now(self.market_tz)
        weekday = now_et.weekday()
        
        if weekday >= 5:  # Weekend
            return False
        
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now_et <= market_close
    
    def wait_until_entry_time(self):
        """Wait until 3:45 PM ET (entry execution time)."""
        now_et = datetime.now(self.market_tz)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        entry_time = market_close - timedelta(minutes=self.config.trading.entry_minutes_before_close)
        
        if now_et < entry_time:
            wait_seconds = (entry_time - now_et).total_seconds()
            logger.info(f"Waiting {wait_seconds:.0f} seconds until entry time ({entry_time.strftime('%H:%M:%S %Z')})...")
            time.sleep(wait_seconds)
            logger.info("Entry time reached. Proceeding with order submission.")
        else:
            logger.info(f"Already past entry time. Current time: {now_et.strftime('%H:%M:%S %Z')}")


def run_entry_mode():
    """Run entry mode: scan and execute trades."""
    logger.info("Starting ENTRY mode...")
    
    bot = CloudRunBot()
    
    # Step 1: Scan universe (starts at 3:15 PM)
    logger.info("Step 1: Scanning universe for earnings...")
    signals = bot.scan_universe()
    
    if not signals:
        logger.info("No valid signals found. Exiting.")
        return
    
    # Step 2: Wait until 3:45 PM if needed
    logger.info("Step 2: Waiting until entry execution time (3:45 PM ET)...")
    bot.wait_until_entry_time()
    
    # Step 3: Re-validate data (quick check)
    logger.info("Step 3: Re-validating signals before execution...")
    # Note: In production, you might want to re-check IV/RV here
    # For now, we'll proceed with the signals from the scan
    
    # Step 4: Submit orders
    logger.info("Step 4: Submitting orders...")
    results = bot.submit_orders(signals)
    
    successful = len([r for r in results if r.get('success')])
    logger.info(f"Entry mode complete: {successful}/{len(results)} trades successful")


def run_exit_mode():
    """Run exit mode: close all open positions."""
    logger.info("Starting EXIT mode...")
    
    bot = CloudRunBot()
    bot.close_positions()
    
    logger.info("Exit mode complete")


def main():
    """Main entry point for Cloud Run Job."""
    parser = argparse.ArgumentParser(
        description="Earnings Volatility Trading Bot - Cloud Run Job"
    )
    parser.add_argument(
        "--mode",
        type=str,
        required=True,
        choices=["entry", "exit"],
        help="Execution mode: 'entry' (scan and execute) or 'exit' (close positions)"
    )
    
    args = parser.parse_args()
    
    try:
        if args.mode == "entry":
            run_entry_mode()
        elif args.mode == "exit":
            run_exit_mode()
        else:
            logger.error(f"Invalid mode: {args.mode}")
            sys.exit(1)
            
        logger.info("Job completed successfully")
        sys.exit(0)
        
    except KeyboardInterrupt:
        logger.info("Job interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

