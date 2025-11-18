"""Configuration management for the trading alert system."""

import os
import re
from pathlib import Path
from typing import Optional
from dataclasses import dataclass
import yaml


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite:///./data/trading_alerts.db"
    echo: bool = False
    
    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Create database config from environment variables (Supabase)."""
        # Supabase connection string format:
        # postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres
        # Or direct: postgresql://postgres:[PASSWORD]@[HOST]:5432/postgres
        
        db_url = os.getenv("DATABASE_URL")
        
        # Check if DATABASE_URL is actually a Supabase API URL (wrong format)
        # If it starts with https://, it's the API URL, not the database URL
        if db_url and db_url.startswith("https://"):
            # This is the Supabase API URL, not the database connection string
            # Ignore it and try to construct from env vars
            db_url = None
        
        # If DATABASE_URL not set or invalid, try to construct from Supabase env vars
        if not db_url:
            supabase_url = os.getenv("SUPABASE_URL")
            supabase_db_password = os.getenv("SUPABASE_DB_PASSWORD")
            supabase_db_host = os.getenv("SUPABASE_DB_HOST")
            
            if supabase_url and supabase_db_password:
                # Extract project ref from Supabase URL
                # e.g., https://rpugqgjacxfbfeqguqbs.supabase.co -> rpugqgjacxfbfeqguqbs
                match = re.search(r'https://([^.]+)\.supabase\.co', supabase_url)
                if match:
                    project_ref = match.group(1)
                    # Try direct connection first (more reliable)
                    # Format: postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres
                    db_url = f"postgresql://postgres:{supabase_db_password}@db.{project_ref}.supabase.co:5432/postgres"
                elif supabase_db_host:
                    # Use direct connection if host provided
                    db_url = f"postgresql://postgres:{supabase_db_password}@{supabase_db_host}:5432/postgres"
        
        return cls(
            url=db_url or "sqlite:///./data/trading_alerts.db",
            echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"
        )


@dataclass
class UniverseConfig:
    """Universe filtering configuration."""
    min_market_cap: int = 5_000_000_000  # $5B
    three_month_min_return: float = 80.0  # 80%
    six_month_min_return: float = 90.0  # 90%
    ytd_min_return: float = 100.0  # 100%
    lookback_months: int = 13


@dataclass
class RsiConfig:
    """RSI calculation configuration."""
    period: int = 14
    threshold: float = 28.0  # Cross-under threshold


@dataclass
class AlertConfig:
    """Alert and trade rule configuration."""
    take_profit_pct: float = 3.0  # 3% take profit
    max_holding_days: int = 20  # 20 calendar days


@dataclass
class SchedulerConfig:
    """Scheduler configuration."""
    update_interval_minutes: int = 5
    market_hours_only: bool = True
    market_open_hour: int = 9  # 9:30 AM ET (9:00 UTC offset)
    market_close_hour: int = 16  # 4:00 PM ET (16:00 UTC offset)


@dataclass
class ApiConfig:
    """API configuration."""
    alpha_vantage_api_key: Optional[str] = None
    sec_api_base_url: str = "https://api.sec.gov"
    rate_limit_delay_seconds: float = 0.2


@dataclass
class Config:
    """Main configuration class."""
    database: DatabaseConfig
    universe: UniverseConfig
    rsi: RsiConfig
    alert: AlertConfig
    scheduler: SchedulerConfig
    api: ApiConfig

    @classmethod
    def from_yaml(cls, config_path: Optional[Path] = None) -> "Config":
        """Load configuration from YAML file."""
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config.yaml"
        
        config_dict = {}
        if config_path.exists():
            with open(config_path, "r") as f:
                config_dict = yaml.safe_load(f) or {}
        
        # Override with environment variables
        return cls.from_dict(config_dict)
    
    @classmethod
    def from_dict(cls, config_dict: dict) -> "Config":
        """Create config from dictionary with environment variable overrides."""
        # Try to get database config from environment (Supabase)
        try:
            db_config = DatabaseConfig.from_env()
        except:
            # Fallback to config file or default
            db_config = DatabaseConfig(
                url=os.getenv("DATABASE_URL", config_dict.get("database", {}).get("url", "sqlite:///./data/trading_alerts.db")),
                echo=os.getenv("DATABASE_ECHO", "false").lower() == "true"
            )
        
        return cls(
            database=db_config,
            universe=UniverseConfig(
                min_market_cap=int(os.getenv("MIN_MARKET_CAP", config_dict.get("universe", {}).get("min_market_cap", 5_000_000_000))),
                three_month_min_return=float(os.getenv("THREE_MONTH_MIN_RETURN", config_dict.get("universe", {}).get("three_month_min_return", 80.0))),
                six_month_min_return=float(os.getenv("SIX_MONTH_MIN_RETURN", config_dict.get("universe", {}).get("six_month_min_return", 90.0))),
                ytd_min_return=float(os.getenv("YTD_MIN_RETURN", config_dict.get("universe", {}).get("ytd_min_return", 100.0))),
                lookback_months=int(os.getenv("LOOKBACK_MONTHS", config_dict.get("universe", {}).get("lookback_months", 13)))
            ),
            rsi=RsiConfig(
                period=int(os.getenv("RSI_PERIOD", config_dict.get("rsi", {}).get("period", 14))),
                threshold=float(os.getenv("RSI_THRESHOLD", config_dict.get("rsi", {}).get("threshold", 28.0)))
            ),
            alert=AlertConfig(
                take_profit_pct=float(os.getenv("TAKE_PROFIT_PCT", config_dict.get("alert", {}).get("take_profit_pct", 3.0))),
                max_holding_days=int(os.getenv("MAX_HOLDING_DAYS", config_dict.get("alert", {}).get("max_holding_days", 20)))
            ),
            scheduler=SchedulerConfig(
                update_interval_minutes=int(os.getenv("UPDATE_INTERVAL_MINUTES", config_dict.get("scheduler", {}).get("update_interval_minutes", 5))),
                market_hours_only=os.getenv("MARKET_HOURS_ONLY", "true").lower() == "true",
                market_open_hour=int(os.getenv("MARKET_OPEN_HOUR", config_dict.get("scheduler", {}).get("market_open_hour", 9))),
                market_close_hour=int(os.getenv("MARKET_CLOSE_HOUR", config_dict.get("scheduler", {}).get("market_close_hour", 16)))
            ),
            api=ApiConfig(
                alpha_vantage_api_key=os.getenv("ALPHA_VANTAGE_API_KEY", config_dict.get("api", {}).get("alpha_vantage_api_key")),
                sec_api_base_url=os.getenv("SEC_API_BASE_URL", config_dict.get("api", {}).get("sec_api_base_url", "https://api.sec.gov")),
                rate_limit_delay_seconds=float(os.getenv("RATE_LIMIT_DELAY", config_dict.get("api", {}).get("rate_limit_delay_seconds", 0.2)))
            )
        )


# Global config instance (lazy-loaded)
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.from_yaml()
    return _config

