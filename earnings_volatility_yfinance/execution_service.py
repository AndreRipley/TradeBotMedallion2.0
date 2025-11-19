"""Execution service for placing trades via Alpaca API."""

from datetime import datetime
from typing import Optional, Dict, Any, Tuple
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import MarketOrderRequest, LimitOrderRequest
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.models import Order
from loguru import logger
from .config import get_config


class ExecutionService:
    """Service for executing trades via Alpaca API."""
    
    def __init__(self):
        """Initialize Alpaca trading client."""
        config = get_config()
        self.client = TradingClient(
            api_key=config.alpaca.api_key,
            secret_key=config.alpaca.api_secret,
            paper=config.alpaca.paper,
            url_override=config.alpaca.base_url
        )
        self.config = config
    
    def get_account_equity(self) -> float:
        """Get current account equity.
        
        Returns:
            Account equity value
        """
        try:
            account = self.client.get_account()
            return float(account.equity)
        except Exception as e:
            logger.error(f"Error fetching account equity: {e}")
            return 0.0
    
    def calculate_position_size(self, entry_price: float) -> int:
        """Calculate position size using risk-based sizing.
        
        Args:
            entry_price: Net debit/credit price per contract
            
        Returns:
            Number of contracts to trade
        """
        equity = self.get_account_equity()
        
        if equity == 0:
            logger.error("Account equity is zero")
            return 0
        
        # Calculate risk amount
        risk_pct = self.config.trading.risk_per_trade_pct / 100.0
        risk_amount = equity * risk_pct
        
        # Calculate number of contracts
        if entry_price == 0:
            logger.error("Entry price is zero")
            return 0
        
        contracts = int(risk_amount / abs(entry_price))
        
        # Ensure minimum of 1 contract if we have enough capital
        if contracts == 0 and risk_amount >= abs(entry_price):
            contracts = 1
        
        logger.info(f"Position size: {contracts} contracts (Risk: ${risk_amount:.2f}, Entry: ${entry_price:.2f})")
        
        return contracts
    
    def submit_calendar_spread(
        self,
        ticker: str,
        front_expiry: datetime,
        back_expiry: datetime,
        strike: float,
        option_type: str,
        front_bid: float,
        front_ask: float,
        back_bid: float,
        back_ask: float,
        quantity: int
    ) -> Tuple[Optional[str], Optional[float], Optional[str]]:
        """Submit a calendar spread order.
        
        Strategy: Long Calendar Spread
        - Sell front month (short)
        - Buy back month (long)
        
        Note: Alpaca doesn't natively support calendar spreads as a single order.
        We submit two separate orders sequentially:
        1. Buy back month (long leg)
        2. Sell front month (short leg)
        
        Args:
            ticker: Underlying stock ticker
            front_expiry: Front month expiration date
            back_expiry: Back month expiration date
            strike: Strike price
            option_type: "call" or "put"
            front_bid: Front month bid price
            front_ask: Front month ask price
            back_bid: Back month bid price
            back_ask: Back month ask price
            quantity: Number of contracts
            
        Returns:
            Tuple of:
            - Order ID if successful, None otherwise
            - Entry price (net debit/credit) if successful
            - Error message if failed, None otherwise
        """
        if quantity <= 0:
            return None, None, "Invalid quantity"
        
        try:
            # Construct option symbols for Alpaca
            front_symbol = self._construct_option_symbol(
                ticker, front_expiry, strike, option_type
            )
            back_symbol = self._construct_option_symbol(
                ticker, back_expiry, strike, option_type
            )
            
            logger.info(f"Submitting calendar spread: Sell {front_symbol}, Buy {back_symbol}, Qty: {quantity}")
            
            # Calculate mid prices
            front_mid = (front_bid + front_ask) / 2
            back_mid = (back_bid + back_ask) / 2
            
            # Calendar spread: Sell front month, Buy back month
            # Net credit if front > back, net debit if back > front
            net_price = front_mid - back_mid
            
            # Step 1: Buy back month (Long leg)
            logger.info(f"Step 1: Buying back month {back_symbol}")
            back_order = self._submit_option_order(
                symbol=back_symbol,
                side=OrderSide.BUY,
                quantity=quantity,
                limit_price=back_mid
            )
            
            if not back_order:
                return None, None, "Failed to submit back month order"
            
            # Step 2: Sell front month (Short leg)
            logger.info(f"Step 2: Selling front month {front_symbol}")
            front_order = self._submit_option_order(
                symbol=front_symbol,
                side=OrderSide.SELL,
                quantity=quantity,
                limit_price=front_mid
            )
            
            if not front_order:
                # Try to cancel back order if front order fails
                try:
                    self.client.cancel_order_by_id(back_order.id)
                    logger.warning(f"Cancelled back order {back_order.id} due to front order failure")
                except:
                    pass
                return None, None, "Failed to submit front month order"
            
            logger.info(f"Calendar spread submitted: Front={front_order.id}, Back={back_order.id}")
            
            # Return the first order ID as reference
            return front_order.id, net_price, None
            
        except Exception as e:
            logger.error(f"Error submitting calendar spread for {ticker}: {e}")
            return None, None, str(e)
    
    def _submit_option_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        limit_price: float
    ) -> Optional[Order]:
        """Submit a single option order.
        
        Args:
            symbol: Option symbol
            side: BUY or SELL
            quantity: Number of contracts
            limit_price: Limit price per contract
            
        Returns:
            Order object if successful, None otherwise
        """
        try:
            order_request = LimitOrderRequest(
                symbol=symbol,
                qty=quantity,
                side=side,
                time_in_force=TimeInForce.DAY,
                limit_price=limit_price
            )
            
            order = self.client.submit_order(order_request)
            logger.info(f"Submitted {side.value} order for {symbol}: {order.id}")
            return order
            
        except Exception as e:
            logger.error(f"Error submitting order for {symbol}: {e}")
            return None
    
    def _construct_option_symbol(
        self,
        ticker: str,
        expiry: datetime,
        strike: float,
        option_type: str
    ) -> str:
        """Construct Alpaca option symbol.
        
        Format: TICKER YYMMDD C/P STRIKE
        Example: AAPL 240315C00150000
        
        Args:
            ticker: Stock ticker
            expiry: Expiration date
            strike: Strike price
            option_type: "call" or "put"
            
        Returns:
            Option symbol string
        """
        # Format date as YYMMDD
        date_str = expiry.strftime("%y%m%d")
        
        # Option type: C for call, P for put
        type_char = "C" if option_type.lower() == "call" else "P"
        
        # Format strike: 8 digits with leading zeros, no decimal
        # Example: 150.0 -> 00150000
        strike_str = f"{int(strike * 1000):08d}"
        
        # Construct symbol
        symbol = f"{ticker} {date_str}{type_char}{strike_str}"
        
        return symbol
    
    def close_position(
        self,
        ticker: str,
        front_expiry: datetime,
        back_expiry: datetime,
        strike: float,
        option_type: str,
        quantity: int
    ) -> Tuple[Optional[str], Optional[float], Optional[str]]:
        """Close a calendar spread position.
        
        Args:
            ticker: Underlying stock ticker
            front_expiry: Front month expiration date
            back_expiry: Back month expiration date
            strike: Strike price
            option_type: "call" or "put"
            quantity: Number of contracts to close
            
        Returns:
            Tuple of:
            - Order ID if successful, None otherwise
            - Exit price if successful
            - Error message if failed
        """
        try:
            # Construct option symbols
            front_symbol = self._construct_option_symbol(
                ticker, front_expiry, strike, option_type
            )
            back_symbol = self._construct_option_symbol(
                ticker, back_expiry, strike, option_type
            )
            
            logger.info(f"Closing calendar spread: Buy {front_symbol}, Sell {back_symbol}, Qty: {quantity}")
            
            # Close spread: Buy back front month, Sell back month
            # This reverses the original position
            
            # Buy front month (to close short)
            front_order = self._submit_option_order(
                symbol=front_symbol,
                side=OrderSide.BUY,
                quantity=quantity,
                limit_price=0  # Market order (set to 0 or fetch current price)
            )
            
            if not front_order:
                return None, None, "Failed to close front month"
            
            # Sell back month (to close long)
            back_order = self._submit_option_order(
                symbol=back_symbol,
                side=OrderSide.SELL,
                quantity=quantity,
                limit_price=0  # Market order
            )
            
            if not back_order:
                return None, None, "Failed to close back month"
            
            # Calculate exit price (would need to fetch actual fill prices)
            # For now, return placeholder
            exit_price = 0.0  # TODO: Fetch actual exit price from order fills
            
            logger.info(f"Calendar spread closed: Front={front_order.id}, Back={back_order.id}")
            
            return front_order.id, exit_price, None
            
        except Exception as e:
            logger.error(f"Error closing calendar spread for {ticker}: {e}")
            return None, None, str(e)
    
    def get_open_positions(self) -> list:
        """Get all open positions.
        
        Returns:
            List of Position objects
        """
        try:
            positions = self.client.get_all_positions()
            return positions
        except Exception as e:
            logger.error(f"Error fetching open positions: {e}")
            return []

