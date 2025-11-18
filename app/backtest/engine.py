"""Backtest engine for simulating trade rules on historical alerts."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple
from dataclasses import dataclass
import pandas as pd
from sqlalchemy.orm import Session
from app.models import Alert, Candle, get_session, init_db
from app.config import get_config

logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """Represents a simulated trade."""
    symbol: str
    entry_time: datetime
    entry_price: float
    exit_time: Optional[datetime]
    exit_price: Optional[float]
    exit_reason: Optional[str]  # "take_profit", "max_holding", "end_of_data"
    pnl: Optional[float]  # Percentage return
    holding_days: Optional[float]
    alert_id: int


@dataclass
class BacktestResults:
    """Backtest results summary."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_return: float
    avg_return: float
    avg_winning_return: float
    avg_losing_return: float
    max_win: float
    max_loss: float
    avg_holding_days: float
    trades: List[Trade]


class BacktestEngine:
    """Backtest engine for simulating trades based on alerts."""
    
    def __init__(self):
        self.config = get_config()
    
    def find_entry_candle(
        self,
        symbol: str,
        alert_time: datetime,
        session: Session
    ) -> Optional[Candle]:
        """
        Find the next 5-minute candle after alert time (entry candle).
        
        Entry rule: Buy next 5-minute candle after alert.
        """
        # Get candles after alert time, ordered by timestamp
        candles = session.query(Candle).filter(
            Candle.symbol == symbol,
            Candle.ts > alert_time
        ).order_by(Candle.ts).limit(1).all()
        
        if candles:
            return candles[0]
        return None
    
    def find_exit_candle(
        self,
        symbol: str,
        entry_time: datetime,
        entry_price: float,
        take_profit_pct: float,
        max_holding_days: int,
        session: Session
    ) -> Tuple[Optional[Candle], str]:
        """
        Find exit candle based on take profit or max holding time.
        
        Returns:
            (exit_candle, exit_reason)
        """
        # Calculate target prices
        take_profit_price = entry_price * (1 + take_profit_pct / 100)
        max_holding_date = entry_time + timedelta(days=max_holding_days)
        
        # Get all candles after entry
        candles = session.query(Candle).filter(
            Candle.symbol == symbol,
            Candle.ts > entry_time
        ).order_by(Candle.ts).all()
        
        if not candles:
            return None, "end_of_data"
        
        # Check each candle for exit conditions
        for candle in candles:
            # Check take profit (check if high reached target)
            if candle.high >= take_profit_price:
                # Exit at take profit price (use the candle but note we exit at target)
                # For PnL calculation, we'll use take_profit_price as exit_price
                return candle, "take_profit"
            
            # Check max holding time
            if candle.ts >= max_holding_date:
                # Exit at close of this candle
                return candle, "max_holding"
        
        # No exit condition met, use last candle
        return candles[-1], "end_of_data"
    
    def simulate_trade(
        self,
        alert: Alert,
        session: Session
    ) -> Optional[Trade]:
        """
        Simulate a trade from an alert.
        
        Returns:
            Trade object or None if entry candle not found
        """
        # Find entry candle (next 5-min candle after alert)
        entry_candle = self.find_entry_candle(alert.symbol, alert.ts, session)
        
        if not entry_candle:
            logger.warning(f"No entry candle found for alert {alert.id} ({alert.symbol})")
            return None
        
        entry_time = entry_candle.ts
        entry_price = entry_candle.close  # Use close price for entry
        
        # Find exit candle
        exit_candle, exit_reason = self.find_exit_candle(
            alert.symbol,
            entry_time,
            entry_price,
            alert.take_profit_pct,
            alert.max_holding_days,
            session
        )
        
        if not exit_candle:
            return None
        
        exit_time = exit_candle.ts
        
        # For take profit exits, use the target price; otherwise use close
        if exit_reason == "take_profit":
            take_profit_price = entry_price * (1 + alert.take_profit_pct / 100)
            exit_price = min(take_profit_price, exit_candle.close)  # Can't exceed actual high
        else:
            exit_price = exit_candle.close
        
        # Calculate PnL
        pnl = ((exit_price - entry_price) / entry_price) * 100
        holding_days = (exit_time - entry_time).total_seconds() / (24 * 3600)
        
        return Trade(
            symbol=alert.symbol,
            entry_time=entry_time,
            entry_price=entry_price,
            exit_time=exit_time,
            exit_price=exit_price,
            exit_reason=exit_reason,
            pnl=pnl,
            holding_days=holding_days,
            alert_id=alert.id
        )
    
    def run_backtest(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        symbol: Optional[str] = None,
        session: Optional[Session] = None
    ) -> BacktestResults:
        """
        Run backtest on historical alerts.
        
        Args:
            start_date: Start date for alerts (default: all)
            end_date: End date for alerts (default: all)
            symbol: Filter by symbol (default: all)
            session: Database session
            
        Returns:
            BacktestResults object
        """
        if session is None:
            session = get_session()
            should_close = True
        else:
            should_close = False
        
        try:
            # Initialize database if needed
            init_db()
            
            # Load alerts
            query = session.query(Alert)
            
            if start_date:
                query = query.filter(Alert.ts >= start_date)
            if end_date:
                query = query.filter(Alert.ts <= end_date)
            if symbol:
                query = query.filter(Alert.symbol == symbol)
            
            alerts = query.order_by(Alert.ts).all()
            
            if not alerts:
                logger.warning("No alerts found in database. You need to:")
                logger.warning("1. Build the universe: python -m app.universe.build")
                logger.warning("2. Compute RSI: python -m app.indicators.compute_rsi --all")
                logger.warning("3. Run monitor to generate alerts: python -m app.realtime.monitor")
                return BacktestResults(
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0.0,
                    total_return=0.0,
                    avg_return=0.0,
                    avg_winning_return=0.0,
                    avg_losing_return=0.0,
                    max_win=0.0,
                    max_loss=0.0,
                    avg_holding_days=0.0,
                    trades=[]
                )
            
            logger.info(f"Running backtest on {len(alerts)} alerts")
            
            # Simulate trades
            trades = []
            for alert in alerts:
                trade = self.simulate_trade(alert, session)
                if trade:
                    trades.append(trade)
            
            # Calculate statistics
            if not trades:
                logger.warning("No trades simulated")
                return BacktestResults(
                    total_trades=0,
                    winning_trades=0,
                    losing_trades=0,
                    win_rate=0.0,
                    total_return=0.0,
                    avg_return=0.0,
                    avg_winning_return=0.0,
                    avg_losing_return=0.0,
                    max_win=0.0,
                    max_loss=0.0,
                    avg_holding_days=0.0,
                    trades=[]
                )
            
            winning_trades = [t for t in trades if t.pnl > 0]
            losing_trades = [t for t in trades if t.pnl <= 0]
            
            total_return = sum(t.pnl for t in trades)
            avg_return = total_return / len(trades)
            win_rate = len(winning_trades) / len(trades) * 100
            
            avg_winning_return = (
                sum(t.pnl for t in winning_trades) / len(winning_trades)
                if winning_trades else 0.0
            )
            avg_losing_return = (
                sum(t.pnl for t in losing_trades) / len(losing_trades)
                if losing_trades else 0.0
            )
            
            max_win = max(t.pnl for t in trades) if trades else 0.0
            max_loss = min(t.pnl for t in trades) if trades else 0.0
            
            avg_holding_days = sum(t.holding_days for t in trades) / len(trades)
            
            results = BacktestResults(
                total_trades=len(trades),
                winning_trades=len(winning_trades),
                losing_trades=len(losing_trades),
                win_rate=win_rate,
                total_return=total_return,
                avg_return=avg_return,
                avg_winning_return=avg_winning_return,
                avg_losing_return=avg_losing_return,
                max_win=max_win,
                max_loss=max_loss,
                avg_holding_days=avg_holding_days,
                trades=trades
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error running backtest: {e}", exc_info=True)
            raise
        finally:
            if should_close:
                session.close()
    
    def print_results(self, results: BacktestResults) -> None:
        """Print backtest results in a readable format."""
        print("\n" + "="*60)
        print("BACKTEST RESULTS")
        print("="*60)
        print(f"Total Trades:        {results.total_trades}")
        print(f"Winning Trades:      {results.winning_trades}")
        print(f"Losing Trades:       {results.losing_trades}")
        print(f"Win Rate:            {results.win_rate:.2f}%")
        print(f"\nReturns:")
        print(f"  Total Return:      {results.total_return:.2f}%")
        print(f"  Average Return:    {results.avg_return:.2f}%")
        print(f"  Avg Winning:       {results.avg_winning_return:.2f}%")
        print(f"  Avg Losing:        {results.avg_losing_return:.2f}%")
        print(f"  Max Win:           {results.max_win:.2f}%")
        print(f"  Max Loss:          {results.max_loss:.2f}%")
        print(f"\nHolding Period:")
        print(f"  Avg Holding Days:  {results.avg_holding_days:.2f}")
        print("="*60)
        
        # Exit reasons breakdown
        exit_reasons = {}
        for trade in results.trades:
            reason = trade.exit_reason
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        print("\nExit Reasons:")
        for reason, count in exit_reasons.items():
            print(f"  {reason}: {count} ({count/len(results.trades)*100:.1f}%)")
        
        print("\n" + "="*60)
    
    def export_results(self, results: BacktestResults, filepath: str) -> None:
        """Export backtest results to CSV."""
        df = pd.DataFrame([{
            "symbol": t.symbol,
            "entry_time": t.entry_time,
            "entry_price": t.entry_price,
            "exit_time": t.exit_time,
            "exit_price": t.exit_price,
            "exit_reason": t.exit_reason,
            "pnl_pct": t.pnl,
            "holding_days": t.holding_days,
            "alert_id": t.alert_id
        } for t in results.trades])
        
        df.to_csv(filepath, index=False)
        logger.info(f"Exported {len(df)} trades to {filepath}")

