# Changelog

All notable changes to CodeConCat will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.9.2] - 2026-01-28

### Fixed

- **OpenAI API key validation**: Added explicit validation during provider initialization that raises `ValueError` with helpful error message when API key is not configured, preventing cryptic runtime errors
- **ProcessPoolExecutor resource leak**: Added proper exception handling around parallel parsing to ensure worker processes are cleaned up even when errors occur
- **Unsafe dict deserialization**: Replaced direct `**dict` unpacking in multiprocessing worker with explicit type validation and Pydantic `model_validate()` for config, preventing potential injection attacks through malformed input
- **jsonschema import bug**: Fixed ineffective dependency check in API module that never actually imported jsonschema, now properly verifies library availability at startup
- **Password hashing security**: Increased PBKDF2 iterations from 100,000 to 210,000 to meet OWASP 2024 recommendations for password storage

### Changed

- **Constants file**: Replaced magic numbers with named constants (`KILOBYTE`, `MEGABYTE`) for better readability and maintainability of file size limits

## [0.9.1] - 2026-01-28

### Fixed

- **Severity serialization**: Use enum `.name` (string like "HIGH") instead of `.value` (numeric) across all writers (json, markdown, xml) and rendering adapters
- **Security issue masking**: Respect `mask_output_content` config flag in standalone writers (json, markdown, xml) to suppress security issue details when enabled
- **PEP 604 isinstance compatibility**: Fix `isinstance(v, str | int | float | bool)` to use tuple form `isinstance(v, (str, int, float, bool))` in rendering_adapters.py for Python 3.9 compatibility
- **Signal handler thread safety**: Guard `signal.signal()` call in `SignalHandler.install()` to only run from the main thread, preventing `ValueError` in worker threads
- **Config validation**: Allow `source_url` and `diff` configs without requiring `target_path`, fixing early validation error for remote/diff workflows
- **Docstring accuracy**: Fix `process_codebase()` docstring that incorrectly claimed `CancelledException` is raised (it returns `None` on cancellation)
- **Parse result reconstruction**: Properly reconstruct `ParseResult` dataclass from dict when deserializing multiprocess worker results in unified_pipeline.py

### Changed

- **Default output filename convention**: Output files now use `ccc_{folder_name}_{mmddyy}.{ext}` pattern (e.g., `ccc_myproject_012826.md`) instead of the old `{folder_name}_ccc.{format}` pattern. Format names are mapped to proper file extensions (`markdown` → `.md`, `text` → `.txt`). Date stamp is included for easy versioning.

### Added

- **Graceful Interrupt Handling (Ctrl+C)**: Full cooperative cancellation support
  - First Ctrl+C triggers graceful cancellation with progress preservation
  - Second Ctrl+C within 2 seconds forces immediate exit
  - Thread-safe `CancellationToken` for cooperative task cancellation
  - `SignalHandler` class with context manager support
  - Cancellation checks throughout the processing pipeline
  - New module: `codeconcat/utils/cancellation.py`

- **Unified Progress Dashboard**: Flicker-free Rich Live panel display
  - Single persistent dashboard showing all 4 processing stages (Collecting → Parsing → Annotating → Writing)
  - Visual progress bars with percentage and item counts
  - Stage status icons: ○ pending, ● in progress, ✓ completed, ✗ failed
  - Elapsed time tracking per stage and total
  - TTY detection with automatic fallback to `SimpleProgress` for non-interactive environments
  - Refresh rate limiting (10 Hz) to reduce CPU usage and flicker
  - New module: `codeconcat/cli/progress.py`

- **5 New AI Providers for Code Summarization**:
  - **Google Gemini**: Native SDK integration via `google-genai`
    - Supports Gemini 2.5 Pro, Gemini 2.0 Flash, Gemini 1.5 Flash
    - Both API key and Vertex AI (ADC) authentication
    - Install: `pip install google-genai` or `poetry install -E google`
  - **DeepSeek**: OpenAI-compatible API via LocalServerProvider
    - Models: `deepseek-chat`, `deepseek-coder`, `deepseek-reasoner`
    - Extremely cost-effective ($0.14/1M input tokens)
  - **MiniMax**: OpenAI-compatible API via LocalServerProvider
    - Models: `MiniMax-Text-01` (1M context), `abab6.5s-chat`
  - **Qwen/DashScope**: OpenAI-compatible API via LocalServerProvider
    - Models: `qwen-coder-plus`, `qwen-coder-turbo`, `qwen3-235b-instruct`
  - **Zhipu GLM**: Native SDK integration via `zhipuai`
    - Models: `glm-4`, `glm-4-plus`, `glm-4-flash`, `codegeex-4`
    - Install: `pip install zhipuai` or `poetry install -E zhipu`

