#!/usr/bin/env python3
"""
Claude Config - Claude Code를 나에게 맞게 튜닝하는 도구
https://github.com/besslframework-stack/claude-config
"""

import argparse
import json
import sys
from pathlib import Path
from datetime import datetime

from claude_config.log_analyzer import LogAnalyzer
from claude_config.pattern_extractor import PatternExtractor
from claude_config.claude_md_updater import ClaudeMdUpdater
from claude_config.config_generator import ConfigGenerator
from claude_config.hooks_manager import HooksManager, HOOK_TEMPLATES
from claude_config.handoff_generator import HandoffGenerator

VERSION = "0.2.0"


def init_command(args):
    """CLAUDE.md 초기 설정"""
    generator = ConfigGenerator()
    generator.init(
        output_path=args.output,
        skip_questions=args.yes
    )


def learn_command(args):
    """대화 로그 학습 및 업데이트 제안"""
    print("대화 로그 분석 중...\n")

    # 분석
    analyzer = LogAnalyzer()
    conversations = analyzer.get_recent_conversations(limit=args.limit)

    if not conversations:
        print("분석할 대화 로그가 없습니다.")
        return

    extractor = PatternExtractor()
    patterns = extractor.analyze(conversations)

    # 제안 생성
    updater = ClaudeMdUpdater(args.claude_md)
    report = updater.get_update_report(patterns)

    print(report)

    if args.apply:
        suggestions = updater.generate_suggestions(patterns)
        if suggestions:
            if not args.yes:
                confirm = input("이 제안을 적용하시겠습니까? (y/N): ")
                if confirm.lower() != 'y':
                    print("취소되었습니다.")
                    return
            updater.apply_suggestions(suggestions, dry_run=False)
            print("CLAUDE.md가 업데이트되었습니다.")


def analyze_command(args):
    """대화 로그 상세 분석"""
    print("대화 로그 분석 중...\n")

    analyzer = LogAnalyzer()
    conversations = analyzer.get_recent_conversations(
        limit=args.limit,
        project_filter=args.project
    )

    print(f"분석된 대화 수: {len(conversations)}\n")

    # 도구 사용 통계
    tool_usage = analyzer.get_all_tool_usage(conversations)
    print("=== 도구 사용 빈도 ===")
    for tool, count in list(tool_usage.items())[:10]:
        print(f"  {tool}: {count}")

    # 사용자 패턴
    patterns = analyzer.get_user_patterns(conversations)
    print(f"\n=== 사용자 패턴 ===")
    print(f"  평균 메시지 길이: {patterns['avg_message_length']:.0f}자")
    print(f"  질문 비율: {patterns['question_ratio']:.1%}")
    print(f"  코드 요청 비율: {patterns['code_request_ratio']:.1%}")

    # 패턴 추출
    extractor = PatternExtractor()
    extracted = extractor.analyze(conversations)

    print(f"\n=== 추출된 패턴 ===")
    print(f"  교정 횟수: {len(extracted['corrections'])}")
    print(f"  반복 요청 유형: {len(extracted['repeated_requests'])}가지")
    print(f"  워크플로우 패턴: {len(extracted['workflows'])}개")

    if args.output:
        output_path = Path(args.output)
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "conversation_count": len(conversations),
            "tool_usage": tool_usage,
            "user_patterns": patterns,
            "extracted_patterns": {
                "corrections": extracted["corrections"],
                "repeated_requests": extracted["repeated_requests"],
                "edit_patterns": extracted["edit_patterns"],
            }
        }
        output_path.write_text(json.dumps(output_data, ensure_ascii=False, indent=2))
        print(f"\n분석 결과 저장: {output_path}")


def doc_command(args):
    """세션 → 문서 자동 생성 (Phase 2)"""
    print("문서 자동 생성 기능은 곧 출시됩니다.")
    print("https://github.com/besslframework-stack/claude-config 에서 업데이트를 확인하세요.")


