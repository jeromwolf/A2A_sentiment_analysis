# 슬라이드 22: 데이터 수집 병렬화

## 성능 최적화: 동시 실행

### 순차 실행 (기존 방식)
```
News (2초) → Twitter (3초) → SEC (2초) = 총 7초
```

### 병렬 실행 (A2A 방식)
```python
# 모든 에이전트에게 동시 요청
tasks = []
for agent in ["news", "twitter", "sec", "mcp"]:
    task = self.send_message(
        recipient=agent,
        action="collect_data",
        payload={"ticker": ticker}
    )
    tasks.append(task)

# 동시 실행
await asyncio.gather(*tasks)
```

### 결과
```
News ──┐
Twitter ├─→ 최대 3초 (가장 느린 것)
SEC ────┘
```

**성능 향상: 7초 → 3초 (57% 단축)**