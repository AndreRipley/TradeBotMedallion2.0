"""Database operations for Earnings Volatility Trading Bot using Supabase."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from supabase import create_client, Client
from loguru import logger
from .config import get_config


class DatabaseService:
    """Service for interacting with Supabase database."""
    
    def __init__(self):
        """Initialize Supabase client."""
        config = get_config()
        self.client: Client = create_client(config.supabase.url, config.supabase.key)
        self.table_name = "earnings_signals"
    
    def init_db(self):
        """Initialize database table if it doesn't exist."""
        # Note: This is a placeholder - actual table creation should be done via migration
        # In production, run the SQL migration script
        pass
    
    def log_signal(
        self,
        ticker: str,
        earnings_date: datetime,
        earnings_time: str,
        iv_slope: float,
        iv_rv_ratio: float,
        volume_30d: int,
        front_month_expiry: datetime,
        back_month_expiry: datetime,
        front_month_strike: float,
        back_month_strike: float,
        option_type: str,
        rejection_reason: Optional[str] = None
    ) -> Optional[str]:
        """Log a trading signal to the database.
        
        Args:
            ticker: Stock ticker symbol
            earnings_date: Date of earnings announcement
            earnings_time: "BMO" or "AMC"
            iv_slope: Calculated IV term structure slope
            iv_rv_ratio: IV to Realized Volatility ratio
            volume_30d: 30-day average volume
            front_month_expiry: Expiration date of front month option
            back_month_expiry: Expiration date of back month option
            front_month_strike: Strike price of front month option
            back_month_strike: Strike price of back month option
            option_type: "call" or "put"
            rejection_reason: Reason for rejection if signal was filtered out
            
        Returns:
            Record ID if successful, None otherwise
        """
        try:
            data = {
                "ticker": ticker,
                "earnings_date": earnings_date.isoformat() if isinstance(earnings_date, datetime) else str(earnings_date),
                "earnings_time": earnings_time,
                "signal_time": datetime.utcnow().isoformat(),
                "status": "cancelled" if rejection_reason else "signal",
                "front_month_expiry": front_month_expiry.isoformat() if isinstance(front_month_expiry, datetime) else str(front_month_expiry),
                "back_month_expiry": back_month_expiry.isoformat() if isinstance(back_month_expiry, datetime) else str(back_month_expiry),
                "front_month_strike": float(front_month_strike),
                "back_month_strike": float(back_month_strike),
                "option_type": option_type,
                "iv_slope": float(iv_slope),
                "iv_rv_ratio": float(iv_rv_ratio),
                "volume_30d": int(volume_30d),
                "rejection_reason": rejection_reason,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table(self.table_name).insert(data).execute()
            
            if result.data:
                record_id = result.data[0].get("id")
                logger.info(f"Logged signal for {ticker}: {record_id}")
                return record_id
            else:
                logger.error(f"Failed to log signal for {ticker}: No data returned")
                return None
                
        except Exception as e:
            logger.error(f"Error logging signal for {ticker}: {e}")
            return None
    
    def log_trade(
        self,
        record_id: str,
        entry_time: datetime,
        entry_price: float,
        position_size: float
    ) -> bool:
        """Log trade execution details.
        
        Args:
            record_id: ID of the signal record
            entry_time: Time when trade was executed
            entry_price: Net debit/credit price of the spread
            position_size: Number of contracts
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "status": "traded",
                "entry_time": entry_time.isoformat(),
                "entry_price": float(entry_price),
                "position_size": int(position_size),
                "updated_at": datetime.utcnow().isoformat()
            }
            
            result = self.client.table(self.table_name).update(data).eq("id", record_id).execute()
            
            if result.data:
                logger.info(f"Updated trade record {record_id} with entry details")
                return True
            else:
                logger.error(f"Failed to update trade record {record_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error logging trade for record {record_id}: {e}")
            return False
    
    def update_position_status(
        self,
        record_id: str,
        status: str,
        exit_time: Optional[datetime] = None,
        exit_price: Optional[float] = None,
        pnl: Optional[float] = None
    ) -> bool:
        """Update position status (e.g., closed, cancelled).
        
        Args:
            record_id: ID of the trade record
            status: New status ("closed", "cancelled", etc.)
            exit_time: Time when position was closed
            exit_price: Exit price of the spread
            pnl: Profit/Loss
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if exit_time:
                data["exit_time"] = exit_time.isoformat()
            if exit_price is not None:
                data["exit_price"] = float(exit_price)
            if pnl is not None:
                data["pnl"] = float(pnl)
            
            result = self.client.table(self.table_name).update(data).eq("id", record_id).execute()
            
            if result.data:
                logger.info(f"Updated position status for record {record_id} to {status}")
                return True
            else:
                logger.error(f"Failed to update position status for record {record_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating position status for record {record_id}: {e}")
            return False
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions (status = 'traded').
        
        Returns:
            List of open position records
        """
        try:
            result = self.client.table(self.table_name).select("*").eq("status", "traded").execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching open positions: {e}")
            return []

