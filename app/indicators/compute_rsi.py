"""CLI entrypoint for computing RSI."""

import argparse
import logging
from app.indicators import RsiCalculator
from app.models import Universe, get_session
from app.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Compute RSI for symbol(s)."""
    parser = argparse.ArgumentParser(description="Compute RSI(14) Wilder for symbols")
    parser.add_argument(
        "--symbol",
        type=str,
        help="Single symbol to compute RSI for"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Compute RSI for all symbols in universe"
    )
    parser.add_argument(
        "--lookback-months",
        type=int,
        default=None,
        help="Number of months to look back (default from config)"
    )
    
    args = parser.parse_args()
    
    if not args.symbol and not args.all:
        parser.error("Must specify --symbol or --all")
    
    calculator = RsiCalculator()
    
    if args.symbol:
        logger.info(f"Computing RSI for {args.symbol}")
        count = calculator.compute_rsi_for_symbol(
            args.symbol,
            lookback_months=args.lookback_months
        )
        print(f"Computed {count} RSI values for {args.symbol}")
    
    elif args.all:
        session = get_session()
        try:
            universe_symbols = [
                u.symbol for u in session.query(Universe).filter_by(active=True).all()
            ]
            logger.info(f"Computing RSI for {len(universe_symbols)} symbols in universe")
            
            for symbol in universe_symbols:
                count = calculator.compute_rsi_for_symbol(
                    symbol,
                    lookback_months=args.lookback_months
                )
                print(f"{symbol}: {count} RSI values")
        finally:
            session.close()


if __name__ == "__main__":
    main()

