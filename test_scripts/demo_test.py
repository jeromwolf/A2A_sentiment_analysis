"""
MCP 데모 테스트 - 사용자가 직접 실행할 수 있는 간단한 테스트
"""

import asyncio
import httpx
import json
from datetime import datetime

async def analyze_stock(ticker: str):
    """주식 분석 시뮬레이션"""
    print(f"\n🔍 '{ticker} 분석해줘' 요청 처리 중...\n")
    
    async with httpx.AsyncClient() as client:
        # 1. Yahoo Finance에서 주가 정보
        print("1️⃣ Yahoo Finance MCP에서 실시간 주가 조회...")
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
        
        # 2. Alpha Vantage에서 기술적 지표
        print("2️⃣ Alpha Vantage MCP에서 RSI 지표 조회...")
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
        
        # 3. 분석 결과 출력
        print(f"\n📊 {ticker} 종합 분석 결과:")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        print(f"💰 현재가: ${yahoo_data['regularMarketPrice']:.2f}")
        print(f"📈 전일 종가: ${yahoo_data['previousClose']:.2f}")
        change = yahoo_data['regularMarketPrice'] - yahoo_data['previousClose']
        change_pct = (change / yahoo_data['previousClose']) * 100
        print(f"🔄 변동: ${change:.2f} ({change_pct:+.2f}%)")
        print(f"📊 거래량: {yahoo_data['volume']:,}")
        print(f"\n📉 기술적 지표:")
        print(f"   RSI: {alpha_data['RSI']:.2f} ({alpha_data['signal']})")
        
        # 4. 투자 의견
        print(f"\n💡 AI 투자 의견:")
        if change_pct > 2:
            trend = "강한 상승세"
        elif change_pct > 0:
            trend = "상승세"
        elif change_pct > -2:
            trend = "보합세"
        else:
            trend = "하락세"
            
        if alpha_data['RSI'] > 70:
            rsi_signal = "과매수 구간으로 단기 조정 가능성"
        elif alpha_data['RSI'] < 30:
            rsi_signal = "과매도 구간으로 반등 가능성"
        else:
            rsi_signal = "중립 구간"
            
        print(f"   • 현재 주가는 {trend}를 보이고 있습니다")
        print(f"   • RSI 지표는 {rsi_signal}을 나타냅니다")
        print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

async def main():
    print("🚀 MCP 투자 분석 데모")
    print("=" * 40)
    
    while True:
        print("\n주식 티커를 입력하세요 (예: AAPL, GOOGL, TSLA)")
        print("종료하려면 'exit' 입력")
        ticker = input("👉 ").strip().upper()
        
        if ticker == 'EXIT':
            print("👋 종료합니다!")
            break
            
        if ticker:
            try:
                await analyze_stock(ticker)
            except Exception as e:
                print(f"❌ 오류 발생: {e}")
                print("MCP 서버가 실행 중인지 확인해주세요!")

if __name__ == "__main__":
    asyncio.run(main())