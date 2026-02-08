"""
Handoff 생성기
세션 인수인계용 HANDOFF.md 자동 생성
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

from claude_config.log_analyzer import LogAnalyzer


@dataclass
class HandoffContext:
    summary: str
    completed_tasks: list[str]
    pending_tasks: list[str]
    key_decisions: list[str]
    important_files: list[str]
    next_steps: list[str]


class HandoffGenerator:
    def __init__(self, claude_dir: Optional[str] = None):
        self.analyzer = LogAnalyzer(claude_dir)

    def get_latest_session(self) -> Optional[Path]:
        """가장 최근 세션 파일 반환"""
        for project_dir in self.analyzer.get_all_project_dirs():
            session_files = self.analyzer.get_session_files(project_dir)
            if session_files:
                return session_files[0]
        return None

    def extract_context_from_session(self, session_path: Path) -> HandoffContext:
        """세션에서 컨텍스트 추출"""
        conv = self.analyzer.extract_conversation(session_path)

        completed_tasks = []
        pending_tasks = []
        key_decisions = []
        important_files = set()
        summary_parts = []

        for msg in conv.messages:
            content = msg.content
            if isinstance(content, list):
                content = " ".join(str(item) for item in content)
            elif not isinstance(content, str):
                content = str(content) if content else ""

            # 완료된 작업 감지
            if msg.role == "assistant":
                if "완료" in content or "done" in content.lower():
                    # 간단한 요약 추출
                    lines = content.split('\n')
                    for line in lines[:3]:
                        if line.strip() and len(line) < 100:
                            completed_tasks.append(line.strip()[:80])
                            break

                # 도구 사용에서 파일 추출
                for tool in msg.tool_calls:
                    tool_input = tool.get("input", {})
                    file_path = tool_input.get("file_path", "")
                    if file_path and not file_path.startswith("/tmp"):
                        # 상대 경로로 변환
                        try:
                            rel_path = Path(file_path).name
                            important_files.add(rel_path)
                        except:
                            pass

            # 사용자 요청에서 TODO 추출
            if msg.role == "user":
                content_lower = content.lower()
                if any(kw in content_lower for kw in ["해줘", "해주세요", "하자", "해야", "필요", "todo"]):
                    if len(content) < 150:
                        # 이미 완료된 것과 겹치지 않으면 pending으로
                        pending_tasks.append(content.strip()[:100])

        # 중복 제거 및 최근 것 우선
        completed_tasks = list(dict.fromkeys(completed_tasks))[-5:]
        pending_tasks = list(dict.fromkeys(pending_tasks))[-5:]

        # 첫 번째 사용자 메시지를 요약으로
        for msg in conv.messages:
            if msg.role == "user":
                content = msg.content
                if isinstance(content, list):
                    content = " ".join(str(item) for item in content)
                elif not isinstance(content, str):
                    content = str(content) if content else ""
                if content:
                    summary_parts.append(content[:200])
                    break

        return HandoffContext(
            summary=summary_parts[0] if summary_parts else "세션 요약 없음",
            completed_tasks=completed_tasks,
            pending_tasks=pending_tasks,
            key_decisions=key_decisions,
            important_files=list(important_files)[:10],
            next_steps=pending_tasks[:3] if pending_tasks else ["다음 작업을 정의하세요"]
        )

    def generate_handoff_md(
        self,
        context: HandoffContext,
        session_id: Optional[str] = None,
        custom_notes: Optional[str] = None
    ) -> str:
        """HANDOFF.md 내용 생성"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M")

        # 완료된 작업 섹션
        completed_section = ""
        if context.completed_tasks:
            completed_section = "\n".join(f"- [x] {task}" for task in context.completed_tasks)
        else:
            completed_section = "- 아직 완료된 작업 없음"

        # 남은 작업 섹션
        pending_section = ""
        if context.pending_tasks:
            pending_section = "\n".join(f"- [ ] {task}" for task in context.pending_tasks)
        else:
            pending_section = "- 남은 작업 없음"

        # 중요 파일 섹션
        files_section = ""
        if context.important_files:
            files_section = "\n".join(f"- `{f}`" for f in context.important_files)
        else:
            files_section = "- 특별히 없음"

        # 다음 단계 섹션
        next_steps_section = ""
        if context.next_steps:
            next_steps_section = "\n".join(f"{i+1}. {step}" for i, step in enumerate(context.next_steps))
        else:
            next_steps_section = "1. 다음 작업을 정의하세요"

        # 커스텀 노트
        notes_section = ""
        if custom_notes:
            notes_section = f"""
## 추가 메모

{custom_notes}
"""

        md = f"""# HANDOFF.md

> 세션 인수인계 문서
> 생성: {timestamp}
> 세션 ID: {session_id or "N/A"}

---

## 요약

{context.summary}

---

## 완료된 작업

{completed_section}

---

## 남은 작업

{pending_section}

---

## 중요 파일

{files_section}

---

## 다음 단계

{next_steps_section}
{notes_section}
---

## 사용 방법

이 파일을 새 Claude 세션에 붙여넣으면 컨텍스트가 전달됩니다:

```
아래 HANDOFF.md를 읽고 이전 작업을 이어서 진행해주세요.

[HANDOFF.md 내용 붙여넣기]
```

---

*Generated by [Claude Config](https://github.com/besslframework-stack/claude-config)*
"""

        return md

    def create_handoff(
        self,
        output_path: Optional[str] = None,
        session_id: Optional[str] = None,
        custom_notes: Optional[str] = None
    ) -> str:
        """HANDOFF.md 생성"""
        # 세션 찾기
        if session_id and session_id != "latest":
            # 특정 세션 ID로 찾기
            session_path = None
            for project_dir in self.analyzer.get_all_project_dirs():
                potential_path = project_dir / f"{session_id}.jsonl"
                if potential_path.exists():
                    session_path = potential_path
                    break
        else:
            session_path = self.get_latest_session()

        if not session_path:
            return ""

        # 컨텍스트 추출
        context = self.extract_context_from_session(session_path)

        # HANDOFF.md 생성
        content = self.generate_handoff_md(
            context,
            session_id=session_path.stem if session_path else None,
            custom_notes=custom_notes
        )

        # 저장
        if output_path:
            output = Path(output_path)
        else:
            output = Path.cwd() / "HANDOFF.md"

        output.write_text(content, encoding="utf-8")

        return str(output)

    def create_quick_handoff(self, notes: str) -> str:
        """빠른 수동 핸드오프 생성 (로그 분석 없이)"""
        now = datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M")

        md = f"""# HANDOFF.md

> 빠른 세션 인수인계
> 생성: {timestamp}

---

## 현재 상태

{notes}

---

## 사용 방법

이 파일을 새 Claude 세션에 붙여넣으면 컨텍스트가 전달됩니다.

---

*Generated by [Claude Config](https://github.com/besslframework-stack/claude-config)*
"""

        output = Path.cwd() / "HANDOFF.md"
        output.write_text(md, encoding="utf-8")

        return str(output)


if __name__ == "__main__":
    generator = HandoffGenerator()
    latest = generator.get_latest_session()

    if latest:
        print(f"Latest session: {latest}")
        context = generator.extract_context_from_session(latest)
        print(f"\nSummary: {context.summary[:100]}...")
        print(f"Completed: {len(context.completed_tasks)}")
        print(f"Pending: {len(context.pending_tasks)}")
        print(f"Files: {context.important_files}")
    else:
        print("No sessions found")
