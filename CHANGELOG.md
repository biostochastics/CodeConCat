# Changelog NEW ENTRIES APPEAR ON TOP

## [Unreleased]

### Fixed
- **Output Path Configuration**: Fixed issue where the `--output` CLI flag was being ignored and output was always written to `codeconcat_ccc.markdown`
  - Modified `main.py` to respect user-specified output paths from CLI
  - Updated `config_builder.py` to only set default output paths when no explicit path is provided
  - Changed output path override logic to preserve CLI and YAML specified paths

### Added
- **Comprehensive Test Coverage**: Improved test coverage from 51% to higher levels by adding comprehensive test suites:
  - Created extensive tests for `python_parser.py` covering all Python language features
  - Added comprehensive tests for `php_parser.py` covering PHP 5-8+ features
  - Created tests for `tree_sitter_php_parser.py` with mock support for tree-sitter availability
  - Added tests for `interactive_config.py` covering all user interaction flows
  - Created tests for `enhanced_pipeline.py` covering parser selection and caching

### Changed
- **Test Organization**: Organized new test files following existing conventions with descriptive test names and comprehensive coverage

## [0.7.4] - 2025-05-26

### Fixed
- **Tree-Sitter Parser Compatibility**: Fixed multiple compatibility issues with tree-sitter grammars:
  - Fixed regex escaping in doc comment patterns for Rust, C++, and PHP parsers (asterisks properly escaped)
  - Fixed tuple unpacking to handle both 2-tuple and 3-tuple returns from `query.captures()` across all 9 tree-sitter parsers
  - Updated query field names to match current grammar versions:
    - Rust: Removed invalid `visibility:` field references, capturing visibility as separate nodes instead
    - C++: Fixed `declaration:` field to use correct field names
    - C#: Changed `using_static_directive` to `using_directive`, fixed `type_parameter_list` to `type_parameters`
    - JavaScript/TypeScript: Fixed field references for assignment expressions
    - PHP: Changed `path:` to `name:` for namespace paths, removed invalid `modifier:` field
    - Julia: Updated node types - `comment` to `line_comment`, `module_expression` to `module_statement`, `block` to `block_expression`

- **API and Exclude Functionality**: 
  - Verified exclude-lists functionality is working correctly with PathSpec/GitWildMatchPattern
  - Confirmed REST API is fully functional with comprehensive test coverage
  - API includes security features: CORS, request tracing, validation middleware

### Added
- **Parser Test Suite**: Added comprehensive test suite `test_tree_sitter_parsers_fixed.py` to verify all parser fixes
- **API Documentation**: Documented API endpoints and functionality in README

### Changed
- **Parser Robustness**: All tree-sitter parsers now gracefully handle grammar version differences
- **Error Handling**: Parser query failures now log warnings but continue processing with fallback behavior

## [0.7.3] - 2025-05-26

### Fixed
- **Error Handling Improvements**: Fixed various error handling issues identified by static analysis:
  - Added debug logging with context when version retrieval fails in API CLI
  - Improved error logging in `get_node_text_safe` from DEBUG to ERROR level with full context
  - Fixed inconsistent error handling documentation in `install_semgrep` function
  
- **Code Quality Improvements**:
  - Extracted duplicated parser instance extraction logic into `_get_parser_name` helper function
  - Fixed invalid legacy format segment assignment in XML writer by validating segments belong to current file
  - Extracted mixed format handling into separate `_get_file_segments` function for better maintainability
  - Added input context (args/kwargs) to unexpected error logs for better debugging
  - Improved `safe_parser_method` decorator docstring with usage examples and return value details
  - Enhanced type hints documentation in `get_node_text_safe` to clarify expected node type

### Changed
- **Logging Improvements**:
  - Critical errors in parser utilities are now logged at ERROR level instead of DEBUG
  - Node text extraction failures now include node type and source type in error messages

## [0.7.2] - 2025-05-25

### Added
- **Common Utilities Module**: Created `parser_utils.py` with reusable parser utilities:
  - `safe_parser_method` decorator for consistent error handling across parsers
  - `extract_safe_substring` for bounds-checked string extraction
  - `get_node_text_safe` for safe tree-sitter node text extraction

