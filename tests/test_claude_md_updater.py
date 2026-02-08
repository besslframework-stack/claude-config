"""
ClaudeMdUpdater 테스트
"""

import pytest

from claude_config.claude_md_updater import ClaudeMdUpdater, UpdateSuggestion


class TestClaudeMdUpdater:
    """ClaudeMdUpdater 클래스 테스트"""

    @pytest.fixture
    def updater(self, tmp_path):
        """ClaudeMdUpdater 인스턴스 생성"""
        claude_md = tmp_path / "CLAUDE.md"
        claude_md.write_text("""# CLAUDE.md

# 영구 규칙 (Permanent)
- 기존 규칙 1

# 검증된 패턴 (Validated)
- 패턴 1

# 최근 학습 (Recent)
- 최근 항목 1

# 폐기 예정 (Deprecated)
- 삭제 예정 항목
""")
        return ClaudeMdUpdater(str(claude_md))

    def test_read_claude_md(self, updater):
        """CLAUDE.md 읽기 테스트"""
        content = updater.read_claude_md()
        assert "# CLAUDE.md" in content
        assert "영구 규칙" in content

    def test_parse_sections(self, updater):
        """섹션 파싱 테스트"""
        content = updater.read_claude_md()
        sections = updater.parse_sections(content)

        assert "permanent" in sections
        assert "validated" in sections
        assert "recent" in sections
        assert "deprecated" in sections

    def test_check_duplicate_rule(self, updater):
        """중복 규칙 확인 테스트"""
        existing = "항상 존댓말을 사용합니다. 반말 금지."

        # 유사한 규칙 - 중복으로 판단
        similar = "존댓말 사용, 반말 금지"
        assert updater.check_duplicate_rule(existing, similar) is True

        # 다른 규칙 - 중복 아님
        different = "TypeScript를 사용합니다."
        assert updater.check_duplicate_rule(existing, different) is False

    def test_generate_suggestions_with_corrections(self, updater):
        """교정 패턴에서 제안 생성 테스트"""
        patterns = {
            "corrections": [
                {"keyword": "반말", "user_correction": "반말 하지 마"},
                {"keyword": "반말", "user_correction": "반말 사용 금지"},
            ],
            "repeated_requests": {},
            "edit_patterns": {"by_extension": {}},
            "workflows": [],
        }

        suggestions = updater.generate_suggestions(patterns)

        assert len(suggestions) >= 1
        assert any(s.section == "permanent" for s in suggestions)

    def test_generate_suggestions_with_requests(self, updater):
        """반복 요청에서 제안 생성 테스트"""
        patterns = {
            "corrections": [],
            "repeated_requests": {"파일 생성": 10, "테스트": 5},
            "edit_patterns": {"by_extension": {}},
            "workflows": [],
        }

        suggestions = updater.generate_suggestions(patterns)

        assert len(suggestions) >= 1

    def test_get_update_report(self, updater):
        """업데이트 리포트 생성 테스트"""
        patterns = {
            "corrections": [],
            "repeated_requests": {"파일 생성": 10},
            "edit_patterns": {"by_extension": {"ts": 15}},
            "workflows": [],
        }

        report = updater.get_update_report(patterns)

        assert "# CLAUDE.md 업데이트 리포트" in report
        assert "생성 시간" in report


class TestUpdateSuggestion:
    """UpdateSuggestion 데이터클래스 테스트"""

    def test_suggestion_creation(self):
        """UpdateSuggestion 생성 테스트"""
        suggestion = UpdateSuggestion(
            section="recent",
            content="### 테스트 규칙\n- 테스트 항목",
            reason="테스트 이유",
            priority=2,
        )

        assert suggestion.section == "recent"
        assert suggestion.priority == 2
        assert "테스트 규칙" in suggestion.content
