"""Alternative data service using earnings calendar API instead of per-ticker checks."""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import requests
from loguru import logger
import time
from .config import get_config


class EarningsCalendarService:
    """Service for fetching earnings calendar from API Ninjas (or other providers)."""
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize earnings calendar service.
        
        Args:
            api_key: API Ninjas API key (optional, can be set via env var)
        """
        self.api_key = api_key or get_config().trading.__dict__.get('api_ninjas_key')
        self.base_url = "https://api.api-ninjas.com/v1/earningscalendar"
        self.delay = 1.0  # Delay between requests
    
    def _rate_limit(self):
        """Apply rate limiting."""
        time.sleep(self.delay)
    
    def get_earnings_for_date(self, date: datetime) -> List[Dict[str, Any]]:
        """Get all earnings announcements for a specific date.
        
        Args:
            date: Date to fetch earnings for
            
        Returns:
            List of earnings announcements with keys:
            - ticker: str
            - date: datetime
            - time: str ("BMO" or "AMC")
        """
        if not self.api_key:
            logger.warning("API Ninjas key not set, cannot fetch earnings calendar")
            return []
        
        try:
            self._rate_limit()
            
            date_str = date.strftime("%Y-%m-%d")
            url = self.base_url
            params = {"date": date_str}
            headers = {"X-Api-Key": self.api_key}
            
            response = requests.get(url, params=params, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                earnings_list = []
                
                for earning in data:
                    ticker = earning.get("symbol") or earning.get("ticker")
                    earnings_date_str = earning.get("date") or earning.get("earnings_date")
                    earnings_time_raw = earning.get("time") or earning.get("earnings_time", "AMC")
                    
                    if not ticker or not earnings_date_str:
                        continue
                    
                    # Parse date
                    try:
                        earnings_date = datetime.strptime(earnings_date_str, "%Y-%m-%d")
                    except:
                        continue
                    
                    # Normalize time
                    earnings_time = self._normalize_earnings_time(earnings_time_raw)
                    
                    earnings_list.append({
                        "ticker": ticker.upper(),
                        "date": earnings_date,
                        "time": earnings_time
                    })
                
                logger.info(f"Found {len(earnings_list)} earnings for {date_str}")
                return earnings_list
            else:
                logger.error(f"API Ninjas returned status {response.status_code}: {response.text[:200]}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching earnings calendar: {e}")
            return []
    
    def get_upcoming_earnings(
        self,
        target_date: Optional[datetime] = None,
        days_ahead: int = 1
    ) -> List[Dict[str, Any]]:
        """Get all earnings for date range.
        
        Args:
            target_date: Start date (default: today)
            days_ahead: Number of days ahead to fetch
            
        Returns:
            List of all earnings announcements in the date range
        """
        if target_date is None:
            target_date = datetime.now()
        
        all_earnings = []
        
        for i in range(days_ahead + 1):
            date = target_date + timedelta(days=i)
            earnings = self.get_earnings_for_date(date)
            all_earnings.extend(earnings)
        
        return all_earnings
    
    @staticmethod
    def _normalize_earnings_time(time_str: str) -> str:
        """Normalize earnings time string to BMO or AMC."""
        if not time_str:
            return "AMC"
        
        time_upper = str(time_str).upper().strip()
        
        bmo_keywords = ["BMO", "BEFORE MARKET OPEN", "BEFORE OPEN", "PRE-MARKET"]
        amc_keywords = ["AMC", "AFTER MARKET CLOSE", "AFTER CLOSE", "AFTER HOURS"]
        
        if any(keyword in time_upper for keyword in bmo_keywords):
            return "BMO"
        elif any(keyword in time_upper for keyword in amc_keywords):
            return "AMC"
        else:
            return "AMC"  # Default

