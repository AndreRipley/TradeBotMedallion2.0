"""Data provider abstractions and implementations."""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import time
import logging
import requests
from dataclasses import dataclass
import pandas as pd
from app.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class SymbolInfo:
    """Symbol information."""
    symbol: str
    company_name: Optional[str] = None
    cik: Optional[str] = None


@dataclass
class CandleData:
    """OHLCV candle data."""
    symbol: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    interval: str = "5min"


class SymbolUniverseProvider(ABC):
    """Abstract interface for symbol universe providers."""
    
    @abstractmethod
    def get_all_symbols(self) -> List[SymbolInfo]:
        """Fetch all U.S.-listed equities."""
        pass


class FundamentalsProvider(ABC):
    """Abstract interface for fundamentals data providers."""
    
    @abstractmethod
    def get_market_cap(self, symbol: str) -> Optional[int]:
        """Get market cap for a symbol in dollars."""
        pass


class IntradayPriceProvider(ABC):
    """Abstract interface for intraday price data providers."""
    
    @abstractmethod
    def get_historical_candles(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "5min"
    ) -> List[CandleData]:
        """Fetch historical candles for a symbol."""
        pass
    
    @abstractmethod
    def get_latest_candles(
        self,
        symbol: str,
        since: Optional[datetime] = None,
        interval: str = "5min"
    ) -> List[CandleData]:
        """Fetch latest candles since a timestamp."""
        pass


# Concrete implementations


class SecApiUniverseProvider(SymbolUniverseProvider):
    """SEC API-based symbol universe provider (mock implementation)."""
    
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or get_config().api.sec_api_base_url
        self.rate_limit_delay = get_config().api.rate_limit_delay_seconds
    
    def get_all_symbols(self) -> List[SymbolInfo]:
        """
        Fetch all U.S.-listed equities.
        
        Note: This is a mock implementation. In production, you would:
        1. Call SEC API or use a ticker list service
        2. Parse the response
        3. Return SymbolInfo objects
        
        For now, returns a sample of common symbols.
        """
        logger.info("Fetching symbol universe from SEC API (mock)")
        time.sleep(self.rate_limit_delay)
        
        # Mock data - in production, replace with actual API call
        # Example: GET {base_url}/files/company_tickers.json
        mock_symbols = [
            SymbolInfo(symbol="AAPL", company_name="Apple Inc.", cik="0000320193"),
            SymbolInfo(symbol="MSFT", company_name="Microsoft Corporation", cik="0000789019"),
            SymbolInfo(symbol="GOOGL", company_name="Alphabet Inc.", cik="0001652044"),
            SymbolInfo(symbol="AMZN", company_name="Amazon.com Inc.", cik="0001018724"),
            SymbolInfo(symbol="TSLA", company_name="Tesla Inc.", cik="0001318605"),
            SymbolInfo(symbol="META", company_name="Meta Platforms Inc.", cik="0001326801"),
            SymbolInfo(symbol="NVDA", company_name="NVIDIA Corporation", cik="0001045810"),
            SymbolInfo(symbol="JPM", company_name="JPMorgan Chase & Co.", cik="0000019617"),
            SymbolInfo(symbol="V", company_name="Visa Inc.", cik="0001403161"),
            SymbolInfo(symbol="JNJ", company_name="Johnson & Johnson", cik="0000200406"),
        ]
        
        logger.info(f"Retrieved {len(mock_symbols)} symbols (mock)")
        return mock_symbols


