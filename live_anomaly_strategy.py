"""
Live Trading Anomaly Detection Strategy
Real-time version of the improved anomaly strategy for live trading
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class LiveAnomalyDetector:
    """Real-time anomaly detector for live trading."""
    
    def __init__(self, lookback_period: int = 20):
        self.lookback_period = lookback_period
    
    def fetch_recent_data(self, symbol: str, days: int = 30) -> pd.DataFrame:
        """Fetch recent stock data for analysis."""
        try:
            ticker = yf.Ticker(symbol)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            data = ticker.history(start=start_date, end=end_date, interval='1d')
            
            if data.empty:
                return pd.DataFrame()
            
            data = data.reset_index()
            data['Date'] = pd.to_datetime(data['Date'])
            return data
        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()
    
    def detect_anomalies(self, symbol: str) -> Dict:
        """Detect anomalies for a stock in real-time."""
        data = self.fetch_recent_data(symbol, days=30)
        
        if data.empty or len(data) < self.lookback_period + 1:
            return {'is_anomaly': False, 'signal_type': None, 'severity': 0}
        
        # Use the last data point as current
        current_idx = len(data) - 1
        
        # Calculate statistics
        historical = data.iloc[current_idx - self.lookback_period:current_idx]
        current = data.iloc[current_idx]
        
        mean_price = historical['Close'].mean()
        std_price = historical['Close'].std()
        current_price = current['Close']
        
        # Z-score
        z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
        
        # Price change
        price_change_pct = ((current['Close'] - data.iloc[current_idx - 1]['Close']) / 
                           data.iloc[current_idx - 1]['Close']) * 100
        
        # Volume
        mean_volume = historical['Volume'].mean()
        volume_ratio = current['Volume'] / mean_volume if mean_volume > 0 else 1
        
        # RSI
        rsi = self._calculate_rsi(data['Close'].iloc[:current_idx + 1], 14)
        current_rsi = rsi.iloc[-1] if len(rsi) > 0 and not pd.isna(rsi.iloc[-1]) else 50
        
        # Gap
        gap_pct = ((current['Open'] - data.iloc[current_idx - 1]['Close']) / 
                  data.iloc[current_idx - 1]['Close']) * 100
        
        # Detect anomalies
        anomalies = []
        severity = 0
        
        # Buy signals
        if z_score < -2.0:
            anomalies.append('oversold')
            severity += abs(z_score)
        if price_change_pct < -3.0:
            anomalies.append('extreme_drop')
            severity += abs(price_change_pct) / 3
        if gap_pct < -2.0:
            anomalies.append('gap_down')
            severity += abs(gap_pct) / 2
        if current_rsi < 30:
            anomalies.append('rsi_oversold')
            severity += (30 - current_rsi) / 10
        
        # Sell signals
        if z_score > 2.0:
            anomalies.append('overbought')
            severity += abs(z_score)
        if price_change_pct > 3.0:
            anomalies.append('extreme_rise')
            severity += abs(price_change_pct) / 3
        if gap_pct > 2.0:
            anomalies.append('gap_up')
            severity += abs(gap_pct) / 2
        if current_rsi > 70:
            anomalies.append('rsi_overbought')
            severity += (current_rsi - 70) / 10
        
        # Volume spike
        if volume_ratio > 2.0:
            anomalies.append('volume_spike')
            severity += 1
        
        # Determine signal type
        buy_signals = ['oversold', 'extreme_drop', 'gap_down', 'rsi_oversold']
        sell_signals = ['overbought', 'extreme_rise', 'gap_up', 'rsi_overbought']
        
        signal_type = None
        if any(signal in anomalies for signal in buy_signals):
            signal_type = 'BUY'
        if any(signal in anomalies for signal in sell_signals):
            if signal_type == 'BUY':
                signal_type = 'MIXED'
            else:
                signal_type = 'SELL'
        
        return {
            'is_anomaly': len(anomalies) > 0,
            'signal_type': signal_type,
            'severity': severity,
            'anomaly_types': anomalies,
            'z_score': z_score,
            'price_change_pct': price_change_pct,
            'rsi': current_rsi,
            'current_price': current_price
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


class LivePositionTracker:
    """Tracks positions with stop-loss and trailing stop. Supports multiple positions per symbol."""
    
    def __init__(self, stop_loss_pct: float = 0.05, trailing_stop_pct: float = 0.05):
        self.positions = {}  # symbol -> List of Position info (allows multiple positions per symbol)
        self.stop_loss_pct = stop_loss_pct
        self.trailing_stop_pct = trailing_stop_pct
    
    def add_position(self, symbol: str, shares: float, entry_price: float):
        """Add a new position (can have multiple positions per symbol)."""
        if symbol not in self.positions:
            self.positions[symbol] = []
        
        self.positions[symbol].append({
            'shares': shares,
            'entry_price': entry_price,
            'entry_date': datetime.now(),
            'highest_price': entry_price,
            'stop_loss_price': entry_price * (1 - self.stop_loss_pct),
            'trailing_stop_price': entry_price * (1 - self.trailing_stop_pct)
        })
    
    def update_position(self, symbol: str, current_price: float) -> Tuple[bool, Optional[str], Optional[Dict]]:
        """
        Update all positions for a symbol and check if stop-loss or trailing stop should trigger.
        
        Returns:
            (should_sell, reason, position_to_sell) - True if should sell, reason, and which position
        """
        if symbol not in self.positions or len(self.positions[symbol]) == 0:
            return False, None, None
        
        # Check each position independently
        for pos in self.positions[symbol]:
            # Update highest price for trailing stop
            if current_price > pos['highest_price']:
                pos['highest_price'] = current_price
                pos['trailing_stop_price'] = current_price * (1 - self.trailing_stop_pct)
            
            # Check stop-loss first (more urgent)
            if current_price <= pos['stop_loss_price']:
                return True, 'STOP_LOSS', pos
            
            # Check trailing stop
            if current_price <= pos['trailing_stop_price']:
                return True, 'TRAILING_STOP', pos
        
        return False, None, None
    
    def remove_position(self, symbol: str, position_to_remove: Optional[Dict] = None):
        """Remove a position. If position_to_remove is None, removes all positions for symbol."""
        if symbol not in self.positions:
            return
        
        if position_to_remove is None:
            # Remove all positions
            del self.positions[symbol]
        else:
            # Remove specific position
            if position_to_remove in self.positions[symbol]:
                self.positions[symbol].remove(position_to_remove)
            
            # Clean up empty lists
            if len(self.positions[symbol]) == 0:
                del self.positions[symbol]
    
    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get first position info for a symbol (for backward compatibility)."""
        if symbol in self.positions and len(self.positions[symbol]) > 0:
            return self.positions[symbol][0]
        return None
    
    def get_all_positions_for_symbol(self, symbol: str) -> List[Dict]:
        """Get all positions for a symbol."""
        return self.positions.get(symbol, []).copy()
    
    def has_position(self, symbol: str) -> bool:
        """Check if we have any position in a symbol."""
        return symbol in self.positions and len(self.positions[symbol]) > 0
    
    def get_all_positions(self) -> Dict:
        """Get all positions (symbol -> list of positions)."""
        return {symbol: positions.copy() for symbol, positions in self.positions.items()}
    
    def get_total_shares(self, symbol: str) -> float:
        """Get total shares across all positions for a symbol."""
        if symbol not in self.positions:
            return 0.0
        return sum(pos['shares'] for pos in self.positions[symbol])


