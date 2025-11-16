"""
Scheduler module to execute trades using Improved Anomaly Buy+Sell Strategy.
"""
import schedule
import time
import logging
from datetime import datetime, timedelta
import pytz
from typing import Dict, Optional
from config import Config
from trader import Trader
from live_anomaly_strategy import LiveAnomalyStrategy, LivePositionTracker

logger = logging.getLogger(__name__)


class TradingScheduler:
    """Schedules and executes trading logic using Improved Anomaly Buy+Sell Strategy."""
    
    def __init__(self):
        self.trader = Trader()
        self.stocks = Config.STOCKS
        self.trade_time = Config.TRADE_TIME
        self.timezone = pytz.timezone(Config.TIMEZONE)
        self.position_size = Config.POSITION_SIZE
        
        # Initialize improved anomaly strategy
        self.strategy = LiveAnomalyStrategy(
            min_severity=1.0,
            stop_loss_pct=0.05,
            trailing_stop_pct=0.05
        )
        
        logger.info("Improved Anomaly Buy+Sell Strategy initialized")
        logger.info(f"Stop-Loss: 5%, Trailing Stop: 5%, Min Severity: 1.0")
        
    def _is_market_hours(self) -> bool:
        """Check if current time is during market hours (9:30 AM - 4:00 PM ET)."""
        now = datetime.now(self.timezone)
        market_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        market_close = now.replace(hour=16, minute=0, second=0, microsecond=0)
        
        # Check if it's a weekday (Monday=0, Sunday=6)
        is_weekday = now.weekday() < 5
        
        return is_weekday and market_open <= now <= market_close
    
    def _get_next_market_open(self) -> datetime:
        """Calculate the next market open time."""
        now = datetime.now(self.timezone)
        today_open = now.replace(hour=9, minute=30, second=0, microsecond=0)
        
        # If market already opened today, check tomorrow
        if now >= today_open.replace(hour=16, minute=0) or now.weekday() >= 5:
            # Market closed for today or it's weekend
            days_ahead = 1
            # Skip weekends
            while (now + timedelta(days=days_ahead)).weekday() >= 5:
                days_ahead += 1
            next_open = (now + timedelta(days=days_ahead)).replace(hour=9, minute=30, second=0, microsecond=0)
        elif now < today_open:
            # Market hasn't opened yet today
            next_open = today_open
        else:
            # Market is currently open, return current time (shouldn't happen in this context)
            next_open = now
        
        return next_open
    
    def run(self):
        """Start the scheduler and run continuously."""
        logger.info(f"Starting trading bot scheduler")
        logger.info(f"Monitoring stocks: {', '.join(self.stocks)}")
        logger.info(f"Checking frequency: Every minute during market hours (9:30 AM - 4:00 PM ET)")
        logger.info(f"Position monitoring: Every minute (integrated with signal checks)")
        
        logger.info("Scheduler started. Checking for anomalies and monitoring positions every minute during market hours...")
        
        # Run scheduler - optimized to only check during market hours
        try:
            while True:
                # Check if it's market hours
                if self._is_market_hours():
                    # Execute trading logic every minute during market hours
                    # This now also checks positions (better risk management)
                    self._execute_trading_logic()
                    # Also check positions separately for positions not in watchlist
                    self._monitor_positions()
                    
                    # Sleep for 1 minute during market hours
                    time.sleep(60)
                else:
                    # Outside market hours - sleep until next market open
                    next_open = self._get_next_market_open()
                    now = datetime.now(self.timezone)
                    sleep_seconds = (next_open - now).total_seconds()
                    
                    if sleep_seconds > 0:
                        logger.info(f"⏸️  Market closed. Next market open: {next_open.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                        logger.info(f"   Sleeping for {sleep_seconds/3600:.1f} hours until market opens...")
                        time.sleep(min(sleep_seconds, 3600))  # Sleep max 1 hour at a time to check for market hours
                    else:
                        # Shouldn't happen, but fallback to 1 minute
                        time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
    
    def _execute_trading_logic(self):
        """Execute the main trading logic using Improved Anomaly Strategy."""
        # Only log when there's actual activity to reduce verbosity
        has_activity = False
        
        for symbol in self.stocks:
            symbol = symbol.strip().upper()
            if not symbol:
                continue
            
            # Check for trading signals
            signal = self.strategy.check_signals(symbol)
            
            if signal['action'] == 'BUY':
                has_activity = True
                logger.info("=" * 60)
                logger.info(f"🕐 {datetime.now(self.timezone).strftime('%H:%M:%S')} - BUY SIGNAL detected")
                logger.info("=" * 60)
                logger.info(f"🟢 BUY SIGNAL detected for {symbol}")
                logger.info(f"   Reason: {signal.get('reason', 'Anomaly detected')}")
                logger.info(f"   Severity: {signal.get('severity', 0):.2f}")
                logger.info(f"   Anomaly Types: {', '.join(signal.get('anomaly_types', []))}")
                
                # Get dynamic position size
                position_size = self.strategy.get_position_size(symbol, self.position_size)
                logger.info(f"   Position Size: ${position_size:.2f}")
                
                success = self.trader.buy_stock(symbol, position_size)
                
                if success:
                    # Get actual shares and entry price from position
                    position = self.trader.get_position(symbol)
                    if position:
                        # Calculate new shares added (Alpaca combines positions, so we need to track incrementally)
                        existing_positions = self.strategy.position_tracker.get_all_positions_for_symbol(symbol)
                        existing_total_shares = sum(p['shares'] for p in existing_positions)
                        new_shares = position['shares'] - existing_total_shares
                        
                        if new_shares > 0:
                            # Add new logical position with current entry price
                            # Note: Alpaca averages entry prices, but we track each buy separately
                            self.strategy.position_tracker.add_position(
                                symbol,
                                new_shares,
                                position['avg_entry_price']  # Use Alpaca's averaged price for new shares
                            )
                            logger.info(f"✅ Successfully executed buy order for {symbol}")
                            logger.info(f"   New Shares: {new_shares:.2f}, Entry: ${position['avg_entry_price']:.2f}")
                            logger.info(f"   Total Shares: {position['shares']:.2f} ({len(existing_positions) + 1} positions)")
                        else:
                            logger.info(f"✅ Buy order executed for {symbol} (shares already tracked)")
                    else:
                        logger.warning(f"⚠️  Buy order executed but position not found")
                else:
                    logger.error(f"❌ Failed to execute buy order for {symbol}")
            
            elif signal['action'] == 'SELL':
                has_activity = True
                logger.info("=" * 60)
                logger.info(f"🕐 {datetime.now(self.timezone).strftime('%H:%M:%S')} - SELL SIGNAL detected")
                logger.info("=" * 60)
                logger.info(f"🔴 SELL SIGNAL detected for {symbol}")
                logger.info(f"   Reason: {signal.get('reason', 'Anomaly detected')}")
                
                # Get all positions for this symbol
                all_positions = self.strategy.position_tracker.get_all_positions_for_symbol(symbol)
                if all_positions:
                    current_price = signal.get('current_price', 0)
                    total_shares = sum(p['shares'] for p in all_positions)
                    
                    logger.info(f"   Positions: {len(all_positions)}")
                    for i, pos in enumerate(all_positions, 1):
                        logger.info(f"   Position {i}: {pos['shares']:.2f} shares @ ${pos['entry_price']:.2f}")
                    logger.info(f"   Current Price: ${current_price:.2f}")
                    
                    success = self.trader.sell_stock(symbol)
                    
                    if success:
                        # Calculate profit for all positions (Alpaca sells everything)
                        total_profit = 0
                        for pos in all_positions:
                            profit = (current_price - pos['entry_price']) * pos['shares']
                            total_profit += profit
                            self.strategy.update_performance(symbol, profit)
                        
                        # Remove all positions (Alpaca sells everything)
                        self.strategy.position_tracker.remove_position(symbol)
                        logger.info(f"✅ Successfully executed sell order for {symbol}")
                        logger.info(f"   Total Profit/Loss: ${total_profit:.2f} ({len(all_positions)} positions closed)")
                    else:
                        logger.error(f"❌ Failed to execute sell order for {symbol}")
                else:
                    logger.warning(f"⚠️  Sell signal but no position found for {symbol}")
            
            # Don't log HOLD signals to reduce verbosity (checking every minute)
        
        # Only log completion if there was activity
        if has_activity:
            logger.info("=" * 60)
            logger.info("Trading logic execution complete.\n")
    
    def _monitor_positions(self):
        """Monitor existing positions for stop-loss and trailing stop triggers."""
        all_positions_dict = self.strategy.position_tracker.get_all_positions()
        
        if not all_positions_dict:
            return
        
        total_positions = sum(len(positions) for positions in all_positions_dict.values())
        logger.info(f"\n🔍 Monitoring {total_positions} positions across {len(all_positions_dict)} symbols for stop-loss/trailing stop...")
        
        for symbol, positions_list in all_positions_dict.items():
            # Get current price
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                current_data = ticker.history(period='1d', interval='1m')
                if not current_data.empty:
                    current_price = float(current_data['Close'].iloc[-1])
                    
                    # Log price check to Supabase
                    try:
                        from supabase_logger import log_price_check
                        log_price_check(
                            symbol=symbol,
                            price=current_price,
                            context='position_monitor',
                            additional_data={'volume': float(current_data['Volume'].iloc[-1]) if 'Volume' in current_data.columns else None}
                        )
                    except Exception as e:
                        # Don't fail if Supabase logging fails
                        pass
                    
                    # Check stop-loss and trailing stop
                    should_sell, reason, position_to_sell = self.strategy.position_tracker.update_position(symbol, current_price)
                    
                    if should_sell:
                        # Get all positions for this symbol
                        all_positions = self.strategy.position_tracker.get_all_positions_for_symbol(symbol)
                        total_shares = sum(p['shares'] for p in all_positions)
                        
                        logger.warning(f"⚠️  {reason} triggered for {symbol} at ${current_price:.2f}")
                        if position_to_sell:
                            logger.info(f"   Triggering Position: Entry ${position_to_sell['entry_price']:.2f}, Highest: ${position_to_sell['highest_price']:.2f}")
                        logger.info(f"   Total Positions: {len(all_positions)}, Total Shares: {total_shares:.2f}")
                        
                        success = self.trader.sell_stock(symbol)
                        
                        if success:
                            # Calculate profit for all positions (Alpaca sells everything)
                            total_profit = 0
                            for pos in all_positions:
                                profit = (current_price - pos['entry_price']) * pos['shares']
                                total_profit += profit
                                self.strategy.update_performance(symbol, profit)
                            
                            # Remove all positions (Alpaca sells everything)
                            self.strategy.position_tracker.remove_position(symbol)
                            logger.info(f"✅ Position closed for {symbol}")
                            logger.info(f"   Total Profit/Loss: ${total_profit:.2f} ({len(all_positions)} positions closed)")
                        else:
                            logger.error(f"❌ Failed to close position for {symbol}")
            except Exception as e:
                logger.error(f"Error monitoring position for {symbol}: {e}")

