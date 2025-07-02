"""
정량적 데이터 분석 에이전트 V2 - A2A 프로토콜 기반
주가, 기술적 지표, 재무제표 등 정량적 데이터를 분석하는 에이전트
"""
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import yfinance as yf
import pandas as pd
import numpy as np

from fastapi import FastAPI
from contextlib import asynccontextmanager

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuantitativeAgentV2(BaseAgent):
    """정량적 데이터 분석 A2A 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="Quantitative Analysis Agent V2",
            description="주가, 기술적 지표, 재무제표 등 정량적 데이터를 분석하는 A2A 에이전트",
            port=8211
        )
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
    
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            logger.info(f"🔍 메시지 수신 - Type: {message.header.type}, Action: {message.body.action}")
            
            # 이벤트 메시지는 무시
            if message.header.type == MessageType.EVENT:
                return
            
            # 요청 메시지 처리
            if message.header.type == MessageType.REQUEST and message.body.action == "quantitative_analysis":
                ticker = message.body.payload.get("ticker")
                period = message.body.payload.get("period", "1mo")
                
                if not ticker:
                    await self.send_response(
                        message,
                        self.create_response(
                            request_message=message,
                            success=False,
                            error="티커가 제공되지 않았습니다"
                        )
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
                await self.send_response(
                    message,
                    self.create_response(
                        request_message=message,
                        success=True,
                        result=response_data
                    )
                )
                
        except Exception as e:
            logger.error(f"❌ 정량적 분석 실패: {str(e)}")
            await self.send_response(
                message,
                self.create_response(
                    request_message=message,
                    success=False,
                    error=str(e)
                )
            )
    
    async def _analyze_quantitative_data(self, ticker: str, period: str) -> Dict:
        """정량적 데이터 분석 수행"""
        try:
            # yfinance를 사용한 데이터 수집
            stock = yf.Ticker(ticker)
            
            # 1. 가격 데이터 분석
            price_data = self._analyze_price_data(stock, period)
            
            # 2. 기술적 지표 계산
            technical_indicators = self._calculate_technical_indicators(stock, period)
            
            # 3. 재무 데이터 분석
            fundamentals = self._analyze_fundamentals(stock)
            
            # 4. 리스크 지표 계산
            risk_metrics = self._calculate_risk_metrics(stock, period)
            
            return {
                "price_data": price_data,
                "technical_indicators": technical_indicators,
                "fundamentals": fundamentals,
                "risk_metrics": risk_metrics
            }
            
        except Exception as e:
            logger.error(f"분석 중 오류 발생: {str(e)}")
            return {
                "error": str(e),
                "price_data": {},
                "technical_indicators": {},
                "fundamentals": {},
                "risk_metrics": {}
            }
    
    def _analyze_price_data(self, stock: yf.Ticker, period: str) -> Dict:
        """가격 데이터 분석"""
        try:
            # 현재 가격 정보
            info = stock.info
            current_price = info.get('currentPrice', 0)
            
            # 기간별 가격 데이터
            hist = stock.history(period=period)
            if hist.empty:
                return {"error": "가격 데이터를 가져올 수 없습니다"}
            
            # 변화율 계산
            close_prices = hist['Close']
            change_1d = ((close_prices[-1] - close_prices[-2]) / close_prices[-2] * 100) if len(close_prices) > 1 else 0
            change_1w = ((close_prices[-1] - close_prices[-min(5, len(close_prices))]) / close_prices[-min(5, len(close_prices))] * 100) if len(close_prices) > 5 else 0
            change_1m = ((close_prices[-1] - close_prices[0]) / close_prices[0] * 100) if len(close_prices) > 20 else 0
            
            return {
                "current": float(current_price),
                "high_52w": float(info.get('fiftyTwoWeekHigh', 0)),
                "low_52w": float(info.get('fiftyTwoWeekLow', 0)),
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
                "debt_to_equity": round(float(info.get('debtToEquity', 0)) / 100, 2) if info.get('debtToEquity') else None
            }
        except Exception as e:
            logger.error(f"재무 데이터 분석 오류: {str(e)}")
            return {"error": str(e)}
    
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
            
            # 베타 (S&P 500 대비)
            beta = self._calculate_beta(stock.ticker)
            
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
    
    def _calculate_beta(self, ticker: str) -> Optional[float]:
        """베타 계산 (S&P 500 대비)"""
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