class LiveAnomalyStrategy:
    """Live trading version of improved anomaly strategy."""
    
    def __init__(self, min_severity: float = 1.0, stop_loss_pct: float = 0.05,
                 trailing_stop_pct: float = 0.05):
        self.min_severity = min_severity
        self.detector = LiveAnomalyDetector()
        self.position_tracker = LivePositionTracker(stop_loss_pct, trailing_stop_pct)
        self.stock_performance = {}  # For dynamic position sizing
    
    def get_position_size(self, symbol: str, base_size: float) -> float:
        """Get dynamic position size based on performance."""
        if symbol not in self.stock_performance:
            return base_size
        
        perf = self.stock_performance[symbol]
        wins = perf.get('wins', 0)
        losses = perf.get('losses', 0)
        total = wins + losses
        
        if total == 0:
            return base_size
        
        win_rate = wins / total
        
        if win_rate >= 0.6:
            return base_size * 1.2
        elif win_rate >= 0.5:
            return base_size
        elif win_rate >= 0.4:
            return base_size * 0.8
        else:
            return base_size * 0.6
    
    def update_performance(self, symbol: str, profit: float):
        """Update performance tracking."""
        if symbol not in self.stock_performance:
            self.stock_performance[symbol] = {'wins': 0, 'losses': 0}
        
        if profit > 0:
            self.stock_performance[symbol]['wins'] += 1
        else:
            self.stock_performance[symbol]['losses'] += 1
    
    def check_signals(self, symbol: str) -> Dict:
        """
        Check for trading signals for a symbol.
        
        Returns:
            Dict with 'action' ('BUY', 'SELL', 'HOLD'), 'reason', 'severity', etc.
        """
        # Check existing positions for stop-loss/trailing stop
        if self.position_tracker.has_position(symbol):
            # Get current price
            data = self.detector.fetch_recent_data(symbol, days=1)
            if not data.empty:
                current_price = data.iloc[-1]['Close']
                should_sell, reason, position_to_sell = self.position_tracker.update_position(symbol, current_price)
                if should_sell:
                    return {
                        'action': 'SELL',
                        'reason': reason,
                        'symbol': symbol,
                        'current_price': current_price,
                        'position_to_sell': position_to_sell  # Track which position triggered
                    }
        
        # Check for new anomalies
        anomaly_info = self.detector.detect_anomalies(symbol)
        
        if not anomaly_info['is_anomaly']:
            return {'action': 'HOLD', 'reason': 'No anomaly detected'}
        
        if anomaly_info['severity'] < self.min_severity:
            return {'action': 'HOLD', 'reason': f"Severity {anomaly_info['severity']:.2f} below threshold {self.min_severity}"}
        
        signal_type = anomaly_info.get('signal_type')
        
        # Allow multiple positions per symbol (like backtest)
        # Note: Alpaca will combine them into one physical position, but we track them separately
        # for independent stop-loss/trailing stop management
        
        # Handle sell signals (overbought) - only if we have position and strong signal
        if signal_type in ['SELL', 'MIXED'] and self.position_tracker.has_position(symbol):
            if anomaly_info['severity'] >= 3.0:  # Very strong overbought
                return {
                    'action': 'SELL',
                    'reason': 'OVERBOUGHT',
                    'symbol': symbol,
                    'current_price': anomaly_info['current_price'],
                    'severity': anomaly_info['severity']
                }
        
        # Buy signal
        if signal_type in ['BUY', 'MIXED']:
            return {
                'action': 'BUY',
                'reason': ', '.join(anomaly_info['anomaly_types']),
                'symbol': symbol,
                'current_price': anomaly_info['current_price'],
                'severity': anomaly_info['severity'],
                'anomaly_types': anomaly_info['anomaly_types']
            }
        
        return {'action': 'HOLD', 'reason': 'No clear signal'}

