# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Proper package structure (`claude_config/` directory)
- Comprehensive test suite with pytest
- GitHub Actions CI/CD pipeline
- CONTRIBUTING.md with development guide
- This CHANGELOG.md file

### Changed
- Fixed import paths for pip installation
- Updated pyproject.toml with correct package discovery

## [0.1.0] - 2026-02-04

### Added
- Initial release of Claude Config
- `init` command - Interactive CLAUDE.md generator with log analysis
- `learn` command - Pattern learning and update suggestions
- `analyze` command - Detailed conversation statistics
- `doc` command - Placeholder for Phase 2 documentation feature
- LogAnalyzer: Parse Claude Code session logs (`.jsonl` files)
- PatternExtractor: Extract patterns from conversations
- ClaudeMdUpdater: Generate CLAUDE.md update suggestions
- ConfigGenerator: Interactive configuration wizard

### Features
- Parse `~/.claude/projects/` session logs
- Detect user corrections and preferences
- Track tool usage statistics
- Identify repeated request patterns
- Generate contextual CLAUDE.md rules

---

## Release Notes

### v0.1.0 - Initial Release

Claude Config is a CLI tool that helps you personalize Claude Code by analyzing your conversation patterns and generating optimized CLAUDE.md configurations.

**Key Features:**
- **Zero external dependencies** - Pure Python stdlib
- **Privacy-first** - All analysis runs locally
- **Smart suggestions** - Learn from your actual usage patterns

**Installation:**
```bash
pip install claude-config
```

**Quick Start:**
```bash
# Generate initial CLAUDE.md
claude-config init

# Learn from your patterns
claude-config learn

# View detailed statistics
claude-config analyze
```

For more information, see the [README](README.md).
