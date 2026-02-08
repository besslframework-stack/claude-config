"""
HandoffGenerator 테스트
"""

import json
import pytest
from pathlib import Path

from claude_config.handoff_generator import HandoffGenerator, HandoffContext


class TestHandoffGenerator:
    """HandoffGenerator 클래스 테스트"""

    @pytest.fixture
    def generator(self, tmp_path):
        """HandoffGenerator 인스턴스 생성"""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir()
        return HandoffGenerator(str(claude_dir))

    @pytest.fixture
    def sample_session(self, tmp_path):
        """샘플 세션 파일 생성"""
        claude_dir = tmp_path / ".claude"
        claude_dir.mkdir(exist_ok=True)
        projects_dir = claude_dir / "projects"
        projects_dir.mkdir()
        project_dir = projects_dir / "test-project"
        project_dir.mkdir()

        session_file = project_dir / "test-session-123.jsonl"
        session_data = [
            {"type": "user", "message": {"content": "파일을 생성해줘"}},
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "파일을 생성하겠습니다."},
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/test/app.py"}}
            ]}},
            {"type": "user", "message": {"content": "테스트도 작성해줘"}},
            {"type": "assistant", "message": {"content": [
                {"type": "text", "text": "테스트 완료했습니다."},
                {"type": "tool_use", "name": "Write", "input": {"file_path": "/test/test_app.py"}}
            ]}},
        ]
        session_file.write_text("\n".join(json.dumps(d) for d in session_data))

        return session_file

    def test_get_latest_session(self, generator, sample_session):
        """최신 세션 찾기 테스트"""
        # generator의 claude_dir을 sample_session의 부모로 설정
        generator.analyzer.claude_dir = sample_session.parent.parent.parent
        generator.analyzer.projects_dir = sample_session.parent.parent

        latest = generator.get_latest_session()
        assert latest is not None
        assert latest.name == "test-session-123.jsonl"

    def test_extract_context_from_session(self, generator, sample_session):
        """세션에서 컨텍스트 추출 테스트"""
        context = generator.extract_context_from_session(sample_session)

        assert isinstance(context, HandoffContext)
        assert context.summary is not None
        assert "app.py" in context.important_files or "test_app.py" in context.important_files

    def test_generate_handoff_md(self, generator):
        """HANDOFF.md 생성 테스트"""
        context = HandoffContext(
            summary="테스트 프로젝트 작업",
            completed_tasks=["파일 생성 완료", "테스트 작성 완료"],
            pending_tasks=["문서 작성 필요"],
            key_decisions=["Python 사용"],
            important_files=["app.py", "test_app.py"],
            next_steps=["문서 작성", "배포 준비"]
        )

        content = generator.generate_handoff_md(context, session_id="test-123")

        assert "# HANDOFF.md" in content
        assert "테스트 프로젝트 작업" in content
        assert "파일 생성 완료" in content
        assert "문서 작성 필요" in content
        assert "app.py" in content

    def test_generate_handoff_md_with_notes(self, generator):
        """커스텀 노트 포함 HANDOFF.md 생성 테스트"""
        context = HandoffContext(
            summary="요약",
            completed_tasks=[],
            pending_tasks=[],
            key_decisions=[],
            important_files=[],
            next_steps=[]
        )

        content = generator.generate_handoff_md(
            context,
            custom_notes="중요: API 키 설정 필요"
        )

        assert "추가 메모" in content
        assert "API 키 설정 필요" in content

    def test_create_quick_handoff(self, generator, tmp_path, monkeypatch):
        """빠른 핸드오프 생성 테스트"""
        monkeypatch.chdir(tmp_path)

        output = generator.create_quick_handoff("현재 로그인 기능 구현 중")

        assert Path(output).exists()
        content = Path(output).read_text()
        assert "로그인 기능 구현 중" in content
        assert "빠른 세션 인수인계" in content


class TestHandoffContext:
    """HandoffContext 데이터클래스 테스트"""

    def test_context_creation(self):
        """HandoffContext 생성 테스트"""
        context = HandoffContext(
            summary="요약 텍스트",
            completed_tasks=["작업1", "작업2"],
            pending_tasks=["작업3"],
            key_decisions=["결정1"],
            important_files=["file1.py"],
            next_steps=["다음1"]
        )

        assert context.summary == "요약 텍스트"
        assert len(context.completed_tasks) == 2
        assert len(context.pending_tasks) == 1
        assert len(context.important_files) == 1

    def test_context_empty(self):
        """빈 HandoffContext 테스트"""
        context = HandoffContext(
            summary="",
            completed_tasks=[],
            pending_tasks=[],
            key_decisions=[],
            important_files=[],
            next_steps=[]
        )

        assert context.summary == ""
        assert context.completed_tasks == []
