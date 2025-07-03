#!/usr/bin/env python3
"""
V2 시스템 실제 동작 테스트
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_sec_agent():
    """SEC 에이전트 개선사항 테스트"""
    print("\n" + "="*60)
    print("1️⃣ SEC 데이터 분석 개선사항 테스트")
    print("="*60)
    
    message = {
        "header": {
            "message_id": f"test-sec-{datetime.now().timestamp()}",
            "message_type": "request",
            "sender_id": "test-agent",
            "sender": {
                "agent_id": "test-agent",
                "name": "Test Agent"
            },
            "timestamp": datetime.now().isoformat()
        },
        "body": {
            "action": "sec_data_collection",
            "payload": {
                "ticker": "AAPL"
            }
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("📤 SEC 에이전트에 요청 전송...")
            response = await client.post(
                "http://localhost:8210/message",
                json=message
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("body", {}).get("result", {}).get("data", [])
                
                print(f"\n✅ SEC 데이터 수집 성공!")
                print(f"📊 수집된 공시: {len(data)}건\n")
                
                # 상세 정보 확인
                for i, filing in enumerate(data[:3]):
                    print(f"📄 공시 #{i+1}")
                    print(f"  • 타입: {filing.get('form_type')}")
                    print(f"  • 날짜: {filing.get('filing_date')}")
                    print(f"  • 제목: {filing.get('title', 'N/A')}")
                    print(f"  • URL: {filing.get('url', '❌ URL 없음')}")
                    
                    # 핵심 정보 추출 확인
                    extracted = filing.get('extracted_info', {})
                    if extracted:
                        print(f"  ✨ 추출된 정보:")
                        if extracted.get('key_metrics'):
                            print(f"    - 주요 지표: {', '.join(extracted['key_metrics'])}")
                        if extracted.get('quarterly_metrics'):
                            print(f"    - 분기 지표: {', '.join(extracted['quarterly_metrics'])}")
                        if extracted.get('events'):
                            print(f"    - 이벤트: {', '.join(extracted['events'])}")
                        if extracted.get('risks'):
                            print(f"    - 리스크: {', '.join(extracted['risks'])}")
                    else:
                        print(f"  ⚠️  추출된 정보 없음 (API 제한 또는 모의 데이터)")
                    print()
            else:
                print(f"❌ 오류: HTTP {response.status_code}")
                print(f"응답: {response.text}")
                
    except Exception as e:
        print(f"❌ SEC 테스트 실패: {e}")

async def test_news_agent():
    """뉴스 번역 기능 테스트"""
    print("\n" + "="*60)
    print("2️⃣ 뉴스 번역 기능 테스트")
    print("="*60)
    
    message = {
        "header": {
            "message_id": f"test-news-{datetime.now().timestamp()}",
            "message_type": "request",
            "sender_id": "test-agent",
            "sender": {
                "agent_id": "test-agent",
                "name": "Test Agent"
            },
            "timestamp": datetime.now().isoformat()
        },
        "body": {
            "action": "news_data_collection",
            "payload": {
                "ticker": "AAPL"
            }
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("📤 뉴스 에이전트에 요청 전송...")
            response = await client.post(
                "http://localhost:8307/message",
                json=message
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("body", {}).get("result", {}).get("data", [])
                
                print(f"\n✅ 뉴스 데이터 수집 성공!")
                print(f"📰 수집된 뉴스: {len(data)}건\n")
                
                # 번역 기능 확인
                for i, news in enumerate(data[:3]):
                    print(f"📰 뉴스 #{i+1}")
                    print(f"  • 원본: {news.get('title', 'N/A')[:60]}...")
                    
                    # 번역 확인
                    translated = news.get('title_kr', '')
                    if translated and translated != news.get('title'):
                        print(f"  • 번역: {translated[:60]}...")
                    else:
                        print(f"  • 번역: ❌ 번역 안됨")
                    
                    print(f"  • URL: {news.get('url', '❌ URL 없음')}")
                    print(f"  • 날짜: {news.get('published_date', '❌ 날짜 없음')}")
                    print(f"  • 출처: {news.get('source', 'Unknown')}")
                    print()
            else:
                print(f"❌ 오류: HTTP {response.status_code}")
                
    except Exception as e:
        print(f"❌ 뉴스 테스트 실패: {e}")

async def test_twitter_agent():
    """트위터 URL 표시 테스트"""
    print("\n" + "="*60)
    print("3️⃣ 트위터 데이터 출처 표시 테스트")
    print("="*60)
    
    message = {
        "header": {
            "message_id": f"test-twitter-{datetime.now().timestamp()}",
            "message_type": "request",
            "sender_id": "test-agent",
            "sender": {
                "agent_id": "test-agent",
                "name": "Test Agent"
            },
            "timestamp": datetime.now().isoformat()
        },
        "body": {
            "action": "twitter_data_collection",
            "payload": {
                "ticker": "AAPL"
            }
        }
    }
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            print("📤 트위터 에이전트에 요청 전송...")
            response = await client.post(
                "http://localhost:8209/message",
                json=message
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get("body", {}).get("result", {}).get("data", [])
                
                print(f"\n✅ 트위터 데이터 수집 성공!")
                print(f"🐦 수집된 트윗: {len(data)}건\n")
                
                for i, tweet in enumerate(data[:3]):
                    print(f"🐦 트윗 #{i+1}")
                    print(f"  • 내용: {tweet.get('text', 'N/A')[:50]}...")
                    print(f"  • 작성자: {tweet.get('author', 'N/A')}")
                    print(f"  • URL: {tweet.get('url', '❌ URL 없음')}")
                    print(f"  • 시간: {tweet.get('created_at', '❌ 시간 없음')}")
                    print()
            else:
                print(f"❌ 오류: HTTP {response.status_code}")
                
    except Exception as e:
        print(f"❌ 트위터 테스트 실패: {e}")

async def test_full_analysis():
    """전체 시스템 통합 테스트"""
    print("\n" + "="*60)
    print("4️⃣ 전체 시스템 통합 테스트")
    print("="*60)
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            print("📤 전체 분석 요청 전송...")
            response = await client.post(
                "http://localhost:8100/analyze",
                json={"query": "애플 투자 심리 분석해줘"}
            )
            
            if response.status_code == 200:
                result = response.json()
                
                print("\n✅ 전체 분석 완료!")
                print(f"\n📊 분석 결과:")
                print(f"  • 티커: {result.get('ticker', 'N/A')}")
                print(f"  • 최종 점수: {result.get('final_score', 'N/A')}")
                print(f"  • 감정: {result.get('sentiment', 'N/A')}")
                
                # 데이터 수집 현황
                data_summary = result.get('data_summary', {})
                print(f"\n📈 데이터 수집 현황:")
                print(f"  • 뉴스: {data_summary.get('news', 0)}건")
                print(f"  • 트위터: {data_summary.get('twitter', 0)}건")
                print(f"  • SEC: {data_summary.get('sec', 0)}건")
                
                # 개선사항 확인
                report = result.get('report', '')
                if report:
                    print(f"\n✨ 개선사항 확인:")
                    print(f"  • URL 링크 포함: {'✅' if 'href=' in report else '❌'}")
                    print(f"  • 타임스탬프 표시: {'✅' if ('공시일:' in report or '발행일:' in report) else '❌'}")
                    print(f"  • 번역 기능: {'✅' if ('번역' in report or '한글' in report) else '❌'}")
                    print(f"  • SEC 상세 분석: {'✅' if ('주요 지표:' in report or '주요 이벤트:' in report) else '❌'}")
                    
                    # 리포트 일부 출력
                    print(f"\n📄 리포트 미리보기 (처음 500자):")
                    print("-" * 50)
                    # HTML 태그 제거하고 텍스트만 추출
                    import re
                    text_only = re.sub('<[^<]+?>', '', report)
                    print(text_only[:500] + "...")
                    
            else:
                print(f"❌ 오류: HTTP {response.status_code}")
                print(f"응답: {response.text[:200]}...")
                
    except Exception as e:
        print(f"❌ 전체 분석 테스트 실패: {e}")

async def main():
    """메인 테스트 실행"""
    print("\n" + "🧪"*30)
    print("A2A V2 시스템 실제 동작 테스트")
    print("🧪"*30)
    
    # 개별 에이전트 테스트
    await test_sec_agent()
    await test_news_agent()
    await test_twitter_agent()
    
    # 전체 시스템 테스트
    await test_full_analysis()
    
    print("\n" + "="*60)
    print("🏁 테스트 완료!")
    print("="*60)

if __name__ == "__main__":
    asyncio.run(main())