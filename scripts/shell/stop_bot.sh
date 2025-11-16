#!/bin/bash
# Stop the trading bot

cd "$(dirname "$0")"

if [ -f bot.pid ]; then
    PID=$(cat bot.pid)
    if ps -p $PID > /dev/null 2>&1; then
        kill $PID
        rm bot.pid
        echo "✅ Trading bot stopped (PID: $PID)"
    else
        echo "⚠️  Bot process not found (may have already stopped)"
        rm bot.pid
    fi
else
    echo "⚠️  No bot.pid file found. Bot may not be running."
    echo "   Trying to find and kill any running bot processes..."
    pkill -f "python3 main.py"
    echo "✅ Done"
fi

