"""CLI entrypoint for real-time monitoring."""

import asyncio
import logging
from app.realtime import run_realtime_monitor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Run the real-time monitor."""
    logger.info("Starting real-time monitor")
    try:
        asyncio.run(run_realtime_monitor())
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")


if __name__ == "__main__":
    main()