- **Centralized Constants Module**: Added `constants.py` to consolidate shared configuration:
  - `DEFAULT_EXCLUDE_PATTERNS`: Unified file exclusion patterns used across collectors and config modules
  - `COMPRESSION_SETTINGS`: Centralized compression level configurations
  - `TOKEN_LIMITS`: Model-specific token limits
  - `SOURCE_CODE_EXTENSIONS`: Recognized source code file extensions
  - `SECURITY_PATTERNS`: Common security scanning patterns

### Changed
- **Thread Safety Improvements**: 
  - Added thread locks to global caches in `token_counter.py` and `security.py`
  - Prevents race conditions in multi-threaded environments
  - Thread-safe access to `_ENCODER_CACHE` and `FILE_HASH_CACHE`

- **Code Organization**:
  - Removed duplicate `DEFAULT_EXCLUDE_PATTERNS` definitions from multiple modules
  - All modules now import from centralized `constants.py`
  - Simplified compression processor to use constants dictionary

### Fixed
- **Import Organization**: Fixed leftover code fragments in `config_builder.py` from refactoring

## [0.7.2] - 2025-05-25

### Fixed
- **Test Suite Improvements:** Fixed 25+ failing tests to improve code quality and reliability:
  - Fixed configuration field name mismatches (include_patterns → include_paths, exclude_patterns → exclude_paths)
  - Fixed mock object attribute issues by adding required methods and properties to test mocks
  - Fixed function signature mismatches in test expectations
  - Fixed path handling between relative and absolute paths in various components
  - Fixed off-by-one errors in string position tests
  - Fixed language map to include uppercase `.R` extension and `.txt` files
  - Fixed test file extension expectations to use proper language-specific extensions
  - Fixed reconstruction module import and parameter issues
  - Fixed markdown writer AI preamble test by correcting mock patch location
  - Improved test coverage from 13% to 57% overall

### Changed
- **Token Counter Optimization:** Removed Davinci model token counting from TokenStats to eliminate dependency on deprecated model, simplifying the token counting interface

### Added
- **Comprehensive Input Validation System:**
  - Added robust validation framework with specialized validators for file paths, content, URLs, and configurations
  - Implemented schema-based configuration validation using JSON Schema
  - Added security validation with detection for suspicious code patterns, file signature verification, and content sanitization
  - Created API validation middleware with request/response validation, rate limiting, and size restrictions
  - Added file integrity verification with hash-based checks and tamper detection
  - Integrated validation throughout application processing pipeline
  - Included comprehensive test coverage for all validation components
- **Semgrep Security Integration:**
  - Added Semgrep integration with the Apiiro malicious code ruleset for advanced security scanning
  - Implemented auto-installation of Semgrep and ruleset when enabled
  - Added CLI options to control Semgrep security scanning: `--enable-semgrep`, `--install-semgrep`, `--semgrep-ruleset`, `--semgrep-languages`, and `--strict-security`
  - Enhanced security validation to integrate Semgrep findings with existing security checks
  - Added comprehensive documentation for the security validation system
- **Reconstruction Tool:** Added a new `CodeConcatReconstructor` class to handle reconstruction of original files from CodeConCat output.
- **Comprehensive Attack Pattern Detection:** Implemented extensive security patterns for all supported languages:
  - C/C++: Buffer overflows, format strings, command injection, use-after-free, integer overflow
  - Python: Code injection (eval/exec), pickle deserialization, SQL injection, weak crypto
  - R: eval(parse()) injection, system command injection, SQL injection, unsafe RDS loading
  - Julia: eval injection, unsafe ccall, command injection via run()
  - Go: SQL injection, command injection, path traversal, weak random, template injection
  - PHP: SQL injection, XSS, file inclusion, unserialize, command injection
  - Rust: Unsafe unwrap/expect, transmute, raw pointers, mutable statics
  - JavaScript/TypeScript: DOM XSS, eval injection, prototype pollution, React dangerouslySetInnerHTML
  - Cross-language: Hardcoded secrets, cryptocurrency wallets, base64 obfuscation
- **Enhanced Semgrep Integration:** Added custom security rules that complement the Apiiro ruleset with advanced patterns like use-after-free, double-free, SSTI, XXE, SSRF, timing attacks, and more

