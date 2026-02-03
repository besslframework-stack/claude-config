"""
대화 로그 분석기
~/.claude/projects/ 폴더의 jsonl 파일을 파싱하여 대화 내용 추출
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Generator, Optional
from dataclasses import dataclass, field


@dataclass
class Message:
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None
    tool_calls: list = field(default_factory=list)
    tool_results: list = field(default_factory=list)


@dataclass
class Conversation:
    session_id: str
    project_path: str
    messages: list[Message]
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class LogAnalyzer:
    def __init__(self, claude_dir: Optional[str] = None):
        if claude_dir:
            self.claude_dir = Path(claude_dir)
        else:
            self.claude_dir = Path.home() / ".claude"
        self.projects_dir = self.claude_dir / "projects"

    def get_all_project_dirs(self) -> list[Path]:
        """모든 프로젝트 디렉토리 반환"""
        if not self.projects_dir.exists():
            return []
        return [d for d in self.projects_dir.iterdir() if d.is_dir()]

    def get_session_files(self, project_dir: Path) -> list[Path]:
        """프로젝트 내 모든 세션 파일(.jsonl) 반환"""
        return sorted(project_dir.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)

    def parse_jsonl(self, file_path: Path) -> Generator[dict, None, None]:
        """JSONL 파일 파싱"""
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue

    def extract_conversation(self, file_path: Path) -> Conversation:
        """세션 파일에서 대화 추출"""
        messages = []
        session_id = file_path.stem
        project_path = str(file_path.parent)

        for entry in self.parse_jsonl(file_path):
            msg_type = entry.get("type")

            if msg_type == "user":
                content = entry.get("message", {})
                if isinstance(content, dict):
                    text = content.get("content", "")
                else:
                    text = str(content)
                messages.append(Message(role="user", content=text))

            elif msg_type == "assistant":
                content = entry.get("message", {})
                text = ""
                tool_calls = []

                if isinstance(content, dict):
                    content_list = content.get("content", [])
                    for item in content_list:
                        if isinstance(item, dict):
                            if item.get("type") == "text":
                                text += item.get("text", "")
                            elif item.get("type") == "tool_use":
                                tool_calls.append({
                                    "name": item.get("name"),
                                    "input": item.get("input", {})
                                })

                messages.append(Message(
                    role="assistant",
                    content=text,
                    tool_calls=tool_calls
                ))

            elif msg_type == "tool_result":
                if messages and messages[-1].role == "assistant":
                    messages[-1].tool_results.append(entry.get("content", ""))

        return Conversation(
            session_id=session_id,
            project_path=project_path,
            messages=messages
        )

    def get_recent_conversations(self, limit: int = 10, project_filter: Optional[str] = None) -> list[Conversation]:
        """최근 대화 목록 반환"""
        conversations = []

        for project_dir in self.get_all_project_dirs():
            if project_filter and project_filter not in str(project_dir):
                continue

            for session_file in self.get_session_files(project_dir):
                conv = self.extract_conversation(session_file)
                if conv.messages:
                    conversations.append(conv)

                if len(conversations) >= limit:
                    return conversations

        return conversations

    def get_all_tool_usage(self, conversations: list[Conversation]) -> dict[str, int]:
        """모든 대화에서 도구 사용 빈도 집계"""
        tool_counts = {}

        for conv in conversations:
            for msg in conv.messages:
                if msg.role == "assistant":
                    for tool in msg.tool_calls:
                        name = tool.get("name", "unknown")
                        tool_counts[name] = tool_counts.get(name, 0) + 1

        return dict(sorted(tool_counts.items(), key=lambda x: x[1], reverse=True))

    def get_user_patterns(self, conversations: list[Conversation]) -> dict:
        """사용자 메시지 패턴 분석"""
        patterns = {
            "common_requests": {},
            "avg_message_length": 0,
            "question_ratio": 0,
            "code_request_ratio": 0
        }

        total_messages = 0
        total_length = 0
        question_count = 0
        code_request_count = 0

        code_keywords = ["코드", "구현", "함수", "클래스", "작성", "만들어", "생성", "code", "implement", "create", "write"]

        for conv in conversations:
            for msg in conv.messages:
                if msg.role == "user":
                    content = msg.content
                    # content가 list인 경우 문자열로 변환
                    if isinstance(content, list):
                        content = " ".join(str(item) for item in content)
                    elif not isinstance(content, str):
                        content = str(content)

                    total_messages += 1
                    total_length += len(content)

                    if "?" in content or content.strip().endswith("?"):
                        question_count += 1

                    if any(kw in content.lower() for kw in code_keywords):
                        code_request_count += 1

        if total_messages > 0:
            patterns["avg_message_length"] = total_length / total_messages
            patterns["question_ratio"] = question_count / total_messages
            patterns["code_request_ratio"] = code_request_count / total_messages

        return patterns


if __name__ == "__main__":
    analyzer = LogAnalyzer()
    conversations = analyzer.get_recent_conversations(limit=5)

    print(f"분석된 대화 수: {len(conversations)}")

    tool_usage = analyzer.get_all_tool_usage(conversations)
    print("\n도구 사용 빈도:")
    for tool, count in list(tool_usage.items())[:10]:
        print(f"  {tool}: {count}")

    patterns = analyzer.get_user_patterns(conversations)
    print(f"\n사용자 패턴:")
    print(f"  평균 메시지 길이: {patterns['avg_message_length']:.0f}자")
    print(f"  질문 비율: {patterns['question_ratio']:.1%}")
    print(f"  코드 요청 비율: {patterns['code_request_ratio']:.1%}")
