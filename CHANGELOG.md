# Changelog

All notable changes to CodeConcat will be documented in this file

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
