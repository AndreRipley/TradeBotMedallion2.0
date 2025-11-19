"""Main entry point for Earnings Volatility Trading Bot (yfinance version)."""

import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from loguru import logger
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from .config import get_config
from .database import DatabaseService
from .data_service import YahooDataService
from .analysis_engine import AnalysisEngine
from .execution_service import ExecutionService


class EarningsVolatilityBot:
    """Main bot class orchestrating the earnings volatility strategy."""
    
    def __init__(self):
        """Initialize bot components."""
        self.config = get_config()
        self.database = DatabaseService()
        self.data_service = YahooDataService()
        self.analysis_engine = AnalysisEngine(self.data_service)
        self.execution_service = ExecutionService()
        
        # Market timezone (ET)
        self.market_tz = pytz.timezone("America/New_York")
        
        # Initialize database
        self.database.init_db()
        
        # Configure logging
        logger.add(
            "logs/earnings_volatility_yfinance_{time}.log",
            rotation="1 day",
            retention="30 days",
            level="INFO"
        )
    
    def is_market_open(self) -> bool:
        """Check if market is currently open.
        
        Returns:
            True if market is open, False otherwise
        """
        now_et = datetime.now(self.market_tz)
        weekday = now_et.weekday()
        
        # Market is closed on weekends
        if weekday >= 5:  # Saturday = 5, Sunday = 6
            return False
        
        # Market hours: 9:30 AM - 4:00 PM ET
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        
        return market_open <= now_et <= market_close
    
    def scan_and_filter(self) -> List[Dict[str, Any]]:
        """Scan ticker list for earnings and filter.
        
        Returns:
            List of valid trading signals with metrics
        """
        logger.info(f"Scanning {len(self.config.ticker_list)} tickers for earnings")
        
        valid_signals = []
        
        for ticker in self.config.ticker_list:
            try:
                # Analyze ticker
                passed, metrics, rejection_reason = self.analysis_engine.analyze_ticker(ticker)
                
                # Log signal to database
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
        
        logger.info(f"Found {len(valid_signals)} valid signals after filtering")
        
        return valid_signals
    
    def execute_trades(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute trades for valid signals.
        
        Args:
            signals: List of valid trading signals
            
        Returns:
            List of execution results
        """
        if not signals:
            logger.info("No signals to execute")
            return []
        
        # Check max positions limit
        open_positions = self.database.get_open_positions()
        available_slots = self.config.trading.max_positions - len(open_positions)
        
        if available_slots <= 0:
            logger.warning(f"Max positions ({self.config.trading.max_positions}) reached")
            return []
        
        # Limit signals to available slots
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
                
                # Submit calendar spread order
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
                    # Log trade execution
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
        """Close positions that should be exited."""
        open_positions = self.database.get_open_positions()
        
        if not open_positions:
            logger.info("No open positions to close")
            return
        
        now_et = datetime.now(self.market_tz)
        logger.info(f"Checking {len(open_positions)} open positions for exit...")
        
        for position in open_positions:
            earnings_date_str = position.get("earnings_date")
            ticker = position.get("ticker")
            record_id = position.get("id")
            
            if not earnings_date_str or not ticker or not record_id:
                continue
            
            try:
                # Parse earnings date
                if "T" in earnings_date_str or " " in earnings_date_str:
                    earnings_date = datetime.fromisoformat(earnings_date_str.replace("Z", "+00:00"))
                else:
                    earnings_date = datetime.strptime(earnings_date_str, "%Y-%m-%d")
                
                # Convert to ET timezone
                if earnings_date.tzinfo is None:
                    earnings_date_et = self.market_tz.localize(earnings_date)
                else:
                    earnings_date_et = earnings_date.astimezone(self.market_tz)
                
                # Calculate exit time (15 min after market open next trading day)
                exit_date = earnings_date_et + timedelta(days=1)
                while exit_date.weekday() >= 5:  # Skip weekends
                    exit_date += timedelta(days=1)
                
                market_open = exit_date.replace(hour=9, minute=30, second=0, microsecond=0)
                exit_time = market_open + timedelta(minutes=self.config.trading.exit_minutes_after_open)
                
                # Check if it's time to exit
                if now_et >= exit_time:
                    logger.info(f"Closing position for {ticker} (exit time reached)")
                    
                    # Get position details
                    front_expiry_str = position.get("front_month_expiry")
                    back_expiry_str = position.get("back_month_expiry")
                    strike = position.get("front_month_strike")
                    option_type = position.get("option_type", "call")
                    quantity = position.get("position_size", 1)
                    
                    if not all([front_expiry_str, back_expiry_str, strike]):
                        continue
                    
                    # Parse expiration dates
                    try:
                        front_expiry = datetime.fromisoformat(front_expiry_str.replace("Z", "+00:00"))
                        back_expiry = datetime.fromisoformat(back_expiry_str.replace("Z", "+00:00"))
                    except:
                        continue
                    
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
                        
                        self.database.update_position_status(
                            record_id=record_id,
                            status="closed",
                            exit_time=datetime.utcnow(),
                            exit_price=exit_price,
                            pnl=pnl
                        )
                        
                        logger.info(f"✓ Closed {ticker}: Order {order_id}, P&L: ${pnl:.2f}" if pnl else f"✓ Closed {ticker}: Order {order_id}")
                        
            except Exception as e:
                logger.error(f"Error processing position exit for {ticker}: {e}")
    
    def run_scan(self):
        """Run the main scanning and execution loop.
        
        Strategy Timing:
        - Entry: Execute trades ~15 minutes before market close (3:45 PM ET)
        - Exit: Close positions ~15 minutes after market open next day (9:45 AM ET)
        """
        logger.info("=" * 80)
        logger.info("Earnings Volatility Trading Bot (yfinance) - Starting Scan")
        logger.info("=" * 80)
        
        now_et = datetime.now(self.market_tz)
        logger.info(f"Current time: {now_et.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Ticker list: {', '.join(self.config.ticker_list)}")
        
        # Check if market is open
        if not self.is_market_open():
            logger.info("Market is closed. Skipping scan.")
            return
        
        # Determine if we're in entry window or exit window
        market_close = now_et.replace(hour=16, minute=0, second=0, microsecond=0)
        market_open = now_et.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # Entry window: 15 minutes before close (3:45 PM - 4:00 PM ET)
        entry_window_start = market_close - timedelta(minutes=self.config.trading.entry_minutes_before_close)
        entry_window_end = market_close
        
        # Exit window: 15 minutes after open (9:45 AM - 10:00 AM ET)
        exit_window_start = market_open + timedelta(minutes=self.config.trading.exit_minutes_after_open)
        exit_window_end = market_open + timedelta(minutes=self.config.trading.exit_minutes_after_open + 15)
        
        in_entry_window = entry_window_start <= now_et <= entry_window_end
        in_exit_window = exit_window_start <= now_et <= exit_window_end
        
        # Handle entry window (15 min before close)
        if in_entry_window:
            logger.info(f"✓ In ENTRY window: {entry_window_start.strftime('%H:%M:%S')} - {entry_window_end.strftime('%H:%M:%S')} ET")
            logger.info("Scanning tickers for earnings and executing new positions...")
            
            # Scan and filter
            signals = self.scan_and_filter()
            
            if signals:
                # Execute trades
                results = self.execute_trades(signals)
                successful = len([r for r in results if r.get('success')])
                logger.info(f"Execution complete: {successful}/{len(results)} trades successful")
            else:
                logger.info("No valid signals found")
        
        # Handle exit window (15 min after open)
        elif in_exit_window:
            logger.info(f"✓ In EXIT window: {exit_window_start.strftime('%H:%M:%S')} - {exit_window_end.strftime('%H:%M:%S')} ET")
            logger.info("Closing positions that have reached exit time...")
            self.close_positions()
        
        else:
            # Not in either window
            time_until_entry = (entry_window_start - now_et).total_seconds() / 60
            time_until_exit = (exit_window_start - now_et).total_seconds() / 60
            
            if time_until_entry > 0:
                logger.info(f"Not in entry/exit window. Next entry window in {time_until_entry:.0f} minutes")
            elif time_until_exit > 0:
                logger.info(f"Not in entry/exit window. Next exit window in {time_until_exit:.0f} minutes")
            else:
                logger.info("Not in entry/exit window. Waiting for next trading session.")
        
        logger.info("=" * 80)
        logger.info("Scan Complete")
        logger.info("=" * 80)


def main():
    """Main entry point."""
    try:
        bot = EarningsVolatilityBot()
        bot.run_scan()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

