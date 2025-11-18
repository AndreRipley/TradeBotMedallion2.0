# Trading Alert System

A production-quality Python trading alert system that implements RSI-based oversold detection. This system builds a filtered universe of stocks, calculates RSI(14) using Wilder smoothing, and emits alerts when RSI crosses below a threshold.

## Features

- **Universe Building**: Filters stocks by market cap (≥$5B) and performance thresholds (3-month, 6-month, YTD returns)
- **RSI Calculation**: Implements RSI(14) with Wilder smoothing method on 5-minute candles
- **Real-time Monitoring**: Updates candles and RSI every 5 minutes during market hours
- **Alert System**: Detects RSI cross-under events and stores alerts with trade rule metadata
- **Pluggable Data Providers**: Abstract interfaces for easy swapping of data sources
- **Production-ready**: Type hints, logging, configuration management, and unit tests

## Architecture

```
app/
├── config.py              # Configuration management
├── models.py              # SQLAlchemy database models
├── data_providers.py      # Abstract data provider interfaces and implementations
├── universe.py            # Universe building logic
├── indicators.py          # RSI calculation with Wilder smoothing
├── alerts.py              # Alert detection and storage
├── realtime.py            # Real-time monitoring loop
├── universe/
│   └── build.py          # CLI: Build universe
├── indicators/
│   └── compute_rsi.py    # CLI: Compute RSI
└── realtime/
    └── monitor.py         # CLI: Run real-time monitor
```

## Installation

### Prerequisites

- Python 3.11+
- pip

### Setup

1. **Clone or navigate to the project directory**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

Or install with pytest:
```bash
pip install -e ".[test]"
```

3. **Configure environment variables** (optional):
```bash
export ALPHA_VANTAGE_API_KEY="your_api_key_here"
export DATABASE_URL="sqlite:///./data/trading_alerts.db"
export RSI_THRESHOLD=28.0
export MIN_MARKET_CAP=5000000000
```

Or edit `config.yaml` directly.

## Configuration

The system uses `config.yaml` for configuration, with environment variable overrides. Key settings:

- **Universe filters**: Market cap minimum, performance thresholds
- **RSI settings**: Period (14), cross-under threshold (28.0)
- **Alert rules**: Take profit percentage (3%), max holding days (20)
- **Scheduler**: Update interval (5 minutes), market hours

See `config.yaml` for all options.

## Usage

### 1. Build the Universe

Builds the trading universe by:
1. Fetching all U.S.-listed equities
2. Filtering by market cap (≥$5B)
3. Downloading 13 months of 5-minute candles
4. Computing performance metrics
5. Applying performance thresholds

```bash
python -m app.universe.build
```

This will:
- Store symbols in the `symbols` table
- Store candles in the `candles` table
- Store the final universe in the `universe` table

### 2. Compute RSI

Compute RSI(14) Wilder for symbols:

**Single symbol**:
```bash
python -m app.indicators.compute_rsi --symbol AAPL
```

**All symbols in universe**:
```bash
python -m app.indicators.compute_rsi --all
```

RSI values are stored in the `rsi_values` table.

### 3. Run Real-time Monitor

Start the real-time monitoring loop:

```bash
python -m app.realtime.monitor
```

This will:
- Update candles every 5 minutes (during market hours)
- Update RSI values incrementally
- Detect RSI cross-under events (RSI < 28)
- Create and send alerts

Press `Ctrl+C` to stop.

## Database Schema

The system uses SQLite by default (configurable). Tables:

- **symbols**: Symbol metadata (symbol, company_name, cik, market_cap)
- **candles**: 5-minute OHLCV candle data
- **universe**: Final filtered universe of stocks
- **rsi_values**: RSI(14) values computed from candles
- **alerts**: Trading alerts with trade rule metadata

## Strategy Details

### Universe Construction

1. Start with all U.S.-listed equities
2. Filter by market cap: `market_cap >= $5B`
3. Download 13 months of 5-minute candles
4. Compute daily closes and calculate:
   - 3-month percent gain
   - 6-month percent gain
   - YTD percent gain
5. Filter by performance thresholds (configurable):
   - 3-month return ≥ 80%
   - 6-month return ≥ 90%
   - YTD return ≥ 100%

### RSI Calculation

- Uses **RSI(14)** with **Wilder smoothing**
- Computed on 5-minute candles
- Formula:
  - RS = Average Gain / Average Loss (Wilder smoothed)
  - RSI = 100 - (100 / (1 + RS))

### Alert Detection

Alerts are triggered when:
- Previous candle RSI ≥ 28
- Current candle RSI < 28

### Trade Rules (Metadata Only)

Each alert includes suggested trade rules (not simulated):
- **Entry**: Buy next 5-minute candle after alert
- **Take Profit**: +3% from entry
- **Max Holding**: 20 calendar days

These are stored as metadata on alerts for use by external systems.

## Data Providers

The system uses pluggable data providers:

- **SymbolUniverseProvider**: `SecApiUniverseProvider` (mock implementation)
- **FundamentalsProvider**: `AlphaVantageFundamentalsProvider`
- **IntradayPriceProvider**: `MockIntradayPriceProvider` or `AlphaVantageIntradayProvider`

To use real data:
1. Set `ALPHA_VANTAGE_API_KEY` environment variable
2. Implement real SEC API provider (or use ticker list service)
3. Consider premium data providers for 13 months of 5-min data

## Testing

Run unit tests:

```bash
pytest tests/
```

Tests cover:
- RSI Wilder smoothing calculation
- Universe filtering logic
- RSI cross-under detection

## Logging

The system uses Python's `logging` module with structured output:
- INFO: Major operations (universe build, RSI updates, alerts)
- DEBUG: Detailed step-by-step operations
- ERROR: Errors and exceptions

## Limitations & Notes

1. **Mock Data Providers**: The SEC API provider is mocked. Implement real API calls for production.
2. **Alpha Vantage Limits**: Free tier has rate limits and limited historical data. Consider premium providers for 13 months of 5-min data.
3. **Market Hours**: Simple UTC-based market hours check. Implement proper timezone handling for production.
4. **No Backtesting**: This system only generates alerts. No PnL simulation or backtesting is included.

## Development

### Project Structure

- `app/`: Main application code
- `tests/`: Unit tests
- `config.yaml`: Configuration file
- `requirements.txt`: Python dependencies
- `pyproject.toml`: Project metadata

### Adding New Data Providers

1. Implement the abstract interface (`SymbolUniverseProvider`, `FundamentalsProvider`, or `IntradayPriceProvider`)
2. Pass the provider instance to the builder/monitor
3. See `app/data_providers.py` for examples

### Extending Alert Notifications

Modify `AlertService.send_alert_notification()` to add:
- Email notifications
- Slack webhooks
- Custom webhook endpoints

## License

[Your License Here]

## Contributing

[Contributing Guidelines]

