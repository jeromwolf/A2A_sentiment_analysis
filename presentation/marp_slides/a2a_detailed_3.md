---
marp: true
theme: default
paginate: true
---

# A2A 심화 이해 3: 레지스트리 서버

## 우리 프로젝트의 레지스트리 (포트: 8001)

### 실제 레지스트리 서버 API
```python
# 에이전트 등록 API
@app.post("/register")
async def register_agent(agent_info: dict):
    """에이전트 등록 (예: News Agent, Sentiment Agent)"""
    agents[agent_info['name']] = {
        'id': str(uuid.uuid4()),
        'endpoint': agent_info['endpoint'],
        'capabilities': agent_info['capabilities'],
        'registered_at': datetime.utcnow(),
        'last_heartbeat': datetime.utcnow(),
        'status': 'healthy'
    }
    return {"status": "registered", "id": agents[agent_info['name']]['id']}

# 에이전트 발견 API  
@app.get("/discover")
async def discover_agents(capability: str = None):
    """능력별 에이전트 검색"""
    if capability:
        # 예: capability="sentiment_analysis" → sentiment-agent 반환
        return [
            agent for agent in agents.values()
            if capability in agent['capabilities'] 
            and agent['status'] == 'healthy'
        ]
    return list(agents.values())

# 헬스체크 API
@app.post("/heartbeat/{agent_name}")
async def heartbeat(agent_name: str):
    if agent_name in agents:
        agents[agent_name]['last_heartbeat'] = datetime.utcnow()
        return {"status": "ok"}
```

---