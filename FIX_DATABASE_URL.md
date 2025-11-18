# Fix DATABASE_URL in Cloud Run

## ⚠️ Current Issue

The `DATABASE_URL` environment variable in Cloud Run is set incorrectly:
```
DATABASE_URL=https://rpugqgjacxfbfeqguqbs.supabase.co  ❌ WRONG
```

This is the Supabase **API URL**, not the **PostgreSQL database connection string**.

## ✅ Fix Steps

### Step 1: Get Your Database Password

1. Go to: https://supabase.com/dashboard
2. Select your project
3. Go to **Settings** → **Database**
4. Under **Database password**, click **Reset database password** (if needed)
5. **Copy and save the password** securely

### Step 2: Get Connection String

Run locally:
```bash
export SUPABASE_URL="https://rpugqgjacxfbfeqguqbs.supabase.co"
export SUPABASE_DB_PASSWORD="your-password-here"
python3 scripts/get_supabase_connection.py
```

This will test connections and give you the working connection string.

### Step 3: Update Cloud Run Environment Variable

1. Go to: https://console.cloud.google.com/run
2. Click on `trading-bot` service
3. Click **Edit & Deploy New Revision**
4. Go to **Variables & Secrets** tab
5. Find `DATABASE_URL` and click **Edit**
6. Replace with your PostgreSQL connection string:
   ```
   postgresql://postgres.rpugqgjacxfbfeqguqbs:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
7. Click **Deploy**

### Alternative: Use Supabase Env Vars

Instead of `DATABASE_URL`, you can set:
- `SUPABASE_URL=https://rpugqgjacxfbfeqguqbs.supabase.co`
- `SUPABASE_DB_PASSWORD=your-password`

The system will automatically construct the connection string.

## Verify Fix

After updating, check logs:
```bash
gcloud run services logs read trading-bot --region=us-central1 --limit=20
```

You should see:
```
Database: postgresql://postgres.rpugqgjacxfbfeqguqbs:***@aws-0-us-east-1.pooler.supabase.com:6543/postgres
```

Instead of:
```
Database: https://rpugqgjacxfbfeqguqbs.supabase.co  ❌
```

## Current Status

✅ Bot is **running** (service is up)
⚠️ Database connection is **broken** (wrong URL format)
✅ Health check is **working**
⚠️ No data updates (can't connect to database)

After fixing `DATABASE_URL`, the bot will be able to:
- Connect to Supabase
- Build universe
- Compute RSI
- Generate alerts

