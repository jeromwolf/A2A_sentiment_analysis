#!/usr/bin/env python3
"""
PDF 생성 기능 테스트 스크립트
"""
import asyncio
import httpx
import json
from datetime import datetime

async def test_pdf_generation():
    """PDF 생성 기능 테스트"""
    # 테스트 데이터
    test_data = {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "final_score": 0.15,
        "sentiment": "positive",
        "score_details": {
            "source_averages": {"news": 0.2, "sec": 0.1},
            "source_counts": {"news": 5, "sec": 5},
            "weights_applied": {"news": 1.0, "sec": 1.5},
            "total_items": 10
        },
        "data_summary": {"news": 5, "twitter": 0, "sec": 5},
        "sentiment_analysis": [
            {
                "title": "Apple Reports Strong Q4 Earnings",
                "title_kr": "애플, 강력한 4분기 실적 발표",
                "content": "Apple exceeded analyst expectations with record revenue.",
                "content_kr": "애플이 기록적인 매출로 애널리스트 예상을 초과했습니다.",
                "url": "https://example.com/news1",
                "source": "news",
                "published_date": "2025-07-03T10:00:00",
                "sentiment": "positive",
                "summary": "애플의 4분기 실적이 예상을 뛰어넘었습니다.",
                "score": 0.8,
                "confidence": 0.9,
                "financial_impact": "high",
                "key_topics": ["실적", "매출", "성장"],
                "risk_factors": ["경쟁 심화"],
                "opportunities": ["신제품 출시", "서비스 성장"],
                "time_horizon": "short"
            }
        ]
    }
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. PDF 생성과 함께 리포트 생성 테스트
            print("1️⃣ PDF 생성과 함께 리포트 생성 테스트...")
            response = await client.post(
                "http://localhost:8004/generate_report_pdf",
                json=test_data,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ PDF 생성 성공!")
                print(f"   PDF 경로: {result.get('pdf_path', 'N/A')}")
                print(f"   추천: {result.get('recommendation', 'N/A')}")
                print(f"   요약: {result.get('summary', 'N/A')[:100]}...")
            else:
                print(f"❌ PDF 생성 실패: {response.status_code}")
                print(f"   에러: {response.text}")
            
            # 2. PDF 다운로드 테스트
            print("\n2️⃣ PDF 다운로드 테스트...")
            response = await client.post(
                "http://localhost:8004/export_pdf",
                json=test_data,
                timeout=60.0
            )
            
            if response.status_code == 200:
                # PDF 파일 저장
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                pdf_filename = f"test_export_{timestamp}.pdf"
                with open(pdf_filename, "wb") as f:
                    f.write(response.content)
                print(f"✅ PDF 다운로드 성공! 파일 저장: {pdf_filename}")
                print(f"   파일 크기: {len(response.content):,} bytes")
            else:
                print(f"❌ PDF 다운로드 실패: {response.status_code}")
                print(f"   에러: {response.text}")
            
            # 3. 일반 리포트 생성 테스트 (PDF 없이)
            print("\n3️⃣ 일반 리포트 생성 테스트 (PDF 없이)...")
            response = await client.post(
                "http://localhost:8004/generate_report",
                json=test_data,
                timeout=60.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ 일반 리포트 생성 성공!")
                print(f"   PDF 경로 포함 여부: {'pdf_path' in result}")
            else:
                print(f"❌ 일반 리포트 생성 실패: {response.status_code}")
                
        except Exception as e:
            print(f"❌ 테스트 중 오류 발생: {e}")

if __name__ == "__main__":
    print("🚀 PDF 생성 기능 테스트 시작...\n")
    asyncio.run(test_pdf_generation())
    print("\n✅ 테스트 완료!")