### Fixed
- **Parser Import Issues:** Fixed import errors in TOML parser and Tree-sitter base parser that prevented proper module loading
- **Tree-sitter Installation:** Resolved missing tree-sitter dependencies that were listed in requirements.txt but not properly installed
- **File Collection with include_paths:** Fixed issue where include_paths configuration was incorrectly expecting directory paths instead of glob patterns

### Changed  
- **YAML/YML File Handling:** Removed YAML and YML files from default exclusion patterns, allowing them to be processed when included via include_paths


## [0.7.1] - 2025-04-29

### Security
- **Improved Network Security:** Changed default host from `0.0.0.0` to `127.0.0.1` in both CLI and API server to prevent inadvertent exposure on all network interfaces.
- **Enhanced CORS Configuration:** Replaced overly permissive CORS settings with secure defaults and environment variable configuration (`CODECONCAT_ALLOWED_ORIGINS`).

### Added
- **Request Tracing:** Added request ID middleware for distributed tracing and correlation in API logs.
- **Parser Documentation:** Added comprehensive documentation to README about parser types (legacy, enhanced, tree-sitter) and their testing structure.
- **CLI Compression Support:** Added CLI arguments for the compression feature, making it accessible via command line:
  - `--enable-compression`: Enable intelligent code compression to reduce output size
  - `--compression-level`: Set compression intensity (low/medium/high/aggressive)
  - `--compression-placeholder`: Customize placeholder text for omitted segments
  - Advanced options like `--compression-keep-threshold` and `--compression-keep-tags`

### Changed
- **Code Quality Improvements:**
  - Replaced HTTP status code magic numbers with `HTTPStatus` enum for better readability.
  - Implemented proper redirect for API root endpoint using `RedirectResponse`.
  - Optimized tree-sitter dependency checks to reduce redundant filesystem operations.
  - Removed unused `BackgroundTasks` parameter from API upload endpoint.

## [0.7.0] - 2025-04-29

### Added
- **Added Tree-Sitter Parser Support**: enough said, fallbacks implemented.

- **Advanced Compression Support:**
    - Added new `CompressionProcessor` that intelligently compresses code content by preserving important segments and replacing less important ones with placeholder text.
    - Implemented configurable compression levels (low, medium, high, aggressive) with corresponding heuristics.
    - Added configuration options: `enable_compression`, `compression_level`, `compression_placeholder`, `compression_keep_threshold`, and `compression_keep_tags`.
    - Implemented segment-aware rendering in all output formats (Markdown, JSON, XML, text).
    - Smart preservation of security-sensitive code, API endpoints, control flow, and commented segments with keep tags.

- **Interactive Configuration Setup**: Enhanced the `--init` command to provide an interactive setup experience that guides users through creating a customized `.codeconcat.yml` configuration file with helpful prompts and explanations for each option.

- **REST API Server**: Added a FastAPI-based REST API with JSON request/response format, allowing remote access to code aggregation functionality.
    - Created new `codeconcat-api` command-line tool with customizable host, port, and logging options
    - Implemented comprehensive endpoints: `/api/concat` for JSON configuration, `/api/upload` for file uploads
    - Added utility endpoints for configuration discovery: `/api/config/presets`, `/api/config/formats`, `/api/config/languages`
    - Included auto-generated API documentation via Swagger UI at `/api/docs`, OpenAPI schema at `/api/openapi.json`, and ReDoc alternative documentation at `/api/redoc`
    - Added proper request/response validation with Pydantic models and error handling
    - Implemented CORS support for cross-origin requests
- **Configuration System:**
    - Implemented a new `ConfigBuilder` class with a clear four-stage configuration loading process (Defaults → Preset → YAML → CLI).
    - Added `--show-config-detail` flag to print the source of each configuration setting (default/preset/YAML/CLI).
    - Enhanced configuration validation and error reporting for a better user experience.
- **Enhanced Parser Implementations:**
    - Fixed Julia parser to properly identify nested declarations within modules, structs, and functions.
    - Improved Python parser to handle parent-child relationships and nested declarations correctly.
    - Verified JavaScript/TypeScript parser's enhanced declaration detection within classes and functions.
    - Added utility (`enable_debug.py`) to enable debug logging for all parsers with detailed output.
    - Created comprehensive test corpus for validating parser accuracy across all supported languages.
