"""
HooksManager 테스트
"""

import json
import pytest

from claude_config.hooks_manager import HooksManager, Hook, HOOK_TEMPLATES


class TestHooksManager:
    """HooksManager 클래스 테스트"""

    @pytest.fixture
    def manager(self, tmp_path):
        """HooksManager 인스턴스 생성"""
        return HooksManager(str(tmp_path))

    def test_init_default_path(self):
        """기본 경로 초기화 테스트"""
        from pathlib import Path
        manager = HooksManager()
        assert manager.project_dir == Path.cwd()

    def test_ensure_claude_dir(self, manager, tmp_path):
        """Claude 디렉토리 생성 테스트"""
        manager.ensure_claude_dir()
        assert (tmp_path / ".claude").exists()

    def test_init_hooks(self, manager, tmp_path):
        """hooks 초기화 테스트"""
        result = manager.init_hooks()
        assert result is True

        settings = manager.read_settings()
        assert "hooks" in settings
        assert "preToolUse" in settings["hooks"]
        assert "postToolUse" in settings["hooks"]

        # 중복 초기화 시 False 반환
        result2 = manager.init_hooks()
        assert result2 is False

    def test_add_hook_from_template(self, manager):
        """템플릿에서 훅 추가 테스트"""
        manager.init_hooks()
        result = manager.add_hook("lint-python")

        assert result is True

        hooks = manager.get_hooks()
        assert len(hooks["postToolUse"]) == 1
        assert hooks["postToolUse"][0]["matcher"] == "Edit"

    def test_add_custom_hook(self, manager):
        """커스텀 훅 추가 테스트"""
        manager.init_hooks()
        result = manager.add_custom_hook(
            matcher="Bash",
            command="echo 'test'",
            hook_type="preToolUse"
        )

        assert result is True

        hooks = manager.get_hooks()
        assert len(hooks["preToolUse"]) == 1
        assert hooks["preToolUse"][0]["matcher"] == "Bash"

    def test_remove_hook(self, manager):
        """훅 제거 테스트"""
        manager.init_hooks()
        manager.add_hook("lint-python")

        result = manager.remove_hook("Edit")
        assert result is True

        hooks = manager.get_hooks()
        assert len(hooks["postToolUse"]) == 0

    def test_remove_nonexistent_hook(self, manager):
        """존재하지 않는 훅 제거 테스트"""
        manager.init_hooks()
        result = manager.remove_hook("NonexistentMatcher")
        assert result is False

    def test_list_templates(self, manager):
        """템플릿 목록 테스트"""
        templates = manager.list_templates()

        assert len(templates) > 0
        assert all("name" in t for t in templates)
        assert all("matcher" in t for t in templates)
        assert all("command" in t for t in templates)

    def test_suggest_hooks_python(self, manager, tmp_path):
        """Python 프로젝트 훅 추천 테스트"""
        (tmp_path / "pyproject.toml").write_text("[project]\nname='test'")

        suggestions = manager.suggest_hooks()

        assert "lint-python" in suggestions
        assert "test-python" in suggestions

    def test_suggest_hooks_javascript(self, manager, tmp_path):
        """JavaScript 프로젝트 훅 추천 테스트"""
        (tmp_path / "package.json").write_text('{"name": "test"}')

        suggestions = manager.suggest_hooks()

        assert "lint-js" in suggestions
        assert "test-js" in suggestions

    def test_suggest_hooks_typescript(self, manager, tmp_path):
        """TypeScript 프로젝트 훅 추천 테스트"""
        (tmp_path / "package.json").write_text('{"name": "test"}')
        (tmp_path / "tsconfig.json").write_text('{}')

        suggestions = manager.suggest_hooks()

        assert "type-check" in suggestions

    def test_suggest_hooks_git(self, manager, tmp_path):
        """Git 프로젝트 훅 추천 테스트"""
        (tmp_path / ".git").mkdir()

        suggestions = manager.suggest_hooks()

        assert "no-force-push" in suggestions

    def test_suggest_hooks_env(self, manager, tmp_path):
        """환경 변수 파일 훅 추천 테스트"""
        (tmp_path / ".env").write_text("SECRET=value")

        suggestions = manager.suggest_hooks()

        assert "no-env-commit" in suggestions

    def test_read_write_settings(self, manager, tmp_path):
        """설정 읽기/쓰기 테스트"""
        test_settings = {"key": "value", "nested": {"a": 1}}

        manager.write_settings(test_settings)
        read_settings = manager.read_settings()

        assert read_settings == test_settings


class TestHook:
    """Hook 데이터클래스 테스트"""

    def test_hook_creation(self):
        """Hook 생성 테스트"""
        hook = Hook(
            matcher="Edit",
            command="pytest",
            description="테스트 실행"
        )

        assert hook.matcher == "Edit"
        assert hook.command == "pytest"
        assert hook.description == "테스트 실행"


class TestHookTemplates:
    """Hook 템플릿 테스트"""

    def test_templates_exist(self):
        """템플릿 존재 확인"""
        assert len(HOOK_TEMPLATES) > 0

    def test_template_structure(self):
        """템플릿 구조 확인"""
        for name, hook in HOOK_TEMPLATES.items():
            assert isinstance(hook, Hook)
            assert hook.matcher
            assert hook.command
            assert hook.description

    def test_required_templates_exist(self):
        """필수 템플릿 확인"""
        required = ["lint-python", "lint-js", "test-python", "test-js", "no-force-push"]
        for name in required:
            assert name in HOOK_TEMPLATES, f"Required template '{name}' not found"
