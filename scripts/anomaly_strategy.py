"""
Anomaly Detection Trading Strategy
Detects statistical anomalies in stock prices and volumes, then capitalizes on them.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Detects anomalies in stock price and volume data."""
    
    def __init__(self, lookback_period: int = 20):
        """
        Initialize anomaly detector.
        
        Args:
            lookback_period: Number of days to look back for baseline statistics
        """
        self.lookback_period = lookback_period
    
    def detect_price_anomaly(self, data: pd.DataFrame, current_idx: int) -> Dict:
        """
        Detect price anomalies using statistical methods.
        
        Returns dict with anomaly type and severity.
        """
        if current_idx < self.lookback_period:
            return {'is_anomaly': False}
        
        # Get historical data for baseline
        historical = data.iloc[current_idx - self.lookback_period:current_idx]
        current = data.iloc[current_idx]
        
        # Calculate statistics
        mean_price = historical['Close'].mean()
        std_price = historical['Close'].std()
        current_price = current['Close']
        
        # Z-score for price
        z_score = (current_price - mean_price) / std_price if std_price > 0 else 0
        
        # Price change anomaly
        price_change = current['Close'] - data.iloc[current_idx - 1]['Close']
        price_change_pct = (price_change / data.iloc[current_idx - 1]['Close']) * 100
        
        # Volatility anomaly (using ATR-like measure)
        historical_volatility = historical['Close'].pct_change().std() * 100
        current_volatility = abs(price_change_pct)
        
        anomalies = []
        severity = 0
        
        # Negative price anomaly (oversold) - BUY signal
        if z_score < -2.0:  # Price is 2+ standard deviations below mean
            anomalies.append('oversold')
            severity += abs(z_score)
        
        # Positive price anomaly (overbought) - SELL signal
        if z_score > 2.0:  # Price is 2+ standard deviations above mean
            anomalies.append('overbought')
            severity += abs(z_score)
        
        # Extreme drop anomaly - BUY signal
        if price_change_pct < -3.0:  # Drop of more than 3%
            anomalies.append('extreme_drop')
            severity += abs(price_change_pct) / 3
        
        # Extreme rise anomaly - SELL signal
        if price_change_pct > 3.0:  # Rise of more than 3%
            anomalies.append('extreme_rise')
            severity += abs(price_change_pct) / 3
        
        # Volatility spike (can be either direction)
        if current_volatility > historical_volatility * 2:
            anomalies.append('volatility_spike')
            severity += 1
        
        return {
            'is_anomaly': len(anomalies) > 0,
            'anomaly_types': anomalies,
            'severity': severity,
            'z_score': z_score,
            'price_change_pct': price_change_pct
        }
    
    def detect_volume_anomaly(self, data: pd.DataFrame, current_idx: int) -> Dict:
        """Detect volume anomalies."""
        if current_idx < self.lookback_period:
            return {'is_anomaly': False}
        
        historical = data.iloc[current_idx - self.lookback_period:current_idx]
        current = data.iloc[current_idx]
        
        mean_volume = historical['Volume'].mean()
        std_volume = historical['Volume'].std()
        current_volume = current['Volume']
        
        # Volume spike (unusually high volume)
        volume_ratio = current_volume / mean_volume if mean_volume > 0 else 1
        
        is_anomaly = volume_ratio > 2.0  # Volume is 2x+ the average
        
        return {
            'is_anomaly': is_anomaly,
            'volume_ratio': volume_ratio,
            'volume_spike': is_anomaly
        }
    
    def detect_gap_anomaly(self, data: pd.DataFrame, current_idx: int) -> Dict:
        """Detect price gap anomalies."""
        if current_idx < 1:
            return {'is_anomaly': False}
        
        current = data.iloc[current_idx]
        previous = data.iloc[current_idx - 1]
        
        # Gap down (opening price significantly lower than previous close) - BUY signal
        gap = current['Open'] - previous['Close']
        gap_pct = (gap / previous['Close']) * 100
        
        is_gap_down = gap_pct < -2.0  # Gap down more than 2%
        is_gap_up = gap_pct > 2.0  # Gap up more than 2% - SELL signal
        
        return {
            'is_anomaly': is_gap_down or is_gap_up,
            'gap_pct': gap_pct,
            'gap_down': is_gap_down,
            'gap_up': is_gap_up
        }
    
    def detect_rsi_anomaly(self, data: pd.DataFrame, current_idx: int) -> Dict:
        """Detect RSI-based anomalies (oversold and overbought conditions)."""
        if current_idx < 14:
            return {'is_anomaly': False}
        
        # Calculate RSI
        prices = data['Close'].iloc[:current_idx + 1]
        rsi = self._calculate_rsi(prices, 14)
        
        if len(rsi) == 0 or pd.isna(rsi.iloc[-1]):
            return {'is_anomaly': False}
        
        current_rsi = rsi.iloc[-1]
        
        # Oversold anomaly (RSI < 30) - BUY signal
        is_oversold = current_rsi < 30
        # Overbought anomaly (RSI > 70) - SELL signal
        is_overbought = current_rsi > 70
        
        return {
            'is_anomaly': is_oversold or is_overbought,
            'rsi': current_rsi,
            'oversold': is_oversold,
            'overbought': is_overbought
        }
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index."""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def detect_all_anomalies(self, data: pd.DataFrame, current_idx: int) -> Dict:
        """Detect all types of anomalies."""
        price_anomaly = self.detect_price_anomaly(data, current_idx)
        volume_anomaly = self.detect_volume_anomaly(data, current_idx)
        gap_anomaly = self.detect_gap_anomaly(data, current_idx)
        rsi_anomaly = self.detect_rsi_anomaly(data, current_idx)
        
        # Combine anomalies
        all_anomalies = []
        total_severity = 0
        
        if price_anomaly['is_anomaly']:
            all_anomalies.extend(price_anomaly['anomaly_types'])
            total_severity += price_anomaly.get('severity', 0)
        
        if volume_anomaly['is_anomaly']:
            all_anomalies.append('volume_spike')
            total_severity += 1
        
        if gap_anomaly['is_anomaly']:
            if gap_anomaly.get('gap_down', False):
                all_anomalies.append('gap_down')
                total_severity += abs(gap_anomaly['gap_pct']) / 2
            if gap_anomaly.get('gap_up', False):
                all_anomalies.append('gap_up')
                total_severity += abs(gap_anomaly['gap_pct']) / 2
        
        if rsi_anomaly['is_anomaly']:
            if rsi_anomaly.get('oversold', False):
                all_anomalies.append('rsi_oversold')
                total_severity += (30 - rsi_anomaly['rsi']) / 10
            if rsi_anomaly.get('overbought', False):
                all_anomalies.append('rsi_overbought')
                total_severity += (rsi_anomaly['rsi'] - 70) / 10
        
        # Determine if this is a buy or sell signal
        buy_signals = ['oversold', 'extreme_drop', 'gap_down', 'rsi_oversold']
        sell_signals = ['overbought', 'extreme_rise', 'gap_up', 'rsi_overbought']
        
        signal_type = None
        if any(signal in all_anomalies for signal in buy_signals):
            signal_type = 'BUY'
        if any(signal in all_anomalies for signal in sell_signals):
            if signal_type == 'BUY':
                signal_type = 'MIXED'  # Both buy and sell signals
            else:
                signal_type = 'SELL'
        
        return {
            'is_anomaly': len(all_anomalies) > 0,
            'anomaly_types': list(set(all_anomalies)),
            'severity': total_severity,
            'signal_type': signal_type,  # 'BUY', 'SELL', or 'MIXED'
            'price_anomaly': price_anomaly,
            'volume_anomaly': volume_anomaly,
            'gap_anomaly': gap_anomaly,
            'rsi_anomaly': rsi_anomaly
        }


class AnomalyTradingStrategy:
    """Trading strategy that capitalizes on detected anomalies."""
    
    def __init__(self, stocks: List[str], position_size: float = 10.0, min_severity: float = 1.0):
        """
        Initialize strategy.
        
        Args:
            stocks: List of stock symbols
            position_size: Dollar amount per trade
            min_severity: Minimum anomaly severity to trigger trade
        """
        self.stocks = stocks
        self.position_size = position_size
        self.min_severity = min_severity
        self.detector = AnomalyDetector(lookback_period=20)
        self.start_date = (datetime.now() - timedelta(days=365)).strftime('%Y-%m-%d')  # 1 year
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
    
    def backtest_strategy(self, symbol: str) -> Dict:
        """Backtest anomaly detection strategy for a stock."""
        data = self.fetch_stock_data(symbol)
        if data.empty or len(data) < 30:
            return {
                'symbol': symbol,
                'total_trades': 0,
                'total_invested': 0,
                'current_value': 0,
                'profit_loss': 0,
                'return_pct': 0,
                'anomalies_detected': 0,
                'trades': []
            }
        
        trades = []
        total_invested = 0
        total_sold_value = 0
        shares_owned = 0
        anomalies_detected = 0
        
        # Start after lookback period
        for i in range(self.detector.lookback_period, len(data)):
            current_date = data.iloc[i]['Date']
            current_price = data.iloc[i]['Close']
            
            # Detect anomalies
            anomaly_info = self.detector.detect_all_anomalies(data, i)
            
            if anomaly_info['is_anomaly']:
                anomalies_detected += 1
                
                # Only trade if severity meets threshold
                if anomaly_info['severity'] >= self.min_severity:
                    signal_type = anomaly_info.get('signal_type', 'BUY')
                    
                    # Handle BUY signals
                    if signal_type in ['BUY', 'MIXED']:
                        # Buy on oversold/negative anomalies (mean reversion)
                        shares_to_buy = self.position_size / current_price
                        cost = shares_to_buy * current_price
                        
                        trades.append({
                            'date': current_date.strftime('%Y-%m-%d'),
                            'type': 'BUY',
                            'price': round(current_price, 2),
                            'shares': round(shares_to_buy, 4),
                            'cost': round(cost, 2),
                            'anomaly_types': ', '.join(anomaly_info['anomaly_types']),
                            'severity': round(anomaly_info['severity'], 2)
                        })
                        
                        shares_owned += shares_to_buy
                        total_invested += cost
                    
                    # Handle SELL signals
                    if signal_type in ['SELL', 'MIXED'] and shares_owned > 0:
                        # Sell on overbought/positive anomalies (take profits)
                        # Sell proportionally based on position size
                        shares_to_sell = min(shares_owned, self.position_size / current_price)
                        if shares_to_sell > 0:
                            proceeds = shares_to_sell * current_price
                            
                            trades.append({
                                'date': current_date.strftime('%Y-%m-%d'),
                                'type': 'SELL',
                                'price': round(current_price, 2),
                                'shares': round(shares_to_sell, 4),
                                'proceeds': round(proceeds, 2),
                                'anomaly_types': ', '.join(anomaly_info['anomaly_types']),
                                'severity': round(anomaly_info['severity'], 2)
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
                'anomalies_detected': anomalies_detected,
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
                'anomalies_detected': anomalies_detected,
                'trades': []
            }
    
    def run_backtest(self) -> Dict:
        """Run backtest for all stocks."""
        logger.info(f"Starting anomaly detection backtest")
        logger.info(f"Period: {self.start_date} to {self.end_date} (1 year)")
        logger.info(f"Position size: ${self.position_size} per trade")
        logger.info(f"Minimum severity: {self.min_severity}")
        logger.info(f"Stocks: {', '.join(self.stocks)}")
        
        results = {}
        total_invested_all = 0
        total_value_all = 0
        total_anomalies = 0
        
        for symbol in self.stocks:
            symbol = symbol.strip().upper()
            result = self.backtest_strategy(symbol)
            results[symbol] = result
            
            total_invested_all += result['total_invested']
            # Use total_value (includes sold proceeds) instead of just current_value
            total_value_all += result.get('total_value', result['current_value'])
            total_anomalies += result['anomalies_detected']
        
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
                'total_trades': sum(r['total_trades'] for r in results.values()),
                'total_anomalies_detected': total_anomalies
            }
        }
    
    def print_results(self, results: Dict):
        """Print formatted backtest results."""
        print("\n" + "="*100)
        print("ANOMALY DETECTION STRATEGY - BACKTEST RESULTS (1 YEAR)")
        print("="*100)
        print(f"\nPeriod: {results['period']}")
        print(f"Position Size: ${results['position_size']} per trade")
        print(f"Minimum Anomaly Severity: {results['min_severity']}")
        
        print(f"\n{'Stock':<8} {'Anomalies':<12} {'Trades':<8} {'Buys':<6} {'Sells':<6} {'Invested':<12} {'Value':<12} {'P/L':<12} {'Return %':<10}")
        print("-"*120)
        
        for symbol, data in results['stocks'].items():
            print(f"{symbol:<8} {data['anomalies_detected']:<12} {data['total_trades']:<8} "
                  f"{data.get('buy_trades', 0):<6} {data.get('sell_trades', 0):<6} "
                  f"${data['total_invested']:<11.2f} ${data.get('total_value', data['current_value']):<11.2f} "
                  f"${data['profit_loss']:<11.2f} {data['return_pct']:<9.2f}%")
        
        print("-"*100)
        summary = results['summary']
        print(f"{'TOTAL':<8} {summary['total_anomalies_detected']:<12} {summary['total_trades']:<8} "
              f"${summary['total_invested']:<11.2f} ${summary['total_value']:<11.2f} "
              f"${summary['total_profit_loss']:<11.2f} {summary['overall_return_pct']:<9.2f}%")
        
        print("\n" + "="*100)
        print("ANOMALY TYPES DETECTED")
        print("="*100)
        
        # Analyze anomaly types across all trades
        all_anomaly_types = {}
        for symbol, data in results['stocks'].items():
            for trade in data['trades']:
                types = trade['anomaly_types'].split(', ')
                for anomaly_type in types:
                    all_anomaly_types[anomaly_type] = all_anomaly_types.get(anomaly_type, 0) + 1
        
        print("\nAnomaly Type Distribution:")
        for anomaly_type, count in sorted(all_anomaly_types.items(), key=lambda x: -x[1]):
            print(f"  {anomaly_type}: {count} trades")
        
        print("\n" + "="*100)
        print("DETAILED BREAKDOWN BY STOCK")
        print("="*100)
        
        for symbol, data in results['stocks'].items():
            if data['total_trades'] > 0:
                print(f"\n{symbol}:")
                print(f"  Anomalies Detected: {data['anomalies_detected']}")
                print(f"  Trades Executed: {data['total_trades']}")
                print(f"  Total Invested: ${data['total_invested']:.2f}")
                print(f"  Current Value: ${data['current_value']:.2f}")
                print(f"  Profit/Loss: ${data['profit_loss']:.2f} ({data['return_pct']:.2f}%)")
                
                # Show sample trades
                if len(data['trades']) > 0:
                    print(f"  Sample Trades (first 10):")
                    for trade in data['trades'][:10]:
                        trade_type = trade.get('type', 'BUY')
                        if trade_type == 'BUY':
                            print(f"    {trade['date']}: BUY {trade['shares']:.4f} shares @ ${trade['price']:.2f} "
                                  f"({trade['anomaly_types']}, severity: {trade['severity']:.2f})")
                        else:
                            print(f"    {trade['date']}: SELL {trade['shares']:.4f} shares @ ${trade['price']:.2f} "
                                  f"({trade['anomaly_types']}, severity: {trade['severity']:.2f})")
                    if len(data['trades']) > 10:
                        print(f"    ... and {len(data['trades']) - 10} more trades")


def main():
    """Main function to run anomaly detection backtest."""
    # Top 50 stocks by market cap
    stocks = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'V', 'UNH', 'XOM',
        'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX', 'MRK',
        'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT', 'ACN',
        'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE', 'CMCSA',
        'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI', 'INTU'
    ]
    position_size = 10.0
    min_severity = 1.0  # Minimum anomaly severity to trigger trade
    
    strategy = AnomalyTradingStrategy(
        stocks=stocks,
        position_size=position_size,
        min_severity=min_severity
    )
    
    results = strategy.run_backtest()
    strategy.print_results(results)
    
    # Save results to CSV
    df_results = pd.DataFrame([
        {
            'Symbol': symbol,
            'Anomalies_Detected': data['anomalies_detected'],
            'Trades': data['total_trades'],
            'Buy_Trades': data.get('buy_trades', 0),
            'Sell_Trades': data.get('sell_trades', 0),
            'Invested': data['total_invested'],
            'Current_Value': data['current_value'],
            'Total_Sold_Value': data.get('total_sold_value', 0),
            'Total_Value': data.get('total_value', data['current_value']),
            'Profit_Loss': data['profit_loss'],
            'Return_Pct': data['return_pct']
        }
        for symbol, data in results['stocks'].items()
    ])
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"anomaly_backtest_50stocks_{timestamp}.csv"
    df_results.to_csv(output_file, index=False)
    print(f"\n✅ Results saved to {output_file}")


if __name__ == '__main__':
    main()

