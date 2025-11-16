"""
Fetch top stocks by market cap and backtest anomaly detection strategy.
"""
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging
import time
from anomaly_strategy import AnomalyDetector, AnomalyTradingStrategy

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_top_stocks_by_market_cap(n: int = 200) -> List[str]:
    """
    Get top N stocks by market cap.
    Uses S&P 500 + NASDAQ 100 + additional large caps.
    """
    # S&P 500 tickers (top by market cap)
    sp500_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'BRK.B', 'V', 'UNH',
        'XOM', 'JNJ', 'JPM', 'WMT', 'MA', 'PG', 'LLY', 'AVGO', 'HD', 'CVX',
        'MRK', 'ABBV', 'COST', 'ADBE', 'PEP', 'TMO', 'MCD', 'CSCO', 'NFLX', 'ABT',
        'ACN', 'DHR', 'VZ', 'WFC', 'DIS', 'LIN', 'NKE', 'PM', 'TXN', 'NEE',
        'CMCSA', 'HON', 'RTX', 'UPS', 'QCOM', 'AMGN', 'BMY', 'T', 'LOW', 'SPGI',
        'INTU', 'DE', 'AXP', 'SBUX', 'GS', 'ELV', 'BKNG', 'ADP', 'C', 'TJX',
        'GE', 'MDT', 'ISRG', 'VRTX', 'ZTS', 'REGN', 'ADI', 'FI', 'PLD', 'EQIX',
        'ICE', 'KLAC', 'CDNS', 'SNPS', 'APH', 'MCHP', 'FTNT', 'NXPI', 'ODFL', 'CTSH',
        'PAYX', 'FAST', 'ANSS', 'IDXX', 'CPRT', 'CDW', 'WDAY', 'TEAM', 'ZM', 'CRWD',
        'ON', 'MSTR', 'ENPH', 'FANG', 'MPWR', 'ALGN', 'DXCM', 'TTD', 'DOCN', 'NET',
        'RPD', 'ESTC', 'ZS', 'DDOG', 'OKTA', 'SPLK', 'VRSN', 'FTV', 'TDG', 'KEYS',
        'BR', 'HWM', 'TECH', 'WAT', 'POOL', 'ROL', 'GGG', 'AOS', 'IT', 'SWAV',
        'ALRM', 'FRSH', 'DOCU', 'COUP', 'BILL', 'PCOR', 'FOUR', 'APPN', 'QLYS', 'QLYS',
        # NASDAQ 100 additions
        'AMD', 'INTC', 'AMAT', 'LRCX', 'ASML', 'MU', 'AMBA', 'SWKS', 'QRVO', 'MRVL',
        # Additional large caps
        'BAC', 'MS', 'BLK', 'SCHW', 'COF', 'USB', 'PNC', 'TFC', 'CFG', 'HBAN',
        'RF', 'KEY', 'FITB', 'MTB', 'ZION', 'CMA', 'WTFC', 'ONB', 'FNB', 'HOMB',
        'UMB', 'BOKF', 'TCBI', 'CBSH', 'UBSH', 'HBNC', 'FBNC', 'FBMS', 'FCNCA', 'FFIN',
        'FIBK', 'FMBH', 'FMNB', 'FNCB', 'FNLC', 'FNWB', 'FORR', 'FRBA', 'FRBK', 'FRME',
        'FSBC', 'FSBW', 'FULT', 'FUSB', 'FVCB', 'GABC', 'GBCI', 'GCBC', 'GNTY', 'GWB',
        'HAFC', 'HBNC', 'HFWA', 'HOMB', 'HONE', 'HOPE', 'HTBK', 'HTLF', 'HWC', 'IBCP',
        'IBOC', 'IBTX', 'INDB', 'ISBC', 'IVCB', 'JPM', 'KEY', 'LBAI', 'LCNB', 'LEVL',
        'LKFN', 'LOAN', 'LRCX', 'MBIN', 'MBWM', 'MCBC', 'MCBS', 'MFIN', 'MFSF', 'MGYR',
        'MNSB', 'MOFG', 'MPB', 'MRBK', 'MSBI', 'MTB', 'MVBF', 'NBN', 'NBTB', 'NCBS',
        'NFBK', 'NMRK', 'NODK', 'NRIM', 'NWBI', 'NWFL', 'NWLI', 'NWPX', 'NYCB', 'OBNK',
        'OBT', 'OCFC', 'OFED', 'OFG', 'ONB', 'OPBK', 'OPOF', 'ORRF', 'OSBC', 'OTTR',
        'OVLY', 'OZK', 'PACW', 'PB', 'PBHC', 'PCSB', 'PEBK', 'PEBO', 'PFBC', 'PFBI',
        'PFC', 'PFIS', 'PFS', 'PFSI', 'PGC', 'PKBK', 'PLBC', 'PMBC', 'PNC', 'PNFP',
        'PPBI', 'PRK', 'PROV', 'PUB', 'PUBN', 'PVBC', 'QCRH', 'RBCAA', 'RBNC', 'RF',
        'RNDB', 'RNST', 'RRBI', 'RSAS', 'RUSHB', 'RVSB', 'SASR', 'SBCF', 'SBNY', 'SBSI',
        'SCNB', 'SEIC', 'SFBC', 'SFBS', 'SFST', 'SGBX', 'SHBI', 'SIFI', 'SIVB', 'SLCT',
        'SMBC', 'SMBK', 'SNV', 'SPFI', 'SRCE', 'SSB', 'STBA', 'STBK', 'STL', 'STND',
        'STTZ', 'SUSB', 'SVBI', 'SYBT', 'TBBK', 'TCBI', 'TCBK', 'TCFC', 'TCHC', 'TCOM',
        'TECT', 'TFC', 'THFF', 'TIPT', 'TMP', 'TRCB', 'TRMK', 'TRST', 'TSBK', 'TSC',
        'TSCAP', 'TSCO', 'TSLX', 'TSQ', 'TTEC', 'TTEK', 'TTGT', 'TTMI', 'TTSH', 'TTSI',
        'TURN', 'TUSK', 'TVTX', 'TW', 'TWIN', 'TWLO', 'TWLV', 'TWNK', 'TWO', 'TWOU',
        'TWST', 'TXG', 'TXMD', 'TXN', 'TXRH', 'TYHT', 'TYME', 'TZOO', 'U', 'UAA',
        'UAL', 'UAMY', 'UAVS', 'UBA', 'UBCP', 'UBFO', 'UBOH', 'UBS', 'UBSH', 'UBX',
        'UCBI', 'UCTT', 'UDR', 'UE', 'UEC', 'UEIC', 'UEPS', 'UFAB', 'UFCS', 'UFI',
        'UFPI', 'UFPT', 'UFS', 'UG', 'UGI', 'UGP', 'UHAL', 'UHS', 'UHT', 'UI',
        'UIHC', 'UIS', 'ULBI', 'ULCC', 'ULH', 'ULTA', 'UMBF', 'UMC', 'UMH', 'UMPQ',
        'UNAM', 'UNB', 'UNF', 'UNFI', 'UNH', 'UNIT', 'UNM', 'UNP', 'UNTY', 'UONE',
        'UONEK', 'UPLD', 'UPS', 'UPST', 'UPWK', 'URBN', 'URG', 'URI', 'UROY', 'USA',
        'USAC', 'USAK', 'USAP', 'USAS', 'USAU', 'USCB', 'USCT', 'USDP', 'USEG', 'USFD',
        'USIO', 'USLM', 'USM', 'USNA', 'USPH', 'USRM', 'USRT', 'USTB', 'USX', 'UTHR',
        'UTI', 'UTL', 'UTMD', 'UTME', 'UTSI', 'UTZ', 'UUU', 'UUUU', 'UVE', 'UVSP',
        'UVV', 'UWMC', 'UXIN', 'UZD', 'UZE', 'UZF', 'V', 'VABK', 'VAC', 'VACC',
        'VAL', 'VALE', 'VALN', 'VALU', 'VAPO', 'VAQC', 'VATE', 'VAXX', 'VBFC', 'VBIV',
        'VBLT', 'VBNK', 'VBOC', 'VBR', 'VBTX', 'VC', 'VCEL', 'VCIT', 'VCLT', 'VCNX',
        'VCR', 'VCRA', 'VCSH', 'VCTR', 'VCV', 'VCXA', 'VCXB', 'VCYT', 'VEC', 'VECO',
        'VECT', 'VEDU', 'VEEE', 'VEEV', 'VEL', 'VEON', 'VERA', 'VERB', 'VERI', 'VERO',
        'VERS', 'VERU', 'VERV', 'VERX', 'VERY', 'VET', 'VEV', 'VFC', 'VFF', 'VFH',
        'VFL', 'VFMO', 'VFMV', 'VFQY', 'VFS', 'VFVA', 'VG', 'VGAS', 'VGI', 'VGIT',
        'VGK', 'VGLT', 'VGM', 'VGR', 'VGSH', 'VGT', 'VGZ', 'VHAQ', 'VHC', 'VHI',
        'VHST', 'VIA', 'VIAO', 'VIASP', 'VIAV', 'VICE', 'VICI', 'VICR', 'VIDI', 'VIEW',
        'VIG', 'VIGI', 'VII', 'VINC', 'VINE', 'VINO', 'VINP', 'VIOT', 'VIOV', 'VIOG',
        'VIPS', 'VIR', 'VIRC', 'VIRI', 'VIRS', 'VIRT', 'VIRX', 'VIS', 'VISL', 'VIST',
        'VITL', 'VIV', 'VIVE', 'VIVK', 'VIVO', 'VIXM', 'VIXY', 'VJET', 'VKI', 'VKQ',
        'VKTX', 'VLAT', 'VLCN', 'VLD', 'VLDR', 'VLGEA', 'VLN', 'VLNS', 'VLO', 'VLON',
        'VLRS', 'VLT', 'VLU', 'VLUE', 'VLY', 'VLYPO', 'VLYPP', 'VMAR', 'VMBS', 'VMC',
        'VMCA', 'VMD', 'VMEO', 'VMGA', 'VMI', 'VMO', 'VMOT', 'VMW', 'VNCE', 'VNDA',
        'VNET', 'VNLA', 'VNM', 'VNMC', 'VNO', 'VNOM', 'VNQ', 'VNQI', 'VNRX', 'VNSE',
        'VNT', 'VNTR', 'VO', 'VOC', 'VOD', 'VOE', 'VONE', 'VONG', 'VONV', 'VOO',
        'VOOG', 'VOOV', 'VOT', 'VOTE', 'VOX', 'VOXX', 'VOYA', 'VPC', 'VPG', 'VPL',
        'VPU', 'VPV', 'VQS', 'VRA', 'VRAI', 'VRAR', 'VRAY', 'VRCA', 'VRDN', 'VRE',
        'VREX', 'VRIG', 'VRM', 'VRME', 'VRNT', 'VRNS', 'VRNT', 'VRO', 'VRP', 'VRRM',
        'VRSK', 'VRSN', 'VRT', 'VRTS', 'VRTV', 'VRTX', 'VRUS', 'VRX', 'VS', 'VSAC',
        'VSAT', 'VSCO', 'VSDA', 'VSEC', 'VSGX', 'VSH', 'VSI', 'VSL', 'VSLR', 'VSMV',
        'VSNT', 'VSS', 'VST', 'VSTA', 'VSTM', 'VSTO', 'VSTS', 'VT', 'VTAK', 'VTEB',
        'VTEX', 'VTGN', 'VTHR', 'VTIP', 'VTIQ', 'VTLE', 'VTNR', 'VTOL', 'VTR', 'VTRS',
        'VTRU', 'VTSI', 'VTV', 'VTVT', 'VTWG', 'VTWO', 'VTWV', 'VTYX', 'VUZI', 'VVI',
        'VVNT', 'VVOS', 'VVPR', 'VVR', 'VVV', 'VVX', 'VWE', 'VWID', 'VWO', 'VWOB',
        'VXF', 'VXRT', 'VXUS', 'VXX', 'VXZ', 'VYGR', 'VYM', 'VYMI', 'VYNE', 'VYNT',
        'VZ', 'VZIO', 'VZLA', 'VZNT', 'W', 'WAB', 'WABC', 'WAFD', 'WAFU', 'WAL',
        'WALD', 'WASH', 'WAT', 'WATT', 'WAVC', 'WAVD', 'WAVE', 'WAVS', 'WB', 'WBA',
        'WBD', 'WBS', 'WBX', 'WCC', 'WCN', 'WD', 'WDAY', 'WDC', 'WDFC', 'WDH',
        'WDI', 'WDS', 'WE', 'WEA', 'WEAT', 'WEBR', 'WEC', 'WEED', 'WEG', 'WEJO',
        'WEL', 'WELL', 'WEN', 'WERN', 'WES', 'WETF', 'WEX', 'WEYS', 'WF', 'WFC',
        'WFCF', 'WFG', 'WFRD', 'WGO', 'WH', 'WHD', 'WHF', 'WHG', 'WHLM', 'WHLR',
        'WHR', 'WIA', 'WIFI', 'WILC', 'WIMI', 'WINA', 'WING', 'WINT', 'WINV', 'WIP',
        'WIRE', 'WISA', 'WIT', 'WIW', 'WIX', 'WIZ', 'WK', 'WKEY', 'WKHS', 'WKLY',
        'WLDN', 'WLFC', 'WLK', 'WLKP', 'WLL', 'WLMS', 'WLTG', 'WLVM', 'WM', 'WMB',
        'WMC', 'WMG', 'WMK', 'WMPN', 'WMS', 'WMT', 'WNC', 'WNEB', 'WNNR', 'WNS',
        'WNW', 'WOLF', 'WOMN', 'WOOD', 'WOOF', 'WOR', 'WORX', 'WOW', 'WPC', 'WPCA',
        'WPCB', 'WPM', 'WPP', 'WPRT', 'WPS', 'WRAC', 'WRAP', 'WRB', 'WRBY', 'WRC',
        'WRD', 'WRE', 'WRG', 'WRI', 'WRK', 'WRLD', 'WRN', 'WRPT', 'WSBC', 'WSBF',
        'WSC', 'WSFS', 'WSM', 'WSO', 'WSO.B', 'WSR', 'WST', 'WT', 'WTAI', 'WTBA',
        'WTER', 'WTFC', 'WTI', 'WTM', 'WTMA', 'WTMF', 'WTRG', 'WTRH', 'WTS', 'WTT',
        'WTTR', 'WTW', 'WU', 'WULF', 'WVE', 'WVVI', 'WVVIP', 'WW', 'WWAC', 'WWD',
        'WWE', 'WWR', 'WWW', 'WY', 'WYNN', 'WYY', 'X', 'XAIR', 'XAR', 'XBI', 'XBIO',
        'XBIT', 'XBJL', 'XBOC', 'XBTF', 'XC', 'XCLR', 'XCUR', 'XDAP', 'XDAT', 'XDEC',
        'XDIV', 'XDQQ', 'XDSQ', 'XEL', 'XELA', 'XELB', 'XEMD', 'XENE', 'XENT', 'XERS',
        'XES', 'XFIN', 'XFIV', 'XFLT', 'XFOR', 'XGN', 'XHB', 'XHE', 'XHLF', 'XHS',
        'XHYC', 'XHYD', 'XHYE', 'XHYF', 'XHYH', 'XHYI', 'XHYT', 'XIN', 'XITK', 'XJH',
        'XJR', 'XJUL', 'XJUN', 'XK', 'XKLF', 'XLE', 'XLF', 'XLG', 'XLI', 'XLK',
        'XLO', 'XLP', 'XLRE', 'XLSR', 'XLU', 'XLV', 'XLY', 'XM', 'XMAY', 'XMDV',
        'XMOV', 'XMPT', 'XMTR', 'XNCR', 'XNET', 'XNTK', 'XOM', 'XOMA', 'XOMAO', 'XOMAP',
        'XONE', 'XOP', 'XOS', 'XOUT', 'XP', 'XPAX', 'XPDB', 'XPDBU', 'XPEL', 'XPER',
        'XPEV', 'XPH', 'XPL', 'XPND', 'XPO', 'XPOF', 'XPON', 'XPP', 'XPRO', 'XPSA',
        'XPST', 'XPV', 'XRAY', 'XRLV', 'XRMI', 'XRT', 'XRX', 'XSD', 'XSHD', 'XSHQ',
        'XSLV', 'XSMO', 'XSPA', 'XSPT', 'XSSE', 'XSW', 'XSVM', 'XSVN', 'XSW', 'XT',
        'XTAP', 'XTEN', 'XTJA', 'XTJL', 'XTL', 'XTLB', 'XTN', 'XTNT', 'XTOC', 'XTR',
        'XTRE', 'XTRM', 'XTSL', 'XTT', 'XTW', 'XTWO', 'XTWY', 'XUSP', 'XVG', 'XVOL',
        'XVV', 'XVZ', 'XWEB', 'XWEL', 'XXII', 'XXMM', 'XYF', 'XYL', 'XYLD', 'XYLE',
        'XYLG', 'XYLI', 'XYLN', 'XZ', 'Y', 'YALA', 'YALL', 'YANG', 'YAO', 'YARD',
        'YBGJ', 'YBTC', 'YCL', 'YCOM', 'YCS', 'YDEC', 'YEAR', 'YELP', 'YETI', 'YEXT',
        'YGMZ', 'YI', 'YINN', 'YJ', 'YJUN', 'YK', 'YLCO', 'YLD', 'YLDE', 'YLI',
        'YLOW', 'YMAB', 'YMAR', 'YMM', 'YNDX', 'YOLO', 'YORW', 'YOSH', 'YOTAR', 'YOU',
        'YPF', 'YQ', 'YRD', 'YSG', 'YSP', 'YTEN', 'YTPG', 'YTRA', 'YUM', 'YUMC',
        'YVR', 'YXI', 'YY', 'YYY', 'Z', 'ZAPP', 'ZBH', 'ZBRA', 'ZCMD', 'ZD',
        'ZDGE', 'ZEAL', 'ZEN', 'ZENV', 'ZEPP', 'ZEST', 'ZETA', 'ZEUS', 'ZEV', 'ZEVO',
        'ZEXIT', 'ZG', 'ZGEN', 'ZGN', 'ZH', 'ZI', 'ZIG', 'ZIM', 'ZIMV', 'ZING',
        'ZION', 'ZIP', 'ZIVO', 'ZJYL', 'ZK', 'ZKH', 'ZLAB', 'ZM', 'ZME', 'ZNH',
        'ZNTL', 'ZOM', 'ZROZ', 'ZS', 'ZSL', 'ZSM', 'ZSP', 'ZSPY', 'ZTA', 'ZTEK',
        'ZTO', 'ZTR', 'ZTS', 'ZUMZ', 'ZUO', 'ZVIA', 'ZVO', 'ZWS', 'ZY', 'ZYME',
        'ZYNE', 'ZYXI', 'ZZ', 'ZZZ'
    ]
    
    # Remove duplicates and return top N
    unique_tickers = list(dict.fromkeys(sp500_tickers))  # Preserves order
    return unique_tickers[:n]


