#!/usr/bin/env python3
"""
Add missing stocks to Supabase universe table.
This script connects directly to Supabase and adds stocks that are missing.
"""

import os
import sys
import logging
from datetime import datetime
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session
from app.models import Symbol, Universe, get_session, init_db
from app.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Top 100 stocks by market cap
TOP_100_STOCKS = [
    # Top 10
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK.B", "V", "UNH",
    # 11-20
    "XOM", "JNJ", "JPM", "WMT", "MA", "PG", "LLY", "AVGO", "HD", "CVX",
    # 21-30
    "MRK", "ABBV", "COST", "ADBE", "PEP", "TMO", "MCD", "CSCO", "NFLX", "ABT",
    # 31-40
    "ACN", "DHR", "VZ", "WFC", "DIS", "LIN", "NKE", "PM", "TXN", "NEE",
    # 41-50
    "CMCSA", "HON", "RTX", "UPS", "QCOM", "AMGN", "BMY", "T", "LOW", "SPGI",
    # 51-60
    "INTU", "DE", "BKNG", "ADP", "GE", "C", "ELV", "TJX", "AXP", "SYK",
    # 61-70
    "ISRG", "GILD", "LMT", "MDT", "ADI", "CB", "BLK", "MMC", "CI", "ZTS",
    # 71-80
    "EQIX", "CL", "ITW", "ETN", "SHW", "FIS", "ICE", "APH", "KLAC", "HCA",
    # 81-90
    "WM", "CME", "CDNS", "PSA", "FAST", "AON", "NXPI", "MCO", "CTAS", "FTNT",
    # 91-100
    "IDXX", "ODFL", "PAYX", "VRSK", "ANSS", "DXCM", "CTSH", "TTD", "ROST", "PCAR"
]

# Company names mapping
COMPANY_NAMES = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corporation", "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.", "NVDA": "NVIDIA Corporation", "META": "Meta Platforms Inc.",
    "TSLA": "Tesla Inc.", "BRK.B": "Berkshire Hathaway Inc.", "V": "Visa Inc.",
    "UNH": "UnitedHealth Group Inc.", "XOM": "Exxon Mobil Corporation",
    "JNJ": "Johnson & Johnson", "JPM": "JPMorgan Chase & Co.", "WMT": "Walmart Inc.",
    "MA": "Mastercard Incorporated", "PG": "The Procter & Gamble Company",
    "LLY": "Eli Lilly and Company", "AVGO": "Broadcom Inc.", "HD": "The Home Depot Inc.",
    "CVX": "Chevron Corporation", "MRK": "Merck & Co. Inc.", "ABBV": "AbbVie Inc.",
    "COST": "Costco Wholesale Corporation", "ADBE": "Adobe Inc.", "PEP": "PepsiCo Inc.",
    "TMO": "Thermo Fisher Scientific Inc.", "MCD": "McDonald's Corporation",
    "CSCO": "Cisco Systems Inc.", "NFLX": "Netflix Inc.", "ABT": "Abbott Laboratories",
    "ACN": "Accenture plc", "DHR": "Danaher Corporation",
    "VZ": "Verizon Communications Inc.", "WFC": "Wells Fargo & Company",
    "DIS": "The Walt Disney Company", "LIN": "Linde plc", "NKE": "Nike Inc.",
    "PM": "Philip Morris International Inc.", "TXN": "Texas Instruments Incorporated",
    "NEE": "NextEra Energy Inc.", "CMCSA": "Comcast Corporation",
    "HON": "Honeywell International Inc.", "RTX": "RTX Corporation",
    "UPS": "United Parcel Service Inc.", "QCOM": "QUALCOMM Incorporated",
    "AMGN": "Amgen Inc.", "BMY": "Bristol-Myers Squibb Company", "T": "AT&T Inc.",
    "LOW": "Lowe's Companies Inc.", "SPGI": "S&P Global Inc.", "INTU": "Intuit Inc.",
    "DE": "Deere & Company", "BKNG": "Booking Holdings Inc.",
    "ADP": "Automatic Data Processing Inc.", "GE": "General Electric Company",
    "C": "Citigroup Inc.", "ELV": "Elevance Health Inc.", "TJX": "The TJX Companies Inc.",
    "AXP": "American Express Company", "SYK": "Stryker Corporation",
    "ISRG": "Intuitive Surgical Inc.", "GILD": "Gilead Sciences Inc.",
    "LMT": "Lockheed Martin Corporation", "MDT": "Medtronic plc",
    "ADI": "Analog Devices Inc.", "CB": "Chubb Limited", "BLK": "BlackRock Inc.",
    "MMC": "Marsh & McLennan Companies Inc.", "CI": "Cigna Corporation",
    "ZTS": "Zoetis Inc.", "EQIX": "Equinix Inc.", "CL": "Colgate-Palmolive Company",
    "ITW": "Illinois Tool Works Inc.", "ETN": "Eaton Corporation plc",
    "SHW": "The Sherwin-Williams Company",
    "FIS": "Fidelity National Information Services Inc.",
    "ICE": "Intercontinental Exchange Inc.", "APH": "Amphenol Corporation",
    "KLAC": "KLA Corporation", "HCA": "HCA Healthcare Inc.",
    "WM": "Waste Management Inc.", "CME": "CME Group Inc.",
    "CDNS": "Cadence Design Systems Inc.", "PSA": "Public Storage",
    "FAST": "Fastenal Company", "AON": "Aon plc",
    "NXPI": "NXP Semiconductors N.V.", "MCO": "Moody's Corporation",
    "CTAS": "Cintas Corporation", "FTNT": "Fortinet Inc.",
    "IDXX": "IDEXX Laboratories Inc.", "ODFL": "Old Dominion Freight Line Inc.",
    "PAYX": "Paychex Inc.", "VRSK": "Verisk Analytics Inc.",
    "ANSS": "ANSYS Inc.", "DXCM": "Dexcom Inc.",
    "CTSH": "Cognizant Technology Solutions Corporation",
    "TTD": "The Trade Desk Inc.", "ROST": "Ross Stores Inc.",
    "PCAR": "PACCAR Inc."
}


