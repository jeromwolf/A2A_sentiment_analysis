"""
MCP (Model Context Protocol) Server Simulator
JSON-RPC 2.0 표준을 따르는 MCP 서버 시뮬레이터
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from typing import Dict, Any, List, Optional
import uuid
from datetime import datetime
import asyncio

app = FastAPI(title="MCP Server Simulator", version="1.0.0")

# 시뮬레이션 데이터
SIMULATED_TOOLS = [
    {
        "name": "getAnalystReports",
        "description": "최신 애널리스트 리포트 조회",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "주식 티커"},
                "limit": {"type": "integer", "description": "결과 개수 제한", "default": 5}
            },
            "required": ["ticker"]
        }
    },
    {
        "name": "getInsiderTrading",
        "description": "내부자 거래 정보 조회",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "주식 티커"},
                "days": {"type": "integer", "description": "조회 기간(일)", "default": 90}
            },
            "required": ["ticker"]
        }
    },
    {
        "name": "getMarketSentiment",
        "description": "시장 심리 지표 조회",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "주식 티커"}
            },
            "required": ["ticker"]
        }
    },
    {
        "name": "getRealTimePrice",
        "description": "실시간 주가 조회",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {"type": "string", "description": "주식 티커"}
            },
            "required": ["ticker"]
        }
    }
]

SIMULATED_RESOURCES = [
    {
        "uri": "market://bloomberg/terminal",
        "name": "Bloomberg Terminal",
        "description": "Bloomberg Terminal 데이터 접근",
        "mimeType": "application/json"
    },
    {
        "uri": "market://refinitiv/eikon",
        "name": "Refinitiv Eikon",
        "description": "Refinitiv Eikon 데이터 접근",
        "mimeType": "application/json"
    }
]


@app.post("/")
async def handle_jsonrpc(request: Request):
    """JSON-RPC 2.0 요청 처리"""
    try:
        body = await request.json()
        print(f"📥 [MCP] JSON-RPC 요청 수신:")
        print(f"   - Method: {body.get('method')}")
        print(f"   - ID: {body.get('id')}")
        print(f"   - Params: {body.get('params')}")
        
        method = body.get("method")
        params = body.get("params", {})
        request_id = body.get("id")
        
        # 메서드별 처리
        if method == "initialize":
            response = await handle_initialize(params)
        elif method == "tools/list":
            response = await handle_tools_list(params)
        elif method == "tools/call":
            response = await handle_tools_call(params)
        elif method == "resources/list":
            response = await handle_resources_list(params)
        elif method == "resources/read":
            response = await handle_resources_read(params)
        else:
            # 지원하지 않는 메서드
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            })
        
        # 성공 응답
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": response
        })
        
    except Exception as e:
        print(f"❌ [MCP] 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": body.get("id") if "body" in locals() else None,
            "error": {
                "code": -32603,
                "message": f"Internal error: {str(e)}"
            }
        })


async def handle_initialize(params: Dict[str, Any]) -> Dict[str, Any]:
    """초기화 요청 처리"""
    print("🚀 [MCP] 초기화 요청 처리")
    
    client_info = params.get("clientInfo", {})
    print(f"   - Client: {client_info.get('name', 'Unknown')}")
    print(f"   - Version: {client_info.get('version', 'Unknown')}")
    
    return {
        "protocolVersion": "2024-11-05",
        "serverInfo": {
            "name": "MCP Investment Data Server",
            "version": "1.0.0"
        },
        "capabilities": {
            "tools": {},
            "resources": {
                "subscribe": True,
                "listResources": True
            }
        }
    }


async def handle_tools_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """도구 목록 요청 처리"""
    print("🔧 [MCP] 도구 목록 요청")
    
    return {
        "tools": SIMULATED_TOOLS
    }


async def handle_tools_call(params: Dict[str, Any]) -> Dict[str, Any]:
    """도구 실행 요청 처리"""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    print(f"⚡ [MCP] 도구 실행 요청:")
    print(f"   - Tool: {tool_name}")
    print(f"   - Arguments: {arguments}")
    
    # 도구별 처리
    if tool_name == "getAnalystReports":
        result = await get_analyst_reports(arguments.get("ticker"), arguments.get("limit", 5))
    elif tool_name == "getInsiderTrading":
        result = await get_insider_trading(arguments.get("ticker"), arguments.get("days", 90))
    elif tool_name == "getMarketSentiment":
        result = await get_market_sentiment(arguments.get("ticker"))
    elif tool_name == "getRealTimePrice":
        result = await get_realtime_price(arguments.get("ticker"))
    else:
        raise ValueError(f"Unknown tool: {tool_name}")
    
    return {
        "content": [
            {
                "type": "text",
                "text": f"Successfully executed {tool_name}"
            },
            {
                "type": "data",
                "data": result
            }
        ]
    }


async def handle_resources_list(params: Dict[str, Any]) -> Dict[str, Any]:
    """리소스 목록 요청 처리"""
    print("📚 [MCP] 리소스 목록 요청")
    
    return {
        "resources": SIMULATED_RESOURCES
    }


async def handle_resources_read(params: Dict[str, Any]) -> Dict[str, Any]:
    """리소스 읽기 요청 처리"""
    uri = params.get("uri")
    print(f"📖 [MCP] 리소스 읽기 요청: {uri}")
    
    # 시뮬레이션 데이터 반환
    if "bloomberg" in uri:
        content = {
            "source": "Bloomberg Terminal",
            "data": {
                "market_cap": "3.5T",
                "pe_ratio": 32.5,
                "analyst_consensus": "BUY"
            }
        }
    elif "refinitiv" in uri:
        content = {
            "source": "Refinitiv Eikon",
            "data": {
                "esg_score": 85,
                "risk_rating": "AA",
                "sector_rank": 2
            }
        }
    else:
        content = {"error": "Resource not found"}
    
    return {
        "contents": [
            {
                "uri": uri,
                "mimeType": "application/json",
                "text": str(content)
            }
        ]
    }


# 시뮬레이션 데이터 생성 함수들
async def get_analyst_reports(ticker: str, limit: int) -> List[Dict[str, Any]]:
    """애널리스트 리포트 시뮬레이션 데이터"""
    reports = []
    
    analysts = ["Goldman Sachs", "Morgan Stanley", "JP Morgan", "Bank of America", "Citi"]
    ratings = ["BUY", "HOLD", "SELL", "STRONG BUY", "STRONG SELL"]
    
    for i in range(min(limit, len(analysts))):
        reports.append({
            "id": str(uuid.uuid4()),
            "ticker": ticker,
            "analyst": analysts[i],
            "date": datetime.now().isoformat(),
            "rating": ratings[i % len(ratings)],
            "target_price": 150 + (i * 10),
            "current_price": 145,
            "summary": f"{analysts[i]} maintains {ratings[i % len(ratings)]} rating on {ticker}"
        })
    
    return reports


async def get_insider_trading(ticker: str, days: int) -> List[Dict[str, Any]]:
    """내부자 거래 시뮬레이션 데이터"""
    transactions = []
    
    insiders = ["CEO John Doe", "CFO Jane Smith", "Director Mike Johnson"]
    
    for i, insider in enumerate(insiders):
        transactions.append({
            "id": str(uuid.uuid4()),
            "ticker": ticker,
            "insider": insider,
            "date": datetime.now().isoformat(),
            "transaction_type": "BUY" if i % 2 == 0 else "SELL",
            "shares": 10000 * (i + 1),
            "price": 145 + i,
            "total_value": (10000 * (i + 1)) * (145 + i)
        })
    
    return transactions


async def get_market_sentiment(ticker: str) -> Dict[str, Any]:
    """시장 심리 시뮬레이션 데이터"""
    import random
    
    return {
        "ticker": ticker,
        "timestamp": datetime.now().isoformat(),
        "sentiment_score": round(random.uniform(0.3, 0.8), 2),
        "bullish_percent": round(random.uniform(60, 80), 1),
        "bearish_percent": round(random.uniform(20, 40), 1),
        "volume_trend": "increasing" if random.random() > 0.5 else "decreasing",
        "social_mentions": random.randint(1000, 10000),
        "news_sentiment": "positive" if random.random() > 0.3 else "neutral"
    }


async def get_realtime_price(ticker: str) -> Dict[str, Any]:
    """실시간 가격 시뮬레이션 데이터"""
    import random
    
    base_price = 150
    
    return {
        "ticker": ticker,
        "timestamp": datetime.now().isoformat(),
        "price": round(base_price + random.uniform(-5, 5), 2),
        "change": round(random.uniform(-2, 2), 2),
        "change_percent": round(random.uniform(-1.5, 1.5), 2),
        "volume": random.randint(10000000, 30000000),
        "bid": round(base_price + random.uniform(-5, 5) - 0.01, 2),
        "ask": round(base_price + random.uniform(-5, 5) + 0.01, 2),
        "high": round(base_price + random.uniform(0, 5), 2),
        "low": round(base_price - random.uniform(0, 5), 2)
    }


@app.get("/")
async def root():
    """서버 상태 확인"""
    return {
        "status": "running",
        "server": "MCP Server Simulator",
        "version": "1.0.0",
        "protocol": "JSON-RPC 2.0",
        "endpoints": {
            "jsonrpc": "POST /",
            "status": "GET /"
        }
    }


@app.get("/health")
async def health():
    """헬스 체크"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    print("🚀 MCP Server Simulator 시작 (포트: 3000)")
    print("📡 JSON-RPC 2.0 엔드포인트: http://localhost:3000/")
    uvicorn.run(app, host="0.0.0.0", port=3000)