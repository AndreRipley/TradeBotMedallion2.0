# Supabase Database Setup for Trading Alert System

## Overview

The Trading Alert System now uses **Supabase PostgreSQL** as its database instead of SQLite. This provides:
- ✅ Persistent storage (data survives container restarts)
- ✅ Better performance for large datasets
- ✅ Multi-instance support
- ✅ Built-in backups and monitoring

## Database Tables Created

The following tables have been created in your Supabase database:

1. **`symbols`** - Stock symbol metadata
2. **`candles`** - 5-minute OHLCV candle data
3. **`universe`** - Filtered universe of stocks
4. **`rsi_values`** - Computed RSI(14) values
5. **`alerts`** - Trading alerts from RSI cross-under events

## Connection Setup

### Option 1: Direct Connection String (Recommended)

Set the `DATABASE_URL` environment variable with your Supabase PostgreSQL connection string:

```bash
export DATABASE_URL="postgresql://postgres.[PROJECT_REF]:[PASSWORD]@aws-0-[REGION].pooler.supabase.com:6543/postgres"
```

**To get your connection string:**
1. Go to your Supabase project dashboard
2. Click "Settings" → "Database"
3. Under "Connection string", select "URI" or "Connection pooling"
4. Copy the connection string
5. Replace `[YOUR-PASSWORD]` with your database password

**Example:**
```
postgresql://postgres.rpugqgjacxfbfeqguqbs:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

### Option 2: Environment Variables

Set these environment variables and the system will construct the connection string:

```bash
export SUPABASE_URL="https://rpugqgjacxfbfeqguqbs.supabase.co"
export SUPABASE_DB_PASSWORD="your-database-password"
export SUPABASE_DB_HOST="aws-0-us-east-1.pooler.supabase.com"  # Optional
```

## For Cloud Run Deployment

Set the environment variable in Cloud Run console:

1. Go to Cloud Run → `trading-bot` → Edit & Deploy New Revision
2. Go to "Variables & Secrets" tab
3. Add environment variable:
   - **Name**: `DATABASE_URL`
   - **Value**: Your Supabase PostgreSQL connection string

Or use the Supabase env vars:
- `SUPABASE_URL`
- `SUPABASE_DB_PASSWORD`
- `SUPABASE_DB_HOST` (optional)

## Verify Connection

Test the connection:

```bash
# Set environment variable
export DATABASE_URL="your-connection-string"

# Test connection
python3 -c "from app.models import get_engine, init_db; init_db(); print('✅ Connected to Supabase')"
```

## Database Password

**Important**: You need your Supabase database password. If you don't have it:

1. Go to Supabase Dashboard → Settings → Database
2. Under "Database password", click "Reset database password"
3. Save the new password securely
4. Use it in your connection string

## Connection Pooling

Supabase provides connection pooling for better performance. Use the pooler URL:
- Port `6543` for connection pooling (recommended)
- Port `5432` for direct connection

The system defaults to using the pooler (`:6543`).

## Security Notes

- **Never commit passwords** to version control
- Use environment variables or Cloud Run secrets
- Row Level Security (RLS) is enabled on all tables
- Adjust RLS policies in Supabase dashboard if needed

## Migration from SQLite

If you have existing SQLite data:

1. Export data from SQLite:
   ```bash
   sqlite3 data/trading_alerts.db .dump > backup.sql
   ```

2. Convert and import to Supabase (manual process or use migration tools)

3. Or start fresh - the system will rebuild the universe automatically

## Troubleshooting

### Connection Errors

- Verify your password is correct
- Check that your IP is allowed (if using IP restrictions)
- Ensure you're using the correct port (6543 for pooling, 5432 for direct)

### Table Not Found

The tables are created via migration. If tables don't exist:
```bash
python3 -c "from app.models import init_db; init_db()"
```

### Performance Issues

- Use connection pooling (port 6543)
- Add indexes (already created by migration)
- Monitor query performance in Supabase dashboard

## Next Steps

1. ✅ Tables created in Supabase
2. ✅ Set `DATABASE_URL` environment variable
3. ✅ Deploy to Cloud Run with env var set
4. ✅ Initialize universe: `python3 -m app.universe.build`
5. ✅ Compute RSI: `python3 -m app.indicators.compute_rsi --all`

