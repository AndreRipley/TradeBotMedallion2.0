"""Data service for fetching market data from Yahoo Finance (yfinance)."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import yfinance as yf
import pandas as pd
import numpy as np
from loguru import logger
import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError
)
from .config import get_config


class YFRateLimitError(Exception):
    """Custom exception for yfinance rate limits."""
    pass


class YahooDataService:
    """Service for interacting with Yahoo Finance via yfinance."""
    
    def __init__(self):
        """Initialize Yahoo Finance data service."""
        self.config = get_config()
        self.delay = self.config.trading.yfinance_delay_seconds
    
    def _rate_limit(self):
        """Apply rate limiting between requests."""
        time.sleep(self.delay)
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((YFRateLimitError, Exception)),
        reraise=True
    )
    def get_earnings_date(self, ticker: str) -> Optional[Dict[str, Any]]:
        """Get next earnings announcement date and time.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dictionary with keys:
            - date: datetime (earnings date)
            - time: str ("BMO" or "AMC")
            - None if no earnings found or error
        """
        try:
            self._rate_limit()
            
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # Try to get earnings date from info
            earnings_date = None
            earnings_time = "AMC"  # Default to after market close
            
            # Check various possible fields in info
            # yfinance may have: earningsDate, earningsTimestamp, earningsTimestampStart, etc.
            earnings_fields = ["earningsDate", "earningsTimestamp", "earningsTimestampStart"]
            
            for field in earnings_fields:
                if field in info and info[field]:
                    earnings_date_raw = info[field]
                    
                    # Handle different formats
                    if isinstance(earnings_date_raw, list) and len(earnings_date_raw) > 0:
                        earnings_date_raw = earnings_date_raw[0]
                    
                    if isinstance(earnings_date_raw, (int, float)):
                        # Unix timestamp
                        try:
                            earnings_date = datetime.fromtimestamp(earnings_date_raw)
                            break  # Found valid date
                        except:
                            continue
                    elif isinstance(earnings_date_raw, str):
                        # Try parsing string date
                        try:
                            earnings_date = datetime.strptime(earnings_date_raw, "%Y-%m-%d")
                            break  # Found valid date
                        except:
                            try:
                                earnings_date = datetime.fromtimestamp(int(earnings_date_raw))
                                break  # Found valid date
                            except:
                                continue
            
            # Also check earningsCalendar
            if earnings_date is None:
                try:
                    self._rate_limit()
                    calendar = stock.calendar
                    if calendar is not None:
                        # Calendar can be a dict or DataFrame
                        if isinstance(calendar, dict):
                            # Dict format: {"Earnings Date": [date1, date2, ...]}
                            if "Earnings Date" in calendar:
                                earnings_dates_list = calendar["Earnings Date"]
                                if earnings_dates_list and len(earnings_dates_list) > 0:
                                    # Get first earnings date
                                    earnings_date_obj = earnings_dates_list[0]
                                    # Convert date to datetime
                                    if hasattr(earnings_date_obj, 'year'):
                                        earnings_date = datetime.combine(earnings_date_obj, datetime.min.time())
                                    else:
                                        earnings_date = datetime.fromisoformat(str(earnings_date_obj))
                        elif hasattr(calendar, 'index'):
                            # DataFrame format (less common)
                            earnings_dates = calendar.index.tolist()
                            if earnings_dates:
                                earnings_date = earnings_dates[0].to_pydatetime()
                except Exception as e:
                    logger.debug(f"Could not get earnings calendar for {ticker}: {e}")
            
            if earnings_date is None:
                logger.debug(f"No earnings date found for {ticker}")
                return None
            
            # Determine if BMO or AMC (default to AMC)
            # yfinance doesn't always provide this, so we'll default to AMC
            # You could enhance this by checking earnings time from other sources
            
            # Convert to UTC and then to date
            if earnings_date.tzinfo is None:
                earnings_date = earnings_date.replace(tzinfo=None)
            
            return {
                "date": earnings_date,
                "time": earnings_time
            }
            
        except Exception as e:
            logger.error(f"Error fetching earnings date for {ticker}: {e}")
            # Check if it's a rate limit issue
            if "429" in str(e) or "rate limit" in str(e).lower():
                raise YFRateLimitError(f"Rate limit hit for {ticker}")
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((YFRateLimitError, Exception)),
        reraise=True
    )
    def get_market_data(self, ticker: str, days: int = 30) -> Optional[Dict[str, Any]]:
        """Fetch historical market data for a ticker.
        
        Args:
            ticker: Stock ticker symbol
            days: Number of days of history to fetch
            
        Returns:
            Dictionary with keys:
            - prices: List of close prices
            - volumes: List of volumes
            - dates: List of dates
            - current_price: float
            - avg_volume_30d: float
        """
        try:
            self._rate_limit()
            
            stock = yf.Ticker(ticker)
            
            # Fetch historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 10)  # Add buffer
            
            hist = stock.history(start=start_date, end=end_date, interval="1d")
            
            if hist is None or hist.empty:
                logger.warning(f"No market data returned for {ticker}")
                return None
            
            # Extract data
            prices = hist["Close"].tolist()
            volumes = hist["Volume"].tolist()
            dates = hist.index.tolist()
            
            if not prices:
                logger.warning(f"Empty price data for {ticker}")
                return None
            
            # Calculate 30-day average volume
            recent_volumes = volumes[-30:] if len(volumes) >= 30 else volumes
            avg_volume_30d = sum(recent_volumes) / len(recent_volumes) if recent_volumes else 0
            
            current_price = prices[-1]
            
            return {
                "prices": prices,
                "volumes": volumes,
                "dates": dates,
                "current_price": current_price,
                "avg_volume_30d": avg_volume_30d
            }
            
        except Exception as e:
            logger.error(f"Error fetching market data for {ticker}: {e}")
            if "429" in str(e) or "rate limit" in str(e).lower():
                raise YFRateLimitError(f"Rate limit hit for {ticker}")
            raise
    
    @retry(
        stop=stop_after_attempt(5),
        wait=wait_exponential(multiplier=2, min=4, max=60),
        retry=retry_if_exception_type((YFRateLimitError, Exception)),
        reraise=True
    )
    def get_atm_iv(self, ticker: str, expiration: datetime, current_price: float) -> Optional[Dict[str, Any]]:
        """Get ATM (At-The-Money) option IV for a specific expiration.
        
        Args:
            ticker: Stock ticker symbol
            expiration: Option expiration date
            current_price: Current stock price
            
        Returns:
            Dictionary with keys:
            - iv: float (implied volatility)
            - strike: float (ATM strike price)
            - bid: float
            - ask: float
            - option_type: str ("call" or "put")
            - None if not found
        """
        try:
            self._rate_limit()
            
            stock = yf.Ticker(ticker)
            
            # Get option chain for the expiration date
            # Format expiration as YYYY-MM-DD
            exp_str = expiration.strftime("%Y-%m-%d")
            
            try:
                # Get option chain
                opt_chain = stock.option_chain(exp_str)
            except Exception as e:
                logger.debug(f"No options chain for {ticker} {exp_str}: {e}")
                return None
            
            if opt_chain is None:
                return None
            
            # Try calls first (preferred)
            calls = opt_chain.calls if hasattr(opt_chain, 'calls') else None
            puts = opt_chain.puts if hasattr(opt_chain, 'puts') else None
            
            preferred_type = self.config.trading.preferred_option_type.lower()
            
            # Find ATM option
            result = None
            
            if preferred_type == "call" and calls is not None and not calls.empty:
                result = self._find_atm_option(calls, current_price, "call")
            
            if result is None and puts is not None and not puts.empty:
                result = self._find_atm_option(puts, current_price, "put")
            
            if result is None and calls is not None and not calls.empty:
                result = self._find_atm_option(calls, current_price, "call")
            
            return result
            
        except Exception as e:
            logger.error(f"Error fetching ATM IV for {ticker} {expiration.date()}: {e}")
            if "429" in str(e) or "rate limit" in str(e).lower():
                raise YFRateLimitError(f"Rate limit hit for {ticker}")
            return None
    
    def _find_atm_option(self, options_df: pd.DataFrame, current_price: float, option_type: str) -> Optional[Dict[str, Any]]:
        """Find the ATM option from a dataframe.
        
        Args:
            options_df: DataFrame with option chain data
            current_price: Current stock price
            option_type: "call" or "put"
            
        Returns:
            Dictionary with option data or None
        """
        try:
            if options_df.empty:
                return None
            
            # Find ATM strike (minimize abs(strike - current_price))
            if "strike" not in options_df.columns:
                # Try alternative column names
                strike_col = None
                for col in ["strike", "Strike", "strikePrice", "strike_price"]:
                    if col in options_df.columns:
                        strike_col = col
                        break
                
                if strike_col is None:
                    logger.warning("No strike column found in options dataframe")
                    return None
            else:
                strike_col = "strike"
            
            # Calculate distance from current price
            options_df = options_df.copy()
            options_df["distance"] = abs(options_df[strike_col] - current_price)
            
            # Find minimum distance (ATM)
            atm_idx = options_df["distance"].idxmin()
            atm_option = options_df.loc[atm_idx]
            
            # Extract IV
            iv_col = None
            for col in ["impliedVolatility", "implied_volatility", "iv", "IV"]:
                if col in options_df.columns:
                    iv_col = col
                    break
            
            iv = float(atm_option[iv_col]) if iv_col and pd.notna(atm_option[iv_col]) else 0.0
            
            # Extract bid/ask
            bid = float(atm_option.get("bid", 0) or 0) if pd.notna(atm_option.get("bid")) else 0.0
            ask = float(atm_option.get("ask", 0) or 0) if pd.notna(atm_option.get("ask")) else 0.0
            
            strike = float(atm_option[strike_col])
            
            return {
                "iv": iv,
                "strike": strike,
                "bid": bid,
                "ask": ask,
                "option_type": option_type
            }
            
        except Exception as e:
            logger.error(f"Error finding ATM option: {e}")
            return None
    
    def find_option_expirations(self, ticker: str, earnings_date: datetime, back_month_days_offset: int = 30) -> Optional[List[datetime]]:
        """Find suitable option expiration dates around earnings.
        
        Args:
            ticker: Stock ticker symbol
            earnings_date: Date of earnings announcement
            back_month_days_offset: Days after front month for back month
            
        Returns:
            List of expiration dates [front_month, back_month]
        """
        try:
            self._rate_limit()
            
            stock = yf.Ticker(ticker)
            
            # Get available expiration dates
            try:
                expirations = stock.options
            except Exception as e:
                logger.error(f"Could not get option expirations for {ticker}: {e}")
                return None
            
            if not expirations:
                return None
            
            # Convert to datetime objects
            exp_dates = []
            for exp_str in expirations:
                try:
                    exp_date = datetime.strptime(exp_str, "%Y-%m-%d")
                    exp_dates.append(exp_date)
                except:
                    continue
            
            if not exp_dates:
                return None
            
            # Sort dates
            exp_dates.sort()
            
            # Find front month: First expiration AFTER earnings
            front_expiry = None
            for exp_date in exp_dates:
                if exp_date.date() > earnings_date.date():
                    front_expiry = exp_date
                    break
            
            if front_expiry is None:
                logger.warning(f"No front month expiration found after {earnings_date.date()}")
                return None
            
            # Find back month: ~30 days after front month
            target_back_date = front_expiry + timedelta(days=back_month_days_offset)
            back_expiry = None
            
            for exp_date in exp_dates:
                if exp_date >= target_back_date:
                    back_expiry = exp_date
                    break
            
            if back_expiry is None:
                # Use the last available expiration
                back_expiry = exp_dates[-1]
                if back_expiry <= front_expiry:
                    logger.warning(f"No suitable back month expiration found")
                    return None
            
            return [front_expiry, back_expiry]
            
        except Exception as e:
            logger.error(f"Error finding option expirations for {ticker}: {e}")
            return None

