"""Universe building logic."""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
import pandas as pd
from sqlalchemy.orm import Session
from app.models import Symbol, Candle, Universe, get_session, init_db
from app.data_providers import (
    SymbolUniverseProvider, FundamentalsProvider, IntradayPriceProvider,
    SecApiUniverseProvider, AlphaVantageFundamentalsProvider
)
from app.config import get_config

logger = logging.getLogger(__name__)


class UniverseBuilder:
    """Builds and maintains the trading universe."""
    
    def __init__(
        self,
        symbol_provider: Optional[SymbolUniverseProvider] = None,
        fundamentals_provider: Optional[FundamentalsProvider] = None,
        price_provider: Optional[IntradayPriceProvider] = None
    ):
        self.config = get_config()
        self.symbol_provider = symbol_provider or SecApiUniverseProvider()
        self.fundamentals_provider = fundamentals_provider or AlphaVantageFundamentalsProvider()
        self.price_provider = price_provider
        
        if self.price_provider is None:
            from app.data_providers import MockIntradayPriceProvider
            self.price_provider = MockIntradayPriceProvider()
    
    def build(self) -> List[str]:
        """
        Build the universe by:
        1. Fetching all symbols
        2. Filtering by market cap (≥ $5B)
        3. Downloading 13 months of candles
        4. Computing performance metrics
        5. Filtering by performance thresholds
        6. Storing results
        
        Returns:
            List of symbols in the final universe
        """
        logger.info("Starting universe build process")
        init_db()
        
        session = get_session()
        try:
            # Step 1: Fetch all symbols
            logger.info("Step 1: Fetching symbol universe")
            all_symbols = self.symbol_provider.get_all_symbols()
            logger.info(f"Retrieved {len(all_symbols)} symbols")
            
            # Step 2: Enrich with market cap and filter
            logger.info("Step 2: Enriching with market cap and filtering")
            seed_list = []
            
            for symbol_info in all_symbols:
                market_cap = self.fundamentals_provider.get_market_cap(symbol_info.symbol)
                
                if market_cap and market_cap >= self.config.universe.min_market_cap:
                    # Store or update symbol
                    symbol_obj = session.query(Symbol).filter_by(symbol=symbol_info.symbol).first()
                    if not symbol_obj:
                        symbol_obj = Symbol(
                            symbol=symbol_info.symbol,
                            company_name=symbol_info.company_name,
                            cik=symbol_info.cik,
                            market_cap=market_cap,
                            is_active=True
                        )
                        session.add(symbol_obj)
                    else:
                        symbol_obj.market_cap = market_cap
                        symbol_obj.company_name = symbol_info.company_name
                        symbol_obj.cik = symbol_info.cik
                    
                    seed_list.append(symbol_info.symbol)
                    logger.debug(f"Added {symbol_info.symbol} to seed list (market cap: ${market_cap:,})")
            
            session.commit()
            logger.info(f"Seed list size: {len(seed_list)} symbols")
            
            # Step 3: Download candles and compute performance
            logger.info("Step 3: Downloading candles and computing performance")
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30 * self.config.universe.lookback_months)
            
            performance_data = {}
            
            for symbol in seed_list:
                logger.info(f"Processing {symbol}...")
                
                # Download candles
                candles = self.price_provider.get_historical_candles(
                    symbol, start_date, end_date, interval="5min"
                )
                
                if not candles:
                    logger.warning(f"No candles retrieved for {symbol}")
                    continue
                
                # Store candles
                for candle_data in candles:
                    existing = session.query(Candle).filter_by(
                        symbol=candle_data.symbol,
                        ts=candle_data.ts
                    ).first()
                    
                    if not existing:
                        candle = Candle(
                            symbol=candle_data.symbol,
                            ts=candle_data.ts,
                            open=candle_data.open,
                            high=candle_data.high,
                            low=candle_data.low,
                            close=candle_data.close,
                            volume=candle_data.volume,
                            interval=candle_data.interval
                        )
                        session.add(candle)
                
                session.commit()
                
                # Compute performance metrics
                perf = self._compute_performance_metrics(session, symbol, end_date)
                if perf:
                    performance_data[symbol] = perf
            
            # Step 4: Filter by performance thresholds
            logger.info("Step 4: Filtering by performance thresholds")
            universe_symbols = []
            
            for symbol, perf in performance_data.items():
                if (perf["three_month_return"] >= self.config.universe.three_month_min_return and
                    perf["six_month_return"] >= self.config.universe.six_month_min_return and
                    perf["ytd_return"] >= self.config.universe.ytd_min_return):
                    universe_symbols.append(symbol)
                    
                    # Store in universe table
                    universe_entry = session.query(Universe).filter_by(symbol=symbol).first()
                    if not universe_entry:
                        universe_entry = Universe(symbol=symbol, active=True)
                        session.add(universe_entry)
                    else:
                        universe_entry.active = True
                        universe_entry.updated_at = datetime.utcnow()
            
            # Deactivate symbols no longer in universe
            active_universe = set(universe_symbols)
            for entry in session.query(Universe).filter_by(active=True).all():
                if entry.symbol not in active_universe:
                    entry.active = False
                    entry.updated_at = datetime.utcnow()
            
            session.commit()
            
            logger.info(f"Universe build complete. Final universe size: {len(universe_symbols)} symbols")
            return universe_symbols
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error building universe: {e}", exc_info=True)
            raise
        finally:
            session.close()
    
    def _compute_performance_metrics(
        self,
        session: Session,
        symbol: str,
        end_date: datetime
    ) -> Optional[dict]:
        """Compute 3-month, 6-month, and YTD returns."""
        try:
            # Get all candles for symbol
            candles = session.query(Candle).filter_by(symbol=symbol).order_by(Candle.ts).all()
            
            if len(candles) < 2:
                return None
            
            # Convert to DataFrame
            df = pd.DataFrame([{
                "ts": c.ts,
                "close": c.close
            } for c in candles])
            
            # Resample to daily closes
            df["date"] = pd.to_datetime(df["ts"]).dt.date
            daily_closes = df.groupby("date")["close"].last().reset_index()
            daily_closes["date"] = pd.to_datetime(daily_closes["date"])
            daily_closes = daily_closes.sort_values("date")
            
            if len(daily_closes) < 2:
                return None
            
            latest_close = daily_closes["close"].iloc[-1]
            
            # Compute returns
            three_months_ago = end_date - timedelta(days=90)
            six_months_ago = end_date - timedelta(days=180)
            ytd_start = datetime(end_date.year, 1, 1)
            
            def get_closest_close(target_date):
                """Get closest close price before or at target date."""
                mask = daily_closes["date"] <= target_date
                if mask.any():
                    return daily_closes[mask]["close"].iloc[-1]
                return daily_closes["close"].iloc[0]
            
            three_month_close = get_closest_close(three_months_ago)
            six_month_close = get_closest_close(six_months_ago)
            ytd_close = get_closest_close(ytd_start)
            
            three_month_return = ((latest_close - three_month_close) / three_month_close) * 100
            six_month_return = ((latest_close - six_month_close) / six_month_close) * 100
            ytd_return = ((latest_close - ytd_close) / ytd_close) * 100
            
            return {
                "three_month_return": three_month_return,
                "six_month_return": six_month_return,
                "ytd_return": ytd_return
            }
            
        except Exception as e:
            logger.error(f"Error computing performance for {symbol}: {e}")
            return None