- **Parser Diagnostics:**
    - Implemented parser debug utility (`debug_parsers.py`) to compare basic and enhanced parsers.
    - Added capabilities for printing detailed diagnostics, parent-child relationships, and creating minimal test files.
- **Comprehensive Test Suite:**
    - Added unit tests for all system components with proper fixtures, assertions, and debug logging.
    - Implemented integration tests for the full parsing and rendering pipeline.
    - Added tests for configuration stages, rendering adapters, parser implementations, and end-to-end workflows.
- **Remote Input:** Added initial support for cloning remote Git repositories using `subprocess`, handling HTTPS, SSH, and `owner/repo[/ref]` shorthands.
- **Security Processing:**
    - Implemented sensitive data masking (PII, common secret patterns) using regex.
    - Added semgrep integration for security scanning.
- **Mask Output Content:** Added `--mask-output` flag to mask sensitive data directly in the final output content.
- **Output Masking:** Added `--mask-output` CLI flag and `mask_output_content` config option to mask detected secrets directly in the output content.
- **Enhanced Language Parsers:**
    - **Regex Parser Restoration:** Restored, enhanced, and integrated regex-based parsers for R, Rust, and Julia languages.
    - **Tree-sitter Query Improvements:** Added Tree-sitter queries for 10 major languages:
        - **R:** Improved Roxygen docstring extraction, S3/S4/R6 class detection, and function/variable declarations.
        - **Rust:** Enhanced trait implementation detection, generics, modifiers, and doc comments.
        - **Julia:** Better macro, struct, and type handling with improved docstring extraction.
        - **JavaScript/TypeScript:** Added support for modern ECMAScript features like decorators, async/await, React components, JSX/TSX, TypeScript types, and enhanced JSDoc parsing.
        - **PHP:** Added support for PHP 8+ features (attributes, enums, constructor property promotion), improved namespace resolution and PHPDoc handling.
        - **Python:** Better support for type hints, async functions, decorators, dataclasses, and docstring parsing.
        - **Java:** Enhanced generics, annotations, lambda expressions, records, and Javadoc extraction.
        - **C/C++:** Improved template handling, operator overloading, constructor/destructor detection, and doc comment parsing.
        - **C#:** Enhanced support for generics, interfaces, async methods, attributes, properties, and XML documentation.
        - **Go:** Better interface detection, embedded types, generics, and Go doc comment parsing.

### Changed
- **Code Quality Improvements:**
    - Applied black formatting with 100-character line length for consistent style across the codebase.
    - Fixed 80+ linting issues using ruff, including unused imports and variables.
    - Added properly configured .coveragerc file for code coverage reporting.
    - Fixed imports in language_parsers/__init__.py to match available classes.
    - Standardized import structure across test modules for better maintainability.
    
- **CLI Simplification:**
    - Renamed confusing flags: replaced `--no-tree/disable_tree` with clearer `--parser-engine={regex,tree_sitter}`.
    - Grouped CLI options into "Basic" and "Advanced" categories, hiding advanced options by default.
    - Added `--advanced` flag to show all advanced options in help output.
    - Improved help text and organization of related option groups.
- **Rendering Architecture:**
    - Decoupled data models from rendering logic to improve maintainability and extensibility.
    - Created dedicated rendering adapters for each output format (markdown, json, xml, text).
    - Modified `AnnotatedFileData` and `ParsedDocData` to store only structured data without rendering logic.
    - Implemented consistent rendering interfaces for all output formats.
- **Remote Input Refactoring:**
    - Renamed config fields in `CodeConCatConfig`: `github_url` -> `source_url`, `github_ref` -> `source_ref`.
    - Renamed CLI arguments: `--github` -> `--source-url`, `--ref` -> `--source-ref`.
    - Renamed collector module: `github_collector.py` -> `remote_collector.py`.
    - Renamed functions: `collect_github_files` -> `collect_git_repo`, `parse_github_url` -> `parse_git_url`.
    - Removed the `PyGithub` dependency as cloning is now handled via `subprocess`.
    - Updated `main.py` logic to use the new configuration fields and collector function.
- **Parser Interface Standardization:**
    - All language parsers now implement a common `ParserInterface` for consistent behavior.
    - Refactored regex parsers to follow the same interface as Tree-sitter parsers.
    - Updated parser selection logic to properly include all available parsers.
    - Improved documentation and logging for parser selection and fallback behavior.
