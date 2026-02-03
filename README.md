# Claude Config

> Claude Code를 나에게 맞게 튜닝하는 오픈소스 도구

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

---

## 왜 Claude Config인가?

Claude Code는 강력하지만, 나에게 맞게 설정하려면 CLAUDE.md를 직접 관리해야 합니다.

**Claude Config**는:
- 대화 로그를 분석해서 **내 스타일을 학습**합니다
- 맞춤형 **CLAUDE.md를 자동 생성**합니다
- 실수 패턴을 감지해서 **규칙을 제안**합니다

---

## 설치

```bash
pip install claude-config
```

또는 pipx 사용:

```bash
pipx install claude-config
```

---

## 사용법

### 1. 초기 설정

```bash
claude-config init
```

몇 가지 질문에 답하면 맞춤형 CLAUDE.md가 생성됩니다.

```
=== Claude Config 초기 설정 ===

1. 주로 어떤 역할로 Claude를 사용하시나요?
   1) 백엔드 개발자
   2) 프론트엔드 개발자
   ...

CLAUDE.md 생성 완료: ./CLAUDE.md
```

### 2. 학습

```bash
claude-config learn
```

대화 로그를 분석해서 업데이트 제안을 받습니다.

```
# CLAUDE.md 업데이트 리포트

## 제안 사항 (3건)

### 1. [높음] 말투 관련 교정 4회 감지
- 항상 존댓말 사용
- 반말 사용 금지
...
```

제안을 바로 적용하려면:

```bash
claude-config learn --apply
```

### 3. 상세 분석

```bash
claude-config analyze
```

```
=== 도구 사용 빈도 ===
  Edit: 234
  Read: 189
  Bash: 156
  ...

=== 사용자 패턴 ===
  평균 메시지 길이: 127자
  질문 비율: 34.2%
  코드 요청 비율: 62.1%
```

---

## 명령어

| 명령어 | 설명 |
|--------|------|
| `init` | CLAUDE.md 초기 생성 |
| `learn` | 대화 분석 및 업데이트 제안 |
| `analyze` | 상세 통계 분석 |
| `doc` | 세션 → 문서 자동 생성 (곧 출시) |

---

## 로드맵

- [x] `init` - CLAUDE.md 초기 생성
- [x] `learn` - 패턴 학습 및 제안
- [x] `analyze` - 상세 분석
- [ ] `doc` - 문서 자동 생성
- [ ] Pro 플랜 - 클라우드 동기화, 팀 공유

---

## 기여

이슈와 PR을 환영합니다!

```bash
git clone https://github.com/bessl-co/claude-config
cd claude-config
pip install -e .
```

---

## 라이선스

MIT License

---

## 후원

이 프로젝트가 도움이 되셨다면:

[![Buy Me A Coffee](https://img.shields.io/badge/Buy%20Me%20A%20Coffee-donate-yellow.svg)](https://buymeacoffee.com/bessl)
[![GitHub Sponsors](https://img.shields.io/badge/GitHub%20Sponsors-sponsor-pink.svg)](https://github.com/sponsors/bessl-co)

---

Made with ❤️ by [BESSL](https://bessl.co)