- **New Optional Dependencies**: AI providers now available as extras
  - `poetry install -E openai` - OpenAI provider
  - `poetry install -E anthropic` - Anthropic provider
  - `poetry install -E google` - Google Gemini provider
  - `poetry install -E zhipu` - Zhipu GLM provider
  - `poetry install -E all-ai` - All AI providers

### Changed

- **Tree-sitter Upgraded to 0.25.2**: Updated tree-sitter from 0.24.0 to 0.25.2
  - Fixes Crystal parser compatibility (language version 15 support)
  - All 1520 tests passing

- **Solidity Parser Security Patterns**: Implemented comprehensive security pattern detection
  - Assembly blocks, delegatecall, selfdestruct, external calls (.call, .send, .transfer)
  - Security issues now tracked in `result.security_issues` list

### Fixed

- **Reconstruction Parsing Hardening**: Improved markdown section parsing (supports paths with spaces), robust fenced code extraction, and diff-only block handling.
  - Added strict parsing mode by default (with optional lenient repairs) for JSON/XML inputs
  - XML reconstruction now prefers `defusedxml` when available for safer parsing

- **Swift Parser Partial Results Merging**: Tree-sitter partial parse results now merge with regex parser
  - When tree-sitter encounters unsupported syntax (e.g., Swift 5.10+ `nonisolated(unsafe)`), it now includes partial results for merging instead of discarding them
  - Fallback regex parsers always run when tree-sitter has errors, ensuring modern language features are captured
  - Improves parsing of codebases using cutting-edge Swift/language features not yet in tree-sitter grammars

- **Multiprocessing Compatibility**: Fixed `_compile_and_test_regex` serialization
  - Moved local function to module level for Process target compatibility
  - Affects `CustomSecurityPattern.validate_regex` in `base_types.py`

- **Solidity Corpus Tests**: Fixed test compatibility issues
  - `result.errors` → `result.error` (singular)
  - `d.type` → `d.kind` for Declaration objects
  - `result.metadata` → `result.security_issues` for security patterns

- **Unified Pipeline Merging Tests**: Disabled `parser_early_termination` in tests
  - Early termination was preventing result merging from occurring
  - Tests now properly verify merging behavior

- **Verbose Debug Logging During Annotation Failures**: Removed debug code that dumped entire `ParsedFileData` objects (including full file contents) to stderr when annotation exceptions occurred
  - Previously, `repr(file)` was logged which could output megabytes of content for large files
  - Now logs only the file path and exception message

- **Declaration Attribute Access in Writers**: Fixed `'dict' object has no attribute 'kind'` errors
  - Declarations may be stored as either `Declaration` objects or dict representations
  - Added `_get_decl_attr()` helper function across all writer modules for defensive attribute access
  - Affected files: `annotator.py`, `markdown_writer.py`, `json_writer.py`, `xml_writer.py`, `rendering_adapters.py`

- **Security Issue Attribute Access in Writers**: Fixed `'dict' object has no attribute 'severity'` errors
  - Security issues may be stored as either `SecurityIssue` objects or dict representations
  - Added `_get_issue_attr()` helper function across all writer modules for defensive attribute access
  - Handles both enum values (with `.value`/`.name`) and string severity values
  - Affected files: `markdown_writer.py`, `json_writer.py`, `xml_writer.py`, `rendering_adapters.py`

- **Parallel Processing Dataclass Reconstruction**: Fixed `'dict' object has no attribute 'kind'` error in summarization processor when processing large codebases (50+ files)
  - Root cause: `dataclasses.asdict()` in parallel processing worker converted nested `Declaration`, `TokenStats`, `SecurityIssue`, and `DiffMetadata` objects to plain dictionaries
  - When `ParsedFileData(**result_dict)` reconstructed the object, nested dataclasses remained as dicts instead of being converted back to their proper types
  - Added `_reconstruct_parsed_file_data()` and `_reconstruct_declaration()` helper functions in `unified_pipeline.py` to properly reconstruct all nested dataclass objects
  - Handles recursive `Declaration.children` reconstruction and `modifiers` set/list conversion
  - Affected file: `codeconcat/parser/unified_pipeline.py`

