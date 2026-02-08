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

    def detect_project_type(self) -> dict:
        """프로젝트 파일 구조에서 타입과 스택 자동 감지"""
        cwd = Path.cwd()
        detected = {
            "type": "general",
            "languages": [],
            "frameworks": []
        }

        # 언어/프레임워크 감지 규칙
        detections = [
            ("package.json", "JavaScript/TypeScript", ["Node.js"]),
            ("tsconfig.json", "TypeScript", []),
            ("pyproject.toml", "Python", []),
            ("requirements.txt", "Python", []),
            ("go.mod", "Go", []),
            ("Cargo.toml", "Rust", []),
            ("pom.xml", "Java", ["Maven"]),
            ("build.gradle", "Java/Kotlin", ["Gradle"]),
            ("Gemfile", "Ruby", []),
            ("composer.json", "PHP", []),
            ("pubspec.yaml", "Dart", ["Flutter"]),
        ]

        for filename, lang, frameworks in detections:
            if (cwd / filename).exists():
                if lang not in detected["languages"]:
                    detected["languages"].append(lang)
                detected["frameworks"].extend(frameworks)

        # 프레임워크 세부 감지
        if (cwd / "package.json").exists():
            try:
                import json
                pkg = json.loads((cwd / "package.json").read_text())
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "react" in deps:
                    detected["frameworks"].append("React")
                if "next" in deps:
                    detected["frameworks"].append("Next.js")
                if "vue" in deps:
                    detected["frameworks"].append("Vue")
                if "express" in deps:
                    detected["frameworks"].append("Express")
            except:
                pass

        return detected

    def ask_questions(self) -> dict:
        """사용자에게 질문하여 선호도 수집"""
        print("\n=== Claude Config 초기 설정 ===\n")

        answers = {}

        # 0. 프로젝트 자동 감지
        detected = self.detect_project_type()
        if detected["languages"]:
            print(f"감지된 스택: {', '.join(detected['languages'])}")
            if detected["frameworks"]:
                print(f"감지된 프레임워크: {', '.join(detected['frameworks'])}")
            print()

        # 1. 주 언어 (자동 감지 결과 제시)
        default_langs = ", ".join(detected["languages"]) if detected["languages"] else "TypeScript, Python"
        print(f"1. 이 프로젝트의 주요 언어는? (쉼표로 구분)")
        print(f"   감지됨: {default_langs}")
        languages = input(f"   언어 [{default_langs}]: ").strip() or default_langs
        answers["languages"] = [l.strip() for l in languages.split(",")]

        # 2. 말투
        print("\n2. Claude의 말투 선호는?")
        print("   1) 존댓말 (정중한 어투)")
        print("   2) 반말 (편한 어투)")
        print("   3) 영어")
        tone_map = {
            "1": "존댓말",
            "2": "반말",
            "3": "영어"
        }
        tone_input = input("   선택 (1-3) [1]: ").strip() or "1"
        answers["tone"] = tone_map.get(tone_input, "존댓말")

        # 3. 코드 스타일
        print("\n3. 선호하는 코드 스타일은?")
        print("   1) 간결함 우선 (최소한의 코드)")
        print("   2) 명확함 우선 (주석, 타입 명시)")
        print("   3) 밸런스")
        style_map = {
            "1": "간결함",
            "2": "명확함",
            "3": "밸런스"
        }
        style_input = input("   선택 (1-3) [3]: ").strip() or "3"
        answers["code_style"] = style_map.get(style_input, "밸런스")

        # 4. 추가 규칙
        print("\n4. 추가하고 싶은 규칙이 있나요? (선택, 엔터로 스킵)")
        print("   예: 테스트 코드 항상 작성, 한글 주석 사용")
        extra = input("   추가 규칙: ").strip()
        answers["extra_rules"] = extra if extra else None

        # 감지된 프레임워크 저장
        answers["frameworks"] = detected["frameworks"]

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
        """CLAUDE.md 내용 생성 - 계층화된 구조 사용"""
        today = datetime.now().strftime("%Y-%m-%d")

        # 기술 스택 문자열 생성
        tech_stack = "\n".join(f"- {lang}" for lang in answers['languages'])
        if answers.get('frameworks'):
            tech_stack += "\n" + "\n".join(f"- {fw}" for fw in answers['frameworks'])

        # 말투 규칙
        tone_rule = "항상 존댓말을 사용합니다." if answers['tone'] == "존댓말" else \
                    "반말로 대화합니다." if answers['tone'] == "반말" else \
                    "Respond in English."

        # 코드 스타일 규칙
        if answers['code_style'] == "간결함":
            style_rules = """- 최소한의 코드로 작성
- 불필요한 주석 제거
- 자명한 코드 선호"""
        elif answers['code_style'] == "명확함":
            style_rules = """- 명시적인 타입 선언
- 복잡한 로직에 주석 추가
- 함수/변수명은 설명적으로"""
        else:
            style_rules = """- 간결함과 명확함의 균형
- 필요한 곳에만 주석
- 일관된 네이밍 컨벤션"""

        # 추가 규칙
        extra_rules_section = ""
        if answers.get('extra_rules'):
            extra_rules_section = f"\n### 추가 규칙\n- {answers['extra_rules']}\n"

        # 학습된 패턴 섹션
        learned_patterns = ""
        if analysis:
            corrections = analysis.get("corrections", [])
            requests = analysis.get("repeated_requests", {})
            extensions = analysis.get("top_extensions", [])

            if corrections or requests or extensions:
                learned_patterns = f"\n### [{today}] 로그 분석 결과\n"

                if corrections:
                    tone_corrections = [c for c in corrections if "반말" in c.get("keyword", "") or "존댓말" in c.get("keyword", "")]
                    if tone_corrections:
                        learned_patterns += "- 말투 관련 교정 감지됨\n"

                if requests:
                    for req, count in list(requests.items())[:2]:
                        learned_patterns += f"- {req}: {count}회 반복\n"

                if extensions:
                    top_ext = extensions[0] if extensions else None
                    if top_ext:
                        learned_patterns += f"- 주요 파일: .{top_ext[0]} ({top_ext[1]}회)\n"

        md = f"""# CLAUDE.md

> 생성: {today} | Claude Config v0.2.0

---

# 영구 규칙 (Permanent)

> 변하지 않는 핵심 규칙. 삭제/수정 시 신중하게.

## 프로젝트 개요

### 기술 스택
{tech_stack}

## 코딩 규칙

### 말투
- {tone_rule}

### 코드 스타일
{style_rules}
{extra_rules_section}
### 커밋 메시지
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

# 검증된 패턴 (Validated)

> 2회 이상 유용했던 규칙. "최근 학습"에서 승격됨.

<!-- 검증된 패턴이 여기에 추가됩니다 -->

---

# 최근 학습 (Recent)

> 새로 발견한 패턴. 2회 이상 유용하면 "검증된 패턴"으로 승격.
> `claude-config learn` 실행 시 자동 업데이트됨.
{learned_patterns}
<!-- 새로운 학습은 여기에 날짜와 함께 추가 -->

---

# 폐기 예정 (Deprecated)

> 더 이상 적용 안 되거나 대체된 규칙. 다음 정리 시 삭제됨.

<!-- 폐기 예정 규칙은 여기에 추가 -->

---

## CLAUDE.md 관리 규칙

- 새 패턴 발견 시: "최근 학습" 섹션에 날짜와 함께 추가
- 2회 이상 유용했으면: "검증된 패턴"으로 이동
- 더 이상 유효하지 않으면: "폐기 예정"으로 이동
- `claude-config learn` 실행: 패턴 자동 분석 및 제안

---

*Generated by [Claude Config](https://github.com/besslframework-stack/claude-config)*
"""

        return md

    def init(self, output_path: Optional[str] = None, skip_questions: bool = False) -> str:
        """초기 설정 실행"""
        # 질문
        if skip_questions:
            detected = self.detect_project_type()
            answers = {
                "languages": detected["languages"] if detected["languages"] else ["TypeScript", "Python"],
                "frameworks": detected["frameworks"],
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
