# Claude Config PRD

## 한 줄 요약
> Claude Code를 나에게 맞게 튜닝하는 오픈소스 도구

---

## 문제 정의

### 현재 상황
- Claude Code 사용자는 CLAUDE.md를 수동으로 관리해야 함
- 대화 로그에서 유용한 패턴이 있어도 휘발됨
- 프롬프트 최적화에 시간을 쓰기 어려움

### 타겟 사용자
- Claude Code 사용하는 개발자
- 설정 최적화에 관심 있지만 시간 없는 사람
- 소규모 팀 (2-10명)

---

## 솔루션

### 핵심 기능

| 기능 | 설명 | 우선순위 |
|------|------|----------|
| `init` | 대화 로그 분석 + 질문으로 CLAUDE.md 생성 | P0 |
| `learn` | 패턴 추출, CLAUDE.md 업데이트 제안 | P0 |
| `doc` | 세션 → 작업 로그/문서 자동 생성 | P1 |
| `analyze` | 프롬프트 효과 분석, 개선 제안 | P2 |
| `sync` | 클라우드 동기화 (Pro) | P2 |

### 사용 흐름

```bash
# 설치
npm install -g claude-config
# 또는
pip install claude-config

# 초기 설정
claude-config init

# 학습 (정기 실행)
claude-config learn

# 문서 생성
claude-config doc

# 분석
claude-config analyze
```

---

## 수익 모델

### 오픈소스 + Pro 플랜

| 플랜 | 가격 | 기능 |
|------|------|------|
| **Free** | $0 | CLI 전체 기능, 로컬 실행 |
| **Pro** | $12/월 | 클라우드 동기화, 팀 공유, 자동 백업, 웹 대시보드 |
| **Team** | $8/월/인 | Pro + 팀 통계, 공유 규칙 |

### 수익 목표
- 6개월: 100 Pro 사용자 ($1,200/월)
- 12개월: 500 Pro 사용자 ($6,000/월)

---

## MVP 범위 (Phase 1)

### 포함
- [x] `learn` - 현재 구현 완료
- [ ] `init` - CLAUDE.md 초기 생성
- [ ] CLI 패키징 (npm/pip)
- [ ] GitHub 오픈소스 공개
- [ ] 랜딩 페이지

### 제외 (Phase 2)
- `doc` - 문서 자동 생성
- `analyze` - 프롬프트 분석
- `sync` - 클라우드 동기화
- 웹 대시보드
- 팀 기능

---

## 기술 스택

### CLI (오픈소스)
- **언어**: TypeScript (Node.js) 또는 Python
- **패키징**: npm / pip
- **저장**: 로컬 파일 시스템

### Pro 백엔드 (Phase 2)
- **API**: Supabase 또는 Firebase
- **인증**: GitHub OAuth
- **결제**: Stripe

---

## 마케팅 전략

### 런칭
1. GitHub 공개 + README 잘 작성
2. Twitter/X 발표
3. Hacker News Show HN
4. Reddit r/ClaudeAI

### 지속
- 주간 업데이트 공유
- 사용자 피드백 반영
- 커뮤니티 스킬/템플릿 공유

---

## 경쟁 분석

| 경쟁자 | 차별점 |
|--------|--------|
| 수동 CLAUDE.md | 자동화 + 학습 |
| oh-my-opencode | 설정 특화 (범용 아님) |
| Cursor Rules | Claude Code 전용 |

---

## 로드맵

### Phase 1: MVP (2주)
- `init`, `learn` 완성
- npm 패키지 배포
- GitHub 공개
- 랜딩 페이지

### Phase 2: 확장 (1개월)
- `doc`, `analyze` 추가
- Pro 플랜 결제 연동
- 웹 대시보드

### Phase 3: 팀 (2개월)
- 팀 기능
- 공유 규칙
- 통계 대시보드

---

## 성공 지표

| 지표 | 목표 (6개월) |
|------|-------------|
| GitHub Stars | 1,000+ |
| 설치 수 | 5,000+ |
| Pro 전환율 | 2% |
| MRR | $1,200 |

---

*2026-02-04*
