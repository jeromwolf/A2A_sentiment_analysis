"""DART 에이전트 테스트 스크립트"""

import asyncio
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

async def test_dart_agent():
    """DART 에이전트 테스트"""
    
    api_key = os.getenv("A2A_API_KEY", "test-api-key")
    
    # 1. DART 에이전트 직접 테스트
    print("=== DART 에이전트 테스트 ===")
    
    try:
        async with httpx.AsyncClient() as client:
            # 한국 기업 테스트
            test_tickers = ["삼성전자", "SK하이닉스", "005930", "SAMSUNG"]
            
            for ticker in test_tickers:
                print(f"\n테스트 티커: {ticker}")
                response = await client.post(
                    "http://localhost:8213/collect_dart",
                    json={"ticker": ticker},
                    headers={"X-API-Key": api_key},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 성공: {result['count']}개의 공시 수집")
                    if result['data']:
                        print(f"   첫 번째 공시: {result['data'][0].get('title', 'N/A')}")
                else:
                    print(f"❌ 실패: {response.status_code}")
                    print(f"   응답: {response.text}")
                    
    except httpx.ConnectError:
        print("❌ DART 에이전트 연결 실패 - 에이전트가 실행 중인지 확인하세요")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")
    
    # 2. NLU 에이전트 한국 기업 인식 테스트
    print("\n\n=== NLU 에이전트 한국 기업 인식 테스트 ===")
    
    try:
        async with httpx.AsyncClient() as client:
            test_queries = [
                "삼성전자 주가 어때?",
                "SK하이닉스 분석해줘",
                "네이버 투자 전망은?",
                "현대차 최근 실적은?"
            ]
            
            for query in test_queries:
                print(f"\n질문: {query}")
                response = await client.post(
                    "http://localhost:8108/extract_ticker",
                    json={"query": query},
                    headers={"X-API-Key": api_key},
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"✅ 티커: {result.get('ticker')}")
                    print(f"   회사명: {result.get('company_name')}")
                    print(f"   거래소: {result.get('exchange', 'N/A')}")
                else:
                    print(f"❌ 실패: {response.status_code}")
                    
    except httpx.ConnectError:
        print("❌ NLU 에이전트 연결 실패")
    except Exception as e:
        print(f"❌ 예외 발생: {e}")

if __name__ == "__main__":
    asyncio.run(test_dart_agent())