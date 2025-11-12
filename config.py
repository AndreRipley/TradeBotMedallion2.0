"""
Configuration module for the trading bot.
"""
import os
from typing import List
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration settings for the trading bot."""
    
    # Stock symbols to monitor (comma-separated in .env or list here)
    # Default: 30 diversified stocks for better opportunities and risk management
    # Tech: AAPL, MSFT, GOOGL, AMZN, NVDA, META, TSLA, ADBE, CSCO, NFLX, ACN
    # Finance: V, JPM, MA
    # Healthcare: UNH, JNJ, LLY, MRK, ABBV, ABT, TMO
    # Consumer: WMT, PG, COST, MCD
    # Energy: XOM, CVX
    # Industrial: HD, AVGO
    STOCKS: List[str] = os.getenv(
        'STOCKS', 
        'AAPL,MSFT,GOOGL,AMZN,NVDA,META,TSLA,V,UNH,XOM,JNJ,JPM,WMT,MA,PG,LLY,AVGO,HD,CVX,MRK,ABBV,COST,ADBE,PEP,TMO,MCD,CSCO,NFLX,ABT,ACN'
    ).split(',')
    
    # Trading API Configuration
    # For Alpaca (recommended for paper trading)
    ALPACA_API_KEY = os.getenv('ALPACA_API_KEY', '')
    ALPACA_SECRET_KEY = os.getenv('ALPACA_SECRET_KEY', '')
    ALPACA_BASE_URL = os.getenv('ALPACA_BASE_URL', 'https://paper-api.alpaca.markets')
    
    # For Alpha Vantage (free stock data API)
    ALPHA_VANTAGE_API_KEY = os.getenv('ALPHA_VANTAGE_API_KEY', '')
    
    # Trading settings
    TRADE_TIME = '12:00'  # Noon in 24-hour format
    TIMEZONE = os.getenv('TIMEZONE', 'America/New_York')
    
    # Position sizing (dollar amount per stock)
    POSITION_SIZE = float(os.getenv('POSITION_SIZE', '1000.0'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'trading_bot.log')

