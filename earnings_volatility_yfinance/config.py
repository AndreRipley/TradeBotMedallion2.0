"""Configuration management for Earnings Volatility Trading Bot (yfinance version)."""

import os
from dataclasses import dataclass
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class AlpacaConfig:
    """Alpaca API configuration."""
    api_key: str
    api_secret: str
    base_url: Optional[str] = None  # None = paper trading
    paper: bool = True


@dataclass
class SupabaseConfig:
    """Supabase configuration."""
    url: str
    key: str


@dataclass
class TradingConfig:
    """Trading strategy configuration."""
    # Risk management
    risk_per_trade_pct: float = 5.0  # Percentage of equity per trade
    
    # Entry/Exit timing (minutes before/after market events)
    entry_minutes_before_close: int = 15
    exit_minutes_after_open: int = 15
    
    # Filter thresholds
    iv_slope_threshold: float = 0.05  # Minimum IV slope (front - back month)
    min_volume: int = 1_500_000  # Minimum 30-day average volume
    min_iv_rv_ratio: float = 1.2  # Minimum IV/RV ratio
    
    # Option selection
    preferred_option_type: str = "call"  # "call" or "put"
    back_month_days_offset: int = 30  # Days after front month for back month
    
    # Position sizing
    max_positions: int = 5  # Maximum concurrent positions
    
    # Rate limiting
    yfinance_delay_seconds: float = 2.0  # Delay between yfinance requests


@dataclass
class Config:
    """Main configuration class."""
    alpaca: AlpacaConfig
    supabase: SupabaseConfig
    trading: TradingConfig
    ticker_list: List[str]  # Predefined ticker list
    
    @classmethod
    def from_env(cls) -> "Config":
        """Load configuration from environment variables."""
        # Alpaca configuration (support both naming conventions)
        alpaca_key = os.getenv("ALPACA_KEY") or os.getenv("ALPACA_API_KEY")
        alpaca_secret = os.getenv("ALPACA_SECRET") or os.getenv("ALPACA_SECRET_KEY")
        if not alpaca_key or not alpaca_secret:
            raise ValueError("ALPACA_KEY/ALPACA_API_KEY and ALPACA_SECRET/ALPACA_SECRET_KEY must be set")
        
        alpaca_base_url = os.getenv("ALPACA_BASE_URL")
        alpaca_paper = os.getenv("ALPACA_PAPER", "true").lower() == "true"
        
        # Supabase configuration
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set")
        
        # Trading configuration (with env overrides)
        trading_config = TradingConfig(
            risk_per_trade_pct=float(os.getenv("RISK_PER_TRADE_PCT", "5.0")),
            entry_minutes_before_close=int(os.getenv("ENTRY_MINUTES_BEFORE_CLOSE", "15")),
            exit_minutes_after_open=int(os.getenv("EXIT_MINUTES_AFTER_OPEN", "15")),
            iv_slope_threshold=float(os.getenv("IV_SLOPE_THRESHOLD", "0.05")),
            min_volume=int(os.getenv("MIN_VOLUME", "1500000")),
            min_iv_rv_ratio=float(os.getenv("MIN_IV_RV_RATIO", "1.2")),
            preferred_option_type=os.getenv("PREFERRED_OPTION_TYPE", "call"),
            back_month_days_offset=int(os.getenv("BACK_MONTH_DAYS_OFFSET", "30")),
            max_positions=int(os.getenv("MAX_POSITIONS", "5")),
            yfinance_delay_seconds=float(os.getenv("YFINANCE_DELAY_SECONDS", "2.0"))
        )
        
        # Ticker list - start small to avoid rate limits
        ticker_list_env = os.getenv("TICKER_LIST", "")
        if ticker_list_env:
            ticker_list = [t.strip().upper() for t in ticker_list_env.split(",") if t.strip()]
        else:
            # Default small list for testing
            ticker_list = ["AAPL", "TSLA", "AMD", "NVDA", "META"]
        
        return cls(
            alpaca=AlpacaConfig(
                api_key=alpaca_key,
                api_secret=alpaca_secret,
                base_url=alpaca_base_url,
                paper=alpaca_paper
            ),
            supabase=SupabaseConfig(url=supabase_url, key=supabase_key),
            trading=trading_config,
            ticker_list=ticker_list
        )


# Global config instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_env()
    return _config