- **Writer Refactoring:** Major refactoring of the output writers (`text`, `markdown`, `json`, `xml`) and `ai_context` helper to use polymorphism. Introduced a `WritableItem` interface and moved format-specific rendering logic into `AnnotatedFileData` and `ParsedDocData`. This eliminates type checking, adheres to SOLID principles, and improves maintainability and extensibility.

### Fixed
- **C++ Parser:**
    - Improved the docstring for `CppParser.parse` method to better explain its functionality and the `ParseResult` structure.
    - Added line number and content context to the warning log message when a line fails to match any parsing pattern, aiding debugging.
- **Text Writer:** Replaced hardcoded separator length (`80`) with a `SEPARATOR_LENGTH` constant for better readability and maintainability.
- **Core:** Fixed missing `List` import from `typing` in `main.py`.
- Addressed various linting and formatting issues identified by `isort` and `ruff`.
- **Test Suite Improvements:**
    - Fixed all multi-language corpus tests with better error handling and diagnostics.
    - Updated tests to be more resilient to parser output variations for C-family, Go, and Rust languages.
    - Added comprehensive diagnostics for parser test failures.
    - Fixed line number formatting in Markdown renderer tests.
    - JSON writer tests now handle missing `json_indent` configuration parameter with proper fallback.

## [0.6.6] - 2025-04-27

### Added
- Added `tqdm` progress bars for file collection, parsing, annotation, and output splitting to provide feedback during long operations.
- Added `--no-progress-bar` CLI flag to disable progress bars.
- Added `--use-gitignore`/`--no-use-gitignore` CLI flags and corresponding `use_gitignore` config option (default: True) to control whether `.gitignore` files are respected during file collection.
- Added `--use-default-excludes`/`--no-use-default-excludes` CLI flags and corresponding `use_default_excludes` config option (default: True) to control whether built-in default exclusion patterns (e.g., for `.git`, `__pycache__`) are applied.
- Added `--verbose` flag to enable detailed debug logging, particularly for file inclusion/exclusion decisions.
- Added `--format text` option to output a simple concatenation of processed file contents.
- Implemented Markdown cross-linking functionality for the existing `--cross-link-symbols` flag: generates HTML anchors for declarations and links to them from file summaries.

### Changed
- **Filtering Refactor:** Consolidated all path filtering logic (`include_paths`, `exclude_paths`, default excludes, `.gitignore`) to use the `pathspec` library consistently, providing more robust and predictable `.gitignore`-style pattern matching.
- **Parser Refactor:** Updated all language parsers (Python, Java, Go, C++, Rust, JavaScript/TypeScript, Julia, PHP, R) to return a standardized `ParseResult` object instead of a simple list/tuple. This object now explicitly includes extracted imports (`import`, `use`, `require`, `library`, etc.) alongside declarations, file path, language, and original content. This simplifies downstream processing and improves consistency.
- Made `ParseResult` and `CodeConCatConfig` classes more backward compatible for easier integration.
- Updated docstrings throughout for better documentation.

### Fixed
- Improved error handling in security processor (`_mask_sensitive_data`) to prevent potential index errors.
- Moved `traceback` imports to the top level in relevant files (`security_processor.py`, `github_collector.py`, `file_parser.py`) to avoid potential `ImportError` during exception handling.
- Refactored `load_config` to correctly handle configuration precedence (CLI > `.codeconcat.yml` > defaults) and improve robustness against `None` values from CLI defaults.
- Fixed an issue where the file parser (`file_parser.py`) could fail if a language-specific parser returned the richer `ParseResult` object instead of a simple tuple/list.
- Fixed `collect_local_files` function to correctly process the input path when it points to a single file instead of a directory.


## [0.6.5] - 2025-04-26

### Added
- Added default exclusion patterns (`venv/`, `.venv/`, `env/`, `*env/`, etc.) to automatically skip common virtual environment directories.
- Added debug logging to `local_collector` to show which specific exclusion pattern (default or gitignore) caused a file to be skipped.

