"""
PatternExtractor 테스트
"""

import pytest

from claude_config.log_analyzer import Conversation, Message
from claude_config.pattern_extractor import PatternExtractor, Pattern


class TestPatternExtractor:
    """PatternExtractor 클래스 테스트"""

    @pytest.fixture
    def extractor(self):
        """PatternExtractor 인스턴스 생성"""
        return PatternExtractor()

    @pytest.fixture
    def sample_conversations(self):
        """테스트용 대화 데이터"""
        return [
            Conversation(
                session_id="test-1",
                project_path="/test",
                messages=[
                    Message(role="user", content="파일 만들어줘"),
                    Message(
                        role="assistant",
                        content="네, 생성하겠습니다.",
                        tool_calls=[{"name": "Write", "input": {"file_path": "test.py"}}],
                    ),
                    Message(role="user", content="아니, 그게 아니라 TypeScript로 해줘"),
                    Message(
                        role="assistant",
                        content="알겠습니다.",
                        tool_calls=[{"name": "Edit", "input": {"file_path": "test.ts", "old_string": "", "new_string": ""}}],
                    ),
                ],
            ),
            Conversation(
                session_id="test-2",
                project_path="/test",
                messages=[
                    Message(role="user", content="테스트 실행해줘"),
                    Message(
                        role="assistant",
                        content="테스트를 실행합니다.",
                        tool_calls=[{"name": "Bash", "input": {"command": "pytest"}}],
                    ),
                ],
            ),
        ]

    def test_extract_user_corrections(self, extractor, sample_conversations):
        """사용자 교정 추출 테스트"""
        corrections = extractor.extract_user_corrections(sample_conversations)

        assert len(corrections) >= 1
        assert any("아니" in c.get("keyword", "") for c in corrections)

    def test_extract_repeated_requests(self, extractor, sample_conversations):
        """반복 요청 추출 테스트"""
        requests = extractor.extract_repeated_requests(sample_conversations)

        assert isinstance(requests, dict)
        # "파일 생성" 또는 "테스트" 키워드가 있어야 함
        assert any(key in ["파일 생성", "테스트"] for key in requests.keys())

    def test_extract_edit_patterns(self, extractor, sample_conversations):
        """Edit 패턴 추출 테스트"""
        edit_patterns = extractor.extract_edit_patterns(sample_conversations)

        assert "total_edits" in edit_patterns
        assert "by_extension" in edit_patterns
        assert "recent_edits" in edit_patterns
        assert edit_patterns["total_edits"] >= 1

    def test_extract_workflow_patterns(self, extractor, sample_conversations):
        """워크플로우 패턴 추출 테스트"""
        workflows = extractor.extract_workflow_patterns(sample_conversations)

        assert isinstance(workflows, list)

    def test_generate_suggested_rules(self, extractor):
        """규칙 제안 생성 테스트"""
        patterns = {
            "corrections": [
                {"keyword": "반말", "user_correction": "반말 하지 마"},
                {"keyword": "반말", "user_correction": "반말 사용하지 마세요"},
            ],
            "repeated_requests": {"파일 생성": 5, "테스트": 3},
            "edit_patterns": {"by_extension": {"ts": 10, "py": 5}},
        }

        suggestions = extractor.generate_suggested_rules(patterns)

        assert isinstance(suggestions, list)
        assert len(suggestions) > 0

    def test_analyze(self, extractor, sample_conversations):
        """전체 분석 테스트"""
        result = extractor.analyze(sample_conversations)

        assert "corrections" in result
        assert "repeated_requests" in result
        assert "edit_patterns" in result
        assert "workflows" in result


class TestPattern:
    """Pattern 데이터클래스 테스트"""

    def test_pattern_creation(self):
        """Pattern 생성 테스트"""
        pattern = Pattern(
            category="mistake",
            description="테스트 패턴",
            frequency=5,
            examples=["예시1", "예시2"],
            suggested_rule="규칙 제안",
        )

        assert pattern.category == "mistake"
        assert pattern.frequency == 5
        assert len(pattern.examples) == 2
