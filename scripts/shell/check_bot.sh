#!/bin/bash
# Check if the trading bot is running

cd "$(dirname "$0")"

if [ -f bot.pid ]; then
    PID=$(cat bot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Trading bot is RUNNING (PID: $PID)"
        echo ""
        echo "Recent log output:"
        echo "=================="
        tail -n 20 trading_bot.log 2>/dev/null || echo "No log file yet"
    else
        echo "❌ Trading bot is NOT running (PID file exists but process not found)"
        rm bot.pid
    fi
else
    echo "❌ Trading bot is NOT running (no PID file)"
fi

