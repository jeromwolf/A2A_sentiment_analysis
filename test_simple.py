#!/usr/bin/env python3
"""
간단한 시스템 테스트
"""

import requests
import json

def test_system():
    """시스템 테스트"""
    print("🧪 A2A 투자 분석 시스템 테스트")
    print("="*50)
    
    # 1. SEC 에이전트 테스트
    print("\n1️⃣ SEC 에이전트 테스트...")
    try:
        response = requests.post(
            "http://localhost:8010/collect",
            json={"ticker": "AAPL"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ SEC 데이터 수집 성공: {len(data)} 건")
            if data:
                print(f"   첫 번째 공시: {data[0].get('form_type', 'N/A')} - {data[0].get('filing_date', 'N/A')}")
        else:
            print(f"❌ SEC 에이전트 오류: {response.status_code}")
    except Exception as e:
        print(f"❌ SEC 에이전트 연결 실패: {e}")
    
    # 2. 뉴스 에이전트 테스트
    print("\n2️⃣ 뉴스 에이전트 테스트...")
    try:
        response = requests.post(
            "http://localhost:8007/collect",
            json={"ticker": "AAPL"},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 뉴스 데이터 수집 성공: {len(data)} 건")
            if data:
                print(f"   첫 번째 뉴스: {data[0].get('title', 'N/A')[:50]}...")
        else:
            print(f"❌ 뉴스 에이전트 오류: {response.status_code}")
    except Exception as e:
        print(f"❌ 뉴스 에이전트 연결 실패: {e}")
    
    # 3. 전체 시스템 테스트
    print("\n3️⃣ 전체 시스템 통합 테스트...")
    try:
        response = requests.post(
            "http://localhost:8000/analyze",
            json={"query": "애플 주가 분석해줘"},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            print("✅ 전체 분석 완료")
            print(f"   최종 점수: {result.get('final_score', 'N/A')}")
            print(f"   감정: {result.get('sentiment', 'N/A')}")
            
            # 데이터 수집 결과
            data_summary = result.get('data_summary', {})
            print(f"\n   📊 데이터 수집 결과:")
            print(f"      - 뉴스: {data_summary.get('news', 0)}건")
            print(f"      - 트위터: {data_summary.get('twitter', 0)}건") 
            print(f"      - SEC: {data_summary.get('sec', 0)}건")
            
        else:
            print(f"❌ 분석 오류: {response.status_code}")
    except Exception as e:
        print(f"❌ 시스템 연결 실패: {e}")
    
    print("\n" + "="*50)
    print("🏁 테스트 완료")

if __name__ == "__main__":
    test_system()