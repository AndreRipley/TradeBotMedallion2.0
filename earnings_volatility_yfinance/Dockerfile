# Dockerfile for Earnings Volatility Trading Bot - Cloud Run Job
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for numpy/pandas/scipy
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libopenblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY earnings_volatility_yfinance/requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY earnings_volatility_yfinance/ /app/earnings_volatility_yfinance/
COPY earnings_volatility_yfinance/__init__.py /app/earnings_volatility_yfinance/__init__.py

# Set PYTHONPATH so imports work
ENV PYTHONPATH=/app

# Set entrypoint (arguments will be passed by Cloud Run Job)
ENTRYPOINT ["python", "-m", "earnings_volatility_yfinance.main_cloud"]

# Default command (can be overridden by Cloud Run Job)
CMD ["--mode", "entry"]

