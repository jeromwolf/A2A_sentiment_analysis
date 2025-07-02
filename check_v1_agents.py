#!/usr/bin/env python3
"""
V1 에이전트들의 상태를 확인하는 스크립트
"""

import httpx
import asyncio
from typing import Dict, Tuple

# V1 에이전트 포트 및 엔드포인트 정의
V1_AGENTS = {
    "News Agent": {
        "port": 8007,
        "health_check": "/docs",
        "test_endpoint": "/collect_news/AAPL",
        "method": "POST"
    },
    "Twitter Agent": {
        "port": 8009,
        "health_check": "/docs",
        "test_endpoint": "/search_tweets/AAPL",
        "method": "POST"
    },
    "SEC Agent": {
        "port": 8010,
        "health_check": "/docs",
        "test_endpoint": "/get_filings/AAPL",
        "method": "POST"
    },
    "NLU Agent": {
        "port": 8008,
        "health_check": "/docs",
        "test_endpoint": "/extract_ticker",
        "method": "POST",
        "test_data": {"query": "애플 주가 어때?"}
    }
}

async def check_agent(name: str, config: Dict) -> Tuple[str, Dict]:
    """개별 에이전트 상태 확인"""
    port = config["port"]
    base_url = f"http://localhost:{port}"
    result = {
        "port": port,
        "status": "offline",
        "health_check": False,
        "endpoint_test": False,
        "error": None
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        # 1. Health check (docs 페이지)
        try:
            response = await client.get(f"{base_url}{config['health_check']}")
            if response.status_code == 200:
                result["health_check"] = True
                result["status"] = "online"
        except Exception as e:
            result["error"] = f"Health check failed: {str(e)}"
            return name, result
        
        # 2. Test endpoint
        try:
            if config["method"] == "POST":
                if "test_data" in config:
                    response = await client.post(
                        f"{base_url}{config['test_endpoint']}", 
                        json=config["test_data"]
                    )
                else:
                    response = await client.post(f"{base_url}{config['test_endpoint']}")
            else:
                response = await client.get(f"{base_url}{config['test_endpoint']}")
            
            if response.status_code in [200, 201, 202]:
                result["endpoint_test"] = True
                result["status"] = "fully operational"
            else:
                result["error"] = f"Endpoint test returned {response.status_code}"
        except Exception as e:
            result["error"] = f"Endpoint test failed: {str(e)}"
    
    return name, result

async def check_all_agents():
    """모든 V1 에이전트 상태 확인"""
    print("🔍 V1 에이전트 상태 확인 중...\n")
    
    # 병렬로 모든 에이전트 확인
    tasks = [check_agent(name, config) for name, config in V1_AGENTS.items()]
    results = await asyncio.gather(*tasks)
    
    # 결과 출력
    all_operational = True
    for name, result in results:
        status_emoji = "✅" if result["status"] == "fully operational" else ("⚠️" if result["status"] == "online" else "❌")
        print(f"{status_emoji} {name} (port {result['port']}): {result['status']}")
        
        if result["health_check"]:
            print(f"   - Health check: ✅")
        else:
            print(f"   - Health check: ❌")
        
        if result["endpoint_test"]:
            print(f"   - Endpoint test: ✅")
        else:
            print(f"   - Endpoint test: ❌")
        
        if result["error"]:
            print(f"   - Error: {result['error']}")
        
        print()
        
        if result["status"] != "fully operational":
            all_operational = False
    
    # 요약
    print("="*50)
    if all_operational:
        print("✅ 모든 V1 에이전트가 정상 작동 중입니다!")
    else:
        print("⚠️ 일부 V1 에이전트가 작동하지 않습니다.")
        print("\n다음 명령어로 모든 에이전트를 시작하세요:")
        print("./start_all.sh")
        
        # 개별 시작 명령어도 제공
        print("\n또는 개별적으로 시작:")
        for name, result in results:
            if result["status"] != "fully operational":
                agent_file = name.lower().replace(" ", "_") + ".py"
                if name == "News Agent":
                    agent_file = "advanced_data_agent.py"
                print(f"uvicorn agents.{agent_file.replace('.py', '')}:app --port {result['port']} --reload &")

if __name__ == "__main__":
    asyncio.run(check_all_agents())