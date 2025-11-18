-- SQL script to add missing stocks to Supabase universe table
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/project/rpugqgjacxfbfeqguqbs/sql

-- First, check current count
SELECT COUNT(*) as current_count FROM universe WHERE active = true;

-- List of all 100 stocks
WITH all_stocks AS (
    SELECT unnest(ARRAY[
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'V', 'UNH',
        'XOM', 'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX',
        'MRK', 'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT',
        'ACN', 'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE',
        'CMCSA', 'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI',
        'INTU', 'DE', 'BKNG', 'ADP', 'GE', 'C', 'ELV', 'TJX', 'AXP', 'SYK',
        'ISRG', 'GILD', 'LMT', 'MDT', 'ADI', 'CB', 'BLK', 'MMC', 'CI', 'ZTS',
        'EQIX', 'CL', 'ITW', 'ETN', 'SHW', 'FIS', 'ICE', 'APH', 'KLAC', 'HCA',
        'WM', 'CME', 'CDNS', 'PSA', 'FAST', 'AON', 'NXPI', 'MCO', 'CTAS', 'FTNT',
        'IDXX', 'ODFL', 'PAYX', 'VRSK', 'ANSS', 'DXCM', 'CTSH', 'TTD', 'ROST', 'PCAR'
    ]) AS symbol
),
existing_stocks AS (
    SELECT symbol FROM universe WHERE active = true
),
missing_stocks AS (
    SELECT a.symbol 
    FROM all_stocks a 
    LEFT JOIN existing_stocks e ON a.symbol = e.symbol 
    WHERE e.symbol IS NULL
)
SELECT symbol FROM missing_stocks ORDER BY symbol;

