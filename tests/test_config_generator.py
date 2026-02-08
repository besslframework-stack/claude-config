"""
ConfigGenerator 테스트
"""

import pytest
from unittest.mock import patch, MagicMock

from claude_config.config_generator import ConfigGenerator


class TestConfigGenerator:
    """ConfigGenerator 클래스 테스트"""

    @pytest.fixture
    def generator(self):
        """ConfigGenerator 인스턴스 생성"""
        return ConfigGenerator()

    def test_generate_claude_md_basic(self, generator):
        """기본 CLAUDE.md 생성 테스트"""
        answers = {
            "languages": ["TypeScript", "Python"],
            "frameworks": [],
            "tone": "존댓말",
            "code_style": "밸런스",
            "extra_rules": None,
        }
        analysis = {}

        content = generator.generate_claude_md(answers, analysis)

        assert "# CLAUDE.md" in content
        assert "TypeScript" in content
        assert "Python" in content
        assert "존댓말" in content

    def test_generate_claude_md_with_extra_rules(self, generator):
        """추가 규칙 포함 CLAUDE.md 생성 테스트"""
        answers = {
            "languages": ["Python"],
            "frameworks": ["FastAPI"],
            "tone": "영어",
            "code_style": "명확함",
            "extra_rules": "테스트 코드 항상 작성",
        }
        analysis = {}

        content = generator.generate_claude_md(answers, analysis)

        assert "테스트 코드 항상 작성" in content
        assert "Respond in English" in content
        assert "명시적인 타입 선언" in content
        assert "FastAPI" in content

    def test_generate_claude_md_with_analysis(self, generator):
        """분석 결과 포함 CLAUDE.md 생성 테스트"""
        answers = {
            "languages": ["TypeScript"],
            "frameworks": ["React"],
            "tone": "반말",
            "code_style": "간결함",
            "extra_rules": None,
        }
        analysis = {
            "corrections": [],
            "repeated_requests": {"파일 생성": 5, "테스트": 3},
            "top_tools": [("Read", 10), ("Write", 5)],
            "top_extensions": [("ts", 20), ("tsx", 15)],
        }

        content = generator.generate_claude_md(answers, analysis)

        assert "로그 분석 결과" in content
        assert "파일 생성" in content
        assert "주요 파일: .ts" in content

    def test_init_with_skip_questions(self, generator, tmp_path):
        """질문 스킵 초기화 테스트"""
        output = tmp_path / "CLAUDE.md"

        # LogAnalyzer 모킹
        with patch.object(generator.analyzer, 'get_recent_conversations', return_value=[]):
            result = generator.init(output_path=str(output), skip_questions=True)

        assert output.exists()
        content = output.read_text()
        assert "# CLAUDE.md" in content
        assert "기술 스택" in content

    def test_analyze_existing_logs_empty(self, generator):
        """로그 없을 때 분석 테스트"""
        with patch.object(generator.analyzer, 'get_recent_conversations', return_value=[]):
            result = generator.analyze_existing_logs()

        assert result == {}

    def test_code_style_options(self, generator):
        """코드 스타일 옵션별 생성 테스트"""
        base_answers = {
            "languages": ["Python"],
            "frameworks": [],
            "tone": "존댓말",
            "extra_rules": None,
        }

        # 간결함
        answers = {**base_answers, "code_style": "간결함"}
        content = generator.generate_claude_md(answers, {})
        assert "최소한의 코드" in content

        # 명확함
        answers = {**base_answers, "code_style": "명확함"}
        content = generator.generate_claude_md(answers, {})
        assert "명시적인 타입 선언" in content

        # 밸런스
        answers = {**base_answers, "code_style": "밸런스"}
        content = generator.generate_claude_md(answers, {})
        assert "간결함과 명확함의 균형" in content
