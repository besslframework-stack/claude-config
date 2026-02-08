"""
LogAnalyzer 테스트
"""

import json
import tempfile
from pathlib import Path

import pytest

from claude_config.log_analyzer import LogAnalyzer, Conversation, Message


class TestLogAnalyzer:
    """LogAnalyzer 클래스 테스트"""

    def test_init_default_path(self):
        """기본 경로 초기화 테스트"""
        analyzer = LogAnalyzer()
        assert analyzer.claude_dir == Path.home() / ".claude"
        assert analyzer.projects_dir == Path.home() / ".claude" / "projects"

    def test_init_custom_path(self):
        """커스텀 경로 초기화 테스트"""
        custom_path = "/tmp/test_claude"
        analyzer = LogAnalyzer(claude_dir=custom_path)
        assert analyzer.claude_dir == Path(custom_path)

    def test_parse_jsonl(self, tmp_path):
        """JSONL 파싱 테스트"""
        # 테스트 JSONL 파일 생성
        test_file = tmp_path / "test.jsonl"
        test_data = [
            {"type": "user", "message": {"content": "Hello"}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "Hi!"}]}},
        ]
        test_file.write_text("\n".join(json.dumps(d) for d in test_data))

        analyzer = LogAnalyzer()
        entries = list(analyzer.parse_jsonl(test_file))

        assert len(entries) == 2
        assert entries[0]["type"] == "user"
        assert entries[1]["type"] == "assistant"

    def test_extract_conversation(self, tmp_path):
        """대화 추출 테스트"""
        # 테스트 세션 파일 생성
        test_file = tmp_path / "test-session.jsonl"
        test_data = [
            {"type": "user", "message": {"content": "코드 작성해줘"}},
            {
                "type": "assistant",
                "message": {
                    "content": [
                        {"type": "text", "text": "네, 작성하겠습니다."},
                        {"type": "tool_use", "name": "Write", "input": {"file_path": "test.py"}},
                    ]
                },
            },
        ]
        test_file.write_text("\n".join(json.dumps(d) for d in test_data))

        analyzer = LogAnalyzer()
        conv = analyzer.extract_conversation(test_file)

        assert conv.session_id == "test-session"
        assert len(conv.messages) == 2
        assert conv.messages[0].role == "user"
        assert conv.messages[1].role == "assistant"
        assert len(conv.messages[1].tool_calls) == 1
        assert conv.messages[1].tool_calls[0]["name"] == "Write"

    def test_get_all_tool_usage(self):
        """도구 사용 집계 테스트"""
        conversations = [
            Conversation(
                session_id="test",
                project_path="/test",
                messages=[
                    Message(role="assistant", content="", tool_calls=[{"name": "Read"}]),
                    Message(role="assistant", content="", tool_calls=[{"name": "Write"}, {"name": "Read"}]),
                ],
            )
        ]

        analyzer = LogAnalyzer()
        tool_usage = analyzer.get_all_tool_usage(conversations)

        assert tool_usage["Read"] == 2
        assert tool_usage["Write"] == 1

    def test_get_user_patterns(self):
        """사용자 패턴 분석 테스트"""
        conversations = [
            Conversation(
                session_id="test",
                project_path="/test",
                messages=[
                    Message(role="user", content="이게 뭐야?"),
                    Message(role="user", content="코드 작성해줘"),
                    Message(role="user", content="테스트해봐"),
                ],
            )
        ]

        analyzer = LogAnalyzer()
        patterns = analyzer.get_user_patterns(conversations)

        assert patterns["avg_message_length"] > 0
        assert patterns["question_ratio"] > 0  # "?" 포함된 메시지 있음
        assert patterns["code_request_ratio"] > 0  # "코드" 포함된 메시지 있음


class TestMessage:
    """Message 데이터클래스 테스트"""

    def test_message_creation(self):
        """Message 생성 테스트"""
        msg = Message(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"
        assert msg.tool_calls == []
        assert msg.tool_results == []


class TestConversation:
    """Conversation 데이터클래스 테스트"""

    def test_conversation_creation(self):
        """Conversation 생성 테스트"""
        conv = Conversation(
            session_id="test-123",
            project_path="/test/project",
            messages=[Message(role="user", content="Hi")],
        )
        assert conv.session_id == "test-123"
        assert conv.project_path == "/test/project"
        assert len(conv.messages) == 1
