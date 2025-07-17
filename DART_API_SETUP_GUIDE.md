# DART API 키 발급 및 MCP 서버 설정 가이드

## 1. DART API 키 발급 방법

### Step 1: OpenDART 사이트 접속
1. **OpenDART 홈페이지 접속**: https://opendart.fss.or.kr/
2. 상단 메뉴에서 **"인증키 신청/관리"** 클릭

### Step 2: 회원가입
1. **"회원가입"** 버튼 클릭
2. 필수 정보 입력:
   - 이메일 주소 (인증 필요)
   - 비밀번호
   - 이름
   - 휴대폰 번호
3. 이메일 인증 완료

### Step 3: 로그인 및 API 키 신청
1. 가입한 계정으로 **로그인**
2. **"오픈API 이용현황"** 메뉴 클릭
3. **"인증키 신청"** 버튼 클릭
4. 사용 목적 작성:
   ```
   예시: "AI 기반 투자 분석 시스템 개발을 위한 
   한국 상장기업 공시 데이터 수집 및 분석"
   ```
5. 신청 완료

### Step 4: API 키 확인
1. 신청 즉시 **API 키 발급** (대기 시간 없음!)
2. "오픈API 이용현황"에서 발급된 키 확인
3. 키 형식: `xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` (40자리)

### Step 5: API 사용 제한
- **일일 호출 한도**: 10,000건
- **초당 호출 제한**: 없음
- **비용**: 완전 무료
- **유효기간**: 무제한

## 2. 환경 변수 설정

### .env 파일에 추가
```bash
# DART API (한국 전자공시)
DART_API_KEY=your_40_character_api_key_here
```

## 3. DART MCP 서버 설정

### Step 1: Docker 설치 확인
```bash
# Docker 설치 여부 확인
docker --version

# 없으면 설치 (Mac)
brew install docker
```

### Step 2: Claude Desktop 설정
Claude Desktop의 설정 파일에 추가:

**Mac**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "DART": {
      "command": "docker",
      "args": [
        "run",
        "--rm",
        "-i",
        "-v", ".:/app/data/mcp/DART",
        "-e", "DART_API_KEY=your_actual_api_key",
        "-e", "USECASE=light",
        "snaiws/dart:latest"
      ]
    }
  }
}
```

### Step 3: 우리 시스템에 통합

#### Option 1: 기존 DART Agent 유지 + MCP 추가
```python
# agents/dart_agent_v2.py는 그대로 두고
# MCP Data Agent에 DART MCP 기능 추가

class MCPDataAgent(BaseAgent):
    async def _fetch_dart_data(self, corp_code: str):
        """DART MCP를 통한 공시 데이터 수집"""
        # MCP 클라이언트로 DART 서버 호출
        pass
```

#### Option 2: 직접 DART API 호출 (현재 방식 유지)
```python
# 이미 구현된 dart_agent_v2.py 활용
# MCP 서버 없이도 작동
```

## 4. 테스트 코드

### DART API 직접 테스트
```python
import requests

# API 키
api_key = "your_dart_api_key"

# 삼성전자 고유번호
corp_code = "00126380"

# 공시 검색 API
url = "https://opendart.fss.or.kr/api/list.json"
params = {
    "crtfc_key": api_key,
    "corp_code": corp_code,
    "bgn_de": "20240101",  # 시작일
    "end_de": "20241231",  # 종료일
    "page_no": 1,
    "page_count": 10
}

response = requests.get(url, params=params)
data = response.json()

print(f"상태: {data['status']}")
print(f"총 {data['total_count']}건의 공시")
```

### 주요 기업 고유번호
```python
CORP_CODES = {
    "삼성전자": "00126380",
    "SK하이닉스": "00164779",
    "LG에너지솔루션": "01459484",
    "현대차": "00164742",
    "POSCO홀딩스": "00131252",
    "NAVER": "00813828",
    "카카오": "00918012",
    "셀트리온": "00821243",
    "현대모비스": "00164788",
    "기아": "00164609"
}
```

## 5. 발표 시 데모 시나리오

### 시나리오 1: DART API 직접 호출
```python
# 이미 구현된 dart_agent_v2.py 사용
"삼성전자 최근 공시 보여줘"
→ DART Agent가 실시간으로 공시 데이터 수집
```

### 시나리오 2: MCP 서버 언급
```
"DART MCP 서버를 통해 한국 기업 공시에 
표준화된 방식으로 접근할 수 있습니다.

Docker 기반으로 배포가 간편하며,
Claude Desktop과 바로 연동 가능합니다."
```

## 6. 주의사항

1. **API 키 보안**: 절대 GitHub에 직접 커밋하지 마세요
2. **호출 제한**: 일 10,000건 제한 고려
3. **데이터 저작권**: DART 데이터는 출처 표시 필요
4. **캐싱 권장**: 동일 데이터 반복 호출 방지

## 7. 추가 활용 가능 API

### DART OpenAPI 제공 항목
1. **공시검색**: 최근 공시 목록
2. **기업개황**: 기업 기본 정보
3. **사업보고서 주요정보**: 
   - 증자(감자) 현황
   - 배당 현황
   - 자기주식 현황
   - 최대주주 현황
   - 임원 현황
4. **재무정보**:
   - 단일회사 재무제표
   - 다중회사 재무제표
   - XBRL 택사노미

이제 실제 한국 기업 공시 데이터를 활용한 데모가 가능합니다!