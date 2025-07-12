# 📋 검토가 필요한 파일들

이 폴더에는 삭제 또는 재정리가 필요할 수 있는 파일들이 모여 있습니다.

## 📁 포함된 파일들

### 1. 테스트 커버리지 보고서
- **`htmlcov/`** - pytest-cov로 생성된 HTML 커버리지 보고서
  - 언제든지 `pytest --cov` 명령으로 재생성 가능
  - 일반적으로 버전 관리에서 제외됨

### 2. 유틸리티 스크립트
- **`check_v2_agents.py`** - 에이전트 상태 확인 스크립트
  - 유용한 도구이므로 `scripts/` 폴더로 이동 권장
  
- **`verify_env_and_restart.py`** - 환경 검증 스크립트
  - 시스템 시작 전 환경 체크용
  - `scripts/` 폴더로 이동 권장

## 🔍 검토 후 조치 사항

### 삭제 권장
- `htmlcov/` - 커버리지 보고서는 필요시 재생성 가능

### 이동 권장
- `check_v2_agents.py` → `scripts/` 또는 프로젝트 루트에 유지
- `verify_env_and_restart.py` → `scripts/` 또는 프로젝트 루트에 유지

### .gitignore에 추가 권장
```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.env

# Testing
.coverage
.pytest_cache/
htmlcov/
*.cover
.hypothesis/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
```

## 📌 주의사항

이 폴더의 파일들을 검토한 후:
1. 필요한 파일은 적절한 위치로 이동
2. 불필요한 파일은 삭제
3. 검토 완료 후 이 폴더도 삭제 가능