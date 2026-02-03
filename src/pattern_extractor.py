"""
패턴 추출기
대화 로그에서 반복되는 패턴, 실수, 선호 스타일 추출
"""

import re
from collections import Counter
from dataclasses import dataclass
from typing import Optional
from log_analyzer import Conversation, Message


@dataclass
class Pattern:
    category: str  # "mistake", "preference", "workflow", "convention"
    description: str
    frequency: int
    examples: list[str]
    suggested_rule: Optional[str] = None


class PatternExtractor:
    def __init__(self):
        self.mistake_patterns = [
            {
                "pattern": r"(수정|고쳐|변경|바꿔).*(다시|다시금)",
                "category": "mistake",
                "description": "코드 수정 후 다시 수정 요청"
            },
            {
                "pattern": r"아니[야요]|그게 아니라|잘못",
                "category": "mistake",
                "description": "AI 응답 오류 지적"
            },
            {
                "pattern": r"반말.*(하지|마)|존댓말",
                "category": "preference",
                "description": "말투 선호"
            },
            {
                "pattern": r"한글|영어|Korean|English",
                "category": "preference",
                "description": "언어 선호"
            },
        ]

        self.workflow_indicators = [
            "먼저", "그 다음", "그리고", "마지막으로",
            "1단계", "2단계", "step 1", "step 2",
            "plan", "계획", "순서"
        ]

        self.code_style_patterns = [
            {
                "pattern": r"camelCase|PascalCase|snake_case|kebab-case",
                "category": "convention",
                "description": "네이밍 컨벤션"
            },
            {
                "pattern": r"TypeScript|JavaScript|Python|한글.*주석|영어.*주석",
                "category": "convention",
                "description": "언어/주석 선호"
            },
        ]

    def extract_edit_patterns(self, conversations: list[Conversation]) -> list[dict]:
        """Edit 도구 사용 패턴 분석"""
        edits = []

        for conv in conversations:
            for msg in conv.messages:
                if msg.role == "assistant":
                    for tool in msg.tool_calls:
                        if tool.get("name") == "Edit":
                            input_data = tool.get("input", {})
                            edits.append({
                                "file_path": input_data.get("file_path", ""),
                                "old_string": input_data.get("old_string", "")[:100],
                                "new_string": input_data.get("new_string", "")[:100],
                            })

        # 파일 확장자별 편집 빈도
        extensions = Counter()
        for edit in edits:
            path = edit.get("file_path", "")
            if "." in path:
                ext = path.split(".")[-1]
                extensions[ext] += 1

        return {
            "total_edits": len(edits),
            "by_extension": dict(extensions.most_common(10)),
            "recent_edits": edits[:5]
        }

    def extract_user_corrections(self, conversations: list[Conversation]) -> list[Pattern]:
        """사용자가 AI를 교정한 패턴 추출"""
        corrections = []

        correction_keywords = [
            "아니", "그게 아니라", "잘못", "틀렸", "다시",
            "이렇게 말고", "그렇게 하지 말고", "반말", "존댓말"
        ]

        for conv in conversations:
            prev_assistant_msg = None
            for msg in conv.messages:
                if msg.role == "assistant":
                    prev_assistant_msg = msg
                elif msg.role == "user" and prev_assistant_msg:
                    # content 타입 정규화
                    content = msg.content
                    if isinstance(content, list):
                        content = " ".join(str(item) for item in content)
                    elif not isinstance(content, str):
                        content = str(content)

                    prev_content = prev_assistant_msg.content
                    if isinstance(prev_content, list):
                        prev_content = " ".join(str(item) for item in prev_content)
                    elif not isinstance(prev_content, str):
                        prev_content = str(prev_content) if prev_content else ""

                    # 사용자 메시지에 교정 키워드가 있는지 확인
                    content_lower = content.lower()
                    for keyword in correction_keywords:
                        if keyword in content_lower:
                            corrections.append({
                                "user_correction": content[:200],
                                "assistant_response": prev_content[:200] if prev_content else "[tool calls only]",
                                "keyword": keyword
                            })
                            break

        return corrections

    def extract_repeated_requests(self, conversations: list[Conversation]) -> dict:
        """반복되는 요청 패턴 추출"""
        request_types = Counter()

        request_patterns = {
            "파일 생성": r"(만들어|생성|create|write).*파일|파일.*(만들어|생성)",
            "파일 수정": r"(수정|변경|edit|modify).*파일|파일.*(수정|변경)",
            "코드 리뷰": r"(리뷰|review|검토|확인)",
            "설명 요청": r"(설명|explain|알려|뭐야|무엇)",
            "테스트": r"(테스트|test|실행|run)",
            "커밋": r"(커밋|commit|푸시|push)",
            "검색": r"(찾아|검색|search|find|어디)",
            "디버깅": r"(에러|error|버그|bug|왜.*안|안.*되|fix)",
        }

        for conv in conversations:
            for msg in conv.messages:
                if msg.role == "user":
                    content = msg.content
                    if isinstance(content, list):
                        content = " ".join(str(item) for item in content)
                    elif not isinstance(content, str):
                        content = str(content)

                    for req_type, pattern in request_patterns.items():
                        if re.search(pattern, content, re.IGNORECASE):
                            request_types[req_type] += 1

        return dict(request_types.most_common())

    def extract_workflow_patterns(self, conversations: list[Conversation]) -> list[dict]:
        """작업 흐름 패턴 추출"""
        workflows = []

        for conv in conversations:
            tool_sequence = []
            for msg in conv.messages:
                if msg.role == "assistant":
                    for tool in msg.tool_calls:
                        tool_sequence.append(tool.get("name"))

            if len(tool_sequence) >= 3:
                # 3개 이상의 도구 시퀀스를 워크플로우로 기록
                workflows.append({
                    "session_id": conv.session_id,
                    "sequence": tool_sequence[:10],
                    "length": len(tool_sequence)
                })

        return workflows

    def generate_suggested_rules(self, patterns: dict) -> list[str]:
        """추출된 패턴에서 CLAUDE.md 규칙 제안 생성"""
        suggestions = []

        # 교정 패턴에서 규칙 생성
        corrections = patterns.get("corrections", [])
        correction_keywords = Counter(c.get("keyword", "") for c in corrections)

        for keyword, count in correction_keywords.most_common(3):
            if count >= 2:
                if "반말" in keyword or "존댓말" in keyword:
                    suggestions.append("## 말투 규칙\n- 항상 존댓말 사용")
                elif "아니" in keyword or "잘못" in keyword:
                    suggestions.append(f"## 확인 필요\n- '{keyword}' 관련 실수 {count}회 발생 - 관련 패턴 주의")

        # 반복 요청에서 규칙 생성
        requests = patterns.get("repeated_requests", {})
        top_requests = list(requests.items())[:3]
        if top_requests:
            workflow_suggestion = "## 자주 하는 작업\n"
            for req_type, count in top_requests:
                workflow_suggestion += f"- {req_type}: {count}회\n"
            suggestions.append(workflow_suggestion)

        # 파일 편집 패턴에서 규칙 생성
        edit_patterns = patterns.get("edit_patterns", {})
        by_extension = edit_patterns.get("by_extension", {})
        if by_extension:
            ext_suggestion = "## 주요 작업 파일 유형\n"
            for ext, count in list(by_extension.items())[:5]:
                ext_suggestion += f"- .{ext}: {count}회 편집\n"
            suggestions.append(ext_suggestion)

        return suggestions

    def analyze(self, conversations: list[Conversation]) -> dict:
        """전체 패턴 분석 실행"""
        return {
            "corrections": self.extract_user_corrections(conversations),
            "repeated_requests": self.extract_repeated_requests(conversations),
            "edit_patterns": self.extract_edit_patterns(conversations),
            "workflows": self.extract_workflow_patterns(conversations),
        }


if __name__ == "__main__":
    from log_analyzer import LogAnalyzer

    analyzer = LogAnalyzer()
    conversations = analyzer.get_recent_conversations(limit=20)

    extractor = PatternExtractor()
    patterns = extractor.analyze(conversations)

    print("=== 패턴 분석 결과 ===\n")

    print(f"교정 횟수: {len(patterns['corrections'])}")
    for c in patterns['corrections'][:3]:
        print(f"  - [{c['keyword']}] {c['user_correction'][:50]}...")

    print(f"\n반복 요청:")
    for req, count in patterns['repeated_requests'].items():
        print(f"  - {req}: {count}회")

    print(f"\n편집 패턴:")
    for ext, count in patterns['edit_patterns'].get('by_extension', {}).items():
        print(f"  - .{ext}: {count}회")

    print("\n=== 규칙 제안 ===")
    suggestions = extractor.generate_suggested_rules(patterns)
    for s in suggestions:
        print(s)
