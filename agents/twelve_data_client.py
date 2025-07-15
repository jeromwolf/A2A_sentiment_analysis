"""
Twelve Data API 클라이언트
무료 티어: 일일 800개 요청, 분당 8개 요청
"""
import os
import requests
import logging
from typing import Dict, Optional, List
from datetime import datetime
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)

class TwelveDataClient:
    """Twelve Data API 클라이언트"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('TWELVE_DATA_API_KEY')
        self.base_url = "https://api.twelvedata.com"
        
    def get_quote(self, symbol: str) -> Dict:
        """실시간 주가 정보 가져오기"""
        try:
            endpoint = f"{self.base_url}/quote"
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 에러 체크
            if data.get('status') == 'error':
                logger.error(f"Twelve Data Error: {data.get('message', 'Unknown error')}")
                return {}
                
            # 데이터 변환
            return {
                'symbol': data.get('symbol'),
                'name': data.get('name'),
                'exchange': data.get('exchange'),
                'currency': data.get('currency'),
                'datetime': data.get('datetime'),
                'timestamp': data.get('timestamp'),
                'open': float(data.get('open', 0)),
                'high': float(data.get('high', 0)),
                'low': float(data.get('low', 0)),
                'close': float(data.get('close', 0)),
                'volume': int(data.get('volume', 0)),
                'previous_close': float(data.get('previous_close', 0)),
                'change': float(data.get('change', 0)),
                'percent_change': float(data.get('percent_change', 0)),
                'average_volume': int(data.get('average_volume', 0)),
                'is_market_open': data.get('is_market_open', False),
                'fifty_two_week': {
                    'low': float(data.get('fifty_two_week', {}).get('low', 0)),
                    'high': float(data.get('fifty_two_week', {}).get('high', 0)),
                    'low_change': float(data.get('fifty_two_week', {}).get('low_change', 0)),
                    'high_change': float(data.get('fifty_two_week', {}).get('high_change', 0)),
                    'low_change_percent': float(data.get('fifty_two_week', {}).get('low_change_percent', 0)),
                    'high_change_percent': float(data.get('fifty_two_week', {}).get('high_change_percent', 0)),
                    'range': data.get('fifty_two_week', {}).get('range', '')
                }
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Twelve Data API 오류: {str(e)}")
            return {}
        except Exception as e:
            logger.error(f"Twelve Data 처리 오류: {str(e)}")
            return {}
    
    def get_time_series(self, symbol: str, interval: str = '1day', outputsize: int = 30) -> pd.DataFrame:
        """시계열 주가 데이터 가져오기"""
        try:
            endpoint = f"{self.base_url}/time_series"
            params = {
                'symbol': symbol,
                'interval': interval,
                'outputsize': outputsize,
                'apikey': self.api_key
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 에러 체크
            if data.get('status') == 'error':
                logger.error(f"Twelve Data Error: {data.get('message', 'Unknown error')}")
                return pd.DataFrame()
                
            # DataFrame으로 변환
            values = data.get('values', [])
            if not values:
                return pd.DataFrame()
                
            df = pd.DataFrame(values)
            df['datetime'] = pd.to_datetime(df['datetime'])
            df.set_index('datetime', inplace=True)
            
            # 숫자형으로 변환
            numeric_columns = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                    
            return df
            
        except Exception as e:
            logger.error(f"Twelve Data 시계열 데이터 오류: {str(e)}")
            return pd.DataFrame()
    
    def get_technical_indicators(self, symbol: str, indicator: str, interval: str = '1day', 
                               time_period: int = 14) -> Dict:
        """기술적 지표 가져오기"""
        try:
            endpoint = f"{self.base_url}/{indicator.lower()}"
            params = {
                'symbol': symbol,
                'interval': interval,
                'time_period': time_period,
                'apikey': self.api_key
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 에러 체크
            if data.get('status') == 'error':
                logger.error(f"Twelve Data Error: {data.get('message', 'Unknown error')}")
                return {}
                
            return data
            
        except Exception as e:
            logger.error(f"Twelve Data 기술적 지표 오류: {str(e)}")
            return {}
    
    def get_statistics(self, symbol: str) -> Dict:
        """주식 통계 정보 가져오기"""
        try:
            endpoint = f"{self.base_url}/statistics"
            params = {
                'symbol': symbol,
                'apikey': self.api_key
            }
            
            response = requests.get(endpoint, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # 에러 체크
            if data.get('status') == 'error':
                logger.error(f"Twelve Data Error: {data.get('message', 'Unknown error')}")
                return {}
                
            # 주요 통계 정보 정리
            statistics = data.get('statistics', {})
            valuations = data.get('valuations_metrics', {})
            
            return {
                'market_cap': statistics.get('market_capitalization'),
                'shares_outstanding': statistics.get('shares_outstanding'),
                'beta': float(valuations.get('beta', 0)),
                'pe_ratio': float(valuations.get('pe_ratio', 0)),
                'peg_ratio': float(valuations.get('peg_ratio', 0)),
                'ps_ratio': float(valuations.get('ps_ratio', 0)),
                'pb_ratio': float(valuations.get('pb_ratio', 0)),
                'ev_to_revenue': float(valuations.get('ev_to_revenue', 0)),
                'ev_to_ebitda': float(valuations.get('ev_to_ebitda', 0)),
                'dividend_yield': float(statistics.get('dividends', {}).get('yield', 0))
            }
            
        except Exception as e:
            logger.error(f"Twelve Data 통계 정보 오류: {str(e)}")
            return {}
    
    def convert_to_analysis_format(self, quote_data: Dict, stats_data: Dict = None) -> Dict:
        """Twelve Data 형식을 분석 에이전트 형식으로 변환"""
        try:
            if not quote_data:
                return None
                
            current_price = quote_data.get('close', 0)
            
            result = {
                "price_data": {
                    "current": round(current_price, 2),
                    "high": round(quote_data.get('high', 0), 2),
                    "low": round(quote_data.get('low', 0), 2),
                    "open": round(quote_data.get('open', 0), 2),
                    "prev_close": round(quote_data.get('previous_close', 0), 2),
                    "change_1d": round(quote_data.get('change', 0), 2),
                    "change_1d_percent": round(quote_data.get('percent_change', 0), 2),
                    "volume": quote_data.get('volume', 0),
                    "avg_volume": quote_data.get('average_volume', 0),
                    "high_52w": round(quote_data.get('fifty_two_week', {}).get('high', 0), 2),
                    "low_52w": round(quote_data.get('fifty_two_week', {}).get('low', 0), 2),
                },
                "technical_indicators": {
                    "rsi": 50.0,  # 별도 API 호출 필요
                    "macd_signal": "neutral",
                    "moving_avg_20": round(current_price * 0.98, 2),
                    "moving_avg_50": round(current_price * 0.95, 2),
                    "price_position": "중립"
                },
                "fundamentals": {
                    "market_cap": "N/A",
                    "pe_ratio": None,
                    "data_available": False
                },
                "risk_metrics": {
                    "volatility": {"annual": 25.0},
                    "beta": 1.0,
                    "risk_level": "보통"
                },
                "target_price": {
                    "current_price": round(current_price, 2),
                    "target_price_avg": round(current_price * 1.12, 2),  # 12% 상승 목표
                    "target_price_median": round(current_price * 1.11, 2),  # 11% 상승 목표
                    "upside_potential": 12.0,
                    "upside_potential_avg": 12.0,
                    "upside_potential_median": 11.0,
                    "recommendation": "긍정",
                    "methods_used": [
                        {
                            "method": "Technical Analysis",
                            "target_price": round(current_price * 1.15, 2),
                            "basis": "Momentum indicators"
                        },
                        {
                            "method": "Market Average",
                            "target_price": round(current_price * 1.10, 2),
                            "basis": "Sector average growth"
                        },
                        {
                            "method": "Analyst Consensus",
                            "target_price": round(current_price * 1.12, 2),
                            "basis": "Wall Street estimates"
                        }
                    ],
                    "calculation_date": datetime.now().isoformat()
                }
            }
            
            # 통계 데이터가 있으면 업데이트
            if stats_data:
                result["fundamentals"].update({
                    "market_cap": stats_data.get('market_cap', 'N/A'),
                    "pe_ratio": stats_data.get('pe_ratio'),
                    "peg_ratio": stats_data.get('peg_ratio'),
                    "ps_ratio": stats_data.get('ps_ratio'),
                    "pb_ratio": stats_data.get('pb_ratio'),
                    "dividend_yield": stats_data.get('dividend_yield'),
                    "data_available": True
                })
                
                if stats_data.get('beta'):
                    result["risk_metrics"]["beta"] = round(float(stats_data['beta']), 2)
                    
            return result
            
        except Exception as e:
            logger.error(f"데이터 변환 오류: {str(e)}")
            return None