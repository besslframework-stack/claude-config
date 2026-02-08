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

VERSION = "0.1.0"


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
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
