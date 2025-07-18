"""
간단한 MCP 데모 - 직접 MCP 호출하여 데이터 표시
"""

import asyncio
import httpx
import json
from datetime import datetime

async def get_stock_data_from_mcp(ticker: str):
    """MCP 서버에서 주식 데이터 가져오기"""
    async with httpx.AsyncClient() as client:
        print(f"\n📊 {ticker} 분석 중...")
        print("=" * 50)
        
        # 1. Yahoo Finance MCP에서 주가 정보
        print("\n1️⃣ Yahoo Finance MCP 호출...")
        yahoo_response = await client.post(
            "http://localhost:3001",
            json={
                "jsonrpc": "2.0",
                "id": 1,
                "method": "tools/call",
                "params": {
                    "name": "getStockQuote",
                    "arguments": {"symbol": ticker}
                }
            }
        )
        
        # 2. Alpha Vantage MCP에서 기술적 지표
        print("2️⃣ Alpha Vantage MCP 호출...")
        alpha_response = await client.post(
            "http://localhost:3002",
            json={
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/call",
                "params": {
                    "name": "RSI",
                    "arguments": {"symbol": ticker}
                }
            }
        )
        
        # 결과 파싱
        yahoo_data = eval(yahoo_response.json()["result"]["content"][0]["text"])
        alpha_data = eval(alpha_response.json()["result"]["content"][0]["text"])
        
        # 3. 회사 정보 (Yahoo MCP)
        print("3️⃣ 회사 정보 조회...")
        company_response = await client.post(
            "http://localhost:3001",
            json={
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": "getCompanyInfo",
                    "arguments": {"symbol": ticker}
                }
            }
        )
        company_data = eval(company_response.json()["result"]["content"][0]["text"])
        
        # 결과 표시
        print(f"\n✅ MCP 데이터 수집 완료!")
        print("=" * 50)
        
        print(f"\n📈 {ticker} 실시간 데이터")
        print(f"회사명: {company_data['longName']}")
        print(f"섹터: {company_data['sector']}")
        print(f"산업: {company_data['industry']}")
        print(f"시가총액: ${company_data['marketCap']:,}")
        
        print(f"\n💰 주가 정보")
        print(f"현재가: ${yahoo_data['regularMarketPrice']:.2f}")
        print(f"전일 종가: ${yahoo_data['previousClose']:.2f}")
        change = yahoo_data['regularMarketPrice'] - yahoo_data['previousClose']
        change_pct = (change / yahoo_data['previousClose']) * 100
        print(f"변동: ${change:.2f} ({change_pct:+.2f}%)")
        print(f"일중 최고: ${yahoo_data['dayHigh']:.2f}")
        print(f"일중 최저: ${yahoo_data['dayLow']:.2f}")
        print(f"거래량: {yahoo_data['volume']:,}")
        
        print(f"\n📉 기술적 지표")
        print(f"RSI: {alpha_data['RSI']:.2f}")
        print(f"RSI 신호: {alpha_data['signal']}")
        
        print(f"\n💡 간단 분석")
        if change_pct > 0:
            trend = "상승"
            emoji = "📈"
        else:
            trend = "하락"
            emoji = "📉"
            
        print(f"{emoji} 오늘 주가는 {abs(change_pct):.2f}% {trend}했습니다.")
        
        if alpha_data['RSI'] > 70:
            print("⚠️ RSI가 70 이상으로 과매수 구간입니다.")
        elif alpha_data['RSI'] < 30:
            print("💡 RSI가 30 이하로 과매도 구간입니다.")
        else:
            print("✅ RSI는 중립 구간입니다.")
        
        # JSON 형태로 반환
        return {
            "ticker": ticker,
            "timestamp": datetime.now().isoformat(),
            "data_source": "MCP (Yahoo Finance + Alpha Vantage)",
            "company": company_data,
            "price": {
                "current": yahoo_data['regularMarketPrice'],
                "change": change,
                "changePercent": change_pct,
                "volume": yahoo_data['volume']
            },
            "technical": {
                "RSI": alpha_data['RSI'],
                "signal": alpha_data['signal']
            }
        }

async def main():
    print("🚀 MCP 직접 호출 데모")
    print("MCP 서버가 실행 중이어야 합니다!")
    
    # AAPL 데이터 가져오기
    try:
        result = await get_stock_data_from_mcp("AAPL")
        print("\n\n📊 JSON 결과:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        print("MCP 서버가 실행 중인지 확인하세요:")
        print("- Yahoo Finance MCP: http://localhost:3001")
        print("- Alpha Vantage MCP: http://localhost:3002")

if __name__ == "__main__":
    asyncio.run(main())