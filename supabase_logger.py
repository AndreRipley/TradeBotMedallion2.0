"""
Supabase logger for ticker price logging.
Logs all ticker price checks to Supabase database.
"""
import logging
from datetime import datetime
from typing import Optional, Dict
from config import Config

logger = logging.getLogger(__name__)

# Supabase client (lazy initialization)
_supabase_client = None


def get_supabase_client():
    """Get or create Supabase client."""
    global _supabase_client
    
    if _supabase_client is not None:
        return _supabase_client
    
    try:
        from supabase import create_client, Client
        
        supabase_url = Config.SUPABASE_URL
        supabase_key = Config.SUPABASE_KEY
        
        if not supabase_url or not supabase_key:
            logger.warning("Supabase credentials not configured. Price logging disabled.")
            return None
        
        _supabase_client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
        return _supabase_client
        
    except ImportError:
        logger.warning("supabase-py not installed. Install with: pip install supabase")
        return None
    except Exception as e:
        logger.error(f"Error initializing Supabase client: {e}")
        return None


def log_ticker_price(
    symbol: str,
    price: float,
    price_type: str = 'close',
    source: str = 'yfinance',
    volume: Optional[float] = None,
    timestamp: Optional[datetime] = None
) -> bool:
    """
    Log ticker price to Supabase.
    
    Args:
        symbol: Stock symbol (e.g., 'AAPL')
        price: Current price
        price_type: Type of price ('close', 'ask', 'bid', 'intraday')
        source: Data source ('yfinance', 'alpaca', etc.)
        volume: Trading volume (optional)
        timestamp: Timestamp (defaults to now)
        
    Returns:
        True if logged successfully, False otherwise
    """
    client = get_supabase_client()
    
    if client is None:
        return False
    
    try:
        if timestamp is None:
            timestamp = datetime.now()
        
        # Prepare data for insertion
        data = {
            'symbol': symbol.upper(),
            'price': float(price),
            'price_type': price_type,
            'source': source,
            'timestamp': timestamp.isoformat(),
        }
        
        if volume is not None:
            data['volume'] = float(volume)
        
        # Insert into Supabase
        response = client.table('ticker_prices').insert(data).execute()
        
        if response.data:
            logger.debug(f"✅ Logged {symbol} price ${price:.2f} to Supabase")
            return True
        else:
            logger.warning(f"⚠️  Failed to log {symbol} price to Supabase: {response}")
            return False
            
    except Exception as e:
        logger.error(f"Error logging ticker price to Supabase: {e}")
        return False


def log_price_check(
    symbol: str,
    price: float,
    context: str = 'signal_check',
    additional_data: Optional[Dict] = None
) -> bool:
    """
    Log a price check with context.
    
    Args:
        symbol: Stock symbol
        price: Price checked
        context: Context of the check ('signal_check', 'position_monitor', 'buy', 'sell')
        additional_data: Additional data to log (optional)
        
    Returns:
        True if logged successfully
    """
    price_type_map = {
        'signal_check': 'close',
        'position_monitor': 'intraday',
        'buy': 'ask',
        'sell': 'bid'
    }
    
    source_map = {
        'signal_check': 'yfinance',
        'position_monitor': 'yfinance',
        'buy': 'alpaca',
        'sell': 'alpaca'
    }
    
    price_type = price_type_map.get(context, 'close')
    source = source_map.get(context, 'yfinance')
    
    data = additional_data or {}
    if 'volume' in data:
        volume = data['volume']
    else:
        volume = None
    
    return log_ticker_price(
        symbol=symbol,
        price=price,
        price_type=price_type,
        source=source,
        volume=volume
    )

