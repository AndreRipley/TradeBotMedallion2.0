"""
Main entry point for the trading bot with HTTP health check for Cloud Run.
"""
import logging
import os
import sys
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from config import Config
from scheduler import TradingScheduler


class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks."""
    
    def do_GET(self):
        """Handle GET requests for health checks."""
        if self.path == '/health' or self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'OK')
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress HTTP server logs."""
        pass


def start_health_server(port=8080):
    """Start HTTP server for health checks."""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    logging.info(f"Health check server started on port {port}")
    server.serve_forever()


def setup_logging():
    """Configure logging for the application."""
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    # File handler
    file_handler = logging.FileHandler(Config.LOG_FILE)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format))
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)


def main():
    """Main function to start the trading bot."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("🚀 Trading Bot Starting")
    logger.info("=" * 60)
    
    # Validate configuration
    if not Config.STOCKS:
        logger.error("No stocks configured. Please set STOCKS in .env or config.py")
        sys.exit(1)
    
    # Start health check server in background thread (for Cloud Run)
    health_port = int(os.getenv('PORT', 8080))
    health_thread = threading.Thread(target=start_health_server, args=(health_port,), daemon=True)
    health_thread.start()
    logger.info(f"Health check server started on port {health_port}")
    
    # Start scheduler
    scheduler = TradingScheduler()
    
    try:
        scheduler.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