### Performance

- **Parser Early Termination Threshold**: Increased from 1 to 5 declarations
  - Reduces redundant parser fallback runs while ensuring adequate coverage
  - Files with few declarations still get full parser cascade

- **Parallel Processing Threshold**: Increased from 4 to 50 files
  - Multiprocessing startup overhead (500-1000ms per worker) plus config serialization
  - Sequential processing is faster for small-to-medium codebases

- **AI Concurrency**: Increased default from 5 to 25 concurrent requests
  - Cloud AI APIs handle higher concurrency efficiently
  - Significantly reduces total AI processing time for large codebases

- **AI Cache TTL**: Increased from 1 hour to 7 days
  - Better cache persistence across development sessions
  - Reduces redundant API calls for unchanged code

- **AI Cache Content Normalization**: Improved cache hit rate
  - Strips comments and normalizes whitespace before hashing
  - Formatting-only changes no longer invalidate cached summaries

- **Guesslang Detection Caching**: Added LRU cache (512 entries)
  - Caches ML-based language detection results by content hash
  - Avoids redundant guesslang inference for similar content

- **Mypy Errors**: Fixed type checking issues
  - HLSL/GLSL parsers: aliased duplicate `get_language` imports
  - Google/Zhipu providers: added `from err` for exception chaining
  - Factory: combined nested conditionals (SIM102, SIM117)

- **CI Test Compatibility**: Fixed tests failing in CI environments
  - WAT parser tests: Added pytest fixture that skips when grammar unavailable
  - Crystal parser tests: Added pytest.skip in setup_method for missing grammar
  - Diff functionality tests: Fixed branch name issue (git default may be "master")
    - Now explicitly renames initial branch to "main" after first commit

- **Pydantic V2 Migration**: Modernized all Pydantic usage patterns
  - Replaced deprecated `.dict()` with `.model_dump()` in legacy `app.py`
  - Migrated V1-style nested `Config` classes to V2 `model_config = ConfigDict(...)`
  - Updated `GlobalState` in `cli/config.py` to use `ConfigDict(arbitrary_types_allowed=True)`
  - Updated `CodeConcatRequest` in `api/app.py` to use `ConfigDict(json_schema_extra=...)`
  - Added `@classmethod` decorators to all `@field_validator` methods in `base_types.py`
  - Added proper type hints to validator methods (`value: str -> str`)

- **Type Annotations**: Updated legacy `app.py` to Python 3.10+ syntax
  - Replaced `Optional[str]` with `str | None`
  - Replaced `List[str]` with `list[str]`
  - Added `from __future__ import annotations` for forward compatibility

## [0.8.8] - 2026-01-28

### Performance

- **Parallel Parsing Phase**: Added `ProcessPoolExecutor`-based parallel file parsing
  - 5-7x speedup for large codebases (100+ files)
  - Module-level `_process_file_worker()` for picklability
  - Sequential fallback for small batches (<4 files)
  - 60-second per-file timeout for edge cases
  - Rich progress bars with `as_completed()` pattern

- **Eliminated Redundant File Reads**: Removed legacy file read path in `determine_language()`
  - Skips guesslang detection if content not provided instead of re-reading files
  - 10-15% improvement in file collection phase

### Changed

- **Updated AI Model Token Limits** (January 2026):
  - OpenAI: Added GPT-5, GPT-5.1, GPT-5.2 (up to 1M tokens), o3/o3-mini
  - Anthropic: Added Claude Opus 4.5, Sonnet 4.5, Haiku 4 (up to 500K tokens)
  - Google: Added Gemini 3 Preview, Gemini 2.5 Pro/Flash (up to 2M tokens)
  - Increased default fallback from 100K to 200K tokens

- **Standardized File Size Limits**: Unified to 10MB across all components
  - `DEFAULT_MAX_FILE_SIZE`: 10MB (was inconsistent)
  - `DEFAULT_MAX_BINARY_CHECK_SIZE`: 10MB

