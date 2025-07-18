"""
Simple MCP Agent - MCP 서버와 연동하는 간단한 에이전트
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
import asyncio
from typing import Dict, Any
import logging
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Simple MCP Agent")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP 서버 URL
YAHOO_MCP_URL = "http://localhost:3001"
ALPHA_MCP_URL = "http://localhost:3002"

@app.get("/")
async def root():
    return {"status": "MCP Agent is running", "port": 8215}

@app.post("/collect_mcp_data")
async def collect_mcp_data(request: Dict[str, Any]):
    """MCP 서버에서 데이터 수집"""
    ticker = request.get("ticker", "")
    if not ticker:
        raise HTTPException(status_code=400, detail="ticker is required")
    
    logger.info(f"MCP 데이터 수집 시작: {ticker}")
    
    async with httpx.AsyncClient() as client:
        try:
            # 병렬로 MCP 서버 호출
            tasks = []
            
            # Yahoo Finance MCP
            tasks.append(client.post(
                YAHOO_MCP_URL,
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/call",
                    "params": {
                        "name": "getStockQuote",
                        "arguments": {"symbol": ticker}
                    }
                }
            ))
            
            # Alpha Vantage MCP
            tasks.append(client.post(
                ALPHA_MCP_URL,
                json={
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "RSI",
                        "arguments": {"symbol": ticker}
                    }
                }
            ))
            
            # 회사 정보
            tasks.append(client.post(
                YAHOO_MCP_URL,
                json={
                    "jsonrpc": "2.0",
                    "id": 3,
                    "method": "tools/call",
                    "params": {
                        "name": "getCompanyInfo",
                        "arguments": {"symbol": ticker}
                    }
                }
            ))
            
            # 모든 요청 실행
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 응답 파싱
            mcp_data = {
                "ticker": ticker,
                "timestamp": datetime.now().isoformat(),
                "source": "MCP (Yahoo Finance + Alpha Vantage)",
                "data": {}
            }
            
            # Yahoo Finance 주가 데이터
            if not isinstance(responses[0], Exception):
                yahoo_result = responses[0].json()
                if "result" in yahoo_result:
                    quote_data = eval(yahoo_result["result"]["content"][0]["text"])
                    mcp_data["data"]["price"] = {
                        "current": quote_data.get("regularMarketPrice"),
                        "previous_close": quote_data.get("previousClose"),
                        "day_high": quote_data.get("dayHigh"),
                        "day_low": quote_data.get("dayLow"),
                        "volume": quote_data.get("volume")
                    }
                    
                    # 변화율 계산
                    if quote_data.get("regularMarketPrice") and quote_data.get("previousClose"):
                        change = quote_data["regularMarketPrice"] - quote_data["previousClose"]
                        change_pct = (change / quote_data["previousClose"]) * 100
                        mcp_data["data"]["price"]["change"] = round(change, 2)
                        mcp_data["data"]["price"]["change_percent"] = round(change_pct, 2)
            
            # Alpha Vantage RSI 데이터
            if not isinstance(responses[1], Exception):
                alpha_result = responses[1].json()
                if "result" in alpha_result:
                    rsi_data = eval(alpha_result["result"]["content"][0]["text"])
                    mcp_data["data"]["technical"] = {
                        "RSI": rsi_data.get("RSI"),
                        "RSI_signal": rsi_data.get("signal")
                    }
            
            # 회사 정보
            if not isinstance(responses[2], Exception):
                company_result = responses[2].json()
                if "result" in company_result:
                    company_data = eval(company_result["result"]["content"][0]["text"])
                    mcp_data["data"]["company"] = {
                        "name": company_data.get("longName"),
                        "sector": company_data.get("sector"),
                        "industry": company_data.get("industry"),
                        "market_cap": company_data.get("marketCap")
                    }
            
            # 간단한 분석 추가
            if "price" in mcp_data["data"] and mcp_data["data"]["price"].get("change_percent"):
                change_pct = mcp_data["data"]["price"]["change_percent"]
                if change_pct > 2:
                    sentiment = "매우 긍정적"
                elif change_pct > 0:
                    sentiment = "긍정적"
                elif change_pct > -2:
                    sentiment = "중립"
                else:
                    sentiment = "부정적"
                
                mcp_data["data"]["sentiment"] = {
                    "score": 50 + (change_pct * 10),  # 간단한 점수 계산
                    "label": sentiment
                }
            
            logger.info(f"MCP 데이터 수집 완료: {ticker}")
            # 오케스트레이터가 리스트 형태의 data를 기대하므로 리스트로 래핑
            return {"data": [mcp_data]}
            
        except Exception as e:
            logger.error(f"MCP 데이터 수집 오류: {e}")
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# 레지스트리 등록 (선택사항)
async def register_to_registry():
    """레지스트리에 에이전트 등록"""
    try:
        async with httpx.AsyncClient() as client:
            await client.post(
                "http://localhost:8001/register",
                json={
                    "agent_id": "mcp-agent",
                    "name": "MCP Data Agent",
                    "type": "data_collector",
                    "capabilities": ["mcp_data", "real_time_quotes", "technical_indicators"],
                    "endpoint": "http://localhost:8215",
                    "port": 8215
                }
            )
            logger.info("레지스트리 등록 성공")
    except Exception as e:
        logger.error(f"레지스트리 등록 실패: {e}")

if __name__ == "__main__":
    import uvicorn
    
    # 시작 시 레지스트리 등록
    asyncio.run(register_to_registry())
    
    # 서버 실행
    uvicorn.run(app, host="0.0.0.0", port=8215)