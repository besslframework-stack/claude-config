"""
CLAUDE.md 업데이터
패턴 분석 결과를 바탕으로 CLAUDE.md 업데이트 제안 생성
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass
from collections import Counter


@dataclass
class UpdateSuggestion:
    section: str  # "recent", "validated", "permanent"
    content: str
    reason: str
    priority: int  # 1: high, 2: medium, 3: low


class ClaudeMdUpdater:
    def __init__(self, claude_md_path: Optional[str] = None):
        if claude_md_path:
            self.claude_md_path = Path(claude_md_path)
        else:
            # 기본 경로: 현재 프로젝트의 CLAUDE.md
            self.claude_md_path = Path.cwd() / "CLAUDE.md"

    def read_claude_md(self) -> str:
        """CLAUDE.md 파일 읽기"""
        if self.claude_md_path.exists():
            return self.claude_md_path.read_text(encoding='utf-8')
        return ""

    def parse_sections(self, content: str) -> dict:
        """CLAUDE.md를 섹션별로 파싱"""
        sections = {
            "permanent": "",
            "validated": "",
            "recent": "",
            "deprecated": "",
            "other": ""
        }

        # 섹션 헤더 패턴
        section_patterns = {
            "permanent": r"#\s*영구\s*규칙|#\s*Permanent",
            "validated": r"#\s*검증된\s*패턴|#\s*Validated",
            "recent": r"#\s*최근\s*학습|#\s*Recent",
            "deprecated": r"#\s*폐기\s*예정|#\s*Deprecated",
        }

        current_section = "other"
        current_content = []

        for line in content.split('\n'):
            # 새 섹션 시작 확인
            found_section = False
            for section_name, pattern in section_patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    # 이전 섹션 저장
                    sections[current_section] += '\n'.join(current_content)
                    current_section = section_name
                    current_content = [line]
                    found_section = True
                    break

            if not found_section:
                current_content.append(line)

        # 마지막 섹션 저장
        sections[current_section] += '\n'.join(current_content)

        return sections

    def check_duplicate_rule(self, existing_content: str, new_rule: str) -> bool:
        """중복 규칙 확인"""
        # 핵심 키워드 추출 (명사, 동사 등)
        keywords = re.findall(r'[가-힣]{2,}|[a-zA-Z]{3,}', new_rule.lower())

        # 기존 내용에 유사한 키워드가 많이 있으면 중복으로 판단
        existing_lower = existing_content.lower()
        match_count = sum(1 for kw in keywords if kw in existing_lower)

        return match_count >= len(keywords) * 0.7  # 70% 이상 일치하면 중복

    def generate_suggestions(self, patterns: dict) -> list[UpdateSuggestion]:
        """패턴 분석 결과에서 업데이트 제안 생성"""
        suggestions = []
        today = datetime.now().strftime("%Y-%m-%d")

        # 교정 패턴에서 제안 생성
        corrections = patterns.get("corrections", [])
        if len(corrections) >= 2:
            # 말투 관련 교정
            tone_corrections = [c for c in corrections if "반말" in c.get("keyword", "") or "존댓말" in c.get("keyword", "")]
            if tone_corrections:
                suggestions.append(UpdateSuggestion(
                    section="permanent",
                    content=f"### [{today}] 말투 규칙\n- 항상 존댓말 사용\n- 반말 사용 금지\n",
                    reason=f"말투 관련 교정 {len(tone_corrections)}회 감지",
                    priority=1
                ))

        # 반복 요청에서 제안 생성
        requests = patterns.get("repeated_requests", {})
        if requests:
            top_request = max(requests.items(), key=lambda x: x[1])
            if top_request[1] >= 5:
                suggestions.append(UpdateSuggestion(
                    section="recent",
                    content=f"### [{today}] 자주 하는 작업\n- {top_request[0]}: 효율적인 워크플로우 패턴 정립 필요\n",
                    reason=f"'{top_request[0]}' 작업 {top_request[1]}회 반복",
                    priority=2
                ))

        # 편집 패턴에서 제안 생성
        edit_patterns = patterns.get("edit_patterns", {})
        by_extension = edit_patterns.get("by_extension", {})
        if by_extension:
            primary_ext = max(by_extension.items(), key=lambda x: x[1])
            if primary_ext[1] >= 10:
                suggestions.append(UpdateSuggestion(
                    section="recent",
                    content=f"### [{today}] 주요 작업 파일\n- .{primary_ext[0]} 파일 작업 빈도 높음 ({primary_ext[1]}회)\n- 관련 린팅/포맷팅 규칙 정립 권장\n",
                    reason=f".{primary_ext[0]} 파일 편집 {primary_ext[1]}회",
                    priority=3
                ))

        # 워크플로우 패턴에서 제안 생성
        workflows = patterns.get("workflows", [])
        if workflows:
            # 자주 나타나는 도구 시퀀스 찾기
            sequences = []
            for wf in workflows:
                seq = wf.get("sequence", [])
                if len(seq) >= 2:
                    for i in range(len(seq) - 1):
                        sequences.append(f"{seq[i]} → {seq[i+1]}")

            common_sequences = Counter(sequences).most_common(3)
            if common_sequences and common_sequences[0][1] >= 3:
                workflow_content = f"### [{today}] 작업 패턴\n"
                for seq, count in common_sequences:
                    workflow_content += f"- {seq}: {count}회\n"

                suggestions.append(UpdateSuggestion(
                    section="recent",
                    content=workflow_content,
                    reason="반복되는 도구 사용 패턴 감지",
                    priority=2
                ))

        return sorted(suggestions, key=lambda x: x.priority)

    def apply_suggestions(self, suggestions: list[UpdateSuggestion], dry_run: bool = True) -> str:
        """제안을 CLAUDE.md에 적용"""
        content = self.read_claude_md()
        sections = self.parse_sections(content)

        for suggestion in suggestions:
            section = suggestion.section
            if section in sections:
                # 중복 확인
                if not self.check_duplicate_rule(sections[section], suggestion.content):
                    # 섹션 끝에 추가
                    sections[section] += f"\n{suggestion.content}"

        # 섹션 재조합
        new_content = content

        if dry_run:
            print("\n=== CLAUDE.md 업데이트 미리보기 ===\n")
            for suggestion in suggestions:
                print(f"[{suggestion.section}] (우선순위: {suggestion.priority})")
                print(f"  이유: {suggestion.reason}")
                print(f"  내용:\n{suggestion.content}")
                print()
            return new_content

        # 실제 적용
        self.claude_md_path.write_text(new_content, encoding='utf-8')
        return new_content

    def get_update_report(self, patterns: dict) -> str:
        """업데이트 리포트 생성"""
        suggestions = self.generate_suggestions(patterns)

        report = "# CLAUDE.md 업데이트 리포트\n\n"
        report += f"생성 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"

        if not suggestions:
            report += "새로운 업데이트 제안이 없습니다.\n"
            return report

        report += f"## 제안 사항 ({len(suggestions)}건)\n\n"

        for i, suggestion in enumerate(suggestions, 1):
            priority_label = {1: "높음", 2: "중간", 3: "낮음"}.get(suggestion.priority, "")
            report += f"### {i}. [{priority_label}] {suggestion.reason}\n\n"
            report += f"**섹션**: {suggestion.section}\n\n"
            report += f"**제안 내용**:\n```markdown\n{suggestion.content}\n```\n\n"

        return report


if __name__ == "__main__":
    from claude_config.log_analyzer import LogAnalyzer
    from claude_config.pattern_extractor import PatternExtractor

    # 대화 로그 분석
    analyzer = LogAnalyzer()
    conversations = analyzer.get_recent_conversations(limit=20)

    # 패턴 추출
    extractor = PatternExtractor()
    patterns = extractor.analyze(conversations)

    # CLAUDE.md 업데이트 제안
    updater = ClaudeMdUpdater()

    # 리포트 생성
    report = updater.get_update_report(patterns)
    print(report)

    # 제안 적용 (dry_run=True로 미리보기만)
    suggestions = updater.generate_suggestions(patterns)
    updater.apply_suggestions(suggestions, dry_run=True)
