# Changelog

All notable changes to CodeConCat will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.8.5] - 2025-10-02

### Added
- **Solidity Smart Contract Parser**: Full support for Ethereum/blockchain smart contracts
  - Comprehensive parsing of contracts, interfaces, libraries, and inheritance
  - Functions, modifiers, events, and state variable extraction
  - Struct, enum, and custom error definitions (Solidity 0.8.4+)
  - Constructor, fallback, and receive function support
  - Import statement parsing
  - **Security Pattern Detection**: Syntactic flagging for manual review
    - `selfdestruct` and deprecated `suicide` usage detection
    - `delegatecall` pattern identification
    - Assembly block detection
    - External call tracking (potential reentrancy points)
  - Full test coverage with unit and integration tests
  - Performance optimized (<70ms for 10KB files)
  - Based on JoranHonig/tree-sitter-solidity grammar

### Changed
- Updated language support count from 15+ to 20+ languages in documentation
- Added Solidity examples in Advanced Workflows section
- **AI Model Updates**: Improved default model selection for better performance
  - OpenRouter: Changed default model from `deepseek/deepseek-chat-v3.1` to `qwen/qwen3-coder` (specialized for code)
  - OpenRouter: Updated meta-overview model from `z-ai/glm-4.5` to `z-ai/glm-4.6` (latest version)
  - Fixed incorrect model references in documentation (`gpt-5-nano` → `gpt-5-mini`)

## [0.8.5] - 2025-01-30

### Fixed
- Swift parser declaration type detection using QueryCursor API
- All linting errors resolved (type annotations, unused variables)

### Changed
- Refactored shared doc comment utilities across all parsers
- Improved code consistency and maintainability

## [0.8.4] - 2024-12-15

### Added
- **Intelligent Parser Result Merging**: Advanced approach to code parsing
  - Merges results from multiple parsers instead of picking single winner
  - 4 configurable merge strategies (confidence, union, fast_fail, best_of_breed)
  - Confidence scoring based on parser quality and completeness
  - Signature-based duplicate detection
  - Configurable via `enable_result_merging` and `merge_strategy` settings

- **Modern Syntax Support**: Built-in patterns for latest language features
  - TypeScript 5.0+ (satisfies, const assertions, type predicates)
  - Python 3.11+ (pattern matching, walrus operator, PEP 695)
  - Go 1.18+ (generics, type constraints)
  - Rust (async functions, const generics, impl Trait)
  - PHP 8.0+ (named arguments, match expressions, enums)

- **Differential Outputs**: Generate diffs between Git refs (branches, tags, commits)
  - GitPython integration for robust Git operations
  - Smart filtering shows all relevant changes
  - Rich metadata tracking (additions, deletions, renames)
  - AI-powered change summaries
  - Works with all output formats

### Changed
- **Shared Parser Infrastructure**: Eliminated 600+ lines of duplicate code
  - Unified `CommentExtractor` for all parsers
  - `ModernPatterns` registry for version-specific features
  - Utility methods consolidated in `EnhancedBaseParser`

- **Enhanced ParseResult**: New fields for intelligent merging
  - `confidence_score`: Parser confidence (0.0-1.0)
  - `parser_type`: Parser identification (tree-sitter, enhanced, standard)

## [0.8.3] - 2024-11-20

### Added
- **GitHub Direct Processing**: Process repositories without --source-url flag
  - Automatic detection of GitHub URLs and shorthand notation (owner/repo)
  - Support for SSH URLs
  - Future GitLab/Bitbucket compatibility

### Fixed
- **AI Summary Generation**: Fixed AI summary display across all formats
  - Corrected field mapping issues in Markdown writer
  - Added summary support to XML writer
  - Lowered minimum file threshold from 20 to 5 lines

### Changed
- Improved examples and corrected flag documentation

## [0.8.2] - 2024-10-15

### Added
- **Swift Language Support**: Full parsing with tree-sitter and regex engines
  - Tree-sitter parser using tree-sitter-swift grammar
  - Comprehensive regex fallback parser
  - Modern Swift features: actors, async/await, property wrappers, SwiftUI
  - Documentation comment extraction (/// and /** */)

- **Enhanced AI Context**: Model-aware code truncation based on context windows

### Improved
- Security: Enhanced prompt injection prevention

## [0.8.1] - 2024-09-10

### Added
- Enhanced regex parser support for Python, JavaScript, Go, Rust, PHP
- Modern syntax patterns for Python 3.11+, TypeScript 5.0+

### Fixed
- Parser fallback handling improvements
- Unicode normalization edge cases

## [0.8.0] - 2024-08-01

### Added
- Tree-sitter parser support for 12 languages
- Multiple output formats: Markdown, JSON, XML, Text
- AI summarization with OpenAI, Anthropic, OpenRouter
- Security scanning with Semgrep integration
- Code compression with pattern recognition
- REST API with FastAPI
- Configuration file support (.codeconcat.yml)

### Changed
- Complete CLI rewrite using Typer
- Modernized codebase with type hints and Pydantic validation

## [0.7.0] - 2024-06-15

### Added
- Initial release
- Basic parsing for Python, JavaScript, Java
- Simple output generation
- Command-line interface

---

## Version Numbering

CodeConCat follows Semantic Versioning:
- **Major** (X.0.0): Breaking changes
- **Minor** (0.X.0): New features, backwards compatible
- **Patch** (0.0.X): Bug fixes, backwards compatible

## Links

- [GitHub Repository](https://github.com/biostochastics/codeconcat)
- [Issue Tracker](https://github.com/biostochastics/codeconcat/issues)
- [Documentation](README.md)
