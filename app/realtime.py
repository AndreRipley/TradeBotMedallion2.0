"""Real-time monitoring and update loop."""

import logging
import asyncio
from datetime import datetime, timedelta, time as dt_time
from typing import List, Optional
from sqlalchemy.orm import Session
from app.models import Universe, Candle, RsiValue, get_session
from app.data_providers import IntradayPriceProvider, MockIntradayPriceProvider
from app.indicators import RsiCalculator
from app.alerts import AlertService, RsiCrossUnderEvent
from app.trading import TradeExecutor
from app.config import get_config

logger = logging.getLogger(__name__)


class RealtimeMonitor:
    """Real-time monitor for updating candles, RSI, and detecting alerts."""
    
    def __init__(
        self,
        price_provider: Optional[IntradayPriceProvider] = None
    ):
        self.config = get_config()
        self.price_provider = price_provider or MockIntradayPriceProvider()
        self.rsi_calculator = RsiCalculator()
        self.alert_service = AlertService()
        self.trade_executor = TradeExecutor()
        self.running = False
    
    def is_market_hours(self, dt: Optional[datetime] = None) -> bool:
        """Check if current time is within market hours (9:30 AM - 4:00 PM ET)."""
        if not self.config.scheduler.market_hours_only:
            return True
        
        if dt is None:
            dt = datetime.utcnow()
        
        # Convert UTC to Eastern Time
        try:
            import pytz
            utc = pytz.UTC
            et = pytz.timezone('America/New_York')
            
            # Ensure dt is timezone-aware (UTC)
            if dt.tzinfo is None:
                dt = utc.localize(dt)
            else:
                dt = dt.astimezone(utc)
            
            # Convert to ET
            et_time = dt.astimezone(et)
            
            # Market hours: 9:30 AM - 4:00 PM ET
            market_open = et_time.replace(hour=9, minute=30, second=0, microsecond=0)
            market_close = et_time.replace(hour=16, minute=0, second=0, microsecond=0)
            
            return market_open <= et_time < market_close
            
        except ImportError:
            # Fallback if pytz not available: approximate UTC offset (ET is UTC-5 or UTC-4)
            # This is approximate and doesn't handle DST properly
            logger.warning("pytz not available, using approximate UTC offset")
            et_hour = (dt.hour - 5) % 24  # Approximate UTC-5 (doesn't handle DST)
            return 9 <= et_hour < 16
    
    async def update_candles_for_symbol(
        self,
        symbol: str,
        session: Session
    ) -> int:
        """Fetch and store new candles for a symbol."""
        try:
            # Get last candle timestamp
            last_candle = session.query(Candle).filter_by(
                symbol=symbol
            ).order_by(Candle.ts.desc()).first()
            
            if last_candle:
                since = last_candle.ts
                # Ensure timezone-aware datetime
                if since.tzinfo is None:
                    import pytz
                    since = pytz.UTC.localize(since)
            else:
                import pytz
                since = datetime.now(pytz.UTC) - timedelta(days=1)
            
            # Fetch new candles
            new_candles = self.price_provider.get_latest_candles(
                symbol, since=since, interval="5min"
            )
            
            if not new_candles:
                return 0
            
            # Filter to only new ones (after 'since')
            stored_count = 0
            for candle_data in new_candles:
                if candle_data.ts > since:
                    existing = session.query(Candle).filter_by(
                        symbol=candle_data.symbol,
                        ts=candle_data.ts
                    ).first()
                    
                    if not existing:
                        candle = Candle(
                            symbol=candle_data.symbol,
                            ts=candle_data.ts,
                            open=candle_data.open,
                            high=candle_data.high,
                            low=candle_data.low,
                            close=candle_data.close,
                            volume=candle_data.volume,
                            interval=candle_data.interval
                        )
                        session.add(candle)
                        stored_count += 1
            
            session.commit()
            return stored_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating candles for {symbol}: {e}", exc_info=True)
            return 0
    
    async def update_rsi_for_symbol(
        self,
        symbol: str,
        session: Session
    ) -> int:
        """Update RSI for new candles."""
        try:
            # Get last RSI timestamp
            last_rsi = session.query(RsiValue).filter_by(
                symbol=symbol
            ).order_by(RsiValue.ts.desc()).first()
            
            if last_rsi:
                since = last_rsi.ts
            else:
                # Need to compute full history
                return self.rsi_calculator.compute_rsi_for_symbol(symbol, session=session)
            
            # Compute incremental RSI
            return self.rsi_calculator.compute_rsi_incremental(symbol, since, session=session)
            
        except Exception as e:
            logger.error(f"Error updating RSI for {symbol}: {e}", exc_info=True)
            return 0
    
    async def check_alerts_for_symbol(
        self,
        symbol: str,
        session: Session
    ) -> Optional[RsiCrossUnderEvent]:
        """Check for RSI cross-under alerts."""
        try:
            event = self.alert_service.detect_cross_under(symbol, session=session)
            
            if event:
                alert = self.alert_service.create_alert(event, session=session)
                self.alert_service.send_alert_notification(alert)
                return event
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking alerts for {symbol}: {e}", exc_info=True)
            return None
    
    async def update_symbol(self, symbol: str) -> dict:
        """Update candles, RSI, and check alerts for a symbol."""
        session = get_session()
        try:
            candles_count = await self.update_candles_for_symbol(symbol, session)
            rsi_count = await self.update_rsi_for_symbol(symbol, session)
            alert_event = await self.check_alerts_for_symbol(symbol, session)
            
            return {
                "symbol": symbol,
                "candles_added": candles_count,
                "rsi_values_added": rsi_count,
                "alert_triggered": alert_event is not None
            }
        finally:
            session.close()
    
    async def update_universe(self) -> List[dict]:
        """Update all symbols in the universe."""
        session = get_session()
        try:
            universe_symbols = [
                u.symbol for u in session.query(Universe).filter_by(active=True).all()
            ]
            session.close()
            
            logger.info(f"Updating {len(universe_symbols)} symbols in universe")
            
            results = []
            for symbol in universe_symbols:
                result = await self.update_symbol(symbol)
                results.append(result)
                logger.debug(
                    f"{symbol}: {result['candles_added']} candles, "
                    f"{result['rsi_values_added']} RSI values, "
                    f"alert={'YES' if result['alert_triggered'] else 'NO'}"
                )
            
            return results
            
        except Exception as e:
            logger.error(f"Error updating universe: {e}", exc_info=True)
            return []
    
    async def run_loop(self):
        """Main monitoring loop."""
        self.running = True
        logger.info("Starting real-time monitor")
        
        interval_seconds = self.config.scheduler.update_interval_minutes * 60
        
        while self.running:
            try:
                if self.is_market_hours():
                    logger.info("Running universe update cycle")
                    results = await self.update_universe()
                    
                    total_candles = sum(r["candles_added"] for r in results)
                    total_rsi = sum(r["rsi_values_added"] for r in results)
                    alerts_count = sum(1 for r in results if r["alert_triggered"])
                    
                    logger.info(
                        f"Update cycle complete: {total_candles} candles, "
                        f"{total_rsi} RSI values, {alerts_count} alerts"
                    )
                    
                    # Process trade execution
                    session = get_session()
                    try:
                        # Execute buy orders for pending alerts
                        buys_executed = self.trade_executor.process_pending_alerts(session)
                        if buys_executed > 0:
                            logger.info(f"Executed {buys_executed} buy orders")
                        
                        # Check and exit positions
                        exits_executed = self.trade_executor.check_and_exit_positions(session)
                        if exits_executed > 0:
                            logger.info(f"Executed {exits_executed} sell orders")
                    finally:
                        session.close()
                else:
                    logger.debug("Outside market hours, skipping update")
                
                # Wait for next interval
                await asyncio.sleep(interval_seconds)
                
            except KeyboardInterrupt:
                logger.info("Received interrupt signal, shutting down")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(interval_seconds)
    
    def stop(self):
        """Stop the monitoring loop."""
        self.running = False


async def run_realtime_monitor():
    """
    Main entry point for real-time monitoring.
    
    This function:
    - Loads universe
    - Every 5 minutes, refreshes candles + RSI
    - Detects RSI cross-under events
    - Sends alerts
    """
    monitor = RealtimeMonitor()
    await monitor.run_loop()