### Fixed
- Refactored language detection logic during file collection to prevent potential errors and improve efficiency.
- CLI --include-paths/--exclude-paths now properly override config/YAML
- Parsing works for files from temp directories (GitHub collector)
- LICENSE and README always included by default
- Improved import paths and folder tree call
- **GitHub Default Includes:** When using `--github` without explicitly providing `--include-paths` on the command line, the tool now defaults to including `['**/*', 'LICENSE*', 'README*']`. This overrides potentially restrictive `include_paths` settings from a local `.codeconcat.yml` file, ensuring broader file collection from the target repository by default.

## [0.6.4] - 2025-04-17

### Added

- Multi-stage progress bars for all major processing steps (file collection, parsing, annotation, doc extraction, output writing) using `tqdm`. Toggle with `--no-progress-bar`.
- Markdown cross-linking: symbol summaries in Markdown now link to their definitions for easier navigation. Toggle with `--cross-link-symbols`.

### Fixed
- Grouped CLI arguments for better usability.
- Improved config loading and dynamic versioning using Hatchling (`pyproject.toml` + `version.py`).
- Cleaned up and standardized `pyproject.toml` for modern Python packaging.
- Improved documentation and error messages for output writing and config handling.
- The Markdown output now always includes explicit lists of all functions, classes, structs, and symbols for each file under a dedicated analysis section, improving visibility and AI comprehension.
- The annotation logic was improved and a bug was fixed so that all parsed declarations (not just comments or TODOs) are included in the output.
- CLI/config improvements: grouped arguments, more helpful help output, and new flags for progress bars and cross-linking.
- Fixed bug where annotated functions/classes were not shown in Markdown output due to overly restrictive filtering in the writer.
- Token counting (`tiktoken`) and security scanning (`transformers`) are now documented as optional dependencies and can be installed via `extras_require` (`[token]`, `[security]`, `[all]`).

## [0.6.3] - 2025-04-16

