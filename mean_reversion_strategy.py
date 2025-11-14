"""
Mean-Reversion Anomaly Strategy
Implements a sophisticated mean-reversion strategy with regime filters, 
advanced entry/exit rules, and portfolio risk management.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import sys
import os

# Add parent directory to path to import StrategyBase
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


def calculate_atr(data: pd.DataFrame, period: int = 14) -> pd.Series:
    """Calculate Average True Range."""
    high = data['High']
    low = data['Low']
    close = data['Close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(window=period).mean()
    
    return atr


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """Calculate Relative Strength Index."""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_mad_zscore(data: pd.Series, window: int = 20) -> pd.Series:
    """Calculate z-score using Median Absolute Deviation."""
    median = data.rolling(window=window).median()
    mad = data.rolling(window=window).apply(lambda x: np.median(np.abs(x - np.median(x))))
    mad_scaled = mad * 1.4826  # Scale factor for MAD to approximate std
    z_score = (data - median) / mad_scaled
    return z_score


def calculate_vwap(data: pd.DataFrame, window: int = 20) -> pd.Series:
    """Calculate Volume Weighted Average Price."""
    typical_price = (data['High'] + data['Low'] + data['Close']) / 3
    vwap = (typical_price * data['Volume']).rolling(window=window).sum() / data['Volume'].rolling(window=window).sum()
    return vwap


class MeanReversionStrategy:
    """Mean-Reversion Anomaly Strategy with regime filters and advanced exits."""
    
    def __init__(self, position_size: float = 1000.0, equity: float = 100000.0):
        """
        Initialize mean-reversion strategy.
        
        Args:
            position_size: Base position size (will be adjusted by risk)
            equity: Starting equity for risk calculations
        """
        self.name = "Mean-Reversion Strategy"
        self.base_position_size = position_size
        self.equity = equity
        self.current_equity = equity
        
        # Portfolio tracking
        self.positions = {}  # symbol -> position info
        self.max_positions = 6
        self.daily_pnl = 0
        self.drawdown = 0
        self.peak_equity = equity
        
        # Regime filter cache
        self.regime_cache = {}
        self.last_regime_check = None
        
        # Sector mapping (simplified)
        self.sector_map = {
            'AAPL': 'Technology', 'MSFT': 'Technology', 'GOOGL': 'Technology',
            'AMZN': 'Consumer', 'META': 'Technology', 'TSLA': 'Consumer',
            'NVDA': 'Technology', 'ADBE': 'Technology', 'CSCO': 'Technology',
            'NFLX': 'Consumer', 'ACN': 'Technology', 'AVGO': 'Technology',
            'V': 'Financial', 'JPM': 'Financial', 'MA': 'Financial',
            'UNH': 'Healthcare', 'JNJ': 'Healthcare', 'LLY': 'Healthcare',
            'MRK': 'Healthcare', 'ABBV': 'Healthcare', 'ABT': 'Healthcare',
            'TMO': 'Healthcare', 'XOM': 'Energy', 'CVX': 'Energy',
            'WMT': 'Consumer', 'PG': 'Consumer', 'COST': 'Consumer',
            'MCD': 'Consumer', 'PEP': 'Consumer', 'HD': 'Consumer'
        }
    
    def check_regime(self, date: datetime) -> bool:
        """Check if regime filter allows new entries."""
        date_str = date.strftime('%Y-%m-%d')
        
        # Cache regime check for same day
        if self.last_regime_check == date_str and date_str in self.regime_cache:
            return self.regime_cache[date_str]
        
        try:
            # Fetch VIX
            vix = yf.Ticker('^VIX')
            vix_data = vix.history(start=date_str, end=(date + timedelta(days=1)).strftime('%Y-%m-%d'))
            
            if vix_data.empty:
                # If no VIX data, assume regime is OK (conservative)
                return True
            
            current_vix = vix_data['Close'].iloc[-1] if len(vix_data) > 0 else 25
            
            # Fetch SPY for moving averages
            spy = yf.Ticker('SPY')
            spy_data = spy.history(start=(date - timedelta(days=250)).strftime('%Y-%m-%d'),
                                   end=(date + timedelta(days=1)).strftime('%Y-%m-%d'))
            
            if len(spy_data) < 200:
                return True  # Not enough data, allow trades
            
            spy_50dma = spy_data['Close'].rolling(50).mean().iloc[-1]
            spy_200dma = spy_data['Close'].rolling(200).mean().iloc[-1]
            
            # Regime check: VIX < 25 AND SPY 50DMA > 200DMA
            regime_ok = current_vix < 25 and spy_50dma > spy_200dma
            
            self.regime_cache[date_str] = regime_ok
            self.last_regime_check = date_str
            
            return regime_ok
        except Exception as e:
            logger.warning(f"Error checking regime: {e}")
            return True  # On error, allow trades (conservative)
    
    def calculate_indicators(self, data: pd.DataFrame, current_idx: int) -> Dict:
        """Calculate all required indicators."""
        if current_idx < 20:
            return None
        
        window = min(20, current_idx)
        historical = data.iloc[:current_idx + 1]
        
        # Basic price data
        current = historical.iloc[-1]
        prev_close = historical.iloc[-2]['Close'] if len(historical) > 1 else current['Close']
        
        # z_MAD(20)
        z_mad = calculate_mad_zscore(historical['Close'], window=20)
        current_z_mad = z_mad.iloc[-1] if len(z_mad) > 0 and not pd.isna(z_mad.iloc[-1]) else 0
        
        # RSI(14)
        rsi = calculate_rsi(historical['Close'], period=14)
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]) else 50
        
        # ATR(14)
        atr = calculate_atr(historical, period=14)
        current_atr = atr.iloc[-1] if len(atr) > 0 and not pd.isna(atr.iloc[-1]) else current['Close'] * 0.02
        
        # Gap% and DayMove%
        gap_pct = ((current['Open'] - prev_close) / prev_close) * 100 if prev_close > 0 else 0
        day_move_pct = ((current['Close'] - prev_close) / prev_close) * 100 if prev_close > 0 else 0
        
        # Volume metrics
        volume_ma = historical['Volume'].rolling(20).mean()
        volume_spike = current['Volume'] / volume_ma.iloc[-1] if len(volume_ma) > 0 and volume_ma.iloc[-1] > 0 else 1
        
        # VWAP deviation (approximate with daily VWAP)
        vwap = calculate_vwap(historical, window=20)
        current_vwap = vwap.iloc[-1] if len(vwap) > 0 and not pd.isna(vwap.iloc[-1]) else current['Close']
        vwap_std = (historical['Close'] - vwap).rolling(20).std()
        current_vwap_std = vwap_std.iloc[-1] if len(vwap_std) > 0 and not pd.isna(vwap_std.iloc[-1]) else current['Close'] * 0.02
        
        # VWAP deviation in sigma units
        vwap_deviation_sigma = (current['Close'] - current_vwap) / current_vwap_std if current_vwap_std > 0 else 0
        
        # 20-day median and moving average
        median_20 = historical['Close'].rolling(20).median().iloc[-1]
        ma_20 = historical['Close'].rolling(20).mean().iloc[-1]
        
        # ATR/Price ratio
        atr_price_ratio = current_atr / current['Close'] if current['Close'] > 0 else 0
        
        return {
            'z_mad': current_z_mad,
            'rsi': current_rsi,
            'atr': current_atr,
            'atr_price_ratio': atr_price_ratio,
            'gap_pct': gap_pct,
            'day_move_pct': day_move_pct,
            'volume_spike': volume_spike,
            'vwap_deviation_sigma': vwap_deviation_sigma,
            'median_20': median_20,
            'ma_20': ma_20,
            'current_price': current['Close'],
            'current_date': current['Date'] if 'Date' in current else historical.index[-1]
        }
    
    def check_entry_conditions(self, indicators: Dict) -> Tuple[bool, str]:
        """Check if all entry conditions are met."""
        if indicators is None:
            return False, "Insufficient data"
        
        # All conditions must be true
        conditions = []
        
        # 1. z_MAD(20) < -2.0
        if indicators['z_mad'] < -2.0:
            conditions.append(f"z_MAD={indicators['z_mad']:.2f} < -2.0")
        else:
            return False, f"z_MAD {indicators['z_mad']:.2f} >= -2.0"
        
        # 2. RSI(14) < 30
        if indicators['rsi'] < 30:
            conditions.append(f"RSI={indicators['rsi']:.1f} < 30")
        else:
            return False, f"RSI {indicators['rsi']:.1f} >= 30"
        
        # 3. (Gap%)/(ATR/Price) > 0.6 OR DayMove% <= -3%
        gap_atr_ratio = abs(indicators['gap_pct']) / indicators['atr_price_ratio'] if indicators['atr_price_ratio'] > 0 else 0
        if gap_atr_ratio > 0.6 or indicators['day_move_pct'] <= -3.0:
            conditions.append(f"Gap/ATR={gap_atr_ratio:.2f} OR DayMove={indicators['day_move_pct']:.2f}%")
        else:
            return False, f"Gap/ATR {gap_atr_ratio:.2f} <= 0.6 AND DayMove {indicators['day_move_pct']:.2f}% > -3%"
        
        # 4. VolumeSpike >= 1.5
        if indicators['volume_spike'] >= 1.5:
            conditions.append(f"VolumeSpike={indicators['volume_spike']:.2f} >= 1.5")
        else:
            return False, f"VolumeSpike {indicators['volume_spike']:.2f} < 1.5"
        
        # 5. Price <= -1σ vs intraday VWAP
        if indicators['vwap_deviation_sigma'] <= -1.0:
            conditions.append(f"VWAP_dev={indicators['vwap_deviation_sigma']:.2f}σ <= -1.0")
        else:
            return False, f"VWAP_dev {indicators['vwap_deviation_sigma']:.2f}σ > -1.0"
        
        # 6. Not within earnings window - SKIPPED (would need earnings calendar)
        # 7. Universe/liquidity filters - SKIPPED (assume stocks meet criteria)
        
        reason = ", ".join(conditions)
        return True, reason
    
    def calculate_position_size(self, entry_price: float, stop_price: float) -> float:
        """Calculate position size based on risk (0.5% of equity to stop)."""
        risk_per_trade = self.current_equity * 0.005  # 0.5% risk
        risk_per_share = entry_price - stop_price
        
        if risk_per_share <= 0:
            return 0
        
        shares = risk_per_trade / risk_per_share
        
        # Apply Kelly overlay (simplified - assume 0.25x multiplier)
        kelly_multiplier = 0.25
        shares = shares * kelly_multiplier
        
        # Cap position size
        max_position_value = self.current_equity * 0.10  # Max 10% per name
        max_shares = max_position_value / entry_price
        
        return min(shares, max_shares)
    
    def check_exit_conditions(self, symbol: str, indicators: Dict, position: Dict) -> Tuple[bool, str, float]:
        """
        Check exit conditions (stops, profit targets, time stop).
        
        Returns:
            (should_exit, reason, exit_shares_pct)
        """
        current_price = indicators['current_price']
        entry_price = position['entry_price']
        entry_date = position['entry_date']
        current_date = indicators['current_date']
        
        # Calculate days held
        if isinstance(current_date, pd.Timestamp):
            days_held = (current_date - entry_date).days
        else:
            days_held = 0
        
        # Initial Stop: Entry - 1.5×ATR(14)
        initial_stop = entry_price - (1.5 * position['atr_at_entry'])
        if current_price <= initial_stop:
            return True, "INITIAL_STOP", 1.0
        
        # Trailing Stop: Highest since entry - 2.5×ATR(14)
        highest_price = position.get('highest_price', entry_price)
        if current_price > highest_price:
            position['highest_price'] = current_price
        
        trailing_stop = highest_price - (2.5 * position['atr_at_entry'])
        if current_price <= trailing_stop:
            return True, "TRAILING_STOP", 1.0
        
        # TP1: 20DMA (scale out 50%)
        if current_price >= indicators['ma_20'] and position.get('tp1_hit', False) == False:
            position['tp1_hit'] = True
            return True, "TP1_20DMA", 0.5  # Scale out 50%
        
        # TP2: +1σ above 20-day median (exit remaining)
        median_plus_1sigma = indicators['median_20'] + (indicators['median_20'] * 0.02)  # Approximate 1σ
        if current_price >= median_plus_1sigma and position.get('tp1_hit', False):
            return True, "TP2_MEDIAN+1σ", 1.0
        
        # Time Stop: Exit at close of day 3
        if days_held >= 3:
            return True, "TIME_STOP_3DAYS", 1.0
        
        return False, "", 0.0
    
    def check_signals(self, symbol: str, data: pd.DataFrame, current_idx: int) -> Dict:
        """Check for trading signals."""
        # Calculate indicators
        indicators = self.calculate_indicators(data, current_idx)
        if indicators is None:
            return {'action': 'HOLD', 'reason': 'Insufficient data'}
        
        current_date = indicators['current_date']
        if isinstance(current_date, pd.Timestamp):
            pass
        else:
            # Convert index to datetime if needed
            if isinstance(data.index[0], pd.Timestamp):
                current_date = data.index[current_idx]
            else:
                current_date = datetime.now()
        
        # Don't check exits here - backtest loop handles it
        # Just check if we already have a position
        if symbol in self.positions:
            return {'action': 'HOLD', 'reason': 'Managing position'}
        
        # Check regime filter
        if not self.check_regime(current_date):
            return {'action': 'HOLD', 'reason': 'Regime filter: VIX >= 25 or SPY 50DMA <= 200DMA'}
        
        # Check portfolio limits
        if len(self.positions) >= self.max_positions:
            return {'action': 'HOLD', 'reason': f'Max positions ({self.max_positions}) reached'}
        
        # Check entry conditions
        can_enter, reason = self.check_entry_conditions(indicators)
        
        if can_enter:
            # Calculate position size
            initial_stop = indicators['current_price'] - (1.5 * indicators['atr'])
            position_size_shares = self.calculate_position_size(indicators['current_price'], initial_stop)
            
            if position_size_shares > 0:
                return {
                    'action': 'BUY',
                    'reason': reason,
                    'shares': position_size_shares,
                    'entry_price': indicators['current_price'],
                    'atr': indicators['atr'],
                    'initial_stop': initial_stop
                }
        
        return {'action': 'HOLD', 'reason': reason if not can_enter else 'Position size too small'}
    
    def get_position_size(self, symbol: str, base_size: float) -> float:
        """Get position size (calculated dynamically in check_signals)."""
        # Position size is calculated in check_signals based on risk
        return base_size

