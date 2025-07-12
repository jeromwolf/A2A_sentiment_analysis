"""
정량적 데이터 분석 에이전트 V2 - A2A 프로토콜 기반
주가, 기술적 지표, 재무제표 등 정량적 데이터를 분석하는 에이전트
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np
import requests

from fastapi import FastAPI, Depends
from contextlib import asynccontextmanager
from pydantic import BaseModel

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType

# 설정 관리자 및 커스텀 에러 임포트
from utils.config_manager import config
from utils.errors import APITimeoutError, DataNotFoundError
from utils.rate_limiter import rate_limited
from utils.auth import verify_api_key

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantitativeAgentV2(BaseAgent):
    """정량적 데이터 분석 A2A 에이전트"""
    
    def __init__(self):
        # 설정에서 에이전트 정보 가져오기
        agent_config = config.get_agent_config("quantitative")
        
        super().__init__(
            name=agent_config.get("name", "Quantitative Analysis Agent V2"),
            description="주가, 기술적 지표, 재무제표 등 정량적 데이터를 분석하는 A2A 에이전트",
            port=agent_config.get("port", 8211)
        )
        
        # 타임아웃 및 설정
        self.timeout = agent_config.get("timeout", 30)
        self.default_period = agent_config.get("period", "1mo")
        self.indicators = agent_config.get("indicators", ["rsi", "macd", "moving_averages"])
        
        # 더미 데이터 사용 여부
        self.use_mock_data = config.is_mock_data_enabled()
        logger.info(f"🔍 Mock data 설정: {self.use_mock_data} (USE_MOCK_DATA={os.getenv('USE_MOCK_DATA')})")
        
        # Finnhub API 설정
        self.finnhub_api_key = config.get_env("FINNHUB_API_KEY")
        self.finnhub_base_url = "https://finnhub.io/api/v1"
        self.capabilities = [
            {
                "name": "quantitative_analysis",
                "version": "2.0",
                "description": "주식의 정량적 데이터 분석",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string", "description": "주식 티커"},
                        "period": {"type": "string", "description": "분석 기간", "default": "1mo"}
                    },
                    "required": ["ticker"]
                },
                "output_schema": {
                    "type": "object",
                    "properties": {
                        "price_data": {"type": "object"},
                        "technical_indicators": {"type": "object"},
                        "fundamentals": {"type": "object"},
                        "risk_metrics": {"type": "object"}
                    }
                }
            }
        ]
        
        # HTTP 엔드포인트 추가
        self._setup_http_endpoints()
    
    def _setup_http_endpoints(self):
        """HTTP 엔드포인트 설정"""
        from pydantic import BaseModel
        
        class QuantitativeRequest(BaseModel):
            ticker: str
            period: str = "1mo"
        
        @self.app.post("/quantitative_analysis", dependencies=[Depends(verify_api_key)])
        async def quantitative_analysis(request: QuantitativeRequest):
            """HTTP 엔드포인트로 정량적 분석 수행"""
            logger.info(f"📊 HTTP 요청으로 정량적 분석: {request.ticker}")
            
            # 분석 수행
            analysis_result = await self._analyze_quantitative_data(request.ticker, request.period)
            
            return {
                "ticker": request.ticker,
                "analysis": analysis_result,
                "analysis_date": datetime.now().isoformat()
            }
    
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            action = message.body.get("action")
            logger.info(f"🔍 메시지 수신 - Type: {message.header.message_type}, Action: {action}")
            
            # 이벤트 메시지는 무시
            if message.header.message_type == MessageType.EVENT:
                return
            
            # 요청 메시지 처리
            if message.header.message_type == MessageType.REQUEST and action == "quantitative_analysis":
                payload = message.body.get("payload", {})
                ticker = payload.get("ticker")
                period = payload.get("period", "1mo")
                
                if not ticker:
                    await self.reply_to_message(
                        message,
                        result={"error": "티커가 제공되지 않았습니다"},
                        success=False
                    )
                    return
                
                logger.info(f"📊 정량적 분석 시작: {ticker} (기간: {period})")
                
                # 정량적 데이터 분석 수행
                analysis_result = await self._analyze_quantitative_data(ticker, period)
                
                # 응답 전송
                response_data = {
                    "ticker": ticker,
                    "analysis_date": datetime.now().isoformat(),
                    **analysis_result
                }
                
                # 이벤트 브로드캐스트
                await self._broadcast_analysis_complete(ticker, analysis_result)
                
                # 응답 메시지 생성
                await self.reply_to_message(
                    message,
                    result=response_data,
                    success=True
                )
                
        except Exception as e:
            logger.error(f"❌ 정량적 분석 실패: {str(e)}")
            await self.reply_to_message(
                message,
                result={"error": str(e)},
                success=False
            )
    
    @rate_limited("finnhub")
    async def _analyze_quantitative_data(self, ticker: str, period: str) -> Dict:
        """정량적 데이터 분석 수행"""
        # 더미 데이터 사용 모드인 경우
        if self.use_mock_data:
            logger.info(f"🎭 더미 데이터 모드 활성화 - 모의 정량 데이터 반환")
            return self._get_mock_data(ticker)
            
        try:
            # Finnhub API 사용
            logger.info(f"📊 {ticker} Finnhub 데이터 수집 시작...")
            finnhub_data = self._get_finnhub_data(ticker)
            
            # 데이터 검증
            if not finnhub_data or not finnhub_data.get('quote'):
                logger.warning(f"⚠️ {ticker} 데이터를 가져올 수 없습니다")
                raise DataNotFoundError("Finnhub data", ticker)
                
            # Finnhub 데이터로 분석 수행
            # 1. 가격 데이터 분석
            price_data = self._analyze_finnhub_price_data(finnhub_data)
            
            # 2. 기술적 지표 계산
            technical_indicators = self._calculate_finnhub_technical_indicators(finnhub_data)
            
            # 3. 재무 데이터 분석
            fundamentals = self._analyze_finnhub_fundamentals(finnhub_data)
            
            # 4. 리스크 지표 계산 (캔들 데이터 사용)
            risk_metrics = self._calculate_finnhub_risk_metrics(finnhub_data)
            
            # 목표주가 계산
            target_price_info = self._calculate_finnhub_target_price(finnhub_data, price_data, fundamentals)
            
            return {
                "price_data": price_data,
                "technical_indicators": technical_indicators,
                "fundamentals": fundamentals,
                "risk_metrics": risk_metrics,
                "target_price": target_price_info  # 새로 추가
            }
            
        except Exception as e:
            logger.error(f"분석 중 오류 발생: {str(e)}", exc_info=True)
            # Rate limit 오류인 경우 명시적으로 표시
            if "429" in str(e) or "Too Many Requests" in str(e):
                raise APITimeoutError("yahoo_finance", f"Yahoo Finance rate limit exceeded for {ticker}")
            else:
                # 다른 오류의 경우 재시도 없이 실패
                raise DataNotFoundError("quantitative_data", ticker)
    
    def _analyze_price_data(self, stock: yf.Ticker, period: str) -> Dict:
        """가격 데이터 분석"""
        try:
            # 기간별 가격 데이터 먼저 가져오기 (info보다 안정적)
            hist = stock.history(period=period)
            if hist.empty:
                return {"error": "가격 데이터를 가져올 수 없습니다"}
            
            # 현재 가격은 최신 종가 사용
            current_price = float(hist['Close'].iloc[-1])
            
            # info는 rate limit 에러가 자주 발생하므로 try-except로 처리
            try:
                info = stock.info
                high_52w = float(info.get('fiftyTwoWeekHigh', 0))
                low_52w = float(info.get('fiftyTwoWeekLow', 0))
            except:
                # info 접근 실패 시 history 데이터에서 계산
                hist_1y = stock.history(period="1y")
                if not hist_1y.empty:
                    high_52w = float(hist_1y['High'].max())
                    low_52w = float(hist_1y['Low'].min())
                else:
                    high_52w = float(hist['High'].max())
                    low_52w = float(hist['Low'].min())
            
            # 변화율 계산
            close_prices = hist['Close']
            change_1d = ((close_prices[-1] - close_prices[-2]) / close_prices[-2] * 100) if len(close_prices) > 1 else 0
            change_1w = ((close_prices[-1] - close_prices[-min(5, len(close_prices))]) / close_prices[-min(5, len(close_prices))] * 100) if len(close_prices) > 5 else 0
            change_1m = ((close_prices[-1] - close_prices[0]) / close_prices[0] * 100) if len(close_prices) > 20 else 0
            
            return {
                "current": round(current_price, 2),
                "high_52w": round(high_52w, 2),
                "low_52w": round(low_52w, 2),
                "change_1d": round(float(change_1d), 2),
                "change_1w": round(float(change_1w), 2),
                "change_1m": round(float(change_1m), 2),
                "volume": int(hist['Volume'][-1]) if not hist.empty else 0,
                "avg_volume": int(hist['Volume'].mean()) if not hist.empty else 0
            }
        except Exception as e:
            logger.error(f"가격 데이터 분석 오류: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_technical_indicators(self, stock: yf.Ticker, period: str) -> Dict:
        """기술적 지표 계산"""
        try:
            hist = stock.history(period="3mo")  # 더 긴 기간 데이터 필요
            if hist.empty:
                return {"error": "기술적 지표 계산을 위한 데이터가 부족합니다"}
            
            close_prices = hist['Close']
            
            # RSI 계산
            rsi = self._calculate_rsi(close_prices)
            
            # 이동평균
            ma_20 = float(close_prices.rolling(window=20).mean().iloc[-1]) if len(close_prices) >= 20 else float(close_prices.mean())
            ma_50 = float(close_prices.rolling(window=50).mean().iloc[-1]) if len(close_prices) >= 50 else float(close_prices.mean())
            ma_200 = float(close_prices.rolling(window=200).mean().iloc[-1]) if len(close_prices) >= 200 else None
            
            # MACD
            macd_signal = self._calculate_macd_signal(close_prices)
            
            # 볼린저 밴드
            bb_upper, bb_lower = self._calculate_bollinger_bands(close_prices)
            
            return {
                "rsi": round(float(rsi), 2),
                "macd_signal": macd_signal,
                "moving_avg_20": round(ma_20, 2),
                "moving_avg_50": round(ma_50, 2),
                "moving_avg_200": round(ma_200, 2) if ma_200 else None,
                "bollinger_upper": round(float(bb_upper), 2),
                "bollinger_lower": round(float(bb_lower), 2),
                "price_position": self._determine_price_position(float(close_prices.iloc[-1]), ma_20, ma_50)
            }
        except Exception as e:
            logger.error(f"기술적 지표 계산 오류: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_fundamentals(self, stock: yf.Ticker) -> Dict:
        """재무 데이터 분석"""
        try:
            info = stock.info
            
            # Rate limit 오류가 발생한 경우
            if not info or 'error' in info:
                logger.warning("재무 데이터 접근 실패 - 기본값 사용")
                return {
                    "market_cap": "N/A",
                    "pe_ratio": None,
                    "forward_pe": None,
                    "peg_ratio": None,
                    "ps_ratio": None,
                    "pb_ratio": None,
                    "dividend_yield": None,
                    "earnings_growth": None,
                    "revenue_growth": None,
                    "profit_margin": None,
                    "debt_to_equity": None,
                    "data_available": False
                }
            
            return {
                "market_cap": self._format_large_number(info.get('marketCap', 0)),
                "pe_ratio": round(float(info.get('trailingPE', 0)), 2) if info.get('trailingPE') else None,
                "forward_pe": round(float(info.get('forwardPE', 0)), 2) if info.get('forwardPE') else None,
                "peg_ratio": round(float(info.get('pegRatio', 0)), 2) if info.get('pegRatio') else None,
                "ps_ratio": round(float(info.get('priceToSalesTrailing12Months', 0)), 2) if info.get('priceToSalesTrailing12Months') else None,
                "pb_ratio": round(float(info.get('priceToBook', 0)), 2) if info.get('priceToBook') else None,
                "dividend_yield": round(float(info.get('dividendYield', 0)) * 100, 2) if info.get('dividendYield') else 0,
                "earnings_growth": round(float(info.get('earningsQuarterlyGrowth', 0)) * 100, 2) if info.get('earningsQuarterlyGrowth') else None,
                "revenue_growth": round(float(info.get('revenueQuarterlyGrowth', 0)) * 100, 2) if info.get('revenueQuarterlyGrowth') else None,
                "profit_margin": round(float(info.get('profitMargins', 0)) * 100, 2) if info.get('profitMargins') else None,
                "debt_to_equity": round(float(info.get('debtToEquity', 0)) / 100, 2) if info.get('debtToEquity') else None,
                "data_available": True
            }
        except Exception as e:
            logger.error(f"재무 데이터 분석 오류: {str(e)}")
            return {
                "market_cap": "N/A",
                "pe_ratio": None,
                "forward_pe": None,
                "peg_ratio": None,
                "ps_ratio": None,
                "pb_ratio": None,
                "dividend_yield": None,
                "earnings_growth": None,
                "revenue_growth": None,
                "profit_margin": None,
                "debt_to_equity": None,
                "data_available": False,
                "error": str(e)
            }
    
    def _calculate_risk_metrics(self, stock: yf.Ticker, period: str) -> Dict:
        """리스크 지표 계산"""
        try:
            hist = stock.history(period="1y")  # 1년 데이터로 계산
            if hist.empty:
                return {"error": "리스크 지표 계산을 위한 데이터가 부족합니다"}
            
            # 일별 수익률
            returns = hist['Close'].pct_change().dropna()
            
            # 변동성 (연환산)
            daily_volatility = returns.std()
            annual_volatility = daily_volatility * np.sqrt(252)
            
            # VaR (95% 신뢰수준)
            var_95 = np.percentile(returns, 5)
            
            # 최대 낙폭
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.cummax()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # 샤프 비율 (무위험 수익률 2% 가정)
            risk_free_rate = 0.02
            excess_returns = returns.mean() * 252 - risk_free_rate
            sharpe_ratio = excess_returns / annual_volatility if annual_volatility > 0 else 0
            
            # 베타 (S&P 500 대비) - 동기 함수를 유지하되 내부적으로 처리
            beta = None  # Rate limit 때문에 베타 계산은 생략하거나 캐시 사용
            
            return {
                "volatility": {
                    "daily": round(float(daily_volatility) * 100, 2),
                    "monthly": round(float(daily_volatility * np.sqrt(21)) * 100, 2),
                    "annual": round(float(annual_volatility) * 100, 2)
                },
                "var_95": round(float(var_95) * 100, 2),
                "max_drawdown": round(float(max_drawdown) * 100, 2),
                "sharpe_ratio": round(float(sharpe_ratio), 2),
                "beta": round(float(beta), 2) if beta else None,
                "risk_level": self._determine_risk_level(annual_volatility)
            }
        except Exception as e:
            logger.error(f"리스크 지표 계산 오류: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """RSI 계산"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50
    
    def _calculate_macd_signal(self, prices: pd.Series) -> str:
        """MACD 신호 계산"""
        exp1 = prices.ewm(span=12, adjust=False).mean()
        exp2 = prices.ewm(span=26, adjust=False).mean()
        macd = exp1 - exp2
        signal = macd.ewm(span=9, adjust=False).mean()
        
        if macd.iloc[-1] > signal.iloc[-1]:
            return "bullish"
        else:
            return "bearish"
    
    def _calculate_bollinger_bands(self, prices: pd.Series, period: int = 20) -> tuple:
        """볼린저 밴드 계산"""
        ma = prices.rolling(window=period).mean()
        std = prices.rolling(window=period).std()
        upper = ma + (std * 2)
        lower = ma - (std * 2)
        return upper.iloc[-1], lower.iloc[-1]
    
    @rate_limited("yahoo_finance")
    async def _calculate_beta_async(self, ticker: str) -> Optional[float]:
        """베타 계산 (S&P 500 대비) - 비동기 버전"""
        try:
            stock = yf.Ticker(ticker)
            spy = yf.Ticker("SPY")
            
            stock_hist = stock.history(period="1y")['Close']
            spy_hist = spy.history(period="1y")['Close']
            
            stock_returns = stock_hist.pct_change().dropna()
            spy_returns = spy_hist.pct_change().dropna()
            
            # 날짜 맞추기
            common_dates = stock_returns.index.intersection(spy_returns.index)
            stock_returns = stock_returns[common_dates]
            spy_returns = spy_returns[common_dates]
            
            covariance = np.cov(stock_returns, spy_returns)[0][1]
            spy_variance = np.var(spy_returns)
            
            return covariance / spy_variance if spy_variance > 0 else None
        except:
            return None
    
    def _determine_price_position(self, current_price: float, ma_20: float, ma_50: float) -> str:
        """가격 위치 판단"""
        if current_price > ma_20 and current_price > ma_50:
            return "강세"
        elif current_price < ma_20 and current_price < ma_50:
            return "약세"
        else:
            return "중립"
    
    def _determine_risk_level(self, volatility: float) -> str:
        """리스크 수준 판단"""
        if volatility < 0.15:
            return "낮음"
        elif volatility < 0.25:
            return "보통"
        elif volatility < 0.35:
            return "높음"
        else:
            return "매우 높음"
    
    def _format_large_number(self, num: float) -> str:
        """큰 숫자 포맷팅"""
        if num >= 1e12:
            return f"{num/1e12:.2f}T"
        elif num >= 1e9:
            return f"{num/1e9:.2f}B"
        elif num >= 1e6:
            return f"{num/1e6:.2f}M"
        else:
            return str(int(num))
    
    def _calculate_target_price(self, stock: yf.Ticker, price_data: Dict, fundamentals: Dict) -> Dict:
        """목표주가 산정 - 여러 방법론을 사용하여 종합적으로 계산"""
        try:
            info = stock.info
            current_price = price_data.get('current', 0)
            
            if current_price == 0:
                return {"error": "현재가 정보 없음"}
            
            target_prices = []
            methods_used = []
            
            # 1. PER 멀티플 방식
            pe_ratio = fundamentals.get('pe_ratio')
            if pe_ratio and pe_ratio > 0:
                # 산업 평균 PER을 가정 (실제로는 별도 데이터 필요)
                industry_avg_pe = 20  # 기본값
                eps = current_price / pe_ratio
                
                # 성장률 반영
                growth_rate = fundamentals.get('earnings_growth', 10) / 100
                adjusted_pe = industry_avg_pe * (1 + growth_rate)
                
                target_price_per = eps * adjusted_pe
                target_prices.append(target_price_per)
                methods_used.append({
                    "method": "PER Multiple",
                    "target_price": round(target_price_per, 2),
                    "pe_used": round(adjusted_pe, 2)
                })
            
            # 2. PEG 기반 목표주가
            peg_ratio = fundamentals.get('peg_ratio')
            if peg_ratio and peg_ratio > 0 and pe_ratio:
                # PEG 1.0을 적정 수준으로 가정
                fair_pe = growth_rate * 100  # 성장률과 동일한 PER
                target_price_peg = (current_price / pe_ratio) * fair_pe
                target_prices.append(target_price_peg)
                methods_used.append({
                    "method": "PEG Valuation",
                    "target_price": round(target_price_peg, 2),
                    "fair_peg": 1.0
                })
            
            # 3. PBR 기반 목표주가
            pb_ratio = fundamentals.get('pb_ratio')
            if pb_ratio and pb_ratio > 0:
                # ROE 기반 적정 PBR 계산
                roe = info.get('returnOnEquity', 0.15) * 100  # 기본 ROE 15%
                fair_pbr = roe / 10  # 간단한 공식: ROE/10
                book_value_per_share = current_price / pb_ratio
                
                target_price_pbr = book_value_per_share * fair_pbr
                target_prices.append(target_price_pbr)
                methods_used.append({
                    "method": "PBR-ROE Model",
                    "target_price": round(target_price_pbr, 2),
                    "fair_pbr": round(fair_pbr, 2)
                })
            
            # 4. 기술적 분석 기반 (52주 최고가 대비)
            high_52w = price_data.get('high_52w', 0)
            if high_52w > 0:
                # 52주 최고가의 95%를 목표로
                target_price_technical = high_52w * 0.95
                target_prices.append(target_price_technical)
                methods_used.append({
                    "method": "Technical (52W High)",
                    "target_price": round(target_price_technical, 2),
                    "basis": "95% of 52-week high"
                })
            
            # 목표주가 종합
            if target_prices:
                # 평균 목표주가 계산
                avg_target_price = sum(target_prices) / len(target_prices)
                
                # 중간값 계산
                sorted_prices = sorted(target_prices)
                median_target_price = sorted_prices[len(sorted_prices)//2]
                
                # 상승 여력 계산
                upside_avg = ((avg_target_price / current_price) - 1) * 100
                upside_median = ((median_target_price / current_price) - 1) * 100
                
                # 투자 의견 결정
                if upside_avg > 20:
                    recommendation = "Strong Buy"
                elif upside_avg > 10:
                    recommendation = "Buy"
                elif upside_avg > -5:
                    recommendation = "Hold"
                elif upside_avg > -15:
                    recommendation = "Sell"
                else:
                    recommendation = "Strong Sell"
                
                return {
                    "current_price": round(current_price, 2),
                    "target_price_avg": round(avg_target_price, 2),
                    "target_price_median": round(median_target_price, 2),
                    "upside_potential_avg": round(upside_avg, 1),
                    "upside_potential_median": round(upside_median, 1),
                    "recommendation": recommendation,
                    "methods_used": methods_used,
                    "calculation_date": datetime.now().isoformat()
                }
            else:
                return {
                    "error": "목표주가 계산에 필요한 데이터 부족",
                    "current_price": round(current_price, 2)
                }
                
        except Exception as e:
            logger.error(f"목표주가 계산 오류: {str(e)}")
            return {"error": f"목표주가 계산 실패: {str(e)}"}
    
    async def _broadcast_analysis_complete(self, ticker: str, result: Dict):
        """분석 완료 이벤트 브로드캐스트"""
        event_data = {
            "ticker": ticker,
            "has_price_data": bool(result.get("price_data")),
            "has_technical": bool(result.get("technical_indicators")),
            "has_fundamentals": bool(result.get("fundamentals")),
            "has_risk_metrics": bool(result.get("risk_metrics")),
            "timestamp": datetime.now().isoformat()
        }
        
        await self.broadcast_event("quantitative_analysis_complete", event_data)
        logger.info(f"📢 정량적 분석 완료 이벤트 브로드캐스트: {ticker}")
    
    def _get_finnhub_data(self, ticker: str) -> Dict:
        """Finnhub API를 통해 실시간 데이터 가져오기"""
        try:
            # 1. 실시간 가격 정보
            quote_url = f"{self.finnhub_base_url}/quote?symbol={ticker}&token={self.finnhub_api_key}"
            quote_response = requests.get(quote_url, timeout=10)
            quote_response.raise_for_status()
            quote_data = quote_response.json()
            
            # 2. 기본 재무 지표
            metric_url = f"{self.finnhub_base_url}/stock/metric?symbol={ticker}&metric=all&token={self.finnhub_api_key}"
            metric_response = requests.get(metric_url, timeout=10)
            metric_response.raise_for_status()
            metric_data = metric_response.json()
            
            # 3. 캔들 데이터 (기술적 분석용)
            to_timestamp = int(datetime.now().timestamp())
            from_timestamp = int((datetime.now() - timedelta(days=30)).timestamp())
            candle_url = f"{self.finnhub_base_url}/stock/candle?symbol={ticker}&resolution=D&from={from_timestamp}&to={to_timestamp}&token={self.finnhub_api_key}"
            
            logger.info(f"Candle URL: {candle_url}")
            
            try:
                candle_response = requests.get(candle_url, timeout=10)
                candle_response.raise_for_status()
                candle_data = candle_response.json()
            except:
                # 캔들 데이터 실패 시 빈 데이터 반환
                logger.warning(f"캔들 데이터 수집 실패 - 기본값 사용")
                candle_data = {"s": "no_data", "c": [], "h": [], "l": [], "o": [], "v": []}
            
            return {
                "quote": quote_data,
                "metrics": metric_data,
                "candles": candle_data
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Finnhub API 오류: {str(e)}")
            raise APITimeoutError("finnhub", str(e))
        except Exception as e:
            logger.error(f"Finnhub 데이터 처리 오류: {str(e)}")
            raise DataNotFoundError("finnhub_data", ticker)
    
    def _get_mock_data(self, ticker: str) -> Dict:
        """실제 데이터를 가져올 수 없을 때 기본 모의 데이터 반환"""
        import random
        
        # 티커별 기본 가격 설정
        base_prices = {
            "TSLA": 250.0,
            "AAPL": 195.0,
            "NVDA": 900.0,
            "GOOGL": 150.0,
            "MSFT": 420.0,
            "META": 500.0,
            "AMZN": 180.0,
            "PLTR": 25.0
        }
        
        base_price = base_prices.get(ticker.upper(), 100.0)
        day_change_percent = random.uniform(-3, 3)
        
        return {
            "price_data": {
                "current_price": base_price,
                "day_change": base_price * day_change_percent / 100,
                "day_change_percent": day_change_percent,
                "week_change_percent": random.uniform(-5, 5),
                "month_change_percent": random.uniform(-10, 10),
                "year_change_percent": random.uniform(-20, 50),
                "week_52_high": base_price * 1.2,
                "week_52_low": base_price * 0.8,
                "volume": random.randint(10000000, 100000000),
                "avg_volume": random.randint(20000000, 80000000)
            },
            "technical_indicators": {
                "rsi": random.uniform(30, 70),
                "macd_signal": random.choice(["Buy", "Sell", "Hold"]),
                "moving_avg_20": base_price * 0.98,
                "moving_avg_50": base_price * 0.95,
                "moving_avg_200": base_price * 0.9,
                "bollinger_upper": base_price * 1.05,
                "bollinger_lower": base_price * 0.95,
                "price_position": "Above MA20"
            },
            "fundamentals": {
                "market_cap": f"{random.uniform(50, 3000):.1f}B",
                "pe_ratio": random.uniform(15, 50),
                "forward_pe": random.uniform(12, 45),
                "peg_ratio": random.uniform(0.5, 3),
                "ps_ratio": random.uniform(2, 15),
                "pb_ratio": random.uniform(2, 20),
                "dividend_yield": random.uniform(0, 3),
                "earnings_growth": random.uniform(-5, 25),
                "revenue_growth": random.uniform(-5, 30),
                "profit_margin": random.uniform(5, 35),
                "roe": random.uniform(5, 40),
                "debt_to_equity": random.uniform(0.2, 2)
            },
            "risk_metrics": {
                "beta": random.uniform(0.5, 2),
                "volatility_30d": random.uniform(0.01, 0.05),
                "sharpe_ratio": random.uniform(0.5, 2.5),
                "max_drawdown": -random.uniform(0.05, 0.25),
                "var_95": -random.uniform(0.02, 0.05),
                "market_correlation": random.uniform(0.5, 0.95)
            },
            "target_price": {
                "current_price": base_price,
                "target_price_avg": base_price * random.uniform(1.1, 1.3),
                "target_price_median": base_price * random.uniform(1.05, 1.25),
                "upside_potential_avg": random.uniform(10, 30),
                "upside_potential_median": random.uniform(5, 25),
                "recommendation": random.choice(["Strong Buy", "Buy", "Hold", "Sell"]),
                "methods_used": [
                    {"method": "PER Multiple", "target_price": base_price * 1.2},
                    {"method": "PEG Valuation", "target_price": base_price * 1.15},
                    {"method": "Technical", "target_price": base_price * 1.1}
                ],
                "calculation_date": datetime.now().isoformat()
            }
        }
    
    def _analyze_finnhub_price_data(self, finnhub_data: Dict) -> Dict:
        """Finnhub 가격 데이터 분석"""
        try:
            quote = finnhub_data.get('quote', {})
            metrics = finnhub_data.get('metrics', {}).get('metric', {})
            
            current_price = quote.get('c', 0)  # Current price
            prev_close = quote.get('pc', 0)  # Previous close
            change = current_price - prev_close if prev_close else 0
            change_percent = quote.get('dp', 0)  # Percent change
            
            return {
                "current": round(current_price, 2),
                "high_52w": round(metrics.get('52WeekHigh', 0), 2),
                "low_52w": round(metrics.get('52WeekLow', 0), 2),
                "change_1d": round(change, 2),
                "change_1d_percent": round(change_percent, 2),
                "high": round(quote.get('h', 0), 2),  # Day high
                "low": round(quote.get('l', 0), 2),   # Day low
                "open": round(quote.get('o', 0), 2),  # Open price
                "volume": None,  # Finnhub quote API doesn't provide volume
                "prev_close": round(prev_close, 2)
            }
        except Exception as e:
            logger.error(f"Finnhub 가격 데이터 분석 오류: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_finnhub_technical_indicators(self, finnhub_data: Dict) -> Dict:
        """Finnhub 기술적 지표 계산"""
        try:
            candles = finnhub_data.get('candles', {})
            
            if candles.get('s') != 'ok' or not candles.get('c'):
                # 캔들 데이터가 없는 경우 기본값 반환
                return {
                    "rsi": 50.0,
                    "macd_signal": "neutral",
                    "moving_avg_20": None,
                    "moving_avg_50": None,
                    "bollinger_upper": None,
                    "bollinger_lower": None,
                    "price_position": "데이터 없음"
                }
            
            # 종가 데이터로 pandas Series 생성
            close_prices = pd.Series(candles['c'])
            
            # RSI 계산
            rsi = self._calculate_rsi(close_prices)
            
            # 이동평균
            ma_20 = float(close_prices.rolling(window=20).mean().iloc[-1]) if len(close_prices) >= 20 else float(close_prices.mean())
            ma_50 = float(close_prices.rolling(window=50).mean().iloc[-1]) if len(close_prices) >= 50 else float(close_prices.mean())
            
            # MACD
            macd_signal = self._calculate_macd_signal(close_prices)
            
            # 볼린저 밴드
            bb_upper, bb_lower = self._calculate_bollinger_bands(close_prices)
            
            current_price = close_prices.iloc[-1]
            
            return {
                "rsi": round(float(rsi), 2),
                "macd_signal": macd_signal,
                "moving_avg_20": round(ma_20, 2),
                "moving_avg_50": round(ma_50, 2),
                "bollinger_upper": round(float(bb_upper), 2),
                "bollinger_lower": round(float(bb_lower), 2),
                "price_position": self._determine_price_position(float(current_price), ma_20, ma_50)
            }
        except Exception as e:
            logger.error(f"Finnhub 기술적 지표 계산 오류: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_finnhub_fundamentals(self, finnhub_data: Dict) -> Dict:
        """Finnhub 재무 데이터 분석"""
        try:
            metrics = finnhub_data.get('metrics', {}).get('metric', {})
            
            return {
                "market_cap": self._format_large_number(metrics.get('marketCapitalization', 0) * 1000000),  # M to actual
                "pe_ratio": round(metrics.get('peNormalizedAnnual', 0), 2) if metrics.get('peNormalizedAnnual') else None,
                "forward_pe": None,  # Finnhub doesn't provide forward PE
                "peg_ratio": round(metrics.get('pegRatio', 0), 2) if metrics.get('pegRatio') else None,
                "ps_ratio": round(metrics.get('psAnnual', 0), 2) if metrics.get('psAnnual') else None,
                "pb_ratio": round(metrics.get('pbAnnual', 0), 2) if metrics.get('pbAnnual') else None,
                "dividend_yield": round(metrics.get('dividendYieldIndicatedAnnual', 0), 2) if metrics.get('dividendYieldIndicatedAnnual') else 0,
                "earnings_growth": round(metrics.get('epsGrowth3Y', 0), 2) if metrics.get('epsGrowth3Y') else None,
                "revenue_growth": round(metrics.get('revenueGrowth3Y', 0), 2) if metrics.get('revenueGrowth3Y') else None,
                "profit_margin": round(metrics.get('netProfitMarginAnnual', 0), 2) if metrics.get('netProfitMarginAnnual') else None,
                "roe": round(metrics.get('roeRfy', 0), 2) if metrics.get('roeRfy') else None,
                "debt_to_equity": round(metrics.get('totalDebt/totalEquityAnnual', 0) / 100, 2) if metrics.get('totalDebt/totalEquityAnnual') else None,
                "data_available": True
            }
        except Exception as e:
            logger.error(f"Finnhub 재무 데이터 분석 오류: {str(e)}")
            return {"error": str(e), "data_available": False}
    
    def _calculate_finnhub_risk_metrics(self, finnhub_data: Dict) -> Dict:
        """Finnhub 리스크 지표 계산"""
        try:
            candles = finnhub_data.get('candles', {})
            metrics = finnhub_data.get('metrics', {}).get('metric', {})
            
            if candles.get('s') != 'ok' or not candles.get('c'):
                # 캔들 데이터가 없는 경우 기본값 반환
                beta = metrics.get('beta', 1.0)
                return {
                    "volatility": {
                        "daily": None,
                        "monthly": None,
                        "annual": None
                    },
                    "var_95": None,
                    "max_drawdown": None,
                    "sharpe_ratio": None,
                    "beta": round(float(beta), 2) if beta else None,
                    "risk_level": "데이터 없음"
                }
            
            # 종가로 일별 수익률 계산
            close_prices = pd.Series(candles['c'])
            returns = close_prices.pct_change().dropna()
            
            # 변동성 (연환산)
            daily_volatility = returns.std()
            annual_volatility = daily_volatility * np.sqrt(252)
            
            # VaR (95% 신뢰수준)
            var_95 = np.percentile(returns, 5)
            
            # 최대 낙폭
            cumulative_returns = (1 + returns).cumprod()
            running_max = cumulative_returns.cummax()
            drawdown = (cumulative_returns - running_max) / running_max
            max_drawdown = drawdown.min()
            
            # 샤프 비율
            risk_free_rate = 0.02
            excess_returns = returns.mean() * 252 - risk_free_rate
            sharpe_ratio = excess_returns / annual_volatility if annual_volatility > 0 else 0
            
            # 베타 (Finnhub 제공)
            beta = metrics.get('beta', None)
            
            return {
                "volatility": {
                    "daily": round(float(daily_volatility) * 100, 2),
                    "monthly": round(float(daily_volatility * np.sqrt(21)) * 100, 2),
                    "annual": round(float(annual_volatility) * 100, 2)
                },
                "var_95": round(float(var_95) * 100, 2),
                "max_drawdown": round(float(max_drawdown) * 100, 2),
                "sharpe_ratio": round(float(sharpe_ratio), 2),
                "beta": round(float(beta), 2) if beta else None,
                "risk_level": self._determine_risk_level(annual_volatility)
            }
        except Exception as e:
            logger.error(f"Finnhub 리스크 지표 계산 오류: {str(e)}")
            return {"error": str(e)}
    
    def _calculate_finnhub_target_price(self, finnhub_data: Dict, price_data: Dict, fundamentals: Dict) -> Dict:
        """Finnhub 데이터 기반 목표주가 계산"""
        try:
            current_price = price_data.get('current', 0)
            if current_price == 0:
                return {"error": "현재가 정보 없음"}
            
            metrics = finnhub_data.get('metrics', {}).get('metric', {})
            target_prices = []
            methods_used = []
            
            # 1. PER 기반 (성장주 보정)
            pe_ratio = fundamentals.get('pe_ratio')
            if pe_ratio and pe_ratio > 0:
                # 높은 PE를 가진 성장주는 현재 PE의 일정 비율 사용
                if pe_ratio > 50:  # 고PE 성장주
                    adjusted_pe = pe_ratio * 0.8  # 현재 PE의 80%
                elif pe_ratio > 30:  # 중간 PE
                    adjusted_pe = pe_ratio * 0.9  # 현재 PE의 90%
                else:  # 정상 PE
                    adjusted_pe = min(pe_ratio * 1.1, 30)  # 현재 PE의 110% 또는 30 중 작은 값
                
                eps = current_price / pe_ratio
                target_price_per = eps * adjusted_pe
                target_prices.append(target_price_per)
                methods_used.append({
                    "method": "PER Multiple (Growth Adjusted)",
                    "target_price": round(target_price_per, 2),
                    "pe_used": round(adjusted_pe, 1)
                })
            
            # 2. 52주 최고가 기반
            high_52w = price_data.get('high_52w', 0)
            if high_52w > 0:
                target_price_technical = high_52w * 0.95
                target_prices.append(target_price_technical)
                methods_used.append({
                    "method": "Technical (52W High)",
                    "target_price": round(target_price_technical, 2),
                    "basis": "95% of 52-week high"
                })
            
            # 3. 애널리스트 목표가 (Finnhub에서 제공하는 경우)
            price_target = metrics.get('priceTargetHigh')
            if price_target:
                target_prices.append(price_target)
                methods_used.append({
                    "method": "Analyst Consensus",
                    "target_price": round(price_target, 2),
                    "basis": "Finnhub analyst data"
                })
            
            # 목표주가 종합
            if target_prices:
                avg_target_price = sum(target_prices) / len(target_prices)
                
                # 중간값 계산
                sorted_prices = sorted(target_prices)
                if len(sorted_prices) % 2 == 0:
                    median_target_price = (sorted_prices[len(sorted_prices)//2 - 1] + sorted_prices[len(sorted_prices)//2]) / 2
                else:
                    median_target_price = sorted_prices[len(sorted_prices)//2]
                
                upside_potential = ((avg_target_price / current_price) - 1) * 100
                
                # 투자 의견
                if upside_potential > 20:
                    recommendation = "Strong Buy"
                elif upside_potential > 10:
                    recommendation = "Buy"
                elif upside_potential > -5:
                    recommendation = "Hold"
                else:
                    recommendation = "Sell"
                
                return {
                    "current_price": round(current_price, 2),
                    "target_price_avg": round(avg_target_price, 2),
                    "target_price_median": round(median_target_price, 2),
                    "upside_potential": round(upside_potential, 1),
                    "recommendation": recommendation,
                    "methods_used": methods_used,
                    "calculation_date": datetime.now().isoformat()
                }
            else:
                return {
                    "error": "목표주가 계산에 필요한 데이터 부족",
                    "current_price": round(current_price, 2)
                }
                
        except Exception as e:
            logger.error(f"Finnhub 목표주가 계산 오류: {str(e)}")
            return {"error": f"목표주가 계산 실패: {str(e)}"}
    
    async def on_start(self):
        """에이전트 시작 시 실행"""
        logger.info("✅ Quantitative Analysis Agent V2 초기화 완료")
    
    async def on_stop(self):
        """에이전트 종료 시 실행"""
        logger.info("👋 Quantitative Analysis Agent V2 종료 중...")


# 에이전트 인스턴스 생성
agent = QuantitativeAgentV2()

# BaseAgent의 app을 사용
app = agent.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8211)