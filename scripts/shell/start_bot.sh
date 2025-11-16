#!/bin/bash
# Run the trading bot in the background

cd "$(dirname "$0")"

# Run bot in background, redirect output to log file
nohup python3 main.py > bot_output.log 2>&1 &

# Save the process ID
echo $! > bot.pid

echo "✅ Trading bot started in background!"
echo "📋 Process ID: $(cat bot.pid)"
echo "📝 Logs: bot_output.log and trading_bot.log"
echo ""
echo "To stop the bot, run: ./stop_bot.sh"
echo "To check status, run: ./check_bot.sh"

