#!/usr/bin/env python3
"""
환경 변수 로딩 테스트 스크립트
각 에이전트에서 환경 변수가 올바르게 로드되는지 확인
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def test_env_loading():
    """환경 변수 로딩 테스트"""
    print("=" * 60)
    print("환경 변수 로딩 테스트")
    print("=" * 60)
    
    # 현재 디렉토리 확인
    current_dir = Path.cwd()
    print(f"\n현재 디렉토리: {current_dir}")
    
    # .env 파일 경로
    env_path = current_dir / '.env'
    print(f".env 파일 경로: {env_path}")
    print(f".env 파일 존재: {env_path.exists()}")
    
    # 환경 변수 로드 전 상태
    print("\n[환경 변수 로드 전]")
    test_vars = ['GEMINI_API_KEY', 'FINNHUB_API_KEY', 'TWITTER_BEARER_TOKEN']
    for var in test_vars:
        value = os.getenv(var)
        if value:
            masked = value[:10] + '...' if len(value) > 10 else value
            print(f"{var}: {masked}")
        else:
            print(f"{var}: None")
    
    # .env 파일 로드
    print("\n.env 파일 로드 중...")
    load_dotenv(override=True)
    
    # 환경 변수 로드 후 상태
    print("\n[환경 변수 로드 후]")
    for var in test_vars:
        value = os.getenv(var)
        if value:
            masked = value[:10] + '...' if len(value) > 10 else value
            print(f"{var}: {masked}")
        else:
            print(f"{var}: None")
    
    # Gemini 모델 테스트
    print("\n[Gemini API 테스트]")
    try:
        import google.generativeai as genai
        api_key = os.getenv('GEMINI_API_KEY')
        if api_key:
            genai.configure(api_key=api_key)
            
            # 사용 가능한 모델 확인
            print("사용 가능한 Gemini 모델:")
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    print(f"  - {model.name}")
            
            # gemini-1.5-flash 테스트
            print("\ngemini-1.5-flash 모델 테스트:")
            model = genai.GenerativeModel('gemini-1.5-flash')
            response = model.generate_content("Reply with 'OK' if you receive this")
            print(f"응답: {response.text}")
        else:
            print("GEMINI_API_KEY가 설정되지 않았습니다.")
    except Exception as e:
        print(f"Gemini API 오류: {e}")
    
    # 환경 변수 파일 직접 읽기 테스트
    print("\n[.env 파일 직접 읽기]")
    if env_path.exists():
        with open(env_path, 'r') as f:
            lines = f.readlines()
            for line in lines:
                if 'GEMINI_API_KEY' in line:
                    key, value = line.strip().split('=', 1)
                    masked = value.strip()[:10] + '...' if len(value.strip()) > 10 else value.strip()
                    print(f"파일에서 읽은 {key}: {masked}")
                    break

if __name__ == "__main__":
    test_env_loading()