# Changelog

/\___/\
(  o o  )  
(  =^=  ) ___________________
 (---)  /                    \
/     \/  "Write code as if  |
|      |   the next person    |
|      |   to maintain it is  |
\____/    a psychopath who   |
         knows where you     |
         live."             /
         ________________/

## [0.6.2] - 2025-02-27

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
- 🐛 Fixed GitHub collector tests
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
