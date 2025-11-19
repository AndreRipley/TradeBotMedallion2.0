"""Analysis engine for calculating metrics and filtering signals."""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
import numpy as np
import pandas as pd
from loguru import logger
from .config import get_config
from .data_service import YahooDataService


class AnalysisEngine:
    """Engine for analyzing tickers and calculating trading metrics."""
    
    def __init__(self, data_service: YahooDataService):
        """Initialize analysis engine.
        
        Args:
            data_service: YahooDataService instance for fetching market data
        """
        self.data_service = data_service
        self.config = get_config()
    
    def calculate_rv(self, prices: list) -> float:
        """Calculate 30-day annualized realized volatility.
        
        Uses log returns: log(P_t / P_{t-1})
        Then annualizes: std(log_returns) * sqrt(252)
        
        Args:
            prices: List of closing prices (most recent last)
            
        Returns:
            Annualized volatility as a decimal (e.g., 0.25 for 25%)
        """
        if len(prices) < 2:
            logger.warning("Insufficient prices for RV calculation")
            return 0.0
        
        # Use last 30 days if available, otherwise use all data
        recent_prices = prices[-30:] if len(prices) >= 30 else prices
        
        if len(recent_prices) < 2:
            return 0.0
        
        # Convert to numpy array
        price_array = np.array(recent_prices)
        
        # Calculate log returns: log(P_t / P_{t-1})
        log_returns = np.diff(np.log(price_array))
        
        # Calculate standard deviation of log returns
        std_dev = np.std(log_returns)
        
        # Annualize (assuming 252 trading days per year)
        annualized_rv = std_dev * np.sqrt(252)
        
        return float(annualized_rv)
    
    def analyze_ticker(self, ticker: str) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Analyze a ticker and determine if it meets all filter criteria.
        
        Optimization: Fastest checks first to avoid expensive API calls.
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Tuple of:
            - bool: True if ticker passes all filters
            - Dict: Metrics dictionary if passed, None otherwise
            - str: Rejection reason if failed, None otherwise
        """
        logger.info(f"Analyzing {ticker}")
        
        # Step 1: Check Volume (Fastest check - no options data needed)
        market_data = self.data_service.get_market_data(ticker, days=30)
        if not market_data:
            return False, None, "Failed to fetch market data"
        
        prices = market_data["prices"]
        avg_volume_30d = market_data["avg_volume_30d"]
        current_price = market_data["current_price"]
        
        # Volume filter
        if avg_volume_30d < self.config.trading.min_volume:
            reason = f"Volume {avg_volume_30d:,.0f} < threshold {self.config.trading.min_volume:,.0f}"
            logger.info(f"Rejected {ticker}: {reason}")
            return False, None, reason
        
        # Step 2: Check Earnings Date
        earnings_info = self.data_service.get_earnings_date(ticker)
        if not earnings_info:
            return False, None, "No earnings date found"
        
        earnings_date = earnings_info["date"]
        earnings_time = earnings_info["time"]
        
        # Check if earnings is today (AMC) or tomorrow (BMO)
        today = datetime.now().date()
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        
        earnings_date_only = earnings_date.date() if hasattr(earnings_date, 'date') else earnings_date
        
        if earnings_date_only not in [today, tomorrow]:
            reason = f"Earnings date {earnings_date_only} not today or tomorrow"
            logger.info(f"Rejected {ticker}: {reason}")
            return False, None, reason
        
        # Step 3: Calculate Realized Volatility
        rv = self.calculate_rv(prices)
        if rv == 0:
            return False, None, "Could not calculate realized volatility"
        
        logger.debug(f"{ticker} RV: {rv:.4f} ({rv*100:.2f}%)")
        
        # Step 4: Find option expirations (Slow - requires API call)
        expirations = self.data_service.find_option_expirations(
            ticker,
            earnings_date,
            self.config.trading.back_month_days_offset
        )
        
        if not expirations or len(expirations) < 2:
            return False, None, "Could not find suitable option expirations"
        
        front_expiry = expirations[0]
        back_expiry = expirations[1]
        
        logger.debug(f"{ticker} Front expiry: {front_expiry.date()}, Back expiry: {back_expiry.date()}")
        
        # Step 5: Get ATM IV for front month (Slow - requires API call)
        front_iv_data = self.data_service.get_atm_iv(ticker, front_expiry, current_price)
        if not front_iv_data or front_iv_data["iv"] == 0:
            return False, None, "Could not fetch front month IV"
        
        front_iv = front_iv_data["iv"]
        front_strike = front_iv_data["strike"]
        front_bid = front_iv_data["bid"]
        front_ask = front_iv_data["ask"]
        option_type = front_iv_data["option_type"]
        
        # Step 6: Get ATM IV for back month (Slow - requires API call)
        back_iv_data = self.data_service.get_atm_iv(ticker, back_expiry, current_price)
        if not back_iv_data or back_iv_data["iv"] == 0:
            return False, None, "Could not fetch back month IV"
        
        back_iv = back_iv_data["iv"]
        back_strike = back_iv_data["strike"]
        back_bid = back_iv_data["bid"]
        back_ask = back_iv_data["ask"]
        
        # Ensure same option type
        if back_iv_data["option_type"] != option_type:
            return False, None, f"Option type mismatch: front={option_type}, back={back_iv_data['option_type']}"
        
        # Step 7: Check IV Term Structure Slope (Backwardation)
        iv_slope = front_iv - back_iv
        if iv_slope <= self.config.trading.iv_slope_threshold:
            reason = f"IV Slope {iv_slope:.4f} <= threshold {self.config.trading.iv_slope_threshold:.4f}"
            logger.info(f"Rejected {ticker}: {reason}")
            return False, None, reason
        
        logger.debug(f"{ticker} IV Slope: {iv_slope:.4f} (Front: {front_iv:.4f}, Back: {back_iv:.4f})")
        
        # Step 8: Check IV/RV Ratio
        iv_rv_ratio = front_iv / rv if rv > 0 else 0
        
        if iv_rv_ratio < self.config.trading.min_iv_rv_ratio:
            reason = f"IV/RV Ratio {iv_rv_ratio:.4f} < threshold {self.config.trading.min_iv_rv_ratio:.4f}"
            logger.info(f"Rejected {ticker}: {reason}")
            return False, None, reason
        
        logger.debug(f"{ticker} IV/RV Ratio: {iv_rv_ratio:.4f} (IV: {front_iv:.4f}, RV: {rv:.4f})")
        
        # All filters passed
        metrics = {
            "ticker": ticker,
            "current_price": current_price,
            "rv": rv,
            "front_month_iv": front_iv,
            "back_month_iv": back_iv,
            "iv_slope": iv_slope,
            "iv_rv_ratio": iv_rv_ratio,
            "avg_volume_30d": avg_volume_30d,
            "front_month_expiry": front_expiry,
            "back_month_expiry": back_expiry,
            "front_month_strike": front_strike,
            "back_month_strike": back_strike,
            "option_type": option_type,
            "front_month_bid": front_bid,
            "front_month_ask": front_ask,
            "back_month_bid": back_bid,
            "back_month_ask": back_ask,
            "earnings_date": earnings_date,
            "earnings_time": earnings_time
        }
        
        logger.info(f"✓ {ticker} passed all filters: Slope={iv_slope:.4f}, IV/RV={iv_rv_ratio:.4f}, Vol={avg_volume_30d:,.0f}")
        
        return True, metrics, None

