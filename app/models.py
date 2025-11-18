"""Database models for the trading alert system."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    create_engine, Column, Integer, String, Float, Boolean, DateTime, Index,
    ForeignKey
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from app.config import get_config

Base = declarative_base()


class Symbol(Base):
    """Stock symbol metadata."""
    __tablename__ = "symbols"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), unique=True, nullable=False, index=True)
    company_name = Column(String(255), nullable=True)
    cik = Column(String(20), nullable=True)
    market_cap = Column(Integer, nullable=True)  # In dollars
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    candles = relationship("Candle", back_populates="symbol_obj", cascade="all, delete-orphan")
    rsi_values = relationship("RsiValue", back_populates="symbol_obj", cascade="all, delete-orphan")
    universe_entries = relationship("Universe", back_populates="symbol_obj")
    alerts = relationship("Alert", back_populates="symbol_obj")


class Candle(Base):
    """5-minute OHLCV candle data."""
    __tablename__ = "candles"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), ForeignKey("symbols.symbol"), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(Integer, nullable=False)
    interval = Column(String(10), default="5min", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    symbol_obj = relationship("Symbol", back_populates="candles")
    
    __table_args__ = (
        Index("idx_candles_symbol_ts", "symbol", "ts", unique=True),
    )


class Universe(Base):
    """Universe of stocks that pass all filters."""
    __tablename__ = "universe"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), ForeignKey("symbols.symbol"), unique=True, nullable=False, index=True)
    added_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    active = Column(Boolean, default=True, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    symbol_obj = relationship("Symbol", back_populates="universe_entries")


class RsiValue(Base):
    """RSI(14) values computed from candles."""
    __tablename__ = "rsi_values"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), ForeignKey("symbols.symbol"), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    rsi_14 = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    symbol_obj = relationship("Symbol", back_populates="rsi_values")
    
    __table_args__ = (
        Index("idx_rsi_symbol_ts", "symbol", "ts", unique=True),
    )


class Alert(Base):
    """Trading alerts generated from RSI cross-under events."""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(10), ForeignKey("symbols.symbol"), nullable=False, index=True)
    ts = Column(DateTime, nullable=False, index=True)
    rsi_value = Column(Float, nullable=False)
    price = Column(Float, nullable=False)  # Price at alert time
    status = Column(String(20), default="pending", nullable=False)  # pending, triggered, expired
    take_profit_pct = Column(Float, nullable=False)  # 3% default
    max_holding_days = Column(Integer, nullable=False)  # 20 days default
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relationships
    symbol_obj = relationship("Symbol", back_populates="alerts")


def get_engine():
    """Get SQLAlchemy engine."""
    from pathlib import Path
    
    config = get_config()
    
    # Ensure data directory exists for SQLite
    if config.database.url.startswith("sqlite"):
        db_path = config.database.url.replace("sqlite:///", "")
        if db_path != ":memory:":
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
    
    engine = create_engine(config.database.url, echo=config.database.echo)
    return engine


def get_session() -> Session:
    """Get database session."""
    engine = get_engine()
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def init_db():
    """Initialize database tables."""
    engine = get_engine()
    Base.metadata.create_all(engine)