class AlphaVantageFundamentalsProvider(FundamentalsProvider):
    """Alpha Vantage API-based fundamentals provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_config().api.alpha_vantage_api_key
        self.rate_limit_delay = get_config().api.rate_limit_delay_seconds
        
        if not self.api_key:
            logger.warning("Alpha Vantage API key not configured. Market cap lookups will fail.")
    
    def get_market_cap(self, symbol: str) -> Optional[int]:
        """
        Get market cap for a symbol.
        
        Uses Alpha Vantage OVERVIEW endpoint.
        """
        if not self.api_key:
            logger.warning(f"No API key configured. Returning mock market cap for {symbol}")
            # Mock market cap for testing
            return 10_000_000_000
        
        logger.debug(f"Fetching market cap for {symbol}")
        time.sleep(self.rate_limit_delay)
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "OVERVIEW",
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "MarketCapitalization" in data and data["MarketCapitalization"]:
                market_cap = int(float(data["MarketCapitalization"]))
                logger.debug(f"{symbol} market cap: ${market_cap:,}")
                return market_cap
            else:
                logger.warning(f"No market cap data for {symbol}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching market cap for {symbol}: {e}")
            return None


class MockIntradayPriceProvider(IntradayPriceProvider):
    """Mock intraday price provider for testing."""
    
    def get_historical_candles(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "5min"
    ) -> List[CandleData]:
        """Generate mock historical candles."""
        logger.info(f"Generating mock candles for {symbol} from {start_date} to {end_date}")
        
        candles = []
        current = start_date
        base_price = 100.0
        
        while current <= end_date:
            # Simple random walk for mock data
            import random
            change = random.uniform(-0.5, 0.5)
            base_price += change
            
            candle = CandleData(
                symbol=symbol,
                ts=current,
                open=base_price,
                high=base_price + abs(random.uniform(0, 0.3)),
                low=base_price - abs(random.uniform(0, 0.3)),
                close=base_price + random.uniform(-0.2, 0.2),
                volume=random.randint(100000, 1000000),
                interval=interval
            )
            candles.append(candle)
            current += timedelta(minutes=5)
        
        return candles
    
    def get_latest_candles(
        self,
        symbol: str,
        since: Optional[datetime] = None,
        interval: str = "5min"
    ) -> List[CandleData]:
        """Get latest candles since timestamp."""
        if since is None:
            since = datetime.utcnow() - timedelta(days=1)
        
        end_date = datetime.utcnow()
        return self.get_historical_candles(symbol, since, end_date, interval)


class AlphaVantageIntradayProvider(IntradayPriceProvider):
    """Alpha Vantage API-based intraday price provider."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or get_config().api.alpha_vantage_api_key
        self.rate_limit_delay = get_config().api.rate_limit_delay_seconds
        
        if not self.api_key:
            logger.warning("Alpha Vantage API key not configured. Using mock provider.")
    
    def get_historical_candles(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "5min"
    ) -> List[CandleData]:
        """
        Fetch historical candles from Alpha Vantage.
        
        Note: Alpha Vantage free tier only provides recent data.
        For 13 months of 5-min data, you may need a premium subscription
        or use a different provider (e.g., Polygon.io, IEX Cloud).
        """
        if not self.api_key:
            # Fallback to mock
            provider = MockIntradayPriceProvider()
            return provider.get_historical_candles(symbol, start_date, end_date, interval)
        
        logger.info(f"Fetching historical candles for {symbol} from Alpha Vantage")
        candles = []
        
        # Alpha Vantage INTRADAY endpoint
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "TIME_SERIES_INTRADAY",
            "symbol": symbol,
            "interval": interval,
            "apikey": self.api_key,
            "outputsize": "full"  # Get as much data as available
        }
        
        try:
            time.sleep(self.rate_limit_delay)
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            time_series_key = f"Time Series ({interval})"
            if time_series_key not in data:
                logger.warning(f"No intraday data for {symbol}")
                return []
            
            for ts_str, values in data[time_series_key].items():
                ts = datetime.strptime(ts_str, "%Y-%m-%d %H:%M:%S")
                
                if start_date <= ts <= end_date:
                    candle = CandleData(
                        symbol=symbol,
                        ts=ts,
                        open=float(values["1. open"]),
                        high=float(values["2. high"]),
                        low=float(values["3. low"]),
                        close=float(values["4. close"]),
                        volume=int(values["5. volume"]),
                        interval=interval
                    )
                    candles.append(candle)
            
            logger.info(f"Retrieved {len(candles)} candles for {symbol}")
            return sorted(candles, key=lambda x: x.ts)
            
        except Exception as e:
            logger.error(f"Error fetching candles for {symbol}: {e}")
            return []
    
    def get_latest_candles(
        self,
        symbol: str,
        since: Optional[datetime] = None,
        interval: str = "5min"
    ) -> List[CandleData]:
        """Get latest candles since timestamp."""
        if since is None:
            since = datetime.utcnow() - timedelta(days=1)
        
        end_date = datetime.utcnow()
        return self.get_historical_candles(symbol, since, end_date, interval)

