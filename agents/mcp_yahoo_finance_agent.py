"""
MCP Yahoo Finance Agent - 외부 Yahoo Finance MCP 서버 연동
기존 quantitative_analysis_agent를 대체하여 MCP 서버 호출
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


class MCPYahooFinanceAgent(BaseAgent):
    """Yahoo Finance MCP 서버 연동 에이전트"""
    
    def __init__(self):
        super().__init__(
            name="MCP Yahoo Finance Agent",
            description="Yahoo Finance MCP 서버를 통한 시장 데이터 수집",
            capabilities=["yahoo_finance_data", "technical_analysis", "market_data"],
            port=8213,
            registry_url="http://localhost:8001"
        )
        
        # Yahoo Finance MCP 서버 설정
        self.yahoo_mcp_url = os.getenv("YAHOO_FINANCE_MCP_URL", "http://localhost:3001")
        self.mcp_client = MCPClient(self.yahoo_mcp_url)
        self.initialized = False
        
        # 라우트 설정
        self.app.post("/analyze")(self.analyze_with_yahoo_mcp)
    
    async def initialize_mcp(self):
        """MCP 서버 초기화"""
        if not self.initialized:
            try:
                result = await self.mcp_client.initialize()
                logger.info(f"Yahoo Finance MCP 서버 초기화 성공: {result}")
                self.initialized = True
            except Exception as e:
                logger.error(f"MCP 서버 초기화 실패: {e}")
                raise
    
    async def analyze_with_yahoo_mcp(self, request: Dict[str, Any]):
        """Yahoo Finance MCP를 통한 주식 분석"""
        try:
            ticker = request.get("ticker")
            if not ticker:
                raise HTTPException(status_code=400, detail="ticker가 필요합니다")
            
            # MCP 서버 초기화
            await self.initialize_mcp()
            
            logger.info(f"Yahoo Finance MCP 서버로 {ticker} 데이터 요청")
            
            # 병렬로 여러 MCP 도구 호출
            tasks = []
            
            # 1. 주가 정보
            tasks.append(self._get_stock_quote(ticker))
            
            # 2. 기업 정보
            tasks.append(self._get_company_info(ticker))
            
            # 3. 과거 가격 데이터
            tasks.append(self._get_historical_data(ticker))
            
            # 4. 기술적 지표
            tasks.append(self._get_technical_indicators(ticker))
            
            # 5. 재무제표 (사용 가능한 경우)
            tasks.append(self._get_financials(ticker))
            
            # 모든 데이터 수집
            import asyncio
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 통합
            analysis_result = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "data_source": "yahoo_finance_mcp",
                "quote": results[0] if not isinstance(results[0], Exception) else None,
                "company_info": results[1] if not isinstance(results[1], Exception) else None,
                "historical_data": results[2] if not isinstance(results[2], Exception) else None,
                "technical_indicators": results[3] if not isinstance(results[3], Exception) else None,
                "financials": results[4] if not isinstance(results[4], Exception) else None,
                "analysis_summary": self._generate_summary(results, ticker)
            }
            
            logger.info(f"Yahoo Finance MCP 분석 완료: {ticker}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"Yahoo Finance MCP 분석 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def _get_stock_quote(self, ticker: str) -> Dict[str, Any]:
        """주가 정보 조회"""
        try:
            result = await self.mcp_client.call_tool("getStockQuote", {
                "symbol": ticker
            })
            return result
        except Exception as e:
            logger.error(f"주가 조회 실패: {e}")
            return {}
    
    async def _get_company_info(self, ticker: str) -> Dict[str, Any]:
        """기업 정보 조회"""
        try:
            result = await self.mcp_client.call_tool("getCompanyInfo", {
                "symbol": ticker
            })
            return result
        except Exception as e:
            logger.error(f"기업정보 조회 실패: {e}")
            return {}
    
    async def _get_historical_data(self, ticker: str) -> Dict[str, Any]:
        """과거 가격 데이터 조회"""
        try:
            result = await self.mcp_client.call_tool("getHistoricalData", {
                "symbol": ticker,
                "period": "1mo",
                "interval": "1d"
            })
            return result
        except Exception as e:
            logger.error(f"과거 데이터 조회 실패: {e}")
            return {}
    
    async def _get_technical_indicators(self, ticker: str) -> Dict[str, Any]:
        """기술적 지표 계산"""
        try:
            # MCP 서버가 기술적 지표를 제공하는 경우
            result = await self.mcp_client.call_tool("getTechnicalIndicators", {
                "symbol": ticker,
                "indicators": ["RSI", "MACD", "BB", "SMA"]
            })
            return result
        except Exception as e:
            logger.error(f"기술적 지표 계산 실패: {e}")
            # 대체: 과거 데이터로부터 간단한 지표 계산
            return self._calculate_basic_indicators(ticker)
    
    async def _get_financials(self, ticker: str) -> Dict[str, Any]:
        """재무제표 조회"""
        try:
            result = await self.mcp_client.call_tool("getFinancials", {
                "symbol": ticker,
                "statement_type": "income"
            })
            return result
        except Exception as e:
            logger.error(f"재무제표 조회 실패: {e}")
            return {}
    
    def _calculate_basic_indicators(self, ticker: str) -> Dict[str, Any]:
        """기본 기술적 지표 계산 (폴백)"""
        return {
            "calculated_locally": True,
            "message": "MCP 서버의 기술적 지표를 사용할 수 없어 기본값 제공"
        }
    
    def _generate_summary(self, results: List[Any], ticker: str) -> Dict[str, Any]:
        """분석 요약 생성"""
        summary = {
            "ticker": ticker,
            "data_availability": {
                "quote": bool(results[0] and not isinstance(results[0], Exception)),
                "company_info": bool(results[1] and not isinstance(results[1], Exception)),
                "historical_data": bool(results[2] and not isinstance(results[2], Exception)),
                "technical_indicators": bool(results[3] and not isinstance(results[3], Exception)),
                "financials": bool(results[4] and not isinstance(results[4], Exception))
            }
        }
        
        # 주가 변화율 계산
        if results[0] and not isinstance(results[0], Exception):
            quote = results[0]
            if "regularMarketPrice" in quote and "previousClose" in quote:
                change_percent = ((quote["regularMarketPrice"] - quote["previousClose"]) / 
                                quote["previousClose"] * 100)
                summary["price_change_percent"] = round(change_percent, 2)
        
        # 추천 생성
        if summary.get("price_change_percent"):
            if summary["price_change_percent"] > 2:
                summary["recommendation"] = "강한 상승세"
            elif summary["price_change_percent"] > 0:
                summary["recommendation"] = "상승세"
            elif summary["price_change_percent"] > -2:
                summary["recommendation"] = "보합세"
            else:
                summary["recommendation"] = "하락세"
        
        return summary
    
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
agent = MCPYahooFinanceAgent()
app = agent.app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8213)