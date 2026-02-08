# Contributing to Claude Config

Claude Config에 기여해 주셔서 감사합니다!

## 개발 환경 설정

### 1. 저장소 클론

```bash
git clone https://github.com/bessl-co/claude-config.git
cd claude-config
```

### 2. 가상 환경 생성

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
```

### 3. 개발 의존성 설치

```bash
pip install -e ".[dev]"
```

### 4. 테스트 실행

```bash
pytest
```

## 코드 스타일

- **Black**: 코드 포맷팅
- **isort**: import 정렬
- **mypy**: 타입 체킹 (선택)

### 포맷팅 적용

```bash
black claude_config tests
isort claude_config tests
```

### 포맷팅 확인

```bash
black --check claude_config tests
isort --check-only claude_config tests
```

## Pull Request 가이드

1. **Fork** 저장소
2. **Feature branch** 생성: `git checkout -b feature/amazing-feature`
3. 변경사항 **커밋**: `git commit -m 'feat: Add amazing feature'`
4. Branch **푸시**: `git push origin feature/amazing-feature`
5. **Pull Request** 생성

### 커밋 메시지 규칙

```
feat: 새로운 기능
fix: 버그 수정
docs: 문서 변경
style: 코드 포맷팅
refactor: 리팩토링
test: 테스트 추가/수정
chore: 빌드/설정 변경
```

## 테스트 작성

- 모든 새 기능에는 테스트가 필요합니다
- `tests/` 폴더에 `test_*.py` 파일 추가
- pytest fixtures 활용 권장

### 테스트 실행 예시

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=claude_config

# 특정 테스트만
pytest tests/test_log_analyzer.py -v
```

## 이슈 보고

버그를 발견하셨나요? [GitHub Issues](https://github.com/bessl-co/claude-config/issues)에서 보고해 주세요.

이슈 작성 시 포함할 내용:
- Python 버전
- OS 정보
- 재현 단계
- 예상 결과 vs 실제 결과

## 라이선스

이 프로젝트에 기여하시면 [MIT License](LICENSE)에 동의하는 것으로 간주됩니다.
