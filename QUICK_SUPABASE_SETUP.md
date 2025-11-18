# Quick Supabase Setup Guide

## ✅ Tables Created

All 5 tables have been created in your Supabase database:
- `symbols` - Stock metadata
- `candles` - 5-minute OHLCV data
- `universe` - Filtered stock universe
- `rsi_values` - RSI(14) calculations
- `alerts` - Trading alerts

## 🔑 Get Database Connection String

### Option 1: Use Helper Script (Easiest)

```bash
# Set your Supabase credentials
export SUPABASE_URL="https://rpugqgjacxfbfeqguqbs.supabase.co"
export SUPABASE_DB_PASSWORD="your-database-password"

# Run helper script
python3 scripts/get_supabase_connection.py
```

This will:
- Test different connection methods
- Show you the working connection string
- Give you the exact command to set `DATABASE_URL`

### Option 2: Get from Supabase Dashboard

1. Go to: https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **Database**
4. Under **Connection string**, select:
   - **URI** (for direct connection)
   - **Connection pooling** (recommended for Cloud Run)
5. Copy the connection string
6. Replace `[YOUR-PASSWORD]` with your actual database password

**Example format:**
```
postgresql://postgres.rpugqgjacxfbfeqguqbs:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

## 🚀 Set Environment Variable

### For Local Development

```bash
export DATABASE_URL="postgresql://postgres.rpugqgjacxfbfeqguqbs:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
```

### For Cloud Run

1. Go to Cloud Run console
2. Click on `trading-bot` service
3. Click **Edit & Deploy New Revision**
4. Go to **Variables & Secrets** tab
5. Add environment variable:
   - **Name**: `DATABASE_URL`
   - **Value**: Your Supabase PostgreSQL connection string

## ✅ Test Connection

```bash
# Set DATABASE_URL first
export DATABASE_URL="your-connection-string"

# Test connection
python3 -c "from app.models import get_engine, init_db; init_db(); print('✅ Connected to Supabase!')"
```

## 📝 Database Password

If you don't have your database password:

1. Go to Supabase Dashboard → Settings → Database
2. Under **Database password**, click **Reset database password**
3. **Save the password securely** (you won't see it again!)
4. Use it in your connection string

## 🔄 Next Steps

1. ✅ Tables created
2. ✅ Get connection string
3. ✅ Set `DATABASE_URL` environment variable
4. ✅ Test connection
5. ✅ Deploy to Cloud Run with env var
6. ✅ Initialize: `python3 -m app.universe.build`

## 🎯 Quick Command Reference

```bash
# Get connection string
python3 scripts/get_supabase_connection.py

# Test connection
python3 -c "from app.models import get_engine; engine = get_engine(); print('✅ Connected')"

# Initialize database
python3 -m app.universe.build
```

