# Installing Docker for macOS

## Quick Install (Recommended)

### Option 1: Using Homebrew (Easiest)

If you have Homebrew installed:

```bash
# Install Docker Desktop
brew install --cask docker

# Start Docker Desktop
open -a Docker

# Wait for Docker to start (check the menu bar for Docker icon)
# Then verify installation:
docker --version
```

### Option 2: Manual Download

1. **Download Docker Desktop**:
   - Go to: https://www.docker.com/products/docker-desktop/
   - Click "Download for Mac"
   - Choose the version for your Mac (Intel or Apple Silicon/M1/M2)

2. **Install**:
   - Open the downloaded `.dmg` file
   - Drag Docker to Applications folder
   - Open Docker from Applications
   - Follow the setup wizard

3. **Verify**:
   ```bash
   docker --version
   docker ps
   ```

## After Installation

Once Docker is installed and running:

1. **Verify Docker is running**:
   ```bash
   docker ps
   ```
   Should show an empty list (not an error).

2. **Continue with deployment**:
   ```bash
   ./earnings_volatility_yfinance/gcp_deploy.sh
   ```

## Troubleshooting

### Docker won't start
- Make sure you have enough disk space (Docker needs ~4GB)
- Check System Preferences → Security & Privacy → Allow Docker
- Restart your Mac if needed

### "Docker daemon not running"
- Open Docker Desktop application
- Wait for the Docker icon to appear in menu bar
- Make sure it shows "Docker Desktop is running"

### Permission denied errors
- Docker Desktop should handle permissions automatically
- If issues persist, add your user to docker group (usually not needed on macOS)

## Alternative: Use Cloud Build (No Local Docker Needed)

If you prefer not to install Docker locally, you can use Google Cloud Build instead. I can modify the deployment script to use `gcloud builds submit` instead of local Docker build.

Would you like me to create an alternative deployment method that doesn't require local Docker?

