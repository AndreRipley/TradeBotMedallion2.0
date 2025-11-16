"""
Statistical Arbitrage Enhanced Anomaly Detection Strategy
Combines anomaly detection with pairs trading and mean reversion.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from scipy import stats
from sklearn.preprocessing import StandardScaler

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class StatisticalArbitrageDetector:
    """Detects statistical arbitrage opportunities using pairs trading and mean reversion."""
    
    def __init__(self, lookback_period: int = 60):
        """
        Initialize statistical arbitrage detector.
        
        Args:
            lookback_period: Number of days to look back for correlation/cointegration analysis
        """
        self.lookback_period = lookback_period
    
    def calculate_correlation(self, prices1: pd.Series, prices2: pd.Series) -> float:
        """Calculate correlation between two price series."""
        if len(prices1) < 20 or len(prices2) < 20:
            return 0.0
        return prices1.corr(prices2)
    
    def calculate_cointegration(self, prices1: pd.Series, prices2: pd.Series) -> Dict:
        """
        Test for cointegration between two price series.
        Returns dict with cointegration status and spread statistics.
        """
        if len(prices1) < 30 or len(prices2) < 30:
            return {'is_cointegrated': False, 'spread_mean': 0, 'spread_std': 1, 'z_score': 0}
        
        # Calculate spread
        spread = prices1 - prices2
        
        # Calculate spread statistics
        spread_mean = spread.mean()
        spread_std = spread.std()
        
        if spread_std == 0:
            return {'is_cointegrated': False, 'spread_mean': spread_mean, 'spread_std': 1, 'z_score': 0}
        
        # Calculate z-score of current spread
        current_spread = spread.iloc[-1]
        z_score = (current_spread - spread_mean) / spread_std
        
        # Simple cointegration test (using correlation of price changes)
        returns1 = prices1.pct_change().dropna()
        returns2 = prices2.pct_change().dropna()
        min_len = min(len(returns1), len(returns2))
        if min_len < 20:
            return {'is_cointegrated': False, 'spread_mean': spread_mean, 'spread_std': spread_std, 'z_score': z_score}
        
        corr = returns1.iloc[-min_len:].corr(returns2.iloc[-min_len:])
        is_cointegrated = abs(corr) > 0.7  # High correlation threshold
        
        return {
            'is_cointegrated': is_cointegrated,
            'spread_mean': spread_mean,
            'spread_std': spread_std,
            'z_score': z_score,
            'correlation': corr
        }
    
    def detect_pairs_arbitrage(self, data1: pd.DataFrame, data2: pd.DataFrame, 
                               symbol1: str, symbol2: str) -> Dict:
        """
        Detect pairs trading arbitrage opportunity.
        
        Returns dict with trading signal:
        - BUY signal: Spread is too wide (z-score > 2), buy the underperformer
        - SELL signal: Spread is too narrow (z-score < -2), sell the overperformer
        """
        if len(data1) < self.lookback_period or len(data2) < self.lookback_period:
            return {'is_opportunity': False}
        
        # Get price series
        prices1 = data1['Close'].iloc[-self.lookback_period:]
        prices2 = data2['Close'].iloc[-self.lookback_period:]
        
        # Normalize prices for comparison
        prices1_norm = (prices1 / prices1.iloc[0]) * 100
        prices2_norm = (prices2 / prices2.iloc[0]) * 100
        
        # Calculate spread
        spread = prices1_norm - prices2_norm
        
        # Calculate spread statistics
        spread_mean = spread.mean()
        spread_std = spread.std()
        
        if spread_std == 0:
            return {'is_opportunity': False}
        
        # Current spread z-score
        current_spread = spread.iloc[-1]
        z_score = (current_spread - spread_mean) / spread_std
        
        # Check for arbitrage opportunity
        is_opportunity = abs(z_score) > 2.0
        
        signal = None
        trade_symbol = None
        
        if z_score > 2.0:
            # Spread is too wide - symbol1 is overpriced relative to symbol2
            # Buy symbol2 (underperformer), sell symbol1 (overperformer)
            signal = 'BUY'
            trade_symbol = symbol2  # Buy the underperformer
        elif z_score < -2.0:
            # Spread is too narrow - symbol1 is underpriced relative to symbol2
            # Buy symbol1 (underperformer), sell symbol2 (overperformer)
            signal = 'BUY'
            trade_symbol = symbol1  # Buy the underperformer
        
        return {
            'is_opportunity': is_opportunity,
            'z_score': z_score,
            'signal': signal,
            'trade_symbol': trade_symbol,
            'spread_mean': spread_mean,
            'spread_std': spread_std,
            'correlation': prices1.corr(prices2)
        }
    
    def detect_mean_reversion(self, data: pd.DataFrame, symbol: str) -> Dict:
        """
        Detect mean reversion opportunities using statistical methods.
        
        Returns dict with mean reversion signal based on:
        - Price deviation from moving average
        - Z-score of current price
        - Bollinger Band position
        """
        if len(data) < self.lookback_period:
            return {'is_opportunity': False}
        
        prices = data['Close'].iloc[-self.lookback_period:]
        current_price = prices.iloc[-1]
        
        # Calculate moving averages
        ma20 = prices.rolling(window=20).mean().iloc[-1]
        ma50 = prices.rolling(window=min(50, len(prices))).mean().iloc[-1]
        
        # Calculate z-score
        price_mean = prices.mean()
        price_std = prices.std()
        
        if price_std == 0:
            return {'is_opportunity': False}
        
        z_score = (current_price - price_mean) / price_std
        
        # Bollinger Bands
        bb_upper = price_mean + (2 * price_std)
        bb_lower = price_mean - (2 * price_std)
        
        # Mean reversion signals
        buy_signal = z_score < -2.0  # Price is 2+ std dev below mean
        sell_signal = z_score > 2.0  # Price is 2+ std dev above mean
        
        # Additional mean reversion indicators
        price_below_ma20 = current_price < ma20
        price_below_ma50 = current_price < ma50
        
        is_opportunity = buy_signal or sell_signal
        
        signal = None
        if buy_signal:
            signal = 'BUY'
        elif sell_signal:
            signal = 'SELL'
        
        return {
            'is_opportunity': is_opportunity,
            'signal': signal,
            'z_score': z_score,
            'price_mean': price_mean,
            'price_std': price_std,
            'ma20': ma20,
            'ma50': ma50,
            'bb_upper': bb_upper,
            'bb_lower': bb_lower,
            'price_below_ma20': price_below_ma20,
            'price_below_ma50': price_below_ma50
        }
    
    def detect_statistical_anomaly(self, data: pd.DataFrame, symbol: str) -> Dict:
        """
        Combined statistical arbitrage detection:
        - Mean reversion opportunities
        - Price anomalies relative to statistical norms
        """
        mean_reversion = self.detect_mean_reversion(data, symbol)
        
        if len(data) < 20:
            return mean_reversion
        
        prices = data['Close'].iloc[-20:]
        current_price = prices.iloc[-1]
        
        # Calculate returns
        returns = prices.pct_change().dropna()
        
        # Statistical anomaly detection
        return_mean = returns.mean()
        return_std = returns.std()
        
        if return_std == 0:
            return mean_reversion
        
        # Recent return z-score
        recent_return = returns.iloc[-1] if len(returns) > 0 else 0
        return_z_score = (recent_return - return_mean) / return_std if return_std > 0 else 0
        
        # Combine signals
        combined_signal = mean_reversion.get('signal')
        severity = abs(mean_reversion.get('z_score', 0))
        
        # Enhance with return anomaly
        if abs(return_z_score) > 2.0:
            if return_z_score < -2.0 and combined_signal != 'SELL':
                combined_signal = 'BUY'
                severity += abs(return_z_score)
            elif return_z_score > 2.0 and combined_signal != 'BUY':
                combined_signal = 'SELL'
                severity += abs(return_z_score)
        
        return {
            **mean_reversion,
            'signal': combined_signal,
            'severity': severity,
            'return_z_score': return_z_score,
            'return_mean': return_mean,
            'return_std': return_std
        }


class StatisticalArbitrageStrategy:
    """Trading strategy combining anomaly detection with statistical arbitrage."""
    
    def __init__(self, stocks: List[str], position_size: float = 10.0, 
                 min_severity: float = 1.0, use_pairs_trading: bool = True):
        """
        Initialize statistical arbitrage strategy.
        
        Args:
            stocks: List of stock symbols
            position_size: Dollar amount per trade
            min_severity: Minimum anomaly severity to trigger trade
            use_pairs_trading: Whether to use pairs trading
        """
        self.stocks = stocks
        self.position_size = position_size
        self.min_severity = min_severity
        self.use_pairs_trading = use_pairs_trading
        self.arbitrage_detector = StatisticalArbitrageDetector(lookback_period=60)
        self.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')
        self.end_date = datetime.now().strftime('%Y-%m-%d')
    
    def fetch_stock_data(self, symbol: str) -> pd.DataFrame:
        """Fetch historical stock data."""
        try:
            logger.info(f"Fetching data for {symbol}...")
            ticker = yf.Ticker(symbol)
            data = ticker.history(start=self.start_date, end=self.end_date, interval='1d')
            
            if data.empty:
                return pd.DataFrame()
            
            data = data.reset_index()
            data['Date'] = pd.to_datetime(data['Date'])
            return data
        except Exception as e:
            logger.error(f"Error fetching {symbol}: {e}")
            return pd.DataFrame()
    
    def find_correlated_pairs(self, data_dict: Dict[str, pd.DataFrame]) -> List[Tuple[str, str, float]]:
        """Find pairs of stocks with high correlation."""
        pairs = []
        symbols = list(data_dict.keys())
        
        for i, symbol1 in enumerate(symbols):
            for symbol2 in symbols[i+1:]:
                if symbol1 not in data_dict or symbol2 not in data_dict:
                    continue
                
                data1 = data_dict[symbol1]
                data2 = data_dict[symbol2]
                
                if len(data1) < 60 or len(data2) < 60:
                    continue
                
                prices1 = data1['Close'].iloc[-60:]
                prices2 = data2['Close'].iloc[-60:]
                
                corr = self.arbitrage_detector.calculate_correlation(prices1, prices2)
                
                if abs(corr) > 0.7:  # High correlation threshold
                    pairs.append((symbol1, symbol2, corr))
        
        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)
    
    def backtest_strategy(self, symbol: str, all_data: Dict[str, pd.DataFrame] = None) -> Dict:
        """Backtest statistical arbitrage strategy for a stock."""
        data = self.fetch_stock_data(symbol)
        if data.empty or len(data) < 60:
            return {
                'symbol': symbol,
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'total_invested': 0,
                'total_sold_value': 0,
                'current_value': 0,
                'total_value': 0,
                'profit_loss': 0,
                'return_pct': 0,
                'trades': []
            }
        
        trades = []
        total_invested = 0
        total_sold_value = 0
        shares_owned = 0
        
        # Start after lookback period
        for i in range(self.arbitrage_detector.lookback_period, len(data)):
            current_date = data.iloc[i]['Date']
            current_price = data.iloc[i]['Close']
            current_data = data.iloc[:i+1]
            
            # Statistical arbitrage detection
            stat_arb = self.arbitrage_detector.detect_statistical_anomaly(current_data, symbol)
            
            if stat_arb.get('is_opportunity') and stat_arb.get('severity', 0) >= self.min_severity:
                signal = stat_arb.get('signal')
                
                # Handle BUY signals
                if signal == 'BUY':
                    shares_to_buy = self.position_size / current_price
                    cost = shares_to_buy * current_price
                    
                    trades.append({
                        'date': current_date.strftime('%Y-%m-%d'),
                        'type': 'BUY',
                        'price': round(current_price, 2),
                        'shares': round(shares_to_buy, 4),
                        'cost': round(cost, 2),
                        'method': 'statistical_arbitrage',
                        'z_score': round(stat_arb.get('z_score', 0), 2),
                        'severity': round(stat_arb.get('severity', 0), 2)
                    })
                    
                    shares_owned += shares_to_buy
                    total_invested += cost
                
                # Handle SELL signals
                elif signal == 'SELL' and shares_owned > 0:
                    shares_to_sell = min(shares_owned, self.position_size / current_price)
                    if shares_to_sell > 0:
                        proceeds = shares_to_sell * current_price
                        
                        trades.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'type': 'SELL',
                            'price': round(current_price, 2),
                            'shares': round(shares_to_sell, 4),
                            'proceeds': round(proceeds, 2),
                            'method': 'statistical_arbitrage',
                            'z_score': round(stat_arb.get('z_score', 0), 2),
                            'severity': round(stat_arb.get('severity', 0), 2)
                        })
                        
                        shares_owned -= shares_to_sell
                        total_sold_value += proceeds
        
        # Calculate final value
        if len(data) > 0:
            final_price = data.iloc[-1]['Close']
            current_value = shares_owned * final_price
            total_value = current_value + total_sold_value
            profit_loss = total_value - total_invested
            return_pct = (profit_loss / total_invested * 100) if total_invested > 0 else 0
            
            return {
                'symbol': symbol,
                'total_trades': len(trades),
                'buy_trades': len([t for t in trades if t['type'] == 'BUY']),
                'sell_trades': len([t for t in trades if t['type'] == 'SELL']),
                'total_invested': round(total_invested, 2),
                'total_sold_value': round(total_sold_value, 2),
                'shares_owned': round(shares_owned, 4),
                'final_price': round(final_price, 2),
                'current_value': round(current_value, 2),
                'total_value': round(total_value, 2),
                'profit_loss': round(profit_loss, 2),
                'return_pct': round(return_pct, 2),
                'trades': trades
            }
        else:
            return {
                'symbol': symbol,
                'total_trades': 0,
                'buy_trades': 0,
                'sell_trades': 0,
                'total_invested': 0,
                'total_sold_value': 0,
                'current_value': 0,
                'total_value': 0,
                'profit_loss': 0,
                'return_pct': 0,
                'trades': []
            }
    
    def run_backtest(self) -> Dict:
        """Run backtest for all stocks."""
        logger.info(f"Starting statistical arbitrage backtest")
        logger.info(f"Period: {self.start_date} to {self.end_date} (1 year)")
        logger.info(f"Position size: ${self.position_size} per trade")
        logger.info(f"Minimum severity: {self.min_severity}")
        logger.info(f"Stocks: {', '.join(self.stocks)}")
        
        results = {}
        total_invested_all = 0
        total_value_all = 0
        
        for symbol in self.stocks:
            symbol = symbol.strip().upper()
            result = self.backtest_strategy(symbol)
            results[symbol] = result
            
            total_invested_all += result['total_invested']
            total_value_all += result['total_value']
        
        # Calculate overall statistics
        total_profit_loss = total_value_all - total_invested_all
        overall_return_pct = (total_profit_loss / total_invested_all * 100) if total_invested_all > 0 else 0
        
        return {
            'period': f"{self.start_date} to {self.end_date}",
            'position_size': self.position_size,
            'min_severity': self.min_severity,
            'stocks': results,
            'summary': {
                'total_invested': round(total_invested_all, 2),
                'total_value': round(total_value_all, 2),
                'total_profit_loss': round(total_profit_loss, 2),
                'overall_return_pct': round(overall_return_pct, 2),
                'total_trades': sum(r['total_trades'] for r in results.values())
            }
        }
    
    def print_results(self, results: Dict):
        """Print formatted backtest results."""
        print("\n" + "="*100)
        print("STATISTICAL ARBITRAGE STRATEGY - BACKTEST RESULTS (1 YEAR)")
        print("="*100)
        print(f"\nPeriod: {results['period']}")
        print(f"Position Size: ${results['position_size']} per trade")
        print(f"Minimum Severity: {results['min_severity']}")
        
        print(f"\n{'Stock':<8} {'Trades':<8} {'Buys':<6} {'Sells':<6} {'Invested':<12} {'Value':<12} {'P/L':<12} {'Return %':<10}")
        print("-"*100)
        
        for symbol, data in results['stocks'].items():
            print(f"{symbol:<8} {data['total_trades']:<8} {data['buy_trades']:<6} {data['sell_trades']:<6} "
                  f"${data['total_invested']:<11.2f} ${data['total_value']:<11.2f} "
                  f"${data['profit_loss']:<11.2f} {data['return_pct']:<9.2f}%")
        
        print("-"*100)
        summary = results['summary']
        print(f"{'TOTAL':<8} {summary['total_trades']:<8} {'-':<6} {'-':<6} "
              f"${summary['total_invested']:<11.2f} ${summary['total_value']:<11.2f} "
              f"${summary['total_profit_loss']:<11.2f} {summary['overall_return_pct']:<9.2f}%")


def main():
    """Main function to run statistical arbitrage backtest."""
    # Top 50 stocks by market cap
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN',
        'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE', 'CMCSA',
        'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI', 'INTU'
    ]
    position_size = 10.0
    min_severity = 1.5  # Slightly higher threshold for statistical arbitrage
    
    strategy = StatisticalArbitrageStrategy(
        stocks=stocks,
        position_size=position_size,
        min_severity=min_severity,
        use_pairs_trading=True
    )
    
    results = strategy.run_backtest()
    strategy.print_results(results)
    
    # Save results to CSV
    df_results = pd.DataFrame([
        {
            'Symbol': symbol,
            'Trades': data['total_trades'],
            'Buy_Trades': data['buy_trades'],
            'Sell_Trades': data['sell_trades'],
            'Invested': data['total_invested'],
            'Total_Value': data['total_value'],
            'Profit_Loss': data['profit_loss'],
            'Return_Pct': data['return_pct']
        }
        for symbol, data in results['stocks'].items()
    ])
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"stat_arbitrage_backtest_50stocks_{timestamp}.csv"
    df_results.to_csv(output_file, index=False)
    print(f"\n✅ Results saved to {output_file}")


if __name__ == '__main__':
    main()

