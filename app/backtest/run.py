"""CLI entrypoint for running backtests."""

import argparse
import logging
from datetime import datetime
from app.backtest.engine import BacktestEngine
from app.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Run backtest."""
    parser = argparse.ArgumentParser(description="Run backtest on historical alerts")
    parser.add_argument(
        "--start-date",
        type=str,
        help="Start date (YYYY-MM-DD)",
        default=None
    )
    parser.add_argument(
        "--end-date",
        type=str,
        help="End date (YYYY-MM-DD)",
        default=None
    )
    parser.add_argument(
        "--symbol",
        type=str,
        help="Filter by symbol",
        default=None
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export results to CSV file",
        default=None
    )
    
    args = parser.parse_args()
    
    # Parse dates
    start_date = None
    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    
    end_date = None
    if args.end_date:
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    # Run backtest
    engine = BacktestEngine()
    results = engine.run_backtest(
        start_date=start_date,
        end_date=end_date,
        symbol=args.symbol
    )
    
    # Print results
    engine.print_results(results)
    
    # Export if requested
    if args.export:
        engine.export_results(results, args.export)
        print(f"\nResults exported to {args.export}")


if __name__ == "__main__":
    main()

