"""
CLAUDE.md 설정 생성기
대화형 질문 + 로그 분석으로 맞춤형 CLAUDE.md 생성
"""

from pathlib import Path
from datetime import datetime
from typing import Optional

from claude_config.log_analyzer import LogAnalyzer
from claude_config.pattern_extractor import PatternExtractor


class ConfigGenerator:
    def __init__(self):
        self.analyzer = LogAnalyzer()
        self.extractor = PatternExtractor()

    def ask_questions(self) -> dict:
        """사용자에게 질문하여 선호도 수집"""
        print("\n=== Claude Config 초기 설정 ===\n")

        answers = {}

        # 1. 역할
        print("1. 주로 어떤 역할로 Claude를 사용하시나요?")
        print("   1) 백엔드 개발자")
        print("   2) 프론트엔드 개발자")
        print("   3) 풀스택 개발자")
        print("   4) 데이터/ML 엔지니어")
        print("   5) DevOps/인프라")
        print("   6) 기타")
        role_map = {
            "1": "백엔드 개발자",
            "2": "프론트엔드 개발자",
            "3": "풀스택 개발자",
            "4": "데이터/ML 엔지니어",
            "5": "DevOps/인프라 엔지니어",
            "6": "개발자"
        }
        role_input = input("   선택 (1-6): ").strip() or "3"
        answers["role"] = role_map.get(role_input, "개발자")

        # 2. 주 언어
        print("\n2. 주로 사용하는 프로그래밍 언어는? (쉼표로 구분)")
        print("   예: TypeScript, Python, Go")
        languages = input("   언어: ").strip() or "TypeScript, Python"
        answers["languages"] = [l.strip() for l in languages.split(",")]

        # 3. 말투
        print("\n3. Claude의 말투 선호는?")
        print("   1) 존댓말 (정중한 어투)")
        print("   2) 반말 (편한 어투)")
        print("   3) 영어")
        tone_map = {
            "1": "존댓말",
            "2": "반말",
            "3": "영어"
        }
        tone_input = input("   선택 (1-3): ").strip() or "1"
        answers["tone"] = tone_map.get(tone_input, "존댓말")

        # 4. 코드 스타일
        print("\n4. 선호하는 코드 스타일은?")
        print("   1) 간결함 우선 (최소한의 코드)")
        print("   2) 명확함 우선 (주석, 타입 명시)")
        print("   3) 밸런스")
        style_map = {
            "1": "간결함",
            "2": "명확함",
            "3": "밸런스"
        }
        style_input = input("   선택 (1-3): ").strip() or "3"
        answers["code_style"] = style_map.get(style_input, "밸런스")

        # 5. 추가 규칙
        print("\n5. 추가하고 싶은 규칙이 있나요? (선택, 엔터로 스킵)")
        print("   예: 테스트 코드 항상 작성, 한글 주석 사용")
        extra = input("   추가 규칙: ").strip()
        answers["extra_rules"] = extra if extra else None

        return answers

    def analyze_existing_logs(self, limit: int = 20) -> dict:
        """기존 대화 로그 분석"""
        print("\n기존 대화 로그 분석 중...")

        conversations = self.analyzer.get_recent_conversations(limit=limit)

        if not conversations:
            print("  분석할 대화 로그가 없습니다.")
            return {}

        print(f"  {len(conversations)}개 대화 분석 완료")

        # 패턴 추출
        patterns = self.extractor.analyze(conversations)

        # 도구 사용 통계
        tool_usage = self.analyzer.get_all_tool_usage(conversations)

        # 주요 파일 유형
        edit_patterns = patterns.get("edit_patterns", {})
        top_extensions = list(edit_patterns.get("by_extension", {}).items())[:3]

        return {
            "corrections": patterns.get("corrections", []),
            "repeated_requests": patterns.get("repeated_requests", {}),
            "top_tools": list(tool_usage.items())[:5],
            "top_extensions": top_extensions
        }

    def generate_claude_md(self, answers: dict, analysis: dict) -> str:
        """CLAUDE.md 내용 생성"""
        today = datetime.now().strftime("%Y-%m-%d")

        md = f"""# CLAUDE.md

> 이 파일은 Claude Config에 의해 자동 생성되었습니다.
> 생성일: {today}

---

## 프로젝트 개요

이 프로젝트는 {answers['role']}가 작업하는 코드베이스입니다.

### 주요 기술 스택
{chr(10).join(f"- {lang}" for lang in answers['languages'])}

---

## 코딩 규칙

### 말투
- {"항상 존댓말을 사용합니다." if answers['tone'] == "존댓말" else "반말로 대화합니다." if answers['tone'] == "반말" else "Respond in English."}

### 코드 스타일
"""

        if answers['code_style'] == "간결함":
            md += """- 최소한의 코드로 작성
- 불필요한 주석 제거
- 자명한 코드 선호
"""
        elif answers['code_style'] == "명확함":
            md += """- 명시적인 타입 선언
- 복잡한 로직에 주석 추가
- 함수/변수명은 설명적으로
"""
        else:
            md += """- 간결함과 명확함의 균형
- 필요한 곳에만 주석
- 일관된 네이밍 컨벤션
"""

        # 추가 규칙
        if answers.get('extra_rules'):
            md += f"""
### 추가 규칙
- {answers['extra_rules']}
"""

        # 분석 기반 규칙
        if analysis:
            md += """
---

## 학습된 패턴 (대화 로그 분석)

"""
            # 교정 패턴
            corrections = analysis.get("corrections", [])
            if corrections:
                tone_corrections = [c for c in corrections if "반말" in c.get("keyword", "") or "존댓말" in c.get("keyword", "")]
                if tone_corrections:
                    md += "### 말투 교정 이력\n- 말투 관련 교정이 감지되었습니다. 위 말투 규칙을 준수해주세요.\n\n"

            # 자주 하는 작업
            requests = analysis.get("repeated_requests", {})
            if requests:
                md += "### 자주 하는 작업\n"
                for req, count in list(requests.items())[:3]:
                    md += f"- {req}: {count}회\n"
                md += "\n"

            # 주요 파일 유형
            extensions = analysis.get("top_extensions", [])
            if extensions:
                md += "### 주요 작업 파일\n"
                for ext, count in extensions:
                    md += f"- .{ext}: {count}회 편집\n"
                md += "\n"

        md += """---

## 커밋 메시지 규칙

```
feat: 새로운 기능
fix: 버그 수정
docs: 문서 변경
style: 코드 포맷팅
refactor: 리팩토링
test: 테스트
chore: 빌드/설정
```

---

## 관련 문서

- [Claude Config](https://github.com/besslframework-stack/claude-config)

---

*이 파일은 `claude-config learn` 명령으로 자동 업데이트됩니다.*
"""

        return md

    def init(self, output_path: Optional[str] = None, skip_questions: bool = False) -> str:
        """초기 설정 실행"""
        # 질문
        if skip_questions:
            answers = {
                "role": "풀스택 개발자",
                "languages": ["TypeScript", "Python"],
                "tone": "존댓말",
                "code_style": "밸런스",
                "extra_rules": None
            }
        else:
            answers = self.ask_questions()

        # 로그 분석
        analysis = self.analyze_existing_logs()

        # CLAUDE.md 생성
        content = self.generate_claude_md(answers, analysis)

        # 저장
        if output_path:
            output = Path(output_path)
        else:
            output = Path.cwd() / "CLAUDE.md"

        # 기존 파일 백업
        if output.exists():
            backup = output.with_suffix(".md.backup")
            output.rename(backup)
            print(f"\n기존 파일 백업: {backup}")

        output.write_text(content, encoding="utf-8")
        print(f"\nCLAUDE.md 생성 완료: {output}")

        return str(output)


if __name__ == "__main__":
    generator = ConfigGenerator()
    generator.init()
