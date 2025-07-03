#!/usr/bin/env python3
"""
통합 테스트 스크립트
SEC 분석, 번역, URL 표시 기능 테스트
"""

import asyncio
import httpx
import json
from datetime import datetime

async def test_improvements():
    """개선사항 통합 테스트"""
    
    print("🧪 A2A 투자 분석 시스템 개선사항 테스트 시작\n")
    
    # 테스트 시나리오
    test_query = "애플 주가 분석해줘"
    
    try:
        # 1. 메인 오케스트레이터에 요청
        print("1️⃣ 메인 오케스트레이터 테스트...")
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "http://localhost:8100/analyze",
                json={"query": test_query}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 분석 요청 성공")
                
                # 데이터 수집 결과 확인
                data_summary = result.get("data_summary", {})
                print(f"\n📊 데이터 수집 결과:")
                print(f"  - 뉴스: {data_summary.get('news', 0)}건")
                print(f"  - 트위터: {data_summary.get('twitter', 0)}건")
                print(f"  - SEC: {data_summary.get('sec', 0)}건")
                
                # 감정 분석 결과 확인
                sentiment_data = result.get("sentiment_analysis", [])
                print(f"\n🔍 감정 분석 데이터: {len(sentiment_data)}건")
                
                # 2. SEC 데이터 상세 확인
                print("\n2️⃣ SEC 데이터 분석 확인...")
                sec_items = [item for item in sentiment_data if item.get("source") == "sec"]
                if sec_items:
                    for item in sec_items[:2]:  # 상위 2개만
                        print(f"\n📄 SEC 공시:")
                        print(f"  - 타입: {item.get('form_type', 'N/A')}")
                        print(f"  - 제목: {item.get('title', 'N/A')}")
                        print(f"  - URL: {item.get('url', 'N/A')}")
                        
                        extracted = item.get('extracted_info', {})
                        if extracted:
                            print(f"  - 추출된 정보:")
                            if extracted.get('key_metrics'):
                                print(f"    • 주요 지표: {extracted['key_metrics']}")
                            if extracted.get('events'):
                                print(f"    • 주요 이벤트: {extracted['events']}")
                else:
                    print("  ⚠️ SEC 데이터가 없습니다")
                
                # 3. 번역 기능 확인
                print("\n3️⃣ 뉴스 번역 기능 확인...")
                news_items = [item for item in sentiment_data if item.get("source") == "news"]
                if news_items:
                    for item in news_items[:2]:  # 상위 2개만
                        print(f"\n📰 뉴스:")
                        print(f"  - 원본: {item.get('title', 'N/A')[:80]}...")
                        print(f"  - 번역: {item.get('title_kr', '번역 없음')[:80]}...")
                        print(f"  - URL: {item.get('url', 'N/A')}")
                        print(f"  - 날짜: {item.get('published_date', 'N/A')}")
                else:
                    print("  ⚠️ 뉴스 데이터가 없습니다")
                
                # 4. 트위터 URL 확인
                print("\n4️⃣ 트위터 데이터 출처 확인...")
                twitter_items = [item for item in sentiment_data if item.get("source") == "twitter"]
                if twitter_items:
                    for item in twitter_items[:2]:  # 상위 2개만
                        print(f"\n🐦 트윗:")
                        print(f"  - 내용: {item.get('text', 'N/A')[:80]}...")
                        print(f"  - 작성자: {item.get('author', 'N/A')}")
                        print(f"  - URL: {item.get('url', 'N/A')}")
                        print(f"  - 시간: {item.get('created_at', 'N/A')}")
                else:
                    print("  ⚠️ 트위터 데이터가 없습니다")
                
                # 5. 최종 리포트 확인
                print("\n5️⃣ 최종 리포트 생성 확인...")
                report = result.get("report", "")
                if report:
                    # URL 링크 포함 여부 확인
                    has_links = "href=" in report
                    has_timestamps = "공시일:" in report or "발행일:" in report
                    has_translation = "번역" in report or "한글" in report
                    
                    print(f"  - 리포트 길이: {len(report)} 문자")
                    print(f"  - URL 링크 포함: {'✅' if has_links else '❌'}")
                    print(f"  - 타임스탬프 포함: {'✅' if has_timestamps else '❌'}")
                    print(f"  - 번역 기능 확인: {'✅' if has_translation else '❌'}")
                else:
                    print("  ❌ 리포트가 생성되지 않았습니다")
                
            else:
                print(f"❌ 분석 요청 실패: HTTP {response.status_code}")
                
    except httpx.ConnectError:
        print("❌ 서버 연결 실패. 모든 에이전트가 실행 중인지 확인하세요.")
        print("\n필요한 에이전트:")
        print("  - Main Orchestrator V2 (포트 8100)")
        print("  - News Agent V2 (포트 8307)")
        print("  - Twitter Agent V2 (포트 8209)")
        print("  - SEC Agent V2 (포트 8210)")
        print("  - Sentiment Analysis Agent V2 (포트 8202)")
        print("  - Report Generation Agent V2 (포트 8004)")
        print("\n실행 명령: ./start_all.sh")
        
    except Exception as e:
        print(f"❌ 테스트 중 오류 발생: {str(e)}")
    
    print("\n" + "="*60)
    print("🏁 테스트 완료")
    print("="*60)

if __name__ == "__main__":
    print("A2A 투자 분석 시스템 개선사항 통합 테스트")
    print("="*60)
    print("테스트 내용:")
    print("1. SEC 공시 상세 분석 기능")
    print("2. 뉴스 한글 번역 기능")
    print("3. 데이터 URL 및 타임스탬프 표시")
    print("="*60)
    
    asyncio.run(test_improvements())