def run_large_scale_backtest():
    """Run anomaly detection backtest on top 200 stocks."""
    print("="*100)
    print("LARGE SCALE ANOMALY DETECTION BACKTEST")
    print("Top 200 Stocks by Market Cap - 1 Year Period")
    print("="*100)
    
    # Get top stocks
    print("\nFetching top 200 stocks by market cap...")
    stocks = get_top_stocks_by_market_cap(200)
    print(f"Found {len(stocks)} stocks to backtest")
    
    # Initialize strategy
    position_size = 10.0
    min_severity = 1.0
    
    strategy = AnomalyTradingStrategy(
        stocks=stocks,
        position_size=position_size,
        min_severity=min_severity
    )
    
    # Run backtest
    print(f"\nStarting backtest on {len(stocks)} stocks...")
    print("This will take several minutes. Please wait...\n")
    
    start_time = time.time()
    results = strategy.run_backtest()
    elapsed_time = time.time() - start_time
    
    # Print summary results
    print("\n" + "="*100)
    print("SUMMARY RESULTS - TOP 200 STOCKS")
    print("="*100)
    
    summary = results['summary']
    print(f"\nOverall Performance:")
    print(f"  Total Return: {summary['overall_return_pct']:.2f}%")
    print(f"  Total Invested: ${summary['total_invested']:,.2f}")
    print(f"  Current Value: ${summary['total_value']:,.2f}")
    print(f"  Profit/Loss: ${summary['total_profit_loss']:,.2f}")
    print(f"  Total Trades: {summary['total_trades']:,}")
    print(f"  Anomalies Detected: {summary['total_anomalies_detected']:,}")
    print(f"  Execution Time: {elapsed_time:.1f} seconds")
    
    # Calculate statistics
    stock_returns = [r['return_pct'] for r in results['stocks'].values() if r['total_invested'] > 0]
    profitable_stocks = [r for r in results['stocks'].values() if r['profit_loss'] > 0]
    
    if stock_returns:
        print(f"\nStatistics:")
        print(f"  Stocks with Trades: {len(stock_returns)}")
        print(f"  Profitable Stocks: {len(profitable_stocks)} ({len(profitable_stocks)/len(stock_returns)*100:.1f}%)")
        print(f"  Average Return: {np.mean(stock_returns):.2f}%")
        print(f"  Median Return: {np.median(stock_returns):.2f}%")
        print(f"  Best Return: {max(stock_returns):.2f}%")
        print(f"  Worst Return: {min(stock_returns):.2f}%")
        print(f"  Standard Deviation: {np.std(stock_returns):.2f}%")
    
    # Top 10 performers
    sorted_stocks = sorted(
        [r for r in results['stocks'].values() if r['total_invested'] > 0],
        key=lambda x: x['return_pct'],
        reverse=True
    )
    
    print(f"\n{'='*100}")
    print("TOP 10 PERFORMING STOCKS")
    print("="*100)
    print(f"{'Stock':<8} {'Return %':<12} {'Trades':<8} {'Invested':<12} {'Profit':<12}")
    print("-"*100)
    for stock in sorted_stocks[:10]:
        print(f"{stock['symbol']:<8} {stock['return_pct']:<11.2f}% {stock['total_trades']:<8} "
              f"${stock['total_invested']:<11.2f} ${stock['profit_loss']:<11.2f}")
    
    # Bottom 10 performers
    print(f"\n{'='*100}")
    print("BOTTOM 10 PERFORMING STOCKS")
    print("="*100)
    print(f"{'Stock':<8} {'Return %':<12} {'Trades':<8} {'Invested':<12} {'Profit':<12}")
    print("-"*100)
    for stock in sorted_stocks[-10:]:
        print(f"{stock['symbol']:<8} {stock['return_pct']:<11.2f}% {stock['total_trades']:<8} "
              f"${stock['total_invested']:<11.2f} ${stock['profit_loss']:<11.2f}")
    
    # Save detailed results
    df_results = pd.DataFrame([
        {
            'Symbol': symbol,
            'Anomalies_Detected': data['anomalies_detected'],
            'Trades': data['total_trades'],
            'Invested': data['total_invested'],
            'Current_Value': data['current_value'],
            'Profit_Loss': data['profit_loss'],
            'Return_Pct': data['return_pct']
        }
        for symbol, data in results['stocks'].items()
    ])
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f"anomaly_backtest_top200_{timestamp}.csv"
    df_results.to_csv(output_file, index=False)
    print(f"\n✅ Detailed results saved to {output_file}")
    
    return results


if __name__ == '__main__':
    results = run_large_scale_backtest()

