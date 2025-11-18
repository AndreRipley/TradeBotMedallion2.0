"""Alert service for RSI cross-under detection."""

import logging
from datetime import datetime
from typing import Optional, List
from dataclasses import dataclass
from sqlalchemy.orm import Session
from app.models import Alert, RsiValue, Candle, get_session
from app.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class RsiCrossUnderEvent:
    """RSI cross-under event."""
    symbol: str
    ts: datetime
    rsi_value: float
    price: float


class AlertService:
    """Service for detecting and storing RSI cross-under alerts."""
    
    def __init__(self):
        self.config = get_config()
        self.threshold = self.config.rsi.threshold
    
    def detect_cross_under(
        self,
        symbol: str,
        session: Optional[Session] = None
    ) -> Optional[RsiCrossUnderEvent]:
        """
        Detect if RSI just crossed below threshold.
        
        Checks if:
        - Previous candle RSI >= threshold
        - Current candle RSI < threshold
        
        Args:
            symbol: Stock symbol
            session: Database session
            
        Returns:
            RsiCrossUnderEvent if detected, None otherwise
        """
        if session is None:
            session = get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            # Get last two RSI values
            rsi_values = session.query(RsiValue).filter_by(
                symbol=symbol
            ).order_by(RsiValue.ts.desc()).limit(2).all()
            
            if len(rsi_values) < 2:
                return None
            
            current_rsi = rsi_values[0]
            previous_rsi = rsi_values[1]
            
            # Check for cross-under
            if previous_rsi.rsi_14 >= self.threshold and current_rsi.rsi_14 < self.threshold:
                # Get price at current timestamp
                candle = session.query(Candle).filter_by(
                    symbol=symbol,
                    ts=current_rsi.ts
                ).first()
                
                if candle:
                    event = RsiCrossUnderEvent(
                        symbol=symbol,
                        ts=current_rsi.ts,
                        rsi_value=current_rsi.rsi_14,
                        price=candle.close
                    )
                    return event
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting cross-under for {symbol}: {e}", exc_info=True)
            return None
        finally:
            if should_close:
                session.close()
    
    def create_alert(
        self,
        event: RsiCrossUnderEvent,
        session: Optional[Session] = None
    ) -> Alert:
        """
        Create and store an alert from a cross-under event.
        
        Args:
            event: RSI cross-under event
            session: Database session
            
        Returns:
            Created Alert object
        """
        if session is None:
            session = get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            # Check if alert already exists for this symbol/timestamp
            existing = session.query(Alert).filter_by(
                symbol=event.symbol,
                ts=event.ts
            ).first()
            
            if existing:
                logger.debug(f"Alert already exists for {event.symbol} at {event.ts}")
                return existing
            
            # Create new alert
            alert = Alert(
                symbol=event.symbol,
                ts=event.ts,
                rsi_value=event.rsi_value,
                price=event.price,
                status="pending",
                take_profit_pct=self.config.alert.take_profit_pct,
                max_holding_days=self.config.alert.max_holding_days
            )
            
            session.add(alert)
            session.commit()
            
            logger.info(
                f"Alert created: {event.symbol} RSI={event.rsi_value:.2f} "
                f"at {event.ts} (price=${event.price:.2f})"
            )
            
            return alert
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating alert: {e}", exc_info=True)
            raise
        finally:
            if should_close:
                session.close()
    
    def send_alert_notification(self, alert: Alert) -> None:
        """
        Send alert notification (console, SMS, email, webhook, etc.).
        """
        # Log to console
        logger.info(
            f"ALERT: {alert.symbol} - RSI crossed below {self.threshold} "
            f"(RSI={alert.rsi_value:.2f}, Price=${alert.price:.2f}) "
            f"at {alert.ts}"
        )
        logger.info(
            f"Trade rules: Entry on next 5-min candle, "
            f"Take profit: +{alert.take_profit_pct}%, "
            f"Max holding: {alert.max_holding_days} days"
        )
        
        # Send SMS notification if enabled
        if self.config.sms.enabled:
            self._send_sms_notification(alert)
    
    def _send_sms_notification(self, alert: Alert) -> None:
        """Send SMS notification via Twilio."""
        try:
            from twilio.rest import Client
            
            if not self.config.sms.twilio_account_sid or not self.config.sms.twilio_auth_token:
                logger.warning("Twilio credentials not configured. Skipping SMS notification.")
                return
            
            if not self.config.sms.phone_number:
                logger.warning("SMS phone number not configured. Skipping SMS notification.")
                return
            
            if not self.config.sms.twilio_from_number:
                logger.warning("Twilio from number not configured. Skipping SMS notification.")
                return
            
            # Initialize Twilio client
            client = Client(
                self.config.sms.twilio_account_sid,
                self.config.sms.twilio_auth_token
            )
            
            # Format message
            message = (
                f"🚨 BUY ALERT: {alert.symbol}\n"
                f"RSI: {alert.rsi_value:.2f} (below {self.threshold})\n"
                f"Price: ${alert.price:.2f}\n"
                f"Entry: Next 5-min candle\n"
                f"Take Profit: +{alert.take_profit_pct}%\n"
                f"Max Hold: {alert.max_holding_days} days"
            )
            
            # Send SMS
            message_obj = client.messages.create(
                body=message,
                from_=self.config.sms.twilio_from_number,
                to=self.config.sms.phone_number
            )
            
            logger.info(f"✅ SMS sent to {self.config.sms.phone_number} (SID: {message_obj.sid})")
            
        except ImportError:
            logger.warning("twilio package not installed. Install with: pip install twilio")
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}", exc_info=True)

