#!/usr/bin/env python3
"""
환경 변수 캐싱 문제 해결 및 API 키 검증 스크립트
"""

import os
import sys
import time
import subprocess
import signal
from pathlib import Path
from dotenv import load_dotenv

def kill_all_processes():
    """모든 uvicorn 및 agent 관련 프로세스 종료"""
    print("=" * 60)
    print("1단계: 실행 중인 프로세스 종료")
    print("=" * 60)
    
    # 프로세스 찾기 및 종료
    try:
        # uvicorn 프로세스 찾기
        result = subprocess.run(
            ["ps", "aux"], 
            capture_output=True, 
            text=True
        )
        
        processes_killed = 0
        for line in result.stdout.split('\n'):
            if ('uvicorn' in line or 'agent' in line) and 'grep' not in line and 'verify_env' not in line:
                parts = line.split()
                if len(parts) > 1:
                    pid = parts[1]
                    try:
                        os.kill(int(pid), signal.SIGTERM)
                        print(f"✓ 프로세스 종료: PID {pid}")
                        processes_killed += 1
                    except ProcessLookupError:
                        print(f"- 프로세스 {pid}는 이미 종료됨")
                    except Exception as e:
                        print(f"✗ 프로세스 {pid} 종료 실패: {e}")
        
        if processes_killed == 0:
            print("종료할 프로세스가 없습니다.")
        else:
            print(f"\n총 {processes_killed}개의 프로세스를 종료했습니다.")
            print("프로세스가 완전히 종료될 때까지 3초 대기...")
            time.sleep(3)
            
    except Exception as e:
        print(f"프로세스 종료 중 오류 발생: {e}")

def verify_env_file():
    """환경 변수 파일 검증"""
    print("\n" + "=" * 60)
    print("2단계: 환경 변수 파일 검증")
    print("=" * 60)
    
    env_path = Path('.env')
    
    if not env_path.exists():
        print("✗ .env 파일이 존재하지 않습니다!")
        return False
    
    print(f"✓ .env 파일 위치: {env_path.absolute()}")
    
    # .env 파일 내용 확인 (API 키는 마스킹)
    with open(env_path, 'r') as f:
        content = f.read()
        lines = content.strip().split('\n')
        
    print(f"\n.env 파일 내용 ({len(lines)}개 항목):")
    print("-" * 40)
    
    for line in lines:
        if '=' in line and not line.strip().startswith('#'):
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            
            # API 키 마스킹
            if value and len(value) > 8:
                masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:]
            else:
                masked_value = value
                
            print(f"{key} = {masked_value}")
    
    return True

def load_and_verify_env():
    """환경 변수 로드 및 검증"""
    print("\n" + "=" * 60)
    print("3단계: 환경 변수 로드 및 검증")
    print("=" * 60)
    
    # 기존 환경 변수 초기화
    env_vars = ['GEMINI_API_KEY', 'FINNHUB_API_KEY', 'TWITTER_BEARER_TOKEN', 
                'SEC_API_USER_AGENT', 'MAX_ARTICLES_TO_SCRAPE']
    
    print("기존 환경 변수 제거:")
    for var in env_vars:
        if var in os.environ:
            del os.environ[var]
            print(f"✓ {var} 제거됨")
    
    # .env 파일 새로 로드
    print("\n.env 파일 로드 중...")
    load_dotenv(override=True)
    
    # 로드된 환경 변수 확인
    print("\n로드된 환경 변수:")
    print("-" * 40)
    
    missing_vars = []
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if var in ['GEMINI_API_KEY', 'FINNHUB_API_KEY', 'TWITTER_BEARER_TOKEN']:
                # API 키 마스킹
                if len(value) > 8:
                    masked_value = value[:4] + '*' * (len(value) - 8) + value[-4:]
                else:
                    masked_value = value
                print(f"✓ {var} = {masked_value}")
            else:
                print(f"✓ {var} = {value}")
        else:
            print(f"✗ {var} = None (설정되지 않음)")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n⚠️  경고: {', '.join(missing_vars)} 환경 변수가 설정되지 않았습니다!")
        return False
    
    return True

def test_api_keys():
    """API 키 유효성 테스트"""
    print("\n" + "=" * 60)
    print("4단계: API 키 유효성 테스트")
    print("=" * 60)
    
    # Gemini API 테스트
    gemini_key = os.getenv('GEMINI_API_KEY')
    if gemini_key:
        print("\nGemini API 키 테스트:")
        try:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content("Say 'API key is valid'")
            print(f"✓ Gemini API 키 유효: {response.text[:50]}...")
        except Exception as e:
            print(f"✗ Gemini API 키 오류: {str(e)[:100]}...")
    
    # Finnhub API 테스트
    finnhub_key = os.getenv('FINNHUB_API_KEY')
    if finnhub_key:
        print("\nFinnhub API 키 테스트:")
        try:
            import requests
            response = requests.get(
                f'https://finnhub.io/api/v1/quote?symbol=AAPL&token={finnhub_key}',
                timeout=5
            )
            if response.status_code == 200:
                print("✓ Finnhub API 키 유효")
            else:
                print(f"✗ Finnhub API 응답 오류: {response.status_code}")
        except Exception as e:
            print(f"✗ Finnhub API 테스트 실패: {str(e)[:100]}...")

def show_restart_instructions():
    """재시작 방법 안내"""
    print("\n" + "=" * 60)
    print("5단계: 서비스 재시작 방법")
    print("=" * 60)
    
    print("\n환경 변수가 올바르게 설정되었습니다.")
    print("이제 서비스를 재시작하세요:\n")
    
    print("옵션 1 - 전체 서비스 시작 (권장):")
    print("  ./start_v2_complete.sh")
    
    print("\n옵션 2 - 개별 에이전트 시작:")
    print("  uvicorn main_orchestrator_v2:app --port 8100 --reload &")
    print("  uvicorn agents.nlu_agent_v2:app --port 8108 --reload &")
    print("  uvicorn agents.news_agent_v2_pure:app --port 8307 --reload &")
    print("  # ... 기타 에이전트들")
    
    print("\n옵션 3 - 테스트 모드로 단일 에이전트 실행:")
    print("  python -c \"import os; from dotenv import load_dotenv; load_dotenv(); print('GEMINI_API_KEY:', os.getenv('GEMINI_API_KEY')[:10] + '...')\"")
    print("  uvicorn agents.sentiment_analysis_agent_v2:app --port 8202 --reload")

def main():
    """메인 실행 함수"""
    print("\n🔧 환경 변수 캐싱 문제 해결 스크립트\n")
    
    # 1. 프로세스 종료
    kill_all_processes()
    
    # 2. 환경 변수 파일 확인
    if not verify_env_file():
        print("\n❌ .env 파일을 먼저 생성하세요!")
        sys.exit(1)
    
    # 3. 환경 변수 로드 및 검증
    if not load_and_verify_env():
        print("\n❌ 필수 환경 변수가 설정되지 않았습니다!")
        sys.exit(1)
    
    # 4. API 키 테스트
    test_api_keys()
    
    # 5. 재시작 안내
    show_restart_instructions()
    
    print("\n✅ 환경 변수 검증 완료!\n")

if __name__ == "__main__":
    main()