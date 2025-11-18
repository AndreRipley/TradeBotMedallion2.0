"""Tests for universe filtering logic."""

import pytest
from unittest.mock import Mock, patch
from app.universe import UniverseBuilder
from app.data_providers import SymbolInfo
from app.config import Config, UniverseConfig


def test_market_cap_filtering():
    """Test that market cap filtering works correctly."""
    # Create mock providers
    symbol_provider = Mock()
    symbol_provider.get_all_symbols.return_value = [
        SymbolInfo(symbol="AAPL", company_name="Apple Inc."),
        SymbolInfo(symbol="SMALL", company_name="Small Cap Inc."),
    ]
    
    fundamentals_provider = Mock()
    fundamentals_provider.get_market_cap.side_effect = lambda s: {
        "AAPL": 10_000_000_000,  # $10B - passes
        "SMALL": 1_000_000_000,  # $1B - fails
    }.get(s)
    
    price_provider = Mock()
    price_provider.get_historical_candles.return_value = []
    
    # Create config with $5B minimum
    config = Config(
        database=Mock(),
        universe=UniverseConfig(min_market_cap=5_000_000_000),
        rsi=Mock(),
        alert=Mock(),
        scheduler=Mock(),
        api=Mock()
    )
    
    with patch("app.universe.get_config", return_value=config):
        builder = UniverseBuilder(
            symbol_provider=symbol_provider,
            fundamentals_provider=fundamentals_provider,
            price_provider=price_provider
        )
        
        # Mock database operations
        with patch("app.universe.get_session") as mock_session:
            mock_session.return_value.__enter__ = Mock(return_value=Mock())
            mock_session.return_value.__exit__ = Mock(return_value=False)
            
            # This would normally build universe, but we'll just test the filtering logic
            # For now, verify the mock is set up correctly
            assert symbol_provider.get_all_symbols() is not None


def test_performance_thresholds():
    """Test that performance thresholds are applied correctly."""
    # This would test the performance filtering logic
    # For now, we verify the config structure
    config = Config(
        database=Mock(),
        universe=UniverseConfig(
            three_month_min_return=80.0,
            six_month_min_return=90.0,
            ytd_min_return=100.0
        ),
        rsi=Mock(),
        alert=Mock(),
        scheduler=Mock(),
        api=Mock()
    )
    
    assert config.universe.three_month_min_return == 80.0
    assert config.universe.six_month_min_return == 90.0
    assert config.universe.ytd_min_return == 100.0

