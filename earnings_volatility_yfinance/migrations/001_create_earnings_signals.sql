-- Create earnings_signals table for Supabase
-- Run this migration in your Supabase SQL editor

CREATE TABLE IF NOT EXISTS earnings_signals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    -- Stock and earnings info
    ticker TEXT NOT NULL,
    earnings_date DATE NOT NULL,
    earnings_time TEXT NOT NULL CHECK (earnings_time IN ('BMO', 'AMC')),
    
    -- Timing
    signal_time TIMESTAMPTZ NOT NULL,
    entry_time TIMESTAMPTZ,
    exit_time TIMESTAMPTZ,
    
    -- Status
    status TEXT NOT NULL DEFAULT 'signal' 
        CHECK (status IN ('signal', 'traded', 'closed', 'cancelled')),
    
    -- Option details
    front_month_expiry DATE NOT NULL,
    back_month_expiry DATE NOT NULL,
    front_month_strike DECIMAL(10, 2) NOT NULL,
    back_month_strike DECIMAL(10, 2) NOT NULL,
    option_type TEXT NOT NULL CHECK (option_type IN ('call', 'put')),
    
    -- Metrics
    iv_slope DECIMAL(10, 6),
    iv_rv_ratio DECIMAL(10, 6),
    volume_30d BIGINT,
    
    -- Position details
    position_size INTEGER,
    entry_price DECIMAL(10, 4),
    exit_price DECIMAL(10, 4),
    pnl DECIMAL(10, 2),
    
    -- Rejection reason (if filtered out)
    rejection_reason TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Create indexes for common queries
CREATE INDEX IF NOT EXISTS idx_earnings_signals_ticker ON earnings_signals(ticker);
CREATE INDEX IF NOT EXISTS idx_earnings_signals_earnings_date ON earnings_signals(earnings_date);
CREATE INDEX IF NOT EXISTS idx_earnings_signals_status ON earnings_signals(status);
CREATE INDEX IF NOT EXISTS idx_earnings_signals_signal_time ON earnings_signals(signal_time);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_earnings_signals_updated_at 
    BEFORE UPDATE ON earnings_signals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE earnings_signals IS 'Tracks earnings volatility trading signals and executions';
COMMENT ON COLUMN earnings_signals.earnings_time IS 'BMO = Before Market Open, AMC = After Market Close';
COMMENT ON COLUMN earnings_signals.iv_slope IS 'IV term structure slope (front_month_iv - back_month_iv)';
COMMENT ON COLUMN earnings_signals.iv_rv_ratio IS 'Implied Volatility / Realized Volatility ratio';

