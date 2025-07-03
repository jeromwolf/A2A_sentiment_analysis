#!/usr/bin/env python3
"""데이터 수집 테스트 스크립트"""

import asyncio
import httpx
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

async def test_finnhub():
    """Finnhub API 직접 테스트"""
    api_key = os.getenv("FINNHUB_API_KEY")
    print(f"Finnhub API Key: {'설정됨' if api_key else '없음'}")
    
    if not api_key:
        print("❌ Finnhub API 키가 설정되지 않았습니다")
        return
    
    async with httpx.AsyncClient() as client:
        to_date = datetime.now()
        from_date = to_date - timedelta(days=7)
        
        try:
            response = await client.get(
                "https://finnhub.io/api/v1/company-news",
                params={
                    "symbol": "AAPL",
                    "from": from_date.strftime("%Y-%m-%d"),
                    "to": to_date.strftime("%Y-%m-%d"),
                    "token": api_key
                }
            )
            
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Finnhub 응답: {len(data)}개 뉴스")
                
                if data:
                    print("\n첫 번째 뉴스:")
                    print(f"  제목: {data[0].get('headline', '')}")
                    print(f"  날짜: {datetime.fromtimestamp(data[0].get('datetime', 0))}")
            else:
                print(f"❌ Finnhub 오류: {response.text}")
                
        except Exception as e:
            print(f"❌ 예외 발생: {e}")

async def test_news_agent():
    """News Agent 엔드포인트 테스트"""
    print("\n\n=== News Agent 테스트 ===")
    
    try:
        async with httpx.AsyncClient() as client:
            # HTTP 엔드포인트 직접 호출
            response = await client.post(
                "http://localhost:8307/collect_news_data",
                json={"ticker": "AAPL"},
                timeout=30.0
            )
            
            print(f"상태 코드: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ News Agent 응답:")
                print(f"  - 데이터 수: {len(result.get('data', []))}")
                print(f"  - 카운트: {result.get('count', 0)}")
                print(f"  - 소스: {result.get('source', 'N/A')}")
                if result.get('data'):
                    print(f"\n첫 번째 뉴스:")
                    print(f"  제목: {result['data'][0].get('title', '')}")
            else:
                print(f"❌ News Agent 오류: {response.text}")
                
    except Exception as e:
        print(f"❌ 예외 발생: {e}")

async def main():
    print("=== Finnhub API 직접 테스트 ===")
    await test_finnhub()
    
    print("\n5초 후 News Agent 테스트...")
    await asyncio.sleep(5)
    
    await test_news_agent()

if __name__ == "__main__":
    asyncio.run(main())