- **Hidden Config File Whitelist**: Added `HIDDEN_CONFIG_WHITELIST` with 51 entries
  - JS/TS: `.eslintrc*`, `.prettierrc*`, `.babelrc*`, `.swcrc`, `.npmrc`, `.nvmrc`
  - Python: `.flake8`, `.pylintrc`, `.python-version`, `.pre-commit-config.yaml`
  - Editor: `.editorconfig`
  - Docker: `.dockerignore`
  - Ruby: `.rubocop.yml`, `.ruby-version`
  - Templates: `.env.example`, `.env.template`, `.env.sample`
  - Removed aggressive `**/.*` pattern that excluded valuable config files

### Fixed

- **ABC Import**: Fixed `ParserInterface` class to use imported `ABC`/`abstractmethod` instead of `abc.ABC`
- **Multiprocessing Serialization**: Fixed serialization for parallel parsing workers
  - Clear `ast_root` (tree_sitter.Node) before returning from workers
  - Use `dataclasses.asdict()` for recursive dataclass conversion
- **Mypy Type Errors**: Resolved strict type checking issues across parsers
  - Ruby parser: Fixed `Node | None` handling in documentation extraction
  - Zig parser: Fixed `Query | None` handling in query execution
  - Crystal parser: Fixed parent node reference in lib function extraction
  - Summarization processor: Added proper type annotation for `extra_params`
- **OpenAI Provider Test**: Increased `max_tokens` from 1 to 10 in validation
  - Newer OpenAI models (GPT-5, o-series) require minimum tokens for response

### Code Quality

- **Ruff Lint Fixes**: Applied modern Python idioms across codebase
  - `UP007`: Use `X | Y` union syntax instead of `Optional[X]` or `Union[X, Y]`
  - `UP038`: Use `X | Y` in `isinstance()` calls instead of tuple syntax
  - `B904`: Use `raise ... from err` or `raise ... from None` for exception chaining
  - Reformatted 4 files with Ruff for consistent code style

## [0.8.7] - 2025-01-28

### Performance

- **Consolidated File I/O**: Reduced file reads from 2-4x per file to exactly once
  - `process_file()` now performs single read and uses content for all subsequent checks
  - Binary detection and language detection both use already-read content
  - Removed redundant `should_include_file()` call before executor submission

- **Inverted Language Detection Priority**: Extension-first O(1) lookup before guesslang ML
  - Added `get_language_by_extension()` for fast path-only language detection
  - Guesslang now used only as fallback via `__DETECT_BY_CONTENT__` marker
  - Deferred content-based detection runs in worker threads, not main thread

- **Parser Early Termination**: Skip fallback parsers when tree-sitter succeeds
  - Added `parser_early_termination` config option (default: True)
  - Added `parser_early_termination_threshold` config (default: 1 declaration)
  - Avoids running all 3 parser tiers when primary parser finds sufficient results

- **Parser Instance Caching**: LRU cache for parser instantiation
  - Added `@functools.lru_cache(maxsize=64)` to tree-sitter, enhanced, and standard parser loaders
  - Eliminates repeated module imports and parser object creation

- **Optimized Binary Detection**: Path-only checks before content checks
  - Added `is_likely_binary_by_path()` for fast extension-based binary detection
  - Added `is_binary_content()` for content-based checks using already-read data
  - `BINARY_EXTENSIONS` frozenset and `BINARY_SKIP_PATTERNS` for O(1) lookups

### Fixed

- **API Version Consistency**: FastAPI apps now use dynamic `__version__` from `codeconcat.version`
  - Fixed hardcoded outdated versions in `codeconcat/api/app.py` and `app.py`

## [0.8.6] - 2025-10-04

### Fixed
- **Performance Optimization**: Fixed double UTF-8 encoding in base tree-sitter parser
  - Reduced memory allocation by encoding content only once
  - Improved parsing performance across all tree-sitter based parsers
- **Test Infrastructure**: Fixed Apiiro ruleset mock configuration
  - Corrected git rev-parse stdout mock to return proper string values
  - Improved test reliability for security validation
- **Code Quality**: Resolved all linting warnings
  - Fixed unused parameter warnings in error handling module
  - Improved code maintainability and type safety

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
- **Documentation**: Added DeepWiki badge to README for enhanced documentation access

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
