"""
Mock MCP Server for Demo
간단한 Python 기반 MCP 서버 시뮬레이터
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
from datetime import datetime
import random
import sys

# 포트 번호를 인자로 받기
port = int(sys.argv[1]) if len(sys.argv) > 1 else 3001
server_name = sys.argv[2] if len(sys.argv) > 2 else "yahoo"

app = FastAPI()

@app.post("/")
async def handle_jsonrpc(request: Request):
    """JSON-RPC 2.0 핸들러"""
    body = await request.json()
    print(f"[{server_name}] Received: {body}")
    
    method = body.get("method")
    params = body.get("params", {})
    request_id = body.get("id")
    
    # Initialize
    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}, "resources": {}},
                "serverInfo": {
                    "name": f"mock-{server_name}-mcp",
                    "version": "1.0.0"
                }
            }
        })
    
    # List tools
    elif method == "tools/list":
        if server_name == "yahoo":
            tools = [
                {
                    "name": "getStockQuote",
                    "description": "Get stock quote",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "getCompanyInfo",
                    "description": "Get company information",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"}
                        }
                    }
                }
            ]
        else:  # alpha vantage
            tools = [
                {
                    "name": "QUOTE_ENDPOINT",
                    "description": "Get real-time quote",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"}
                        }
                    }
                },
                {
                    "name": "RSI",
                    "description": "Get RSI indicator",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "symbol": {"type": "string"}
                        }
                    }
                }
            ]
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"tools": tools}
        })
    
    # Call tool
    elif method == "tools/call":
        tool_name = params.get("name")
        arguments = params.get("arguments", {})
        symbol = arguments.get("symbol", "UNKNOWN")
        
        # Yahoo Finance tools
        if tool_name == "getStockQuote":
            price = round(random.uniform(100, 200), 2)
            result = {
                "symbol": symbol,
                "regularMarketPrice": price,
                "previousClose": price - random.uniform(-5, 5),
                "dayHigh": price + random.uniform(0, 5),
                "dayLow": price - random.uniform(0, 5),
                "volume": random.randint(1000000, 50000000)
            }
        
        elif tool_name == "getCompanyInfo":
            result = {
                "symbol": symbol,
                "longName": f"{symbol} Corporation",
                "sector": "Technology",
                "industry": "Software",
                "marketCap": random.randint(1000000000, 3000000000000)
            }
        
        # Alpha Vantage tools
        elif tool_name == "QUOTE_ENDPOINT":
            price = round(random.uniform(100, 300), 2)
            result = {
                "symbol": symbol,
                "price": price,
                "change": round(random.uniform(-5, 5), 2),
                "changePercent": round(random.uniform(-3, 3), 2),
                "timestamp": datetime.now().isoformat()
            }
        
        elif tool_name == "RSI":
            rsi = round(random.uniform(30, 70), 2)
            result = {
                "symbol": symbol,
                "RSI": rsi,
                "signal": "oversold" if rsi < 30 else "overbought" if rsi > 70 else "neutral",
                "timestamp": datetime.now().isoformat()
            }
        
        else:
            result = {"error": f"Unknown tool: {tool_name}"}
        
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "content": [{
                    "type": "text",
                    "text": str(result)
                }]
            }
        })
    
    # Unknown method
    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": -32601,
            "message": f"Method not found: {method}"
        }
    })

if __name__ == "__main__":
    print(f"🚀 Starting Mock {server_name.upper()} MCP Server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)