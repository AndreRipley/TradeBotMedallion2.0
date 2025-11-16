"""
Stock data fetcher module to check if a day is a "red day" (price went down).
"""
import requests
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import Config

logger = logging.getLogger(__name__)


class StockDataFetcher:
    """Fetches stock data and determines if it's a red day."""
    
    def __init__(self):
        self.api_key = Config.ALPHA_VANTAGE_API_KEY
        if not self.api_key:
            logger.warning("Alpha Vantage API key not set. Using fallback method.")
    
    def is_red_day(self, symbol: str) -> Optional[bool]:
        """
        Check if today is a red day (stock price went down).
        
        Args:
            symbol: Stock symbol (e.g., 'AAPL')
            
        Returns:
            True if red day (price went down), False if green day, None if error
        """
        try:
            # Get today's and yesterday's closing prices
            today_price = self._get_current_price(symbol)
            yesterday_price = self._get_previous_close(symbol)
            
            if today_price is None or yesterday_price is None:
                logger.error(f"Could not fetch prices for {symbol}")
                return None
            
            # Red day = current price < previous close
            is_red = today_price < yesterday_price
            
            logger.info(
                f"{symbol}: Today=${today_price:.2f}, "
                f"Yesterday=${yesterday_price:.2f}, "
                f"Red Day={'Yes' if is_red else 'No'}"
            )
            
            return is_red
            
        except Exception as e:
            logger.error(f"Error checking red day for {symbol}: {e}")
            return None
    
    def _get_current_price(self, symbol: str) -> Optional[float]:
        """Get current stock price."""
        try:
            if self.api_key:
                return self._get_price_from_alpha_vantage(symbol)
            else:
                # Fallback to Yahoo Finance (free, no API key needed)
                return self._get_price_from_yahoo(symbol)
        except Exception as e:
            logger.error(f"Error fetching current price for {symbol}: {e}")
            return None
    
    def _get_previous_close(self, symbol: str) -> Optional[float]:
        """Get previous day's closing price."""
        try:
            if self.api_key:
                return self._get_previous_close_from_alpha_vantage(symbol)
            else:
                return self._get_previous_close_from_yahoo(symbol)
        except Exception as e:
            logger.error(f"Error fetching previous close for {symbol}: {e}")
            return None
    
    def _get_price_from_alpha_vantage(self, symbol: str) -> Optional[float]:
        """Fetch current price from Alpha Vantage API."""
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'Global Quote' in data and '05. price' in data['Global Quote']:
            return float(data['Global Quote']['05. price'])
        
        logger.error(f"Unexpected Alpha Vantage response for {symbol}: {data}")
        return None
    
    def _get_previous_close_from_alpha_vantage(self, symbol: str) -> Optional[float]:
        """Fetch previous close from Alpha Vantage API."""
        url = 'https://www.alphavantage.co/query'
        params = {
            'function': 'GLOBAL_QUOTE',
            'symbol': symbol,
            'apikey': self.api_key
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if 'Global Quote' in data and '08. previous close' in data['Global Quote']:
            return float(data['Global Quote']['08. previous close'])
        
        logger.error(f"Unexpected Alpha Vantage response for {symbol}: {data}")
        return None
    
    def _get_price_from_yahoo(self, symbol: str) -> Optional[float]:
        """Fetch current price from Yahoo Finance (fallback, no API key needed)."""
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
            params = {
                'interval': '1d',
                'range': '1d'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                if 'meta' in result and 'regularMarketPrice' in result['meta']:
                    return float(result['meta']['regularMarketPrice'])
            
            logger.error(f"Unexpected Yahoo Finance response for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from Yahoo Finance for {symbol}: {e}")
            return None
    
    def _get_previous_close_from_yahoo(self, symbol: str) -> Optional[float]:
        """Fetch previous close from Yahoo Finance."""
        try:
            url = f'https://query1.finance.yahoo.com/v8/finance/chart/{symbol}'
            params = {
                'interval': '1d',
                'range': '5d'  # Get 5 days to ensure we have previous close
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'chart' in data and 'result' in data['chart']:
                result = data['chart']['result'][0]
                if 'indicators' in result and 'quote' in result['indicators']:
                    quotes = result['indicators']['quote'][0]
                    if 'close' in quotes and len(quotes['close']) >= 2:
                        # Get second-to-last close (previous day)
                        closes = [c for c in quotes['close'] if c is not None]
                        if len(closes) >= 2:
                            return float(closes[-2])
            
            logger.error(f"Could not find previous close from Yahoo Finance for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching previous close from Yahoo Finance for {symbol}: {e}")
            return None

