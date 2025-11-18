"""CLI entrypoint for building the universe."""

import logging
from app.universe import UniverseBuilder
from app.config import get_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Build the universe."""
    logger.info("Starting universe build")
    config = get_config()
    
    builder = UniverseBuilder()
    universe_symbols = builder.build()
    
    logger.info(f"Universe build complete. Size: {len(universe_symbols)} symbols")
    print(f"\nUniverse contains {len(universe_symbols)} symbols:")
    for symbol in sorted(universe_symbols):
        print(f"  - {symbol}")


if __name__ == "__main__":
    main()

