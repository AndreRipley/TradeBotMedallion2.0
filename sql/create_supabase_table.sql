-- Create stock_ohlc_30min table for historical 30-minute OHLC data
-- Run this in Supabase SQL Editor

CREATE TABLE IF NOT EXISTS stock_ohlc_30min (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    datetime TIMESTAMPTZ NOT NULL,
    date DATE NOT NULL,
    time TIME NOT NULL,
    open DECIMAL(10, 2) NOT NULL,
    high DECIMAL(10, 2) NOT NULL,
    low DECIMAL(10, 2) NOT NULL,
    close DECIMAL(10, 2) NOT NULL,
    volume BIGINT NOT NULL,
    trade_count BIGINT,
    vwap DECIMAL(10, 2),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(symbol, datetime)
);

-- Create indexes for faster queries
CREATE INDEX IF NOT EXISTS idx_stock_ohlc_30min_symbol ON stock_ohlc_30min(symbol);
CREATE INDEX IF NOT EXISTS idx_stock_ohlc_30min_datetime ON stock_ohlc_30min(datetime DESC);
CREATE INDEX IF NOT EXISTS idx_stock_ohlc_30min_symbol_datetime ON stock_ohlc_30min(symbol, datetime DESC);
CREATE INDEX IF NOT EXISTS idx_stock_ohlc_30min_date ON stock_ohlc_30min(date);

-- Enable Row Level Security (RLS)
ALTER TABLE stock_ohlc_30min ENABLE ROW LEVEL SECURITY;

-- Create policy to allow inserts
CREATE POLICY "Allow inserts for stock_ohlc_30min" ON stock_ohlc_30min
    FOR INSERT
    WITH CHECK (true);

-- Create policy to allow reads
CREATE POLICY "Allow reads for stock_ohlc_30min" ON stock_ohlc_30min
    FOR SELECT
    USING (true);

