#!/usr/bin/env python3
"""
PDF 내보내기 기능 테스트 스크립트
"""

import asyncio
import httpx
from datetime import datetime

async def test_pdf_export():
    """PDF 내보내기 테스트"""
    
    # 테스트 데이터
    test_data = {
        "ticker": "AAPL",
        "company_name": "Apple Inc.",
        "final_score": 0.45,
        "sentiment": "positive",
        "score_details": {
            "source_averages": {"news": 0.5, "sec": 0.4},
            "source_counts": {"news": 5, "sec": 5},
            "weights_applied": {"news": 1.0, "sec": 1.5},
            "total_items": 10
        },
        "data_summary": {"news": 5, "twitter": 0, "sec": 5},
        "sentiment_analysis": [
            {
                "title": "Apple Reports Strong Q4 Results",
                "content": "Apple exceeded analyst expectations...",
                "score": 0.8,
                "source": "news",
                "sentiment": "positive"
            }
        ]
    }
    
    print("🧪 PDF 내보내기 기능 테스트 시작...")
    
    async with httpx.AsyncClient() as client:
        # 1. PDF 생성과 함께 리포트 생성
        print("\n1️⃣ PDF와 함께 리포트 생성 테스트...")
        try:
            response = await client.post(
                "http://localhost:8004/generate_report_pdf",
                json=test_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 리포트 생성 성공!")
                print(f"   - PDF 경로: {result.get('pdf_path', 'N/A')}")
                print(f"   - 요약: {result.get('summary', '')[:100]}...")
                print(f"   - 추천: {result.get('recommendation', '')}")
            else:
                print(f"❌ 리포트 생성 실패: HTTP {response.status_code}")
                print(f"   응답: {response.text}")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        
        # 2. PDF 다운로드 엔드포인트 테스트
        print("\n2️⃣ PDF 다운로드 테스트...")
        try:
            response = await client.post(
                "http://localhost:8004/export_pdf",
                json=test_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                # PDF 파일로 저장
                pdf_filename = f"test_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                with open(pdf_filename, "wb") as f:
                    f.write(response.content)
                print(f"✅ PDF 다운로드 성공! 파일 저장: {pdf_filename}")
                print(f"   - 파일 크기: {len(response.content):,} bytes")
            else:
                print(f"❌ PDF 다운로드 실패: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")
        
        # 3. 일반 리포트 생성 (PDF 없이)
        print("\n3️⃣ 일반 리포트 생성 테스트 (PDF 없이)...")
        try:
            response = await client.post(
                "http://localhost:8004/generate_report",
                json=test_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 일반 리포트 생성 성공!")
                print(f"   - PDF 경로 포함 여부: {'pdf_path' in result}")
            else:
                print(f"❌ 일반 리포트 생성 실패: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ 오류 발생: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("PDF 내보내기 기능 테스트")
    print("=" * 60)
    
    asyncio.run(test_pdf_export())
    
    print("\n✅ 테스트 완료!")