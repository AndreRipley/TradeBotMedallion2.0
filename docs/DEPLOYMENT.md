# Cloud Deployment Guide

## Options for Running Bot 24/7

### Option 1: Railway (Easiest - Recommended) ⭐

**Cost:** Free tier available, then ~$5-10/month

**Steps:**
1. Sign up at https://railway.app/
2. Connect your GitHub repository
3. Add environment variables (.env settings)
4. Deploy - Railway handles everything automatically

**Pros:**
- Very easy setup
- Free tier available
- Automatic deployments
- Built-in logging

**Setup:**
```bash
# Install Railway CLI
npm i -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

---

### Option 2: Render (Free Tier Available)

**Cost:** Free tier available (with limitations), then $7/month

**Steps:**
1. Sign up at https://render.com/
2. Create new "Web Service"
3. Connect GitHub repo
4. Set environment variables
5. Deploy

**Pros:**
- Free tier available
- Easy setup
- Automatic deployments

**Setup:**
- Use the provided `render.yaml` or configure via web interface
- Set environment variables in dashboard
- Deploy from GitHub

---

### Option 3: DigitalOcean Droplet

**Cost:** $6/month (basic droplet)

**Steps:**
1. Create account at https://www.digitalocean.com/
2. Create a droplet (Ubuntu 22.04)
3. SSH into server
4. Install Python and dependencies
5. Clone repository
6. Set up systemd service

**Setup Script:**
```bash
# On your local machine, create deployment script
# Then SSH into server and run it
```

---

### Option 4: AWS EC2 (Most Flexible)

**Cost:** Free tier available (t2.micro), then ~$5-10/month

**Steps:**
1. Create AWS account
2. Launch EC2 instance (t2.micro for free tier)
3. SSH into instance
4. Install dependencies
5. Set up systemd service

**Pros:**
- Very flexible
- Free tier available
- Scalable

---

### Option 5: Google Cloud Run (Serverless)

**Cost:** Free tier available, pay per use

**Steps:**
1. Create GCP account
2. Set up Cloud Run
3. Deploy containerized bot
4. Set to run continuously

---

## Quick Setup: Railway (Recommended)

### Step 1: Prepare for Deployment

Create these files:

**Procfile** (for Railway/Render):
```
worker: python3 main.py
```

**runtime.txt** (optional):
```
python-3.11
```

### Step 2: Environment Variables

Make sure your `.env` file has all required variables:
- ALPACA_API_KEY
- ALPACA_SECRET_KEY
- ALPACA_BASE_URL
- STOCKS
- POSITION_SIZE
- etc.

### Step 3: Deploy

**Railway:**
1. Go to https://railway.app/
2. Click "New Project"
3. "Deploy from GitHub repo"
4. Select your TradeBot repository
5. Add environment variables
6. Deploy!

**Render:**
1. Go to https://render.com/
2. "New +" → "Web Service"
3. Connect GitHub repo
4. Set environment variables
5. Deploy!

---

## Manual Server Setup (DigitalOcean/AWS)

### Step 1: Create Server

**DigitalOcean:**
- Create droplet: Ubuntu 22.04, $6/month
- Get IP address

**AWS EC2:**
- Launch instance: t2.micro (free tier)
- Ubuntu 22.04
- Get public IP

### Step 2: SSH into Server

```bash
ssh root@YOUR_SERVER_IP
# or
ssh ubuntu@YOUR_SERVER_IP
```

### Step 3: Install Dependencies

```bash
# Update system
apt update && apt upgrade -y

# Install Python and pip
apt install python3 python3-pip git -y

# Install Python dependencies
pip3 install -r requirements.txt
```

### Step 4: Clone Repository

```bash
# Option 1: Clone from GitHub
git clone https://github.com/AndreRipley/TradeBotRedDays.git
cd TradeBotRedDays

# Option 2: Upload files via SCP
# From your local machine:
# scp -r /Users/andreripley/Desktop/TradeBot root@YOUR_SERVER_IP:/opt/trading-bot
```

### Step 5: Set Up Environment Variables

```bash
cd /opt/trading-bot  # or wherever you cloned it
nano .env

# Add your API keys and configuration
# Save with Ctrl+X, then Y, then Enter
```

### Step 6: Create Systemd Service

```bash
sudo nano /etc/systemd/system/trading-bot.service
```

Add this content:
```ini
[Unit]
Description=Trading Bot Service
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/trading-bot
Environment="PATH=/usr/bin:/usr/local/bin"
ExecStart=/usr/bin/python3 /opt/trading-bot/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 7: Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (starts on boot)
sudo systemctl enable trading-bot

# Start service
sudo systemctl start trading-bot

# Check status
sudo systemctl status trading-bot

# View logs
sudo journalctl -u trading-bot -f
```

---

## Deployment Checklist

- [ ] Choose hosting provider
- [ ] Set up account
- [ ] Create server/service
- [ ] Install Python and dependencies
- [ ] Clone/upload code
- [ ] Set environment variables
- [ ] Test bot runs correctly
- [ ] Set up auto-restart (systemd/service)
- [ ] Monitor logs
- [ ] Set up alerts (optional)

---

## Recommended: Railway (Easiest)

**Why Railway:**
- ✅ Easiest setup (5 minutes)
- ✅ Free tier available
- ✅ Automatic deployments from GitHub
- ✅ Built-in logging dashboard
- ✅ No server management needed
- ✅ Scales automatically

**Quick Start:**
1. Push code to GitHub
2. Sign up at railway.app
3. Connect GitHub repo
4. Add environment variables
5. Deploy!

---

## Cost Comparison

| Service | Cost | Difficulty | Best For |
|---------|------|------------|----------|
| Railway | Free/$5-10/mo | ⭐ Easy | Quick setup |
| Render | Free/$7/mo | ⭐ Easy | Simple deployments |
| DigitalOcean | $6/mo | ⭐⭐ Medium | Full control |
| AWS EC2 | Free/$5-10/mo | ⭐⭐⭐ Hard | Advanced users |
| Google Cloud | Free/Pay-per-use | ⭐⭐ Medium | Serverless |

---

## Next Steps

1. **Choose a provider** (Railway recommended for ease)
2. **Push code to GitHub** (if not already)
3. **Follow provider-specific setup**
4. **Test deployment**
5. **Monitor logs**

Would you like me to:
- Create deployment files for Railway/Render?
- Set up a DigitalOcean deployment script?
- Help you choose the best option?

