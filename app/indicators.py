"""Technical indicators - RSI calculation with Wilder smoothing."""

import logging
from datetime import datetime, timedelta
from typing import Optional, List
import pandas as pd
import numpy as np
from sqlalchemy.orm import Session
from app.models import Candle, RsiValue, get_session
from app.config import get_config

logger = logging.getLogger(__name__)


class RsiCalculator:
    """RSI calculator using Wilder smoothing method."""
    
    def __init__(self):
        self.config = get_config()
        self.period = self.config.rsi.period
    
    def compute_rsi_wilder(self, closes: pd.Series) -> pd.Series:
        """
        Compute RSI using Wilder's smoothing method.
        
        RSI = 100 - (100 / (1 + RS))
        RS = Average Gain / Average Loss
        
        Wilder smoothing:
        - First Average Gain = sum of gains over period / period
        - Subsequent Average Gain = (Previous Average Gain * (period - 1) + Current Gain) / period
        - Same for Average Loss
        
        Args:
            closes: Series of closing prices
            
        Returns:
            Series of RSI values (NaN for first period-1 values)
        """
        if len(closes) < self.period + 1:
            return pd.Series([np.nan] * len(closes), index=closes.index)
        
        # Calculate price changes
        deltas = closes.diff()
        
        # Separate gains and losses
        gains = deltas.where(deltas > 0, 0.0)
        losses = -deltas.where(deltas < 0, 0.0)
        
        # Initialize RSI array
        rsi = pd.Series(index=closes.index, dtype=float)
        
        # First average gain/loss (simple average)
        avg_gain = gains.iloc[1:self.period + 1].mean()
        avg_loss = losses.iloc[1:self.period + 1].mean()
        
        if avg_loss == 0:
            rsi.iloc[self.period] = 100.0
        else:
            rs = avg_gain / avg_loss
            rsi.iloc[self.period] = 100 - (100 / (1 + rs))
        
        # Subsequent values using Wilder smoothing
        for i in range(self.period + 1, len(closes)):
            current_gain = gains.iloc[i]
            current_loss = losses.iloc[i]
            
            # Wilder smoothing
            avg_gain = (avg_gain * (self.period - 1) + current_gain) / self.period
            avg_loss = (avg_loss * (self.period - 1) + current_loss) / self.period
            
            if avg_loss == 0:
                rsi.iloc[i] = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi.iloc[i] = 100 - (100 / (1 + rs))
        
        return rsi
    
    def compute_rsi_for_symbol(
        self,
        symbol: str,
        lookback_months: Optional[int] = None,
        session: Optional[Session] = None
    ) -> int:
        """
        Load candles from DB, compute RSI(14) Wilder, and persist results.
        
        Args:
            symbol: Stock symbol
            lookback_months: Number of months to look back (default from config)
            session: Database session (creates new if None)
            
        Returns:
            Number of RSI values computed and stored
        """
        if session is None:
            session = get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            if lookback_months is None:
                lookback_months = get_config().universe.lookback_months
            
            # Get candles
            cutoff_date = datetime.utcnow() - timedelta(days=30 * lookback_months)
            candles = session.query(Candle).filter(
                Candle.symbol == symbol,
                Candle.ts >= cutoff_date
            ).order_by(Candle.ts).all()
            
            if len(candles) < self.period + 1:
                logger.warning(f"Insufficient candles for {symbol}: {len(candles)} < {self.period + 1}")
                return 0
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                "ts": c.ts,
                "close": c.close
            } for c in candles])
            
            # Compute RSI
            closes = pd.Series(df["close"].values, index=df.index)
            rsi_values = self.compute_rsi_wilder(closes)
            
            # Store RSI values
            stored_count = 0
            for idx, (ts, rsi_val) in enumerate(zip(df["ts"], rsi_values)):
                if pd.notna(rsi_val):
                    # Check if already exists
                    existing = session.query(RsiValue).filter_by(
                        symbol=symbol,
                        ts=ts
                    ).first()
                    
                    if not existing:
                        rsi_entry = RsiValue(
                            symbol=symbol,
                            ts=ts,
                            rsi_14=float(rsi_val)
                        )
                        session.add(rsi_entry)
                        stored_count += 1
                    else:
                        # Update existing
                        existing.rsi_14 = float(rsi_val)
                        stored_count += 1
            
            session.commit()
            logger.info(f"Computed and stored {stored_count} RSI values for {symbol}")
            return stored_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error computing RSI for {symbol}: {e}", exc_info=True)
            raise
        finally:
            if should_close:
                session.close()
    
    def compute_rsi_incremental(
        self,
        symbol: str,
        since: datetime,
        session: Optional[Session] = None
    ) -> int:
        """
        Compute RSI for new candles since a timestamp.
        Requires historical RSI values to compute correctly.
        
        Args:
            symbol: Stock symbol
            since: Timestamp to compute from
            session: Database session
            
        Returns:
            Number of new RSI values computed
        """
        if session is None:
            session = get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            # Get all candles up to now (need history for RSI)
            candles = session.query(Candle).filter(
                Candle.symbol == symbol
            ).order_by(Candle.ts).all()
            
            if len(candles) < self.period + 1:
                return 0
            
            # Get the last RSI value before 'since' to maintain continuity
            last_rsi = session.query(RsiValue).filter(
                RsiValue.symbol == symbol,
                RsiValue.ts < since
            ).order_by(RsiValue.ts.desc()).first()
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                "ts": c.ts,
                "close": c.close
            } for c in candles])
            
            # Compute RSI for entire series
            closes = pd.Series(df["close"].values, index=df.index)
            rsi_values = self.compute_rsi_wilder(closes)
            
            # Store only new values (since timestamp)
            stored_count = 0
            for idx, (ts, rsi_val) in enumerate(zip(df["ts"], rsi_values)):
                if pd.notna(rsi_val) and ts >= since:
                    existing = session.query(RsiValue).filter_by(
                        symbol=symbol,
                        ts=ts
                    ).first()
                    
                    if not existing:
                        rsi_entry = RsiValue(
                            symbol=symbol,
                            ts=ts,
                            rsi_14=float(rsi_val)
                        )
                        session.add(rsi_entry)
                        stored_count += 1
            
            session.commit()
            return stored_count
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error computing incremental RSI for {symbol}: {e}", exc_info=True)
            raise
        finally:
            if should_close:
                session.close()

