#!/bin/bash
# Quick Deployment Script for Railway
# This helps you deploy your trading bot to Railway (cloud hosting)

echo "=========================================="
echo "TRADING BOT - CLOUD DEPLOYMENT SETUP"
echo "=========================================="
echo ""
echo "This script will help you deploy to Railway (easiest option)"
echo "Cost: FREE tier available, then ~\$5-10/month"
echo ""
echo "Steps:"
echo "1. Push code to GitHub (if not already)"
echo "2. Sign up at https://railway.app/"
echo "3. Connect GitHub repo"
echo "4. Add environment variables"
echo "5. Deploy!"
echo ""
read -p "Press Enter to continue..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo ""
    echo "⚠️  Git not initialized. Initializing..."
    git init
    echo "✅ Git initialized"
fi

# Check if Procfile exists
if [ ! -f "Procfile" ]; then
    echo "⚠️  Procfile not found. Creating..."
    echo "worker: python3 main.py" > Procfile
    echo "✅ Procfile created"
fi

# Check if runtime.txt exists
if [ ! -f "runtime.txt" ]; then
    echo "⚠️  runtime.txt not found. Creating..."
    echo "python-3.11" > runtime.txt
    echo "✅ runtime.txt created"
fi

echo ""
echo "=========================================="
echo "NEXT STEPS:"
echo "=========================================="
echo ""
echo "1. Push to GitHub:"
echo "   git add ."
echo "   git commit -m 'Prepare for deployment'"
echo "   git push origin main"
echo ""
echo "2. Go to https://railway.app/"
echo "   - Sign up/login"
echo "   - Click 'New Project'"
echo "   - Select 'Deploy from GitHub repo'"
echo "   - Choose your TradeBot repository"
echo ""
echo "3. Add Environment Variables in Railway:"
echo "   - ALPACA_API_KEY"
echo "   - ALPACA_SECRET_KEY"
echo "   - ALPACA_BASE_URL=https://paper-api.alpaca.markets"
echo "   - STOCKS=AAPL,MSFT,GOOGL,AMZN,TSLA"
echo "   - POSITION_SIZE=1000.0"
echo "   - TIMEZONE=America/New_York"
echo "   - LOG_LEVEL=INFO"
echo ""
echo "4. Deploy!"
echo "   Railway will automatically deploy your bot"
echo ""
echo "5. Monitor:"
echo "   - View logs in Railway dashboard"
echo "   - Bot will run 24/7 automatically"
echo ""
echo "=========================================="
echo "ALTERNATIVE: DigitalOcean Setup"
echo "=========================================="
echo ""
echo "If you prefer DigitalOcean (\$6/month):"
echo "1. See DEPLOYMENT.md for detailed instructions"
echo "2. Or run: ./setup_digitalocean.sh"
echo ""
echo "✅ Setup complete! Follow the steps above to deploy."

