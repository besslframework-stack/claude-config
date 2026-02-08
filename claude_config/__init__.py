"""
Claude Config - Claude Code를 나에게 맞게 튜닝하는 도구
"""

__version__ = "0.2.0"

from claude_config.log_analyzer import LogAnalyzer, Conversation, Message
from claude_config.pattern_extractor import PatternExtractor, Pattern
from claude_config.claude_md_updater import ClaudeMdUpdater, UpdateSuggestion
from claude_config.config_generator import ConfigGenerator
from claude_config.hooks_manager import HooksManager, Hook, HOOK_TEMPLATES
from claude_config.handoff_generator import HandoffGenerator, HandoffContext

__all__ = [
    "LogAnalyzer",
    "Conversation",
    "Message",
    "PatternExtractor",
    "Pattern",
    "ClaudeMdUpdater",
    "UpdateSuggestion",
    "ConfigGenerator",
    "HooksManager",
    "Hook",
    "HOOK_TEMPLATES",
    "HandoffGenerator",
    "HandoffContext",
]
