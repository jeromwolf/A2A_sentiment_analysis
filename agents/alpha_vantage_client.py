"""
Alpha Vantage API 클라이언트
무료 티어: 분당 5개 요청, 일일 100개 요청
"""
import os
import requests
import logging
from typing import Dict, Optional
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

class AlphaVantageClient:
    """Alpha Vantage API 클라이언트"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self.base_url = "https://www.alphavantage.co/query"
        
    def get_quote(self, symbol: str) -> Dict:
        """실시간 주가 정보 가져오기"""
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage Error: {data['Error Message']}")
                return {}
                
            if 'Note' in data:  # API 제한
                logger.warning(f"Alpha Vantage Note: {data['Note']}")
                return {}
                
            quote = data.get('Global Quote', {})
            
            if not quote:
                return {}
                
            # 데이터 변환
            return {
                'symbol': quote.get('01. symbol'),
                'open': float(quote.get('02. open', 0)),
                'high': float(quote.get('03. high', 0)),
                'low': float(quote.get('04. low', 0)),
                'price': float(quote.get('05. price', 0)),
                'volume': int(quote.get('06. volume', 0)),
                'latest_trading_day': quote.get('07. latest trading day'),
                'previous_close': float(quote.get('08. previous close', 0)),
                'change': float(quote.get('09. change', 0)),
                'change_percent': quote.get('10. change percent', '0%').replace('%', '')
            }
            
        except Exception as e:
            logger.error(f"Alpha Vantage 오류: {str(e)}")
            return {}
    
    def get_daily_adjusted(self, symbol: str, outputsize: str = 'compact') -> pd.DataFrame:
        """일별 조정 주가 데이터 가져오기"""
        try:
            params = {
                'function': 'TIME_SERIES_DAILY_ADJUSTED',
                'symbol': symbol,
                'outputsize': outputsize,  # 'compact' = 100일, 'full' = 20년
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage Error: {data['Error Message']}")
                return pd.DataFrame()
                
            if 'Note' in data:  # API 제한
                logger.warning(f"Alpha Vantage Note: {data['Note']}")
                return pd.DataFrame()
                
            time_series = data.get('Time Series (Daily)', {})
            
            if not time_series:
                return pd.DataFrame()
                
            # DataFrame으로 변환
            df = pd.DataFrame.from_dict(time_series, orient='index')
            df.index = pd.to_datetime(df.index)
            df = df.sort_index()
            
            # 컬럼명 정리
            df.columns = ['open', 'high', 'low', 'close', 'adjusted_close', 
                         'volume', 'dividend_amount', 'split_coefficient']
            
            # 숫자형으로 변환
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
                
            return df
            
        except Exception as e:
            logger.error(f"Alpha Vantage 일별 데이터 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_technical_indicators(self, symbol: str, indicator: str = 'RSI', 
                               interval: str = 'daily', time_period: int = 14) -> Dict:
        """기술적 지표 가져오기"""
        try:
            params = {
                'function': indicator,
                'symbol': symbol,
                'interval': interval,
                'time_period': time_period,
                'series_type': 'close',
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage Error: {data['Error Message']}")
                return {}
                
            if 'Note' in data:  # API 제한
                logger.warning(f"Alpha Vantage Note: {data['Note']}")
                return {}
                
            return data
            
        except Exception as e:
            logger.error(f"Alpha Vantage 기술적 지표 오류: {str(e)}")
            return {}
    
    def get_company_overview(self, symbol: str) -> Dict:
        """회사 개요 정보 가져오기"""
        try:
            params = {
                'function': 'OVERVIEW',
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(self.base_url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'Error Message' in data:
                logger.error(f"Alpha Vantage Error: {data['Error Message']}")
                return {}
                
            if 'Note' in data:  # API 제한
                logger.warning(f"Alpha Vantage Note: {data['Note']}")
                return {}
                
            return data
            
        except Exception as e:
            logger.error(f"Alpha Vantage 회사 정보 오류: {str(e)}")
            return {}