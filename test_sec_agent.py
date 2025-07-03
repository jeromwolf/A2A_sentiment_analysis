#!/usr/bin/env python3
"""
SEC Agent V2 테스트 스크립트
공시 데이터 파싱 및 핵심 정보 추출 기능 테스트
"""

import asyncio
import httpx

async def test_sec_agent():
    """SEC 에이전트 테스트"""
    
    # 테스트할 티커 목록
    test_tickers = ["AAPL", "TSLA", "NVDA"]
    
    for ticker in test_tickers:
        print(f"\n{'='*60}")
        print(f"Testing SEC Agent for {ticker}")
        print(f"{'='*60}")
        
        try:
            # SEC 에이전트에 요청
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "http://localhost:8210/message",
                    json={
                        "header": {
                            "message_id": f"test-{ticker}-001",
                            "message_type": "request",
                            "sender": {
                                "agent_id": "test-agent",
                                "name": "Test Agent"
                            },
                            "timestamp": "2024-01-01T00:00:00Z"
                        },
                        "body": {
                            "action": "sec_data_collection",
                            "payload": {
                                "ticker": ticker
                            }
                        }
                    },
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    body = result.get("body", {})
                    data = body.get("result", {}).get("data", [])
                    
                    print(f"✅ 수집된 공시 개수: {len(data)}")
                    
                    # 각 공시의 상세 정보 출력
                    for i, filing in enumerate(data):
                        print(f"\n📄 공시 {i+1}:")
                        print(f"  - 타입: {filing.get('form_type')}")
                        print(f"  - 날짜: {filing.get('filing_date')}")
                        print(f"  - 제목: {filing.get('title')}")
                        print(f"  - URL: {filing.get('url')}")
                        
                        # 추출된 정보 확인
                        extracted = filing.get('extracted_info', {})
                        if extracted:
                            print(f"  - 추출된 정보:")
                            if extracted.get('key_metrics'):
                                print(f"    • 주요 지표: {', '.join(extracted['key_metrics'])}")
                            if extracted.get('quarterly_metrics'):
                                print(f"    • 분기 실적: {', '.join(extracted['quarterly_metrics'])}")
                            if extracted.get('events'):
                                print(f"    • 주요 이벤트: {', '.join(extracted['events'])}")
                            if extracted.get('risks'):
                                print(f"    • 리스크 요인: {', '.join(extracted['risks'])}")
                        
                        # 내용 미리보기
                        content = filing.get('content', '')
                        if len(content) > 200:
                            print(f"  - 내용: {content[:200]}...")
                        else:
                            print(f"  - 내용: {content}")
                else:
                    print(f"❌ 요청 실패: HTTP {response.status_code}")
                    
        except Exception as e:
            print(f"❌ 테스트 오류: {str(e)}")
            
    print(f"\n{'='*60}")
    print("테스트 완료")
    print(f"{'='*60}")

if __name__ == "__main__":
    # SEC 에이전트가 실행 중인지 확인
    print("SEC Agent V2 테스트 시작...")
    print("주의: SEC Agent V2가 포트 8210에서 실행 중이어야 합니다.")
    print("실행 명령: uvicorn agents.sec_agent_v2_pure:app --port 8210 --reload")
    input("\nEnter 키를 눌러 테스트를 시작하세요...")
    
    asyncio.run(test_sec_agent())