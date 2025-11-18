"""Tests for alert detection logic."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
from app.alerts import AlertService, RsiCrossUnderEvent
from app.models import RsiValue, Candle
from app.config import Config, RsiConfig


def test_cross_under_detection():
    """Test RSI cross-under detection logic."""
    # Create mock session
    mock_session = Mock()
    
    # Create mock RSI values: previous >= threshold, current < threshold
    previous_rsi = Mock()
    previous_rsi.rsi_14 = 30.0  # Above threshold
    previous_rsi.ts = datetime.utcnow() - timedelta(minutes=5)
    
    current_rsi = Mock()
    current_rsi.rsi_14 = 25.0  # Below threshold
    current_rsi.ts = datetime.utcnow()
    
    mock_session.query.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
        current_rsi, previous_rsi
    ]
    
    # Mock candle
    mock_candle = Mock()
    mock_candle.close = 100.0
    mock_session.query.return_value.filter_by.return_value.first.return_value = mock_candle
    
    config = Config(
        database=Mock(),
        universe=Mock(),
        rsi=RsiConfig(threshold=28.0),
        alert=Mock(),
        scheduler=Mock(),
        api=Mock()
    )
    
    with patch("app.alerts.get_config", return_value=config):
        service = AlertService()
        event = service.detect_cross_under("AAPL", session=mock_session)
        
        assert event is not None
        assert event.symbol == "AAPL"
        assert event.rsi_value == 25.0
        assert event.price == 100.0


def test_no_cross_under_when_above_threshold():
    """Test that no alert is triggered when RSI stays above threshold."""
    mock_session = Mock()
    
    previous_rsi = Mock()
    previous_rsi.rsi_14 = 30.0
    previous_rsi.ts = datetime.utcnow() - timedelta(minutes=5)
    
    current_rsi = Mock()
    current_rsi.rsi_14 = 29.0  # Still above threshold
    current_rsi.ts = datetime.utcnow()
    
    mock_session.query.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
        current_rsi, previous_rsi
    ]
    
    config = Config(
        database=Mock(),
        universe=Mock(),
        rsi=RsiConfig(threshold=28.0),
        alert=Mock(),
        scheduler=Mock(),
        api=Mock()
    )
    
    with patch("app.alerts.get_config", return_value=config):
        service = AlertService()
        event = service.detect_cross_under("AAPL", session=mock_session)
        
        assert event is None


def test_no_cross_under_when_already_below():
    """Test that no alert is triggered when RSI was already below threshold."""
    mock_session = Mock()
    
    previous_rsi = Mock()
    previous_rsi.rsi_14 = 25.0  # Already below
    previous_rsi.ts = datetime.utcnow() - timedelta(minutes=5)
    
    current_rsi = Mock()
    current_rsi.rsi_14 = 24.0  # Still below
    current_rsi.ts = datetime.utcnow()
    
    mock_session.query.return_value.filter_by.return_value.order_by.return_value.limit.return_value.all.return_value = [
        current_rsi, previous_rsi
    ]
    
    config = Config(
        database=Mock(),
        universe=Mock(),
        rsi=RsiConfig(threshold=28.0),
        alert=Mock(),
        scheduler=Mock(),
        api=Mock()
    )
    
    with patch("app.alerts.get_config", return_value=config):
        service = AlertService()
        event = service.detect_cross_under("AAPL", session=mock_session)
        
        assert event is None