def hooks_command(args):
    """Hooks 관리"""
    manager = HooksManager()

    if args.hooks_action == "init":
        if manager.init_hooks():
            print("✓ .claude/settings.json에 hooks 섹션이 초기화되었습니다.")

            # 추천 훅 표시
            suggestions = manager.suggest_hooks()
            if suggestions:
                print("\n추천 훅:")
                for name in suggestions:
                    template = HOOK_TEMPLATES[name]
                    print(f"  - {name}: {template.description}")
                print(f"\n추가하려면: claude-config hooks add <name>")
        else:
            print("hooks 섹션이 이미 존재합니다.")

    elif args.hooks_action == "add":
        if not args.name:
            print("훅 이름을 지정하세요: claude-config hooks add <name>")
            print("\n사용 가능한 훅:")
            for name, hook in HOOK_TEMPLATES.items():
                print(f"  {name}: {hook.description}")
            return

        if args.name in HOOK_TEMPLATES:
            if manager.add_hook(args.name, args.type):
                template = HOOK_TEMPLATES[args.name]
                print(f"✓ '{args.name}' 훅이 추가되었습니다.")
                print(f"  Matcher: {template.matcher}")
                print(f"  Command: {template.command}")
            else:
                print(f"훅 추가 실패: {args.name}")
        else:
            # 커스텀 훅
            if args.matcher and args.command:
                if manager.add_custom_hook(args.matcher, args.command, args.type):
                    print(f"✓ 커스텀 훅이 추가되었습니다.")
                else:
                    print("훅 추가 실패")
            else:
                print(f"'{args.name}'은 템플릿에 없습니다.")
                print("커스텀 훅을 추가하려면: --matcher와 --command를 지정하세요.")

    elif args.hooks_action == "remove":
        if not args.matcher:
            print("제거할 훅의 matcher를 지정하세요: claude-config hooks remove --matcher <matcher>")
            return

        if manager.remove_hook(args.matcher, args.type):
            print(f"✓ '{args.matcher}' 훅이 제거되었습니다.")
        else:
            print(f"'{args.matcher}' 훅을 찾을 수 없습니다.")

    elif args.hooks_action == "list":
        hooks = manager.list_current_hooks()

        if not hooks or (not hooks.get("preToolUse") and not hooks.get("postToolUse")):
            print("설정된 훅이 없습니다.")
            print("훅을 초기화하려면: claude-config hooks init")
            return

        print("=== 현재 설정된 Hooks ===\n")

        for hook_type in ["preToolUse", "postToolUse"]:
            type_hooks = hooks.get(hook_type, [])
            if type_hooks:
                print(f"[{hook_type}]")
                for h in type_hooks:
                    matcher = h.get("matcher", "unknown")
                    hook_list = h.get("hooks", [])
                    print(f"  Matcher: {matcher}")
                    for hook in hook_list:
                        print(f"    → {hook.get('command', hook.get('type', 'unknown'))}")
                print()

    elif args.hooks_action == "suggest":
        suggestions = manager.suggest_hooks()

        if not suggestions:
            print("추천할 훅이 없습니다.")
            return

        print("=== 추천 Hooks ===\n")
        print("프로젝트 구조를 기반으로 추천합니다:\n")

        for name in suggestions:
            template = HOOK_TEMPLATES[name]
            print(f"  {name}")
            print(f"    {template.description}")
            print(f"    Matcher: {template.matcher}")
            print()

        print(f"추가하려면: claude-config hooks add <name>")

    elif args.hooks_action == "templates":
        print("=== 사용 가능한 Hook 템플릿 ===\n")

        for name, hook in HOOK_TEMPLATES.items():
            print(f"  {name}")
            print(f"    {hook.description}")
            print(f"    Matcher: {hook.matcher}")
            print(f"    Command: {hook.command}")
            print()

    else:
        print("사용법: claude-config hooks <init|add|remove|list|suggest|templates>")
        print("\n서브커맨드:")
        print("  init       - hooks 섹션 초기화")
        print("  add        - 훅 추가")
        print("  remove     - 훅 제거")
        print("  list       - 현재 훅 목록")
        print("  suggest    - 프로젝트에 맞는 훅 추천")
        print("  templates  - 사용 가능한 템플릿 목록")


def handoff_command(args):
    """세션 인수인계 HANDOFF.md 생성"""
    generator = HandoffGenerator()

    if args.quick:
        # 빠른 모드: 직접 노트 입력
        if args.notes:
            notes = args.notes
        else:
            print("현재 작업 상태를 입력하세요 (완료하려면 빈 줄 입력):")
            lines = []
            while True:
                try:
                    line = input()
                    if not line:
                        break
                    lines.append(line)
                except EOFError:
                    break
            notes = "\n".join(lines)

        if notes:
            output = generator.create_quick_handoff(notes)
            print(f"✓ HANDOFF.md 생성 완료: {output}")
        else:
            print("내용이 없어 생성을 취소합니다.")
        return

    # 로그 분석 모드
    session = args.session if hasattr(args, 'session') else "latest"

    print(f"세션 분석 중... ({session})")

    output = generator.create_handoff(
        output_path=args.output,
        session_id=session,
        custom_notes=args.notes
    )

    if output:
        print(f"✓ HANDOFF.md 생성 완료: {output}")
        print("\n새 세션에서 이 파일을 사용하세요:")
        print("  1. 새 Claude 세션 시작")
        print("  2. HANDOFF.md 내용 붙여넣기")
        print("  3. '이어서 작업해줘' 요청")
    else:
        print("세션을 찾을 수 없습니다.")
        print("\n빠른 모드를 사용하세요:")
        print("  claude-config handoff --quick")