-- Step 1: Add missing symbols to symbols table (if they don't exist)
INSERT INTO symbols (symbol, company_name, market_cap, is_active, created_at, updated_at)
SELECT 
    symbol,
    CASE symbol
        WHEN 'AAPL' THEN 'Apple Inc.'
        WHEN 'MSFT' THEN 'Microsoft Corporation'
        WHEN 'GOOGL' THEN 'Alphabet Inc.'
        WHEN 'AMZN' THEN 'Amazon.com Inc.'
        WHEN 'NVDA' THEN 'NVIDIA Corporation'
        WHEN 'META' THEN 'Meta Platforms Inc.'
        WHEN 'TSLA' THEN 'Tesla Inc.'
        WHEN 'BRK.B' THEN 'Berkshire Hathaway Inc.'
        WHEN 'V' THEN 'Visa Inc.'
        WHEN 'UNH' THEN 'UnitedHealth Group Inc.'
        WHEN 'XOM' THEN 'Exxon Mobil Corporation'
        WHEN 'JNJ' THEN 'Johnson & Johnson'
        WHEN 'JPM' THEN 'JPMorgan Chase & Co.'
        WHEN 'WMT' THEN 'Walmart Inc.'
        WHEN 'MA' THEN 'Mastercard Incorporated'
        WHEN 'PG' THEN 'The Procter & Gamble Company'
        WHEN 'LLY' THEN 'Eli Lilly and Company'
        WHEN 'AVGO' THEN 'Broadcom Inc.'
        WHEN 'HD' THEN 'The Home Depot Inc.'
        WHEN 'CVX' THEN 'Chevron Corporation'
        WHEN 'MRK' THEN 'Merck & Co. Inc.'
        WHEN 'ABBV' THEN 'AbbVie Inc.'
        WHEN 'COST' THEN 'Costco Wholesale Corporation'
        WHEN 'ADBE' THEN 'Adobe Inc.'
        WHEN 'PEP' THEN 'PepsiCo Inc.'
        WHEN 'TMO' THEN 'Thermo Fisher Scientific Inc.'
        WHEN 'MCD' THEN 'McDonald''s Corporation'
        WHEN 'CSCO' THEN 'Cisco Systems Inc.'
        WHEN 'NFLX' THEN 'Netflix Inc.'
        WHEN 'ABT' THEN 'Abbott Laboratories'
        WHEN 'ACN' THEN 'Accenture plc'
        WHEN 'DHR' THEN 'Danaher Corporation'
        WHEN 'VZ' THEN 'Verizon Communications Inc.'
        WHEN 'WFC' THEN 'Wells Fargo & Company'
        WHEN 'DIS' THEN 'The Walt Disney Company'
        WHEN 'LIN' THEN 'Linde plc'
        WHEN 'NKE' THEN 'Nike Inc.'
        WHEN 'PM' THEN 'Philip Morris International Inc.'
        WHEN 'TXN' THEN 'Texas Instruments Incorporated'
        WHEN 'NEE' THEN 'NextEra Energy Inc.'
        WHEN 'CMCSA' THEN 'Comcast Corporation'
        WHEN 'HON' THEN 'Honeywell International Inc.'
        WHEN 'RTX' THEN 'RTX Corporation'
        WHEN 'UPS' THEN 'United Parcel Service Inc.'
        WHEN 'QCOM' THEN 'QUALCOMM Incorporated'
        WHEN 'AMGN' THEN 'Amgen Inc.'
        WHEN 'BMY' THEN 'Bristol-Myers Squibb Company'
        WHEN 'T' THEN 'AT&T Inc.'
        WHEN 'LOW' THEN 'Lowe''s Companies Inc.'
        WHEN 'SPGI' THEN 'S&P Global Inc.'
        WHEN 'INTU' THEN 'Intuit Inc.'
        WHEN 'DE' THEN 'Deere & Company'
        WHEN 'BKNG' THEN 'Booking Holdings Inc.'
        WHEN 'ADP' THEN 'Automatic Data Processing Inc.'
        WHEN 'GE' THEN 'General Electric Company'
        WHEN 'C' THEN 'Citigroup Inc.'
        WHEN 'ELV' THEN 'Elevance Health Inc.'
        WHEN 'TJX' THEN 'The TJX Companies Inc.'
        WHEN 'AXP' THEN 'American Express Company'
        WHEN 'SYK' THEN 'Stryker Corporation'
        WHEN 'ISRG' THEN 'Intuitive Surgical Inc.'
        WHEN 'GILD' THEN 'Gilead Sciences Inc.'
        WHEN 'LMT' THEN 'Lockheed Martin Corporation'
        WHEN 'MDT' THEN 'Medtronic plc'
        WHEN 'ADI' THEN 'Analog Devices Inc.'
        WHEN 'CB' THEN 'Chubb Limited'
        WHEN 'BLK' THEN 'BlackRock Inc.'
        WHEN 'MMC' THEN 'Marsh & McLennan Companies Inc.'
        WHEN 'CI' THEN 'Cigna Corporation'
        WHEN 'ZTS' THEN 'Zoetis Inc.'
        WHEN 'EQIX' THEN 'Equinix Inc.'
        WHEN 'CL' THEN 'Colgate-Palmolive Company'
        WHEN 'ITW' THEN 'Illinois Tool Works Inc.'
        WHEN 'ETN' THEN 'Eaton Corporation plc'
        WHEN 'SHW' THEN 'The Sherwin-Williams Company'
        WHEN 'FIS' THEN 'Fidelity National Information Services Inc.'
        WHEN 'ICE' THEN 'Intercontinental Exchange Inc.'
        WHEN 'APH' THEN 'Amphenol Corporation'
        WHEN 'KLAC' THEN 'KLA Corporation'
        WHEN 'HCA' THEN 'HCA Healthcare Inc.'
        WHEN 'WM' THEN 'Waste Management Inc.'
        WHEN 'CME' THEN 'CME Group Inc.'
        WHEN 'CDNS' THEN 'Cadence Design Systems Inc.'
        WHEN 'PSA' THEN 'Public Storage'
        WHEN 'FAST' THEN 'Fastenal Company'
        WHEN 'AON' THEN 'Aon plc'
        WHEN 'NXPI' THEN 'NXP Semiconductors N.V.'
        WHEN 'MCO' THEN 'Moody''s Corporation'
        WHEN 'CTAS' THEN 'Cintas Corporation'
        WHEN 'FTNT' THEN 'Fortinet Inc.'
        WHEN 'IDXX' THEN 'IDEXX Laboratories Inc.'
        WHEN 'ODFL' THEN 'Old Dominion Freight Line Inc.'
        WHEN 'PAYX' THEN 'Paychex Inc.'
        WHEN 'VRSK' THEN 'Verisk Analytics Inc.'
        WHEN 'ANSS' THEN 'ANSYS Inc.'
        WHEN 'DXCM' THEN 'Dexcom Inc.'
        WHEN 'CTSH' THEN 'Cognizant Technology Solutions Corporation'
        WHEN 'TTD' THEN 'The Trade Desk Inc.'
        WHEN 'ROST' THEN 'Ross Stores Inc.'
        WHEN 'PCAR' THEN 'PACCAR Inc.'
        ELSE symbol || ' Corporation'
    END AS company_name,
    100000000000 AS market_cap,
    true AS is_active,
    NOW() AS created_at,
    NOW() AS updated_at
FROM (
    SELECT unnest(ARRAY[
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'V', 'UNH',
        'XOM', 'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX',
        'MRK', 'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT',
        'ACN', 'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE',
        'CMCSA', 'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI',
        'INTU', 'DE', 'BKNG', 'ADP', 'GE', 'C', 'ELV', 'TJX', 'AXP', 'SYK',
        'ISRG', 'GILD', 'LMT', 'MDT', 'ADI', 'CB', 'BLK', 'MMC', 'CI', 'ZTS',
        'EQIX', 'CL', 'ITW', 'ETN', 'SHW', 'FIS', 'ICE', 'APH', 'KLAC', 'HCA',
        'WM', 'CME', 'CDNS', 'PSA', 'FAST', 'AON', 'NXPI', 'MCO', 'CTAS', 'FTNT',
        'IDXX', 'ODFL', 'PAYX', 'VRSK', 'ANSS', 'DXCM', 'CTSH', 'TTD', 'ROST', 'PCAR'
    ]) AS symbol
) all_stocks
WHERE NOT EXISTS (
    SELECT 1 FROM symbols WHERE symbols.symbol = all_stocks.symbol
)
ON CONFLICT (symbol) DO UPDATE SET 
    is_active = true,
    updated_at = NOW();

-- Step 2: Add missing stocks to universe table
INSERT INTO universe (symbol, added_at, active, updated_at)
SELECT 
    symbol,
    NOW() AS added_at,
    true AS active,
    NOW() AS updated_at
FROM (
    SELECT unnest(ARRAY[
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'V', 'UNH',
        'XOM', 'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX',
        'MRK', 'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT',
        'ACN', 'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE',
        'CMCSA', 'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI',
        'INTU', 'DE', 'BKNG', 'ADP', 'GE', 'C', 'ELV', 'TJX', 'AXP', 'SYK',
        'ISRG', 'GILD', 'LMT', 'MDT', 'ADI', 'CB', 'BLK', 'MMC', 'CI', 'ZTS',
        'EQIX', 'CL', 'ITW', 'ETN', 'SHW', 'FIS', 'ICE', 'APH', 'KLAC', 'HCA',
        'WM', 'CME', 'CDNS', 'PSA', 'FAST', 'AON', 'NXPI', 'MCO', 'CTAS', 'FTNT',
        'IDXX', 'ODFL', 'PAYX', 'VRSK', 'ANSS', 'DXCM', 'CTSH', 'TTD', 'ROST', 'PCAR'
    ]) AS symbol
) all_stocks
WHERE NOT EXISTS (
    SELECT 1 FROM universe WHERE universe.symbol = all_stocks.symbol AND universe.active = true
)
ON CONFLICT (symbol) DO UPDATE SET 
    active = true,
    updated_at = NOW();

-- Step 3: Verify final count
SELECT COUNT(*) as total_stocks FROM universe WHERE active = true;
-- Should return 100

-- Step 4: List all stocks in universe
SELECT symbol, added_at, active 
FROM universe 
WHERE active = true 
ORDER BY symbol;

