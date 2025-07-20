# 슬라이드 18: 확장성 설계

## 새로운 기능 추가가 쉬운 이유

### 새 데이터 소스 추가 예시

```python
# 1. 새 에이전트 생성
class RedditAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Reddit Agent",
            port=8220
        )
    
    async def collect_reddit_data(self, ticker):
        # Reddit API 호출
        return reddit_posts

# 2. 자동 등록 및 통합
# 시스템 재시작만으로 즉시 사용 가능
```

### 장점
- ✅ 기존 코드 수정 불필요
- ✅ 독립적 배포 가능
- ✅ 장애 격리