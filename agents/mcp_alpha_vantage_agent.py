"""
MCP Alpha Vantage Agent - 외부 Alpha Vantage MCP 서버 연동
실시간 주가, 기업정보, 기술적 지표 제공
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from typing import Dict, Any, List
import logging
from datetime import datetime

from a2a_core.base.base_agent import BaseAgent
from utils.mcp_client import MCPClient

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MCPAlphaVantageAgent(BaseAgent):
    """Alpha Vantage MCP 서버 연동 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="MCP Alpha Vantage Agent",
            description="Alpha Vantage MCP 서버를 통한 고급 시장 데이터 수집",
            capabilities=["alpha_vantage_data", "real_time_quotes", "advanced_indicators"],
            port=8214,
            registry_url="http://localhost:8001"
        )
        
        # Alpha Vantage MCP 서버 설정
        self.alpha_mcp_url = os.getenv("ALPHA_VANTAGE_MCP_URL", "http://localhost:3002")
        self.mcp_client = MCPClient(self.alpha_mcp_url)
        self.initialized = False
        
        # 라우트 설정
        self.app.post("/analyze")(self.analyze_with_alpha_mcp)
        self.app.post("/real_time_quote")(self.get_real_time_quote)
        self.app.post("/advanced_analysis")(self.get_advanced_analysis)
    
    async def initialize_mcp(self):
        """MCP 서버 초기화"""
        if not self.initialized:
            try:
                result = await self.mcp_client.initialize()
                logger.info(f"Alpha Vantage MCP 서버 초기화 성공: {result}")
                
                # 사용 가능한 도구 확인
                tools = await self.mcp_client.list_tools()
                logger.info(f"사용 가능한 도구: {[tool.name for tool in tools]}")
                
                self.initialized = True
            except Exception as e:
                logger.error(f"MCP 서버 초기화 실패: {e}")
                raise
    
    async def analyze_with_alpha_mcp(self, request: Dict[str, Any]):
        """Alpha Vantage MCP를 통한 종합 분석"""
        try:
            ticker = request.get("ticker")
            if not ticker:
                raise HTTPException(status_code=400, detail="ticker가 필요합니다")
            
            # MCP 서버 초기화
            await self.initialize_mcp()
            
            logger.info(f"Alpha Vantage MCP 서버로 {ticker} 데이터 요청")
            
            # 병렬로 여러 MCP 도구 호출
            import asyncio
            tasks = []
            
            # 1. 실시간 주가
            tasks.append(self._get_quote_endpoint(ticker))
            
            # 2. 일간 시계열 데이터
            tasks.append(self._get_daily_time_series(ticker))
            
            # 3. 기술적 지표 (RSI)
            tasks.append(self._get_rsi(ticker))
            
            # 4. 기술적 지표 (MACD)
            tasks.append(self._get_macd(ticker))
            
            # 5. 회사 개요
            tasks.append(self._get_company_overview(ticker))
            
            # 모든 데이터 수집
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 통합
            analysis_result = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "data_source": "alpha_vantage_mcp",
                "real_time_quote": results[0] if not isinstance(results[0], Exception) else None,
                "daily_series": results[1] if not isinstance(results[1], Exception) else None,
                "rsi": results[2] if not isinstance(results[2], Exception) else None,
                "macd": results[3] if not isinstance(results[3], Exception) else None,
                "company_overview": results[4] if not isinstance(results[4], Exception) else None,
                "analysis_summary": self._generate_comprehensive_analysis(results, ticker)
            }
            
            logger.info(f"Alpha Vantage MCP 분석 완료: {ticker}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Alpha Vantage MCP 분석 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_real_time_quote(self, request: Dict[str, Any]):
        """실시간 주가 조회"""
        try:
            ticker = request.get("ticker")
            if not ticker:
                raise HTTPException(status_code=400, detail="ticker가 필요합니다")
            
            await self.initialize_mcp()
            quote = await self._get_quote_endpoint(ticker)
            
            return {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "quote": quote
            }
            
        except Exception as e:
            logger.error(f"실시간 주가 조회 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def get_advanced_analysis(self, request: Dict[str, Any]):
        """고급 기술적 분석"""
        try:
            ticker = request.get("ticker")
            indicators = request.get("indicators", ["RSI", "MACD", "BBANDS"])
            
            if not ticker:
                raise HTTPException(status_code=400, detail="ticker가 필요합니다")
            
            await self.initialize_mcp()
            
            # 요청한 지표들 병렬 수집
            tasks = []
            for indicator in indicators:
                if indicator == "RSI":
                    tasks.append(self._get_rsi(ticker))
                elif indicator == "MACD":
                    tasks.append(self._get_macd(ticker))
                elif indicator == "BBANDS":
                    tasks.append(self._get_bollinger_bands(ticker))
                elif indicator == "SMA":
                    tasks.append(self._get_sma(ticker))
                elif indicator == "EMA":
                    tasks.append(self._get_ema(ticker))
            
            import asyncio
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 정리
            indicator_results = {}
            for i, indicator in enumerate(indicators):
                if not isinstance(results[i], Exception):
                    indicator_results[indicator] = results[i]
            
            return {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "indicators": indicator_results,
                "signal": self._generate_trading_signal(indicator_results)
            }
            
        except Exception as e:
            logger.error(f"고급 분석 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_quote_endpoint(self, symbol: str) -> Dict[str, Any]:
        """QUOTE_ENDPOINT 호출"""
        try:
            result = await self.mcp_client.call_tool("QUOTE_ENDPOINT", {
                "symbol": symbol
            })
            return result
        except Exception as e:
            logger.error(f"Quote endpoint 호출 실패: {e}")
            return {}
    
    async def _get_daily_time_series(self, symbol: str) -> Dict[str, Any]:
        """TIME_SERIES_DAILY 호출"""
        try:
            result = await self.mcp_client.call_tool("TIME_SERIES_DAILY", {
                "symbol": symbol,
                "outputsize": "compact"
            })
            return result
        except Exception as e:
            logger.error(f"Daily time series 호출 실패: {e}")
            return {}
    
    async def _get_rsi(self, symbol: str) -> Dict[str, Any]:
        """RSI 지표 조회"""
        try:
            result = await self.mcp_client.call_tool("RSI", {
                "symbol": symbol,
                "interval": "daily",
                "time_period": 14,
                "series_type": "close"
            })
            return result
        except Exception as e:
            logger.error(f"RSI 조회 실패: {e}")
            return {}
    
    async def _get_macd(self, symbol: str) -> Dict[str, Any]:
        """MACD 지표 조회"""
        try:
            result = await self.mcp_client.call_tool("MACD", {
                "symbol": symbol,
                "interval": "daily",
                "series_type": "close"
            })
            return result
        except Exception as e:
            logger.error(f"MACD 조회 실패: {e}")
            return {}
    
    async def _get_bollinger_bands(self, symbol: str) -> Dict[str, Any]:
        """볼린저 밴드 조회"""
        try:
            result = await self.mcp_client.call_tool("BBANDS", {
                "symbol": symbol,
                "interval": "daily",
                "time_period": 20,
                "series_type": "close"
            })
            return result
        except Exception as e:
            logger.error(f"Bollinger Bands 조회 실패: {e}")
            return {}
    
    async def _get_sma(self, symbol: str) -> Dict[str, Any]:
        """단순이동평균 조회"""
        try:
            result = await self.mcp_client.call_tool("SMA", {
                "symbol": symbol,
                "interval": "daily",
                "time_period": 50,
                "series_type": "close"
            })
            return result
        except Exception as e:
            logger.error(f"SMA 조회 실패: {e}")
            return {}
    
    async def _get_ema(self, symbol: str) -> Dict[str, Any]:
        """지수이동평균 조회"""
        try:
            result = await self.mcp_client.call_tool("EMA", {
                "symbol": symbol,
                "interval": "daily",
                "time_period": 20,
                "series_type": "close"
            })
            return result
        except Exception as e:
            logger.error(f"EMA 조회 실패: {e}")
            return {}
    
    async def _get_company_overview(self, symbol: str) -> Dict[str, Any]:
        """회사 개요 조회"""
        try:
            result = await self.mcp_client.call_tool("OVERVIEW", {
                "symbol": symbol
            })
            return result
        except Exception as e:
            logger.error(f"Company overview 조회 실패: {e}")
            return {}
    
    def _generate_comprehensive_analysis(self, results: List[Any], ticker: str) -> Dict[str, Any]:
        """종합 분석 생성"""
        analysis = {
            "ticker": ticker,
            "technical_summary": "중립",
            "fundamental_summary": "데이터 없음",
            "signals": []
        }
        
        # RSI 분석
        if results[2] and not isinstance(results[2], Exception):
            rsi_data = results[2]
            if rsi_data:
                latest_rsi = self._get_latest_value(rsi_data)
                if latest_rsi:
                    if latest_rsi > 70:
                        analysis["signals"].append("RSI 과매수 신호")
                        analysis["technical_summary"] = "과매수"
                    elif latest_rsi < 30:
                        analysis["signals"].append("RSI 과매도 신호")
                        analysis["technical_summary"] = "과매도"
        
        # MACD 분석
        if results[3] and not isinstance(results[3], Exception):
            macd_data = results[3]
            if macd_data:
                analysis["signals"].append("MACD 데이터 사용 가능")
        
        # 회사 정보 분석
        if results[4] and not isinstance(results[4], Exception):
            overview = results[4]
            if overview:
                pe_ratio = overview.get("PERatio")
                if pe_ratio:
                    analysis["fundamental_summary"] = f"P/E 비율: {pe_ratio}"
        
        return analysis
    
    def _get_latest_value(self, time_series_data: Dict) -> float:
        """시계열 데이터에서 최신 값 추출"""
        try:
            # Alpha Vantage 데이터 구조에 맞게 파싱
            for key in time_series_data:
                if "Technical Analysis" in key or "Time Series" in key:
                    data = time_series_data[key]
                    if isinstance(data, dict):
                        latest_date = sorted(data.keys())[-1]
                        return float(list(data[latest_date].values())[0])
        except:
            pass
        return None
    
    def _generate_trading_signal(self, indicators: Dict[str, Any]) -> str:
        """지표 기반 트레이딩 신호 생성"""
        buy_signals = 0
        sell_signals = 0
        
        # RSI 신호
        if "RSI" in indicators:
            rsi_value = self._get_latest_value(indicators["RSI"])
            if rsi_value:
                if rsi_value < 30:
                    buy_signals += 1
                elif rsi_value > 70:
                    sell_signals += 1
        
        # 추가 지표 분석...
        
        if buy_signals > sell_signals:
            return "매수 신호"
        elif sell_signals > buy_signals:
            return "매도 신호"
        else:
            return "중립/관망"
    
    async def on_shutdown(self):
        """에이전트 종료 시 정리"""
        await self.mcp_client.close()
        await super().on_shutdown()
    
    async def handle_message(self, message: Any) -> Any:
        """메시지 처리 (BaseAgent 추상 메서드)"""
        # A2A 메시지를 처리하는 경우
        pass
    
    async def on_start(self):
        """에이전트 시작 시 (BaseAgent 추상 메서드)"""
        logger.info(f"{self.name} 시작됨")
    
    async def on_stop(self):
        """에이전트 중지 시 (BaseAgent 추상 메서드)"""
        logger.info(f"{self.name} 중지됨")


# FastAPI 앱 인스턴스
agent = MCPAlphaVantageAgent()
app = agent.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8214)