### Added
- Added `--remove-docstrings` CLI option to exclude documentation strings (Python, JS/TS/Java, C#, Rust, R) from the output.
- Added Configurable Security Scanning that introduced several options in .codeconcat.yml to control security scanning:
    - `enable_security_scanning`: Globally enable/disable the scanner (defaults to true).
    - `security_scan_severity_threshold`: Set the minimum severity level to report (defaults to "MEDIUM").
    - `security_ignore_paths`: Specify glob patterns for files/directories to exclude from scanning (e.g., `["tests/", "**/vendor/**"]`).
    - `security_ignore_patterns`: Define regex patterns to ignore specific matched findings based on the content of the finding.
    - `security_custom_patterns`: Add user-defined secret detection rules (each requiring `name`, `regex`, and `severity`).
- Added more built-in regex patterns to detect common secrets like specific GitHub token formats, Slack tokens, PEM private keys, generic passwords, etc.
- Added support for inline comments (`# nosec` or `# codeconcat-ignore-security`) on the same line or the preceding line to suppress security findings.
- Added `--sort-files` flag to alphabetically sort files by path in the final output.
- Added `--split-output X` flag to split Markdown output into X separate files.
- Added unit tests for error handling in updated language parsers.


### Changed
- Updated language parsers (Python, Go, JS/TS, Julia, PHP, R) to raise `LanguageParserError` for syntax errors instead of failing silently or raising generic exceptions.
- Enhanced AI preamble (`ai_context.py`) to include codebase complexity metrics (function count, avg length), potential entry point detection, and key file summaries.
- Improved CLI usability (`main.py`): Added argument groups for clarity in `--help`, implemented `--version` flag, and added `--show-config` flag to display the final merged configuration.
- Refactored default config creation (`main.py`) to use a template file (`config/default_config.template.yml`) instead of a hardcoded string.
- Findings detected within common test or example directory patterns (e.g., `tests/`, `examples/`, files named `*test*`) will now have their severity automatically downgraded (e.g., CRITICAL -> HIGH, HIGH -> MEDIUM) to reduce noise from non-production secrets.
- Corrected the function call to `get_token_stats` in `file_parser.py`.
- SecurityProcessor now raises `LanguageParserError` for invalid syntax
- Refactored token counting to use `get_token_stats` function
- Replaced approximate Claude token counting with accurate offline method using `transformers` (`Xenova/claude-tokenizer`).
- Refactored file inclusion logic in `local_collector.py` into a shared `should_include_file` function to reduce duplication.
- Enhanced configuration loading (`config_loader.py`) and definition (`base_types.py`) using Pydantic for robust validation and clearer error messages.
- Improved C++ parser (`cpp_parser.py`) block end detection to correctly handle braces within preprocessor directives (`#if`/`#else`/`#endif`).
- Refactored file processing logic.

## [0.6.2] - 2025-04-16

### Added

- 📝 Added comprehensive documentation:
  - New `doc_workflows.md` guide for documentation features
  - New `security_processor.md` guide for security scanning
  - Enhanced inline documentation across codebase
- 🔄 Unified return types across collectors:
  - GitHub collector now returns `ParsedFileData` objects
  - Consistent interface between local and GitHub collectors
- ✅ Added GitHub collector tests:
  - URL parsing and clone URL building
  - File collection and error handling
  - Integration with local collector
- 🔍 Improved R language support:
  - Added support for `.R`, `.Rs`, `.rs`, and `.RScript` extensions
  - Case-insensitive extension matching for R files
  - Auto-exclude `.Rcheck`, `.Rhistory`, and `.RData` files
- 🔧 Improved test file handling:
  - Better detection and display of test file content
  - Clear indication when test files are empty
  - Support for various test file naming patterns

### Changed
- ♻️ Refactored GitHub collector:
  - Now uses temporary directory for cloning
  - Reuses local collector for file processing
  - Better error handling and logging
- 📚 Reorganized documentation structure:
  - Moved detailed guides to `docs/` directory
  - Simplified main README for quick start
  - Added comprehensive examples

### Fixed
- 🐛 Fixed issue where test file content was not being displayed in output
- 🐛 Fixed GitHub collector tests
- 🔧 Improved test file handling to show full content while maintaining summaries
- 🔧 Fixed file filtering in local collector
- 📄 Fixed documentation formatting and links

## [0.6.1] - 2025-01-18

### Fixed
  - Minor bugs

## [0.6.0] - 2025-01-12

### Added
- 🔌 Added programmatic Python API for direct code integration
  - New `run_codeconcat_in_memory()` function returns output as string
  - Full access to all CodeConCat features through Python API
  - Comprehensive test suite for API functionality
- 🌐 Added FastAPI web server for HTTP access
  - POST `/concat` endpoint for code processing
  - Support for all output formats (markdown, JSON, XML)
  - Automatic API documentation with Swagger UI
- 📚 Enhanced documentation
  - Added programmatic usage examples
  - Added web API usage guide
  - Updated configuration documentation
- 🎯 Added .gitignore support
  - Automatically respects project's .gitignore rules
  - Added common ignore patterns for build artifacts
  - Improved file filtering performance

### Changed
- ♻️ Refactored core functionality for better reusability
  - Separated CLI concerns from core processing
  - Improved error handling and validation
  - Better type hints and documentation
- 🧪 Improved test coverage
  - Added end-to-end workflow tests
  - Added API-specific test cases
  - Added edge case handling tests

### Fixed
- Fixed output handling to properly return strings in memory
- Improved error handling in file processing
- Enhanced validation of configuration options

## [0.5.2] - 2025-01-08

### Added
- Added token counting for programming quotes using tiktoken
- Added ASCII art frame around programming quotes in terminal output
- Added more programming quotes to the collection
- Added progress spinner for better visibility of processing steps
- Added accurate GPT-4 token counting for all processed content

### Changed
- Improved token counting accuracy by using cl100k_base tokenizer
- Streamlined output display with cleaner token count presentation
- Enhanced progress feedback during file processing

### Fixed
- Improved path handling to better exclude Next.js build artifacts and non-code files
- Enhanced directory exclusion patterns to handle `.next` and other build directories
- Fixed double slash issues in path handling

## [0.5.1] - 2025-01-08

### Added
- 🔒 Added security scanning functionality to detect potential secrets and sensitive information
  - AWS keys and secrets
  - GitHub tokens
  - Generic API keys
  - Private keys (RSA, etc.)
  - Basic auth credentials
  - Bearer tokens
  - Smart detection with ignore patterns for test/sample values
- 📊 Added token counting functionality using tiktoken
  - Support for multiple models (GPT-3.5, GPT-4, Davinci)
  - Approximate token counting for Claude
  - Token statistics in file summaries

### Changed
- 🏗️ Improved code organization:
  - Moved core types to base_types.py
  - Separated security and token counting into dedicated modules
  - Eliminated circular dependencies
  - Better type organization and imports

## [0.5.0] - 2025-01-07

### Added
- 🔄 Introduced `BaseParser` class for standardized parsing across languages
- 🎯 Added `CodeSymbol` class for better code structure representation
- ⚡️ Added new language parsers:
  - Java: Classes, interfaces, enums, methods, annotations
  - Go: Packages, interfaces, structs, functions
  - PHP: Classes, interfaces, traits, methods
- 🔧 Enhanced JavaScript/TypeScript parser:
  - Better decorator handling
  - Improved interface and type support
  - Fixed language detection and initialization
  - Added JSX/TSX support
- ⚡️ Added C, C#, C++ parsers with comprehensive support:
  - Classes, structs, and unions
  - Templates and generics
  - Namespaces and using directives
  - Properties and events (C#)
  - Attributes and annotations
- 🌟 Enhanced Julia parser with comprehensive language support:
  - Functions, structs, abstract types, modules, constants, macros
  - Support for exports and type annotations
  - Block-level construct tracking
- 🔧 Enhanced R parser with improved language features:
  - S4 class and method support
  - Package imports and exports
  - Better variable and constant detection
- ⚡️ Enhanced Rust parser with modern language features:
  - Improved trait and impl block handling
  - Generic parameter support
  - Attribute handling
  - Module system support
- 🎨 Added new CLI options for fine-grained control:
  - `--no-annotations` to disable code annotations
  - `--no-symbols` to disable symbol extraction
  - `--debug` for detailed logging

### Changed
- 🔄 Refactored all language parsers to use the new base parser
- 📦 Improved code organization and modularity
- 🎯 Enhanced symbol relationship tracking
- 🔧 Better handling of language-specific features
- 📝 Improved logging and error messages
- ⚡️ More efficient file processing in local collector
- 🎨 Updated documentation and examples for all languages
- 🔍 Improved language detection accuracy
- 🚀 Enhanced parsing performance across all languages

### Fixed
- 🐛 Better handling of nested code blocks
- 🔒 Improved error handling in file processing
- 🔍 More accurate symbol detection and relationships
- 🎨 Fixed inconsistencies in annotation handling
- 🔧 Fixed JavaScript/TypeScript parser initialization
- 🐛 Resolved language detection edge cases
- 🔍 Fixed parsing issues with complex inheritance
- ⚡️ Addressed memory usage in large codebases

## [0.4.1] - 2025-01-04

### Added
- Enhanced file exclusion patterns for cleaner code tree generation
- Better handling of documentation build artifacts
- Improved handling of molecular dynamics files
- More comprehensive cache directory exclusions
- Added `**` pattern support for nested directory exclusions
- Added specific exclusions for Sphinx documentation artifacts
- Added molecular dynamics file patterns (ANTECHAMBER, PDB, etc.)

### Changed
- Updated version from 0.3.0 to 0.4.0
- Improved pattern matching for nested directories using `**` patterns
- Reorganized exclusion patterns into logical categories
- Enhanced documentation build artifact handling
- More thorough Git-related file exclusions

### Fixed
- Better handling of git-related files and directories
- More thorough exclusion of build and temporary files
- Improved handling of Python cache directories at all depths
- Fixed potential leakage of binary and temporary files
- Better organization of exclusion patterns for maintainability

## [0.3.0] - Initial Release

### Added
- Initial release of CodeConCat
- Multi-language parsing support (Python, JavaScript/TypeScript, R, Julia, C/C++)
- Documentation extraction capabilities (.md, .rst, .txt, .rmd)
- Configurable settings via .codeconcat.yml
- Concurrent file processing with ThreadPoolExecutor
- Multiple output formats (Markdown and JSON)
- GitHub repository support with private token authentication
- Basic symbol extraction for constants and variables
- Default system file exclusions
- Command-line interface (CLI)
- Automatic clipboard support
- Basic regex-based code parsing
- Support for custom file extension mapping

## [0.1.0] - 2024-01-07

### Added
- Initial release
- Basic code concatenation functionality
- Support for multiple languages
- Documentation extraction
- GitHub integration
- Markdown and JSON output formats
- Configuration file support
- Concurrent file processing