def add_missing_stocks_to_supabase():
    """Add missing stocks to Supabase universe table."""
    # Ensure Supabase env vars are set
    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_DB_PASSWORD"):
        logger.error("SUPABASE_URL and SUPABASE_DB_PASSWORD must be set!")
        logger.info("Setting them now...")
        os.environ['SUPABASE_URL'] = 'https://rpugqgjacxfbfeqguqbs.supabase.co'
        os.environ['SUPABASE_DB_PASSWORD'] = 'Disire2424!!'
    
    init_db()
    config = get_config()
    engine = create_engine(config.database.url)
    
    logger.info(f"Connecting to: {config.database.url[:50]}...")
    
    with engine.connect() as conn:
        # Check current count
        result = conn.execute(text('SELECT COUNT(*) FROM universe WHERE active = true'))
        current_count = result.scalar()
        logger.info(f"Current stocks in universe: {current_count}")
        
        # Get existing symbols
        result = conn.execute(text('SELECT symbol FROM universe WHERE active = true'))
        existing_symbols = {row[0] for row in result}
        logger.info(f"Existing symbols: {len(existing_symbols)}")
        
        # Find missing symbols
        missing_symbols = [s for s in TOP_100_STOCKS if s not in existing_symbols]
        logger.info(f"Missing symbols: {len(missing_symbols)}")
        
        if not missing_symbols:
            logger.info("✅ All 100 stocks are already in the universe!")
            return
        
        # Add missing symbols
        added_symbols = 0
        added_universe = 0
        
        for symbol in missing_symbols:
            try:
                # Check if symbol exists in symbols table
                result = conn.execute(text('SELECT id FROM symbols WHERE symbol = :symbol'), {'symbol': symbol})
                symbol_row = result.fetchone()
                
                if not symbol_row:
                    # Add to symbols table first
                    company_name = COMPANY_NAMES.get(symbol, f"{symbol} Corporation")
                    conn.execute(text('''
                        INSERT INTO symbols (symbol, company_name, market_cap, is_active, created_at, updated_at)
                        VALUES (:symbol, :company_name, :market_cap, :is_active, NOW(), NOW())
                    '''), {
                        'symbol': symbol,
                        'company_name': company_name,
                        'market_cap': 100000000000,
                        'is_active': True
                    })
                    conn.commit()
                    added_symbols += 1
                    logger.info(f"Added symbol: {symbol}")
                
                # Add to universe table
                conn.execute(text('''
                    INSERT INTO universe (symbol, added_at, active, updated_at)
                    VALUES (:symbol, NOW(), :active, NOW())
                    ON CONFLICT (symbol) DO UPDATE SET active = :active, updated_at = NOW()
                '''), {
                    'symbol': symbol,
                    'active': True
                })
                conn.commit()
                added_universe += 1
                logger.info(f"Added to universe: {symbol}")
                
            except Exception as e:
                logger.error(f"Error adding {symbol}: {e}")
                conn.rollback()
        
        # Verify final count
        result = conn.execute(text('SELECT COUNT(*) FROM universe WHERE active = true'))
        final_count = result.scalar()
        
        logger.info(f"")
        logger.info(f"✅ Added {added_symbols} new symbols and {added_universe} to universe")
        logger.info(f"📊 Total stocks in universe: {final_count}")
        
        if final_count == 100:
            logger.info("✅ Success! All 100 stocks are now in the universe!")
        else:
            logger.warning(f"⚠️  Expected 100 stocks, but found {final_count}")


if __name__ == "__main__":
    logger.info("Adding missing stocks to Supabase universe...")
    add_missing_stocks_to_supabase()
    logger.info("Done!")

