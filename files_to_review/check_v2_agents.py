#!/usr/bin/env python3
"""
V2 에이전트들의 상태를 확인하는 스크립트
"""

import httpx
import asyncio
from typing import Dict, Tuple

# V2 에이전트 포트 정의
V2_AGENTS = {
    "Registry": {
        "port": 8001,
        "health_check": "/discover",
        "test_endpoint": "/discover",
        "method": "GET"
    },
    "Main Orchestrator V2": {
        "port": 8100,
        "health_check": "/",
        "test_endpoint": "/",
        "method": "GET"
    },
    "NLU Agent V2": {
        "port": 8108,
        "health_check": "/health",
        "test_endpoint": "/health",
        "method": "GET"
    },
    "News Agent V2": {
        "port": 8207,
        "health_check": "/health",
        "test_endpoint": "/health",
        "method": "GET"
    },
    "Twitter Agent V2": {
        "port": 8209,
        "health_check": "/health",
        "test_endpoint": "/health",
        "method": "GET"
    },
    "SEC Agent V2": {
        "port": 8210,
        "health_check": "/health",
        "test_endpoint": "/health",
        "method": "GET"
    },
    "Sentiment Analysis V2": {
        "port": 8202,
        "health_check": "/health",
        "test_endpoint": "/analyze",
        "method": "GET"
    },
    "Score Calculation V2": {
        "port": 8203,
        "health_check": "/health",
        "test_endpoint": "/calculate",
        "method": "GET"
    },
    "Report Generation V2": {
        "port": 8204,
        "health_check": "/health",
        "test_endpoint": "/generate",
        "method": "GET"
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
        "error": None,
        "capabilities": []
    }
    
    async with httpx.AsyncClient(timeout=5.0) as client:
        # 1. Health check
        try:
            response = await client.get(f"{base_url}{config['health_check']}")
            if response.status_code == 200:
                result["health_check"] = True
                result["status"] = "online"
                
                # Registry의 경우 등록된 에이전트 정보 파싱
                if name == "Registry":
                    try:
                        data = response.json()
                        result["registered_agents"] = len(data.get("agents", []))
                    except:
                        pass
                
                # 일반 에이전트의 경우 상태 정보 파싱
                elif "status" in config["health_check"]:
                    try:
                        data = response.json()
                        result["agent_name"] = data.get("name", "Unknown")
                        result["agent_status"] = data.get("status", "Unknown")
                        result["capabilities"] = data.get("capabilities", [])
                    except:
                        pass
                        
        except Exception as e:
            result["error"] = f"Health check failed: {str(e)}"
            return name, result
        
        # 2. Test endpoint (health check와 동일한 경우 스킵)
        if config["test_endpoint"] != config["health_check"]:
            try:
                if config["method"] == "POST":
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
        else:
            result["endpoint_test"] = result["health_check"]
            if result["health_check"]:
                result["status"] = "fully operational"
    
    return name, result

async def check_all_agents():
    """모든 V2 에이전트 상태 확인"""
    print("🔍 V2 에이전트 상태 확인 중...\n")
    
    # 병렬로 모든 에이전트 확인
    tasks = [check_agent(name, config) for name, config in V2_AGENTS.items()]
    results = await asyncio.gather(*tasks)
    
    # 결과 출력
    all_operational = True
    registry_operational = False
    
    for name, result in results:
        status_emoji = "✅" if result["status"] == "fully operational" else ("⚠️" if result["status"] == "online" else "❌")
        print(f"{status_emoji} {name} (port {result['port']}): {result['status']}")
        
        if name == "Registry" and result["status"] == "fully operational":
            registry_operational = True
            if "registered_agents" in result:
                print(f"   - 등록된 에이전트: {result['registered_agents']}개")
        
        if "agent_name" in result:
            print(f"   - 에이전트 이름: {result['agent_name']}")
            
        if "capabilities" in result and result["capabilities"]:
            print(f"   - 능력: {', '.join([cap.get('name', 'Unknown') for cap in result['capabilities']])}")
        
        if result["error"]:
            print(f"   - Error: {result['error']}")
        
        print()
        
        if result["status"] != "fully operational":
            all_operational = False
    
    # 요약
    print("="*50)
    if all_operational:
        print("✅ 모든 V2 에이전트가 정상 작동 중입니다!")
    else:
        print("⚠️ 일부 V2 에이전트가 작동하지 않습니다.")
        
        if not registry_operational:
            print("\n❗ Registry가 실행되지 않았습니다. 먼저 Registry를 시작하세요:")
            print("python -m a2a_core.registry.registry_server")
        
        print("\n다음 명령어로 모든 V2 에이전트를 시작하세요:")
        print("./start_v2_agents.sh")
        
        # 개별 시작 명령어도 제공
        print("\n또는 개별적으로 시작:")
        for name, result in results:
            if result["status"] != "fully operational":
                if name == "Registry":
                    print(f"python -m a2a_core.registry.registry_server")
                elif name == "Main Orchestrator V2":
                    print(f"uvicorn main_orchestrator_v2:app --port {result['port']} --reload &")
                else:
                    agent_file = name.lower().replace(" v2", "_v2").replace(" ", "_")
                    print(f"uvicorn agents.{agent_file}:app --port {result['port']} --reload &")

if __name__ == "__main__":
    asyncio.run(check_all_agents())