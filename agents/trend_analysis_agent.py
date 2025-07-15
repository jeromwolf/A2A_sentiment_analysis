"""
트렌드 분석 에이전트 - 과거 데이터 기반 패턴 및 추세 분석
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
from pydantic import BaseModel
from fastapi import Depends
import asyncio

from a2a_core.base.base_agent import BaseAgent
from a2a_core.protocols.message import A2AMessage, MessageType
from utils.config_manager import config
from utils.auth import verify_api_key
from utils.cache_manager import cache_manager

logger = logging.getLogger(__name__)


class TrendAnalysisRequest(BaseModel):
    ticker: str
    historical_data: Dict[str, Any]
    period: str = "3m"  # 3m, 6m, 1y


class TrendAnalysisAgent(BaseAgent):
    """과거 데이터 기반 트렌드 분석 에이전트"""
    
    def __init__(self):
        agent_config = config.get_agent_config("trend_analysis")
        
        super().__init__(
            name=agent_config.get("name", "Trend Analysis Agent"),
            description="과거 데이터를 분석하여 추세와 패턴을 파악하는 에이전트",
            port=agent_config.get("port", 8214)
        )
        
        self.capabilities = [
            {
                "name": "trend_analysis",
                "version": "1.0",
                "description": "시계열 데이터의 추세 및 패턴 분석",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "ticker": {"type": "string"},
                        "historical_data": {"type": "object"},
                        "period": {"type": "string"}
                    },
                    "required": ["ticker", "historical_data"]
                }
            }
        ]
        
        self._setup_http_endpoints()
        
    def _setup_http_endpoints(self):
        """HTTP 엔드포인트 설정"""
        
        @self.app.post("/analyze_trend", dependencies=[Depends(verify_api_key)])
        async def analyze_trend(request: TrendAnalysisRequest):
            """트렌드 분석 수행"""
            logger.info(f"📈 트렌드 분석 시작: {request.ticker} (기간: {request.period})")
            
            # 캐시 확인
            cache_key = f"trend_{request.ticker}_{request.period}"
            cached_result = await cache_manager.get(cache_key)
            
            if cached_result:
                logger.info("✅ 캐시된 트렌드 분석 결과 사용")
                return cached_result
            
            # 트렌드 분석 수행
            result = await self._perform_trend_analysis(
                request.ticker,
                request.historical_data,
                request.period
            )
            
            # 캐시 저장 (1시간)
            await cache_manager.set(cache_key, result, ttl=3600)
            
            return result
    
    async def _perform_trend_analysis(self, ticker: str, data: Dict, period: str) -> Dict:
        """트렌드 분석 수행"""
        try:
            # 1. 가격 트렌드 분석
            price_trend = self._analyze_price_trend(data.get("price_history", []))
            
            # 2. 감성 트렌드 분석
            sentiment_trend = self._analyze_sentiment_trend(data.get("sentiment_history", []))
            
            # 3. 거래량 트렌드 분석
            volume_trend = self._analyze_volume_trend(data.get("volume_history", []))
            
            # 4. 기술적 지표 트렌드
            technical_trend = self._analyze_technical_trend(data.get("technical_history", []))
            
            # 5. 계절성 분석
            seasonality = self._analyze_seasonality(data.get("price_history", []))
            
            # 6. 변동성 분석
            volatility_analysis = self._analyze_volatility(data.get("price_history", []))
            
            # 7. 예측 모델 (간단한 선형 회귀)
            forecast = self._simple_forecast(data.get("price_history", []))
            
            return {
                "ticker": ticker,
                "period_analyzed": period,
                "analysis_date": datetime.now().isoformat(),
                "price_trend": price_trend,
                "sentiment_trend": sentiment_trend,
                "volume_trend": volume_trend,
                "technical_trend": technical_trend,
                "seasonality": seasonality,
                "volatility": volatility_analysis,
                "forecast": forecast,
                "summary": self._generate_trend_summary(
                    price_trend, sentiment_trend, volume_trend, volatility_analysis
                )
            }
            
        except Exception as e:
            logger.error(f"트렌드 분석 오류: {str(e)}")
            return {
                "error": str(e),
                "ticker": ticker,
                "analysis_date": datetime.now().isoformat()
            }
    
    def _analyze_price_trend(self, price_history: List[Dict]) -> Dict:
        """가격 추세 분석"""
        if not price_history:
            return {"trend": "unknown", "strength": 0}
        
        try:
            # DataFrame 변환
            df = pd.DataFrame(price_history)
            if 'date' in df.columns and 'close' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # 이동평균
                df['MA20'] = df['close'].rolling(window=20).mean()
                df['MA50'] = df['close'].rolling(window=50).mean()
                
                # 추세 계산 (선형 회귀)
                from scipy import stats
                x = np.arange(len(df))
                y = df['close'].values
                slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
                
                # 추세 강도와 방향
                trend_direction = "상승" if slope > 0 else "하락"
                trend_strength = abs(r_value)  # 상관계수로 추세 강도 측정
                
                # 지지/저항선
                support = df['close'].min()
                resistance = df['close'].max()
                
                return {
                    "trend": trend_direction,
                    "strength": round(trend_strength, 3),
                    "slope": round(slope, 4),
                    "support_level": round(support, 2),
                    "resistance_level": round(resistance, 2),
                    "ma20_current": round(df['MA20'].iloc[-1], 2) if not df['MA20'].isna().iloc[-1] else None,
                    "ma50_current": round(df['MA50'].iloc[-1], 2) if not df['MA50'].isna().iloc[-1] else None,
                    "price_vs_ma20": "above" if df['close'].iloc[-1] > df['MA20'].iloc[-1] else "below",
                    "trend_confidence": "high" if trend_strength > 0.7 else "medium" if trend_strength > 0.4 else "low"
                }
                
        except Exception as e:
            logger.error(f"가격 트렌드 분석 오류: {str(e)}")
            return {"trend": "unknown", "error": str(e)}
    
    def _analyze_sentiment_trend(self, sentiment_history: List[Dict]) -> Dict:
        """감성 추세 분석"""
        if not sentiment_history:
            return {"trend": "unknown", "average_sentiment": 0}
        
        try:
            # 시간별 감성 점수 집계
            df = pd.DataFrame(sentiment_history)
            if 'date' in df.columns and 'score' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # 일별 평균
                daily_sentiment = df.groupby(df.index.date)['score'].mean()
                
                # 추세 계산
                if len(daily_sentiment) > 1:
                    x = np.arange(len(daily_sentiment))
                    y = daily_sentiment.values
                    slope, _, _, _, _ = stats.linregress(x, y)
                    
                    trend = "개선" if slope > 0.01 else "악화" if slope < -0.01 else "유지"
                else:
                    trend = "unknown"
                    slope = 0
                
                return {
                    "trend": trend,
                    "average_sentiment": round(daily_sentiment.mean(), 3),
                    "current_sentiment": round(daily_sentiment.iloc[-1], 3),
                    "sentiment_change": round(slope, 4),
                    "positive_days": int((daily_sentiment > 0).sum()),
                    "negative_days": int((daily_sentiment < 0).sum()),
                    "sentiment_volatility": round(daily_sentiment.std(), 3)
                }
                
        except Exception as e:
            logger.error(f"감성 트렌드 분석 오류: {str(e)}")
            return {"trend": "unknown", "error": str(e)}
    
    def _analyze_volume_trend(self, volume_history: List[Dict]) -> Dict:
        """거래량 추세 분석"""
        if not volume_history:
            return {"trend": "unknown", "average_volume": 0}
        
        try:
            df = pd.DataFrame(volume_history)
            if 'date' in df.columns and 'volume' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                
                # 평균 거래량
                avg_volume = df['volume'].mean()
                recent_volume = df['volume'].tail(5).mean()  # 최근 5일
                
                # 거래량 트렌드
                volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
                
                if volume_ratio > 1.5:
                    trend = "급증"
                elif volume_ratio > 1.2:
                    trend = "증가"
                elif volume_ratio < 0.8:
                    trend = "감소"
                else:
                    trend = "보통"
                
                return {
                    "trend": trend,
                    "average_volume": int(avg_volume),
                    "recent_volume": int(recent_volume),
                    "volume_ratio": round(volume_ratio, 2),
                    "highest_volume_date": df['volume'].idxmax().strftime("%Y-%m-%d"),
                    "lowest_volume_date": df['volume'].idxmin().strftime("%Y-%m-%d")
                }
                
        except Exception as e:
            logger.error(f"거래량 트렌드 분석 오류: {str(e)}")
            return {"trend": "unknown", "error": str(e)}
    
    def _analyze_technical_trend(self, technical_history: List[Dict]) -> Dict:
        """기술적 지표 트렌드 분석"""
        if not technical_history:
            return {"rsi_trend": "unknown", "macd_trend": "unknown"}
        
        try:
            df = pd.DataFrame(technical_history)
            result = {}
            
            # RSI 트렌드
            if 'rsi' in df.columns:
                recent_rsi = df['rsi'].tail(10).mean()
                if recent_rsi > 70:
                    result['rsi_trend'] = "과매수"
                elif recent_rsi < 30:
                    result['rsi_trend'] = "과매도"
                else:
                    result['rsi_trend'] = "중립"
                result['current_rsi'] = round(df['rsi'].iloc[-1], 1)
            
            # MACD 트렌드
            if 'macd' in df.columns and 'signal' in df.columns:
                recent_crossover = None
                for i in range(len(df) - 1, 0, -1):
                    if df['macd'].iloc[i] > df['signal'].iloc[i] and df['macd'].iloc[i-1] <= df['signal'].iloc[i-1]:
                        recent_crossover = "bullish"
                        break
                    elif df['macd'].iloc[i] < df['signal'].iloc[i] and df['macd'].iloc[i-1] >= df['signal'].iloc[i-1]:
                        recent_crossover = "bearish"
                        break
                
                result['macd_trend'] = recent_crossover or "no_signal"
            
            return result
            
        except Exception as e:
            logger.error(f"기술적 트렌드 분석 오류: {str(e)}")
            return {"error": str(e)}
    
    def _analyze_seasonality(self, price_history: List[Dict]) -> Dict:
        """계절성 분석"""
        if not price_history or len(price_history) < 365:  # 최소 1년 데이터 필요
            return {"has_seasonality": False, "pattern": "insufficient_data"}
        
        try:
            df = pd.DataFrame(price_history)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 월별 평균 수익률
            df['returns'] = df['close'].pct_change()
            monthly_returns = df['returns'].groupby(df.index.month).mean()
            
            # 가장 좋은/나쁜 달
            best_month = monthly_returns.idxmax()
            worst_month = monthly_returns.idxmin()
            
            # 계절성 강도 (표준편차)
            seasonality_strength = monthly_returns.std()
            
            return {
                "has_seasonality": seasonality_strength > 0.02,
                "best_month": int(best_month),
                "worst_month": int(worst_month),
                "seasonality_strength": round(seasonality_strength, 4),
                "monthly_pattern": {
                    str(i): round(monthly_returns.get(i, 0), 4) 
                    for i in range(1, 13)
                }
            }
            
        except Exception as e:
            logger.error(f"계절성 분석 오류: {str(e)}")
            return {"has_seasonality": False, "error": str(e)}
    
    def _analyze_volatility(self, price_history: List[Dict]) -> Dict:
        """변동성 분석"""
        if not price_history:
            return {"volatility": "unknown"}
        
        try:
            df = pd.DataFrame(price_history)
            df['returns'] = df['close'].pct_change()
            
            # 일일 변동성
            daily_vol = df['returns'].std()
            
            # 연환산 변동성
            annual_vol = daily_vol * np.sqrt(252)
            
            # 변동성 수준 판단
            if annual_vol < 0.15:
                vol_level = "낮음"
            elif annual_vol < 0.25:
                vol_level = "보통"
            elif annual_vol < 0.35:
                vol_level = "높음"
            else:
                vol_level = "매우 높음"
            
            # 최대 일일 변동
            max_gain = df['returns'].max()
            max_loss = df['returns'].min()
            
            return {
                "volatility_level": vol_level,
                "daily_volatility": round(daily_vol * 100, 2),
                "annual_volatility": round(annual_vol * 100, 2),
                "max_daily_gain": round(max_gain * 100, 2),
                "max_daily_loss": round(max_loss * 100, 2),
                "volatility_trend": self._calculate_volatility_trend(df['returns'])
            }
            
        except Exception as e:
            logger.error(f"변동성 분석 오류: {str(e)}")
            return {"volatility": "unknown", "error": str(e)}
    
    def _calculate_volatility_trend(self, returns: pd.Series) -> str:
        """변동성 추세 계산"""
        try:
            # 30일 이동 변동성
            rolling_vol = returns.rolling(window=30).std()
            
            # 최근 vs 과거 변동성 비교
            recent_vol = rolling_vol.tail(30).mean()
            past_vol = rolling_vol.iloc[-60:-30].mean()
            
            if pd.isna(recent_vol) or pd.isna(past_vol):
                return "unknown"
            
            vol_change = (recent_vol - past_vol) / past_vol
            
            if vol_change > 0.2:
                return "증가"
            elif vol_change < -0.2:
                return "감소"
            else:
                return "안정"
                
        except:
            return "unknown"
    
    def _simple_forecast(self, price_history: List[Dict]) -> Dict:
        """간단한 가격 예측 (선형 회귀 기반)"""
        if not price_history or len(price_history) < 30:
            return {"forecast_available": False}
        
        try:
            df = pd.DataFrame(price_history)
            
            # 최근 30일 데이터로 예측
            recent_data = df.tail(30)
            x = np.arange(len(recent_data))
            y = recent_data['close'].values
            
            # 선형 회귀
            from scipy import stats
            slope, intercept, _, _, _ = stats.linregress(x, y)
            
            # 향후 5일 예측
            future_days = 5
            forecast_prices = []
            
            for i in range(1, future_days + 1):
                predicted_price = slope * (len(recent_data) + i - 1) + intercept
                forecast_prices.append(round(predicted_price, 2))
            
            current_price = recent_data['close'].iloc[-1]
            forecast_change = ((forecast_prices[-1] - current_price) / current_price) * 100
            
            return {
                "forecast_available": True,
                "method": "linear_regression",
                "current_price": round(current_price, 2),
                "forecast_5d": forecast_prices,
                "expected_change_5d": round(forecast_change, 2),
                "trend_strength": "strong" if abs(slope) > 1 else "moderate" if abs(slope) > 0.5 else "weak",
                "confidence": "low",  # 선형 회귀는 단순한 방법
                "disclaimer": "이 예측은 단순 통계 모델 기반이며 투자 조언이 아닙니다"
            }
            
        except Exception as e:
            logger.error(f"가격 예측 오류: {str(e)}")
            return {"forecast_available": False, "error": str(e)}
    
    def _generate_trend_summary(self, price_trend: Dict, sentiment_trend: Dict, 
                              volume_trend: Dict, volatility: Dict) -> Dict:
        """종합 트렌드 요약"""
        summary = {
            "overall_trend": "",
            "key_insights": [],
            "risk_level": "",
            "recommendation": ""
        }
        
        # 종합 트렌드 판단
        trends = []
        if price_trend.get("trend") == "상승":
            trends.append("positive")
        elif price_trend.get("trend") == "하락":
            trends.append("negative")
        
        if sentiment_trend.get("trend") == "개선":
            trends.append("positive")
        elif sentiment_trend.get("trend") == "악화":
            trends.append("negative")
        
        positive_count = trends.count("positive")
        negative_count = trends.count("negative")
        
        if positive_count > negative_count:
            summary["overall_trend"] = "긍정적"
        elif negative_count > positive_count:
            summary["overall_trend"] = "부정적"
        else:
            summary["overall_trend"] = "중립적"
        
        # 주요 인사이트
        if price_trend.get("trend") == "상승" and price_trend.get("strength", 0) > 0.7:
            summary["key_insights"].append("강한 상승 추세 지속 중")
        
        if volume_trend.get("trend") == "급증":
            summary["key_insights"].append("거래량 급증 - 주요 이벤트 발생 가능성")
        
        if volatility.get("volatility_level") in ["높음", "매우 높음"]:
            summary["key_insights"].append("높은 변동성 - 리스크 관리 필요")
        
        if sentiment_trend.get("average_sentiment", 0) > 0.5:
            summary["key_insights"].append("시장 심리 매우 긍정적")
        
        # 리스크 수준
        vol_level = volatility.get("annual_volatility", 0)
        if vol_level > 35:
            summary["risk_level"] = "매우 높음"
        elif vol_level > 25:
            summary["risk_level"] = "높음"
        elif vol_level > 15:
            summary["risk_level"] = "보통"
        else:
            summary["risk_level"] = "낮음"
        
        # 투자 제안 (면책조항 포함)
        if summary["overall_trend"] == "긍정적" and summary["risk_level"] in ["낮음", "보통"]:
            summary["recommendation"] = "긍정적 전망 - 추가 분석 권장"
        elif summary["overall_trend"] == "부정적":
            summary["recommendation"] = "신중한 접근 필요"
        else:
            summary["recommendation"] = "관망 권장"
        
        return summary
    
    async def handle_message(self, message: A2AMessage):
        """메시지 처리"""
        try:
            action = message.body.get("action")
            
            if message.header.message_type == MessageType.REQUEST and action == "trend_analysis":
                payload = message.body.get("payload", {})
                
                result = await self._perform_trend_analysis(
                    payload.get("ticker"),
                    payload.get("historical_data", {}),
                    payload.get("period", "3m")
                )
                
                await self.reply_to_message(message, result=result, success=True)
                
        except Exception as e:
            logger.error(f"트렌드 분석 메시지 처리 오류: {str(e)}")
            await self.reply_to_message(
                message,
                result={"error": str(e)},
                success=False
            )


# 에이전트 인스턴스 생성
agent = TrendAnalysisAgent()
app = agent.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8214)