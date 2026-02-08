"""
Hooks 관리자
.claude/settings.json의 hooks 섹션을 관리
"""

import json
from pathlib import Path
from typing import Optional
from dataclasses import dataclass


@dataclass
class Hook:
    matcher: str
    command: str
    description: str


# 자주 사용하는 훅 템플릿
HOOK_TEMPLATES = {
    "lint-python": Hook(
        matcher="Edit",
        command="python -m black --check $FILE && python -m isort --check-only $FILE",
        description="Python 파일 편집 시 Black/isort 체크"
    ),
    "lint-js": Hook(
        matcher="Edit",
        command="npx eslint $FILE",
        description="JavaScript/TypeScript 파일 편집 시 ESLint 체크"
    ),
    "test-python": Hook(
        matcher="Edit",
        command="python -m pytest --tb=short -q",
        description="Python 파일 편집 후 테스트 실행"
    ),
    "test-js": Hook(
        matcher="Edit",
        command="npm test -- --passWithNoTests",
        description="JS 파일 편집 후 테스트 실행"
    ),
    "no-env-commit": Hook(
        matcher="Bash",
        command="! grep -q '\\.env' <<< \"$COMMAND\" || echo 'Warning: .env file operation detected'",
        description=".env 파일 조작 경고"
    ),
    "no-force-push": Hook(
        matcher="Bash",
        command="! grep -q 'push.*--force\\|push.*-f' <<< \"$COMMAND\" || exit 1",
        description="force push 방지"
    ),
    "build-check": Hook(
        matcher="Write",
        command="npm run build --if-present || true",
        description="파일 작성 후 빌드 체크"
    ),
    "type-check": Hook(
        matcher="Edit",
        command="npx tsc --noEmit",
        description="TypeScript 타입 체크"
    ),
}


class HooksManager:
    def __init__(self, project_dir: Optional[str] = None):
        if project_dir:
            self.project_dir = Path(project_dir)
        else:
            self.project_dir = Path.cwd()

        self.claude_dir = self.project_dir / ".claude"
        self.settings_path = self.claude_dir / "settings.json"

    def ensure_claude_dir(self) -> None:
        """Ensure .claude directory exists"""
        self.claude_dir.mkdir(parents=True, exist_ok=True)

    def read_settings(self) -> dict:
        """Read .claude/settings.json"""
        if self.settings_path.exists():
            return json.loads(self.settings_path.read_text(encoding='utf-8'))
        return {}

    def write_settings(self, settings: dict) -> None:
        """Write .claude/settings.json"""
        self.ensure_claude_dir()
        self.settings_path.write_text(
            json.dumps(settings, indent=2, ensure_ascii=False),
            encoding='utf-8'
        )

    def get_hooks(self) -> dict:
        """Get current hooks from settings"""
        settings = self.read_settings()
        return settings.get("hooks", {})

    def init_hooks(self) -> bool:
        """Initialize hooks section in settings"""
        settings = self.read_settings()

        if "hooks" in settings:
            return False  # Already initialized

        settings["hooks"] = {
            "preToolUse": [],
            "postToolUse": []
        }

        self.write_settings(settings)
        return True

    def add_hook(self, template_name: str, hook_type: str = "postToolUse") -> bool:
        """Add a hook from template"""
        if template_name not in HOOK_TEMPLATES:
            return False

        template = HOOK_TEMPLATES[template_name]
        settings = self.read_settings()

        if "hooks" not in settings:
            settings["hooks"] = {"preToolUse": [], "postToolUse": []}

        hook_config = {
            "matcher": template.matcher,
            "hooks": [
                {
                    "type": "command",
                    "command": template.command
                }
            ]
        }

        # Check for duplicates
        existing_hooks = settings["hooks"].get(hook_type, [])
        for existing in existing_hooks:
            if existing.get("matcher") == template.matcher:
                # Update existing hook
                if "hooks" not in existing:
                    existing["hooks"] = []
                existing["hooks"].append(hook_config["hooks"][0])
                self.write_settings(settings)
                return True

        # Add new hook
        settings["hooks"][hook_type].append(hook_config)
        self.write_settings(settings)
        return True

    def add_custom_hook(
        self,
        matcher: str,
        command: str,
        hook_type: str = "postToolUse"
    ) -> bool:
        """Add a custom hook"""
        settings = self.read_settings()

        if "hooks" not in settings:
            settings["hooks"] = {"preToolUse": [], "postToolUse": []}

        hook_config = {
            "matcher": matcher,
            "hooks": [
                {
                    "type": "command",
                    "command": command
                }
            ]
        }

        settings["hooks"][hook_type].append(hook_config)
        self.write_settings(settings)
        return True

    def remove_hook(self, matcher: str, hook_type: str = "postToolUse") -> bool:
        """Remove a hook by matcher"""
        settings = self.read_settings()

        if "hooks" not in settings:
            return False

        hooks = settings["hooks"].get(hook_type, [])
        original_len = len(hooks)
        settings["hooks"][hook_type] = [h for h in hooks if h.get("matcher") != matcher]

        if len(settings["hooks"][hook_type]) < original_len:
            self.write_settings(settings)
            return True

        return False

    def list_templates(self) -> list[dict]:
        """List available hook templates"""
        return [
            {
                "name": name,
                "matcher": hook.matcher,
                "command": hook.command,
                "description": hook.description
            }
            for name, hook in HOOK_TEMPLATES.items()
        ]

    def list_current_hooks(self) -> dict:
        """List currently configured hooks"""
        return self.get_hooks()

    def suggest_hooks(self) -> list[str]:
        """Suggest hooks based on project structure"""
        suggestions = []

        # Python project
        if (self.project_dir / "pyproject.toml").exists() or \
           (self.project_dir / "requirements.txt").exists():
            suggestions.extend(["lint-python", "test-python"])

        # JavaScript/TypeScript project
        if (self.project_dir / "package.json").exists():
            suggestions.extend(["lint-js", "test-js"])

            # Check for TypeScript
            if (self.project_dir / "tsconfig.json").exists():
                suggestions.append("type-check")

        # Git project
        if (self.project_dir / ".git").exists():
            suggestions.append("no-force-push")

        # .env file exists
        if (self.project_dir / ".env").exists() or \
           (self.project_dir / ".env.local").exists():
            suggestions.append("no-env-commit")

        return suggestions


if __name__ == "__main__":
    manager = HooksManager()

    print("=== Hook Templates ===")
    for template in manager.list_templates():
        print(f"\n{template['name']}:")
        print(f"  Matcher: {template['matcher']}")
        print(f"  Command: {template['command']}")
        print(f"  Description: {template['description']}")

    print("\n=== Suggested Hooks ===")
    for suggestion in manager.suggest_hooks():
        print(f"  - {suggestion}")