def main():
    parser = argparse.ArgumentParser(
        prog="claude-config",
        description="Claude Config - Claude Code를 나에게 맞게 튜닝하는 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  claude-config init                    # CLAUDE.md 초기 설정
  claude-config learn                   # 대화 분석 및 업데이트 제안
  claude-config learn --apply           # 제안 바로 적용
  claude-config analyze                 # 상세 분석

문서: https://github.com/besslframework-stack/claude-config
        """
    )

    parser.add_argument("--version", "-v", action="version", version=f"claude-config {VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="명령")

    # init 명령
    init_parser = subparsers.add_parser("init", help="CLAUDE.md 초기 설정")
    init_parser.add_argument("--output", "-o", help="출력 경로 (기본: ./CLAUDE.md)")
    init_parser.add_argument("--yes", "-y", action="store_true", help="질문 없이 기본값 사용")

    # learn 명령 (기존 suggest + apply 통합)
    learn_parser = subparsers.add_parser("learn", help="대화 학습 및 업데이트 제안")
    learn_parser.add_argument("--limit", "-l", type=int, default=30, help="분석할 대화 수")
    learn_parser.add_argument("--claude-md", default=None, help="CLAUDE.md 경로")
    learn_parser.add_argument("--apply", "-a", action="store_true", help="제안 바로 적용")
    learn_parser.add_argument("--yes", "-y", action="store_true", help="확인 없이 적용")

    # analyze 명령
    analyze_parser = subparsers.add_parser("analyze", help="대화 로그 상세 분석")
    analyze_parser.add_argument("--limit", "-l", type=int, default=20, help="분석할 대화 수")
    analyze_parser.add_argument("--project", "-p", help="특정 프로젝트만 분석")
    analyze_parser.add_argument("--output", "-o", help="결과 JSON 저장 경로")

    # doc 명령 (Phase 2)
    doc_parser = subparsers.add_parser("doc", help="세션 → 문서 자동 생성")
    doc_parser.add_argument("--session", "-s", default="latest", help="세션 ID 또는 'latest'")

    # hooks 명령
    hooks_parser = subparsers.add_parser("hooks", help="Hooks 관리")
    hooks_parser.add_argument("hooks_action", nargs="?", default=None,
                              choices=["init", "add", "remove", "list", "suggest", "templates"],
                              help="hooks 서브커맨드")
    hooks_parser.add_argument("name", nargs="?", help="훅 템플릿 이름")
    hooks_parser.add_argument("--type", "-t", default="postToolUse",
                              choices=["preToolUse", "postToolUse"],
                              help="훅 타입 (기본: postToolUse)")
    hooks_parser.add_argument("--matcher", "-m", help="커스텀 훅의 matcher")
    hooks_parser.add_argument("--command", "-c", help="커스텀 훅의 command")

    # handoff 명령
    handoff_parser = subparsers.add_parser("handoff", help="세션 인수인계 HANDOFF.md 생성")
    handoff_parser.add_argument("--session", "-s", default="latest",
                                help="세션 ID 또는 'latest' (기본)")
    handoff_parser.add_argument("--output", "-o", help="출력 경로 (기본: ./HANDOFF.md)")
    handoff_parser.add_argument("--quick", "-q", action="store_true",
                                help="빠른 모드 (로그 분석 없이)")
    handoff_parser.add_argument("--notes", "-n", help="추가 메모")

    args = parser.parse_args()

    # claude-md 기본값 설정
    if hasattr(args, 'claude_md') and args.claude_md is None:
        # 현재 디렉토리 또는 프로젝트 루트에서 CLAUDE.md 찾기
        cwd = Path.cwd()
        if (cwd / "CLAUDE.md").exists():
            args.claude_md = str(cwd / "CLAUDE.md")
        else:
            # 상위 디렉토리 탐색
            for parent in cwd.parents:
                if (parent / "CLAUDE.md").exists():
                    args.claude_md = str(parent / "CLAUDE.md")
                    break
            else:
                args.claude_md = str(cwd / "CLAUDE.md")

    if args.command == "init":
        init_command(args)
    elif args.command == "learn":
        learn_command(args)
    elif args.command == "analyze":
        analyze_command(args)
    elif args.command == "doc":
        doc_command(args)
    elif args.command == "hooks":
        hooks_command(args)
    elif args.command == "handoff":
        handoff_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
