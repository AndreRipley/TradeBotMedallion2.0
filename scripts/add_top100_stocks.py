#!/usr/bin/env python3
"""
Add top 100 stocks by market cap to the universe.
This script adds stocks to both the symbols and universe tables.
"""

import logging
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Symbol, Universe, get_session, init_db
from app.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Top 100 stocks by market cap (as of 2024)
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

# Company names mapping (simplified)
COMPANY_NAMES = {
    "AAPL": "Apple Inc.",
    "MSFT": "Microsoft Corporation",
    "GOOGL": "Alphabet Inc.",
    "AMZN": "Amazon.com Inc.",
    "NVDA": "NVIDIA Corporation",
    "META": "Meta Platforms Inc.",
    "TSLA": "Tesla Inc.",
    "BRK.B": "Berkshire Hathaway Inc.",
    "V": "Visa Inc.",
    "UNH": "UnitedHealth Group Inc.",
    "XOM": "Exxon Mobil Corporation",
    "JNJ": "Johnson & Johnson",
    "JPM": "JPMorgan Chase & Co.",
    "WMT": "Walmart Inc.",
    "MA": "Mastercard Incorporated",
    "PG": "The Procter & Gamble Company",
    "LLY": "Eli Lilly and Company",
    "AVGO": "Broadcom Inc.",
    "HD": "The Home Depot Inc.",
    "CVX": "Chevron Corporation",
    "MRK": "Merck & Co. Inc.",
    "ABBV": "AbbVie Inc.",
    "COST": "Costco Wholesale Corporation",
    "ADBE": "Adobe Inc.",
    "PEP": "PepsiCo Inc.",
    "TMO": "Thermo Fisher Scientific Inc.",
    "MCD": "McDonald's Corporation",
    "CSCO": "Cisco Systems Inc.",
    "NFLX": "Netflix Inc.",
    "ABT": "Abbott Laboratories",
    "ACN": "Accenture plc",
    "DHR": "Danaher Corporation",
    "VZ": "Verizon Communications Inc.",
    "WFC": "Wells Fargo & Company",
    "DIS": "The Walt Disney Company",
    "LIN": "Linde plc",
    "NKE": "Nike Inc.",
    "PM": "Philip Morris International Inc.",
    "TXN": "Texas Instruments Incorporated",
    "NEE": "NextEra Energy Inc.",
    "CMCSA": "Comcast Corporation",
    "HON": "Honeywell International Inc.",
    "RTX": "RTX Corporation",
    "UPS": "United Parcel Service Inc.",
    "QCOM": "QUALCOMM Incorporated",
    "AMGN": "Amgen Inc.",
    "BMY": "Bristol-Myers Squibb Company",
    "T": "AT&T Inc.",
    "LOW": "Lowe's Companies Inc.",
    "SPGI": "S&P Global Inc.",
    "INTU": "Intuit Inc.",
    "DE": "Deere & Company",
    "BKNG": "Booking Holdings Inc.",
    "ADP": "Automatic Data Processing Inc.",
    "GE": "General Electric Company",
    "C": "Citigroup Inc.",
    "ELV": "Elevance Health Inc.",
    "TJX": "The TJX Companies Inc.",
    "AXP": "American Express Company",
    "SYK": "Stryker Corporation",
    "ISRG": "Intuitive Surgical Inc.",
    "GILD": "Gilead Sciences Inc.",
    "LMT": "Lockheed Martin Corporation",
    "MDT": "Medtronic plc",
    "ADI": "Analog Devices Inc.",
    "CB": "Chubb Limited",
    "BLK": "BlackRock Inc.",
    "MMC": "Marsh & McLennan Companies Inc.",
    "CI": "Cigna Corporation",
    "ZTS": "Zoetis Inc.",
    "EQIX": "Equinix Inc.",
    "CL": "Colgate-Palmolive Company",
    "ITW": "Illinois Tool Works Inc.",
    "ETN": "Eaton Corporation plc",
    "SHW": "The Sherwin-Williams Company",
    "FIS": "Fidelity National Information Services Inc.",
    "ICE": "Intercontinental Exchange Inc.",
    "APH": "Amphenol Corporation",
    "KLAC": "KLA Corporation",
    "HCA": "HCA Healthcare Inc.",
    "WM": "Waste Management Inc.",
    "CME": "CME Group Inc.",
    "CDNS": "Cadence Design Systems Inc.",
    "PSA": "Public Storage",
    "FAST": "Fastenal Company",
    "AON": "Aon plc",
    "NXPI": "NXP Semiconductors N.V.",
    "MCO": "Moody's Corporation",
    "CTAS": "Cintas Corporation",
    "FTNT": "Fortinet Inc.",
    "IDXX": "IDEXX Laboratories Inc.",
    "ODFL": "Old Dominion Freight Line Inc.",
    "PAYX": "Paychex Inc.",
    "VRSK": "Verisk Analytics Inc.",
    "ANSS": "ANSYS Inc.",
    "DXCM": "Dexcom Inc.",
    "CTSH": "Cognizant Technology Solutions Corporation",
    "TTD": "The Trade Desk Inc.",
    "ROST": "Ross Stores Inc.",
    "PCAR": "PACCAR Inc."
}


def add_top100_stocks():
    """Add top 100 stocks to symbols and universe tables."""
    init_db()
    session = get_session()
    
    try:
        added_symbols = 0
        added_universe = 0
        
        for symbol in TOP_100_STOCKS:
            # Add or update symbol
            symbol_obj = session.query(Symbol).filter_by(symbol=symbol).first()
            if not symbol_obj:
                symbol_obj = Symbol(
                    symbol=symbol,
                    company_name=COMPANY_NAMES.get(symbol, f"{symbol} Corporation"),
                    market_cap=100000000000,  # Placeholder $100B (will be updated by fundamentals provider)
                    is_active=True
                )
                session.add(symbol_obj)
                added_symbols += 1
                logger.info(f"Added symbol: {symbol}")
            else:
                symbol_obj.is_active = True
                logger.debug(f"Symbol already exists: {symbol}")
            
            # Add to universe if not already there
            universe_obj = session.query(Universe).filter_by(symbol=symbol).first()
            if not universe_obj:
                universe_obj = Universe(
                    symbol=symbol,
                    active=True,
                    added_at=datetime.utcnow()
                )
                session.add(universe_obj)
                added_universe += 1
                logger.info(f"Added to universe: {symbol}")
            else:
                universe_obj.active = True
                logger.debug(f"Already in universe: {symbol}")
        
        session.commit()
        logger.info(f"✅ Successfully added {added_symbols} new symbols and {added_universe} to universe")
        logger.info(f"Total stocks in universe: {len(TOP_100_STOCKS)}")
        
        # Verify
        universe_count = session.query(Universe).filter_by(active=True).count()
        logger.info(f"Verified: {universe_count} active stocks in universe")
        
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding stocks: {e}", exc_info=True)
        raise
    finally:
        session.close()


if __name__ == "__main__":
    logger.info("Adding top 100 stocks to universe...")
    add_top100_stocks()
    logger.info("Done!")

