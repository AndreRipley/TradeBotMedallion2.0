"""
Scheduler module to execute trades using Improved Anomaly Buy+Sell Strategy.
"""
import schedule
import time
import logging
from datetime import datetime
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
    
    def run(self):
        """Start the scheduler and run continuously."""
        logger.info(f"Starting trading bot scheduler")
        logger.info(f"Monitoring stocks: {', '.join(self.stocks)}")
        logger.info(f"Checking frequency: Every minute during market hours (9:30 AM - 4:00 PM ET)")
        logger.info(f"Position monitoring: Every minute (integrated with signal checks)")
        
        logger.info("Scheduler started. Checking for anomalies and monitoring positions every minute during market hours...")
        
        # Run scheduler - check every minute
        try:
            while True:
                # Check if it's market hours
                if self._is_market_hours():
                    # Execute trading logic every minute during market hours
                    # This now also checks positions (better risk management)
                    self._execute_trading_logic()
                    # Also check positions separately for positions not in watchlist
                    self._monitor_positions()
                
                # Sleep for 1 minute before next check
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
                        self.strategy.position_tracker.add_position(
                            symbol,
                            position['shares'],
                            position['avg_entry_price']
                        )
                        logger.info(f"✅ Successfully executed buy order for {symbol}")
                        logger.info(f"   Shares: {position['shares']:.2f}, Entry: ${position['avg_entry_price']:.2f}")
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
                
                # Get position info
                position = self.strategy.position_tracker.get_position(symbol)
                if position:
                    logger.info(f"   Entry Price: ${position['entry_price']:.2f}")
                    logger.info(f"   Current Price: ${signal.get('current_price', 0):.2f}")
                    
                    success = self.trader.sell_stock(symbol)
                    
                    if success:
                        # Calculate profit
                        profit = (signal.get('current_price', 0) - position['entry_price']) * position['shares']
                        self.strategy.update_performance(symbol, profit)
                        self.strategy.position_tracker.remove_position(symbol)
                        logger.info(f"✅ Successfully executed sell order for {symbol}")
                        logger.info(f"   Profit/Loss: ${profit:.2f}")
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
        positions = self.strategy.position_tracker.get_all_positions()
        
        if not positions:
            return
        
        logger.info(f"\n🔍 Monitoring {len(positions)} positions for stop-loss/trailing stop...")
        
        for symbol, position in positions.items():
            # Get current price
            try:
                import yfinance as yf
                ticker = yf.Ticker(symbol)
                current_data = ticker.history(period='1d', interval='1m')
                if not current_data.empty:
                    current_price = float(current_data['Close'].iloc[-1])
                    
                    # Check stop-loss and trailing stop
                    should_sell, reason = self.strategy.position_tracker.update_position(symbol, current_price)
                    
                    if should_sell:
                        logger.warning(f"⚠️  {reason} triggered for {symbol} at ${current_price:.2f}")
                        logger.info(f"   Entry: ${position['entry_price']:.2f}, Highest: ${position['highest_price']:.2f}")
                        
                        success = self.trader.sell_stock(symbol)
                        
                        if success:
                            profit = (current_price - position['entry_price']) * position['shares']
                            self.strategy.update_performance(symbol, profit)
                            self.strategy.position_tracker.remove_position(symbol)
                            logger.info(f"✅ Position closed for {symbol}")
                            logger.info(f"   Profit/Loss: ${profit:.2f}")
                        else:
                            logger.error(f"❌ Failed to close position for {symbol}")
            except Exception as e:
                logger.error(f"Error monitoring position for {symbol}: {e}")

