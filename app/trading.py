"""Automated trade execution based on alerts."""

import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from app.models import Alert, Candle, get_session
from app.config import get_config

logger = logging.getLogger(__name__)


class TradeExecutor:
    """Executes trades based on alerts and manages positions."""
    
    def __init__(self):
        self.config = get_config()
        self.position_size = float(os.getenv("POSITION_SIZE", "1000.0"))  # Default $1000 per position
        self.enabled = os.getenv("TRADING_ENABLED", "true").lower() == "true"
        self.client = None
        if self.enabled:
            self._init_alpaca_client()
        else:
            logger.info("Automated trading is disabled (TRADING_ENABLED=false)")
    
    def _init_alpaca_client(self):
        """Initialize Alpaca trading client."""
        api_key = os.getenv("ALPACA_API_KEY")
        secret_key = os.getenv("ALPACA_SECRET_KEY")
        base_url = os.getenv("ALPACA_BASE_URL", "https://paper-api.alpaca.markets")
        
        if not api_key or not secret_key:
            logger.warning("Alpaca API credentials not set. Trade execution disabled.")
            return None
        
        try:
            from alpaca.trading.client import TradingClient
            from alpaca.trading.requests import MarketOrderRequest
            from alpaca.trading.enums import OrderSide, TimeInForce
            from alpaca.data.historical import StockHistoricalDataClient
            from alpaca.data.requests import StockLatestQuoteRequest
            
            self.client = TradingClient(
                api_key=api_key,
                secret_key=secret_key,
                paper=True if 'paper' in base_url.lower() else False
            )
            self.data_client = StockHistoricalDataClient(
                api_key=api_key,
                secret_key=secret_key
            )
            self.MarketOrderRequest = MarketOrderRequest
            self.OrderSide = OrderSide
            self.TimeInForce = TimeInForce
            self.StockLatestQuoteRequest = StockLatestQuoteRequest
            
            logger.info("Alpaca trading client initialized")
            return self.client
            
        except ImportError:
            logger.error("alpaca-py not installed. Install with: pip install alpaca-py")
            return None
        except Exception as e:
            logger.error(f"Error initializing Alpaca client: {e}")
            return None
    
    def get_account_info(self) -> Optional[Dict]:
        """Get account information."""
        if not self.client:
            return None
        
        try:
            account = self.client.get_account()
            return {
                'cash': float(account.cash),
                'buying_power': float(account.buying_power),
                'portfolio_value': float(account.portfolio_value),
                'equity': float(account.equity)
            }
        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return None
    
    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current market price for a symbol."""
        if not self.data_client:
            return None
        
        try:
            quote_request = self.StockLatestQuoteRequest(symbol_or_symbols=[symbol])
            quote = self.data_client.get_stock_latest_quote(quote_request)
            
            if symbol not in quote or not quote[symbol].ask_price:
                logger.warning(f"No quote data available for {symbol}")
                return None
            
            return float(quote[symbol].ask_price)
        except Exception as e:
            logger.error(f"Error getting price for {symbol}: {e}")
            return None
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get current position for a symbol."""
        if not self.client:
            return None
        
        try:
            position = self.client.get_open_position(symbol)
            if position:
                return {
                    'symbol': position.symbol,
                    'qty': float(position.qty),
                    'avg_entry_price': float(position.avg_entry_price),
                    'market_value': float(position.market_value),
                    'cost_basis': float(position.cost_basis),
                    'unrealized_pl': float(position.unrealized_pl),
                    'unrealized_plpc': float(position.unrealized_plpc)
                }
        except Exception as e:
            # Position doesn't exist
            return None
    
    def execute_buy_order(self, alert: Alert, session: Session) -> bool:
        """
        Execute buy order based on alert.
        
        Entry rule: Buy on next 5-minute candle after alert.
        """
        if not self.enabled:
            logger.debug("Trading disabled. Skipping buy order.")
            return False
        
        if not self.client:
            logger.warning("Alpaca client not initialized. Cannot execute buy order.")
            return False
        
        try:
            # Check if we already have a position
            existing_position = self.get_position(alert.symbol)
            if existing_position:
                logger.info(f"Already have position in {alert.symbol}. Skipping buy.")
                return False
            
            # Get account balance
            account_info = self.get_account_info()
            if not account_info:
                logger.error("Could not get account info")
                return False
            
            if account_info['buying_power'] < self.position_size:
                logger.warning(
                    f"Insufficient buying power: ${account_info['buying_power']:.2f} < ${self.position_size:.2f}"
                )
                return False
            
            # Get current price (use bid for buy, but we'll use ask)
            current_price = self.get_current_price(alert.symbol)
            if not current_price:
                logger.error(f"Could not get current price for {alert.symbol}")
                return False
            
            # Calculate quantity (round down to whole shares)
            quantity = int(self.position_size / current_price)
            if quantity < 1:
                logger.warning(
                    f"Position size ${self.position_size:.2f} too small for {alert.symbol} "
                    f"at ${current_price:.2f}. Minimum 1 share required."
                )
                return False
            
            # Adjust dollar amount to actual quantity
            actual_dollar_amount = quantity * current_price
            
            # Place market order
            order_request = self.MarketOrderRequest(
                symbol=alert.symbol,
                qty=quantity,
                side=self.OrderSide.BUY,
                time_in_force=self.TimeInForce.DAY
            )
            
            order = self.client.submit_order(order_request)
            logger.info(
                f"✅ BUY ORDER EXECUTED: {quantity} shares of {alert.symbol} "
                f"at ~${current_price:.2f} (${actual_dollar_amount:.2f} total)"
            )
            logger.info(f"Order ID: {order.id}")
            
            # Log account balance after order
            account_info = self.get_account_info()
            if account_info:
                logger.info(
                    f"💰 Updated Balance: ${account_info['buying_power']:.2f} buying power remaining"
                )
            
            # Update alert status
            alert.status = "triggered"
            session.commit()
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing buy order for {alert.symbol}: {e}", exc_info=True)
            return False
    
    def check_exit_conditions(self, alert: Alert, session: Session) -> Optional[str]:
        """
        Check if exit conditions are met for a position.
        
        Returns:
            Exit reason ("take_profit" or "max_holding") or None
        """
        if not self.client:
            return None
        
        try:
            position = self.get_position(alert.symbol)
            if not position:
                return None
            
            # Check take profit
            entry_price = position['avg_entry_price']
            take_profit_price = entry_price * (1 + alert.take_profit_pct / 100)
            current_price = self.get_current_price(alert.symbol)
            
            if current_price and current_price >= take_profit_price:
                return "take_profit"
            
            # Check max holding time
            # Get alert timestamp and calculate days held
            alert_time = alert.ts
            days_held = (datetime.utcnow() - alert_time).days
            
            if days_held >= alert.max_holding_days:
                return "max_holding"
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking exit conditions for {alert.symbol}: {e}", exc_info=True)
            return None
    
    def execute_sell_order(self, symbol: str, reason: str) -> bool:
        """Execute sell order to close position."""
        if not self.client:
            logger.warning("Alpaca client not initialized. Cannot execute sell order.")
            return False
        
        try:
            position = self.get_position(symbol)
            if not position:
                logger.info(f"No position to sell for {symbol}")
                return False
            
            quantity = int(position['qty'])
            if quantity <= 0:
                return False
            
            # Place market sell order
            order_request = self.MarketOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=self.OrderSide.SELL,
                time_in_force=self.TimeInForce.DAY
            )
            
            order = self.client.submit_order(order_request)
            current_price = self.get_current_price(symbol)
            
            if current_price:
                proceeds = quantity * current_price
                logger.info(
                    f"✅ SELL ORDER EXECUTED: {quantity} shares of {symbol} "
                    f"at ~${current_price:.2f} (${proceeds:.2f} proceeds, Reason: {reason})"
                )
            else:
                logger.info(
                    f"✅ SELL ORDER EXECUTED: {quantity} shares of {symbol} "
                    f"(Reason: {reason})"
                )
            logger.info(f"Order ID: {order.id}")
            
            # Log account balance after order
            account_info = self.get_account_info()
            if account_info:
                logger.info(
                    f"💰 Updated Balance: ${account_info['buying_power']:.2f} buying power"
                )
            
            return True
            
        except Exception as e:
            logger.error(f"Error executing sell order for {symbol}: {e}", exc_info=True)
            return False
    
    def process_pending_alerts(self, session: Session) -> int:
        """Process pending alerts and execute buy orders."""
        if not self.enabled or not self.client:
            return 0
        
        try:
            # Get pending alerts that haven't been triggered
            pending_alerts = session.query(Alert).filter_by(
                status="pending"
            ).all()
            
            executed_count = 0
            for alert in pending_alerts:
                # Check if enough time has passed (next 5-min candle)
                # For now, execute immediately if alert is older than 5 minutes
                time_since_alert = datetime.utcnow() - alert.ts
                if time_since_alert >= timedelta(minutes=5):
                    if self.execute_buy_order(alert, session):
                        executed_count += 1
            
            return executed_count
            
        except Exception as e:
            logger.error(f"Error processing pending alerts: {e}", exc_info=True)
            return 0
    
    def check_and_exit_positions(self, session: Session) -> int:
        """Check all positions and exit if conditions are met."""
        if not self.enabled or not self.client:
            return 0
        
        try:
            # Get all triggered alerts (positions we're tracking)
            triggered_alerts = session.query(Alert).filter_by(
                status="triggered"
            ).all()
            
            exited_count = 0
            for alert in triggered_alerts:
                exit_reason = self.check_exit_conditions(alert, session)
                if exit_reason:
                    if self.execute_sell_order(alert.symbol, exit_reason):
                        alert.status = "expired"
                        session.commit()
                        exited_count += 1
            
            return exited_count
            
        except Exception as e:
            logger.error(f"Error checking exit conditions: {e}", exc_info=True)
            return 0

