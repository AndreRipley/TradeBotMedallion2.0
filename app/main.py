"""Main entrypoint for Cloud Run deployment."""

import os
import logging
import asyncio
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
# Import from parent app package
import sys
from pathlib import Path
# Add parent directory to path to import from app package
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))
# Import directly from realtime.py module (avoiding package conflict)
import importlib.util
realtime_path = Path(__file__).parent / "realtime.py"
spec = importlib.util.spec_from_file_location("realtime", realtime_path)
realtime = importlib.util.module_from_spec(spec)
spec.loader.exec_module(realtime)
run_realtime_monitor = realtime.run_realtime_monitor
from app.config import get_config

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for Cloud Run health checks."""
    
    def do_GET(self):
        """Handle GET requests for health checks."""
        if self.path == "/" or self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(b"OK - Trading Alert System Running")
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs."""
        pass


def start_http_server(port=8080):
    """Start HTTP server for Cloud Run health checks."""
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.info(f"HTTP health check server started on port {port}")
    server.serve_forever()


def main():
    """Main entrypoint for Cloud Run."""
    logger.info("Starting Trading Alert System")
    logger.info("=" * 60)
    
    # Log configuration
    config = get_config()
    logger.info(f"Database: {config.database.url}")
    logger.info(f"RSI Threshold: {config.rsi.threshold}")
    logger.info(f"Update Interval: {config.scheduler.update_interval_minutes} minutes")
    logger.info(f"Market Hours Only: {config.scheduler.market_hours_only}")
    logger.info("=" * 60)
    
    # Start HTTP server for Cloud Run health checks (in background thread)
    port = int(os.getenv("PORT", "8080"))
    http_thread = Thread(target=start_http_server, args=(port,), daemon=True)
    http_thread.start()
    
    # Run the real-time monitor (main process)
    try:
        asyncio.run(run_realtime_monitor())
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()

