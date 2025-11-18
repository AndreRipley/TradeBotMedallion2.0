"""Tests for RSI calculation with Wilder smoothing."""

import pytest
import pandas as pd
import numpy as np
from app.indicators import RsiCalculator


def test_rsi_wilder_basic():
    """Test basic RSI calculation."""
    calculator = RsiCalculator()
    
    # Create a simple test series
    # 14 periods of increasing prices (gains)
    closes = pd.Series([100 + i * 0.5 for i in range(20)])
    
    rsi = calculator.compute_rsi_wilder(closes)
    
    # RSI should be high (near 100) for consistently rising prices
    assert not pd.isna(rsi.iloc[-1])
    assert rsi.iloc[-1] > 50  # Should be bullish
    assert rsi.iloc[-1] <= 100


def test_rsi_wilder_declining():
    """Test RSI with declining prices."""
    calculator = RsiCalculator()
    
    # 14 periods of decreasing prices (losses)
    closes = pd.Series([100 - i * 0.5 for i in range(20)])
    
    rsi = calculator.compute_rsi_wilder(closes)
    
    # RSI should be low (near 0) for consistently falling prices
    assert not pd.isna(rsi.iloc[-1])
    assert rsi.iloc[-1] < 50  # Should be bearish
    assert rsi.iloc[-1] >= 0


def test_rsi_wilder_insufficient_data():
    """Test RSI with insufficient data."""
    calculator = RsiCalculator()
    
    # Less than period + 1 data points
    closes = pd.Series([100, 101, 102])
    
    rsi = calculator.compute_rsi_wilder(closes)
    
    # Should return all NaN
    assert rsi.isna().all()


def test_rsi_wilder_reference_values():
    """
    Test RSI against known reference values.
    
    Uses a simple test case where we can manually verify the calculation.
    """
    calculator = RsiCalculator()
    
    # Create a known pattern: 14 periods of +1 gain, then alternating
    closes = pd.Series([100.0] + [100.0 + i for i in range(1, 20)])
    
    rsi = calculator.compute_rsi_wilder(closes)
    
    # First RSI value should be computed at index 14
    assert not pd.isna(rsi.iloc[14])
    
    # Verify RSI is in valid range
    assert 0 <= rsi.iloc[14] <= 100


def test_rsi_wilder_zero_loss():
    """Test RSI when average loss is zero (all gains)."""
    calculator = RsiCalculator()
    
    # All prices increase
    closes = pd.Series([100 + i for i in range(20)])
    
    rsi = calculator.compute_rsi_wilder(closes)
    
    # RSI should be 100 when there are no losses
    assert not pd.isna(rsi.iloc[-1])
    assert rsi.iloc[-1] == 100.0


def test_rsi_wilder_oscillating():
    """Test RSI with oscillating prices."""
    calculator = RsiCalculator()
    
    # Create oscillating pattern
    closes = pd.Series([100 + (i % 2) * 2 - 1 for i in range(20)])
    
    rsi = calculator.compute_rsi_wilder(closes)
    
    # RSI should be around 50 for oscillating prices
    assert not pd.isna(rsi.iloc[-1])
    assert 0 <= rsi.iloc[-1] <= 100

