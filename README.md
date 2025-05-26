# CodeConCat

<p align="center">
  <img src="assets/codeconcat_logo.png" alt="CodeConCat Logo" width="300"/>
</p>

> A simple code aggregator and documentation extractor optimized for AI comprehension and collaborative workflows

## Overview

CodeConCat is your semi-intelligent companion for preparing codebases. It automatically ingests, processes, and formats your code in a way that's optimized for AI comprehension and collaborative/iterative workflows. The tool provides structured output with smart context generation, making it ideal for sharing code with AI assistants and collaborators.

With enhanced language parsers for 10 major programming languages, CodeConCat extracts rich semantic information from your codebase, including functions, classes, imports, and documentation.

```python
from codeconcat import run_codeconcat_in_memory, CodeConCatConfig

# Process a codebase and get the output as a string
config = CodeConCatConfig(
    target_path="path/to/code",
    format="markdown"
)
output = run_codeconcat_in_memory(config)
```

## Installation

```bash
# Clone the repository
git clone https://github.com/biostochastics/codeconcat.git
cd codeconcat

# Install in editable mode (recommended for development)
pip install -e .
```

## Optional Dependencies & Extras

Some features require optional dependencies. You can install them via [extras_require](https://pip.pypa.io/en/stable/topics/dependency-management/#extras-optional-dependencies):

- **Clipboard Integration** (`pyperclip`): Used for copying output to the clipboard. Installed by default.
- **Token Counting** (`tiktoken`): For accurate GPT-4 token counting.
- **Security Scanning** (`transformers`): For advanced code security scanning (if enabled in config) and Claude tokenizer.
- **Tree-sitter Parsing** (`tree_sitter`): For enhanced code parsing capabilities. All Tree-sitter language bindings are bundled with CodeConCat for use with supported languages.

Install with extras:

```bash
# Token counting support
pip install -e ".[token]"

# Security scanning support
pip install -e ".[security]"

# All optional features (web, token, security, test)
pip install -e ".[all]"
```

## Features

- **AI-Optimized Output**: Structured content with smart context generation
- **Smart File Collection**: Intelligent filtering and organization of your codebase, including support for `.gitignore` rules and consistent glob pattern matching via the `pathspec` library.
- **Documentation Extraction**: Automatically extract and process documentation
- **Directory Tree**: Visual representation of your project structure
- **Multiple Formats**: Output in Markdown, JSON, XML, or plain Text (`--format text`).
- **Language Detection**: Automatic language detection and syntax highlighting
- **Clipboard Integration**: One-click copy to clipboard
- **Advanced Compression**: Intelligently omit less important code segments while preserving critical metadata and important code
- **Markdown Cross-Linking**: When using `--format markdown` and the `--cross-link-symbols` flag, symbol summaries in the Markdown output will link to their corresponding definitions via HTML anchors for easier navigation.
- **Token Counting**: Accurate GPT-4 token counting for all processed content
- **Progress Tracking**: Real-time progress indication during processing (multi-stage progress bars for file collection, parsing, annotation, doc extraction, output writing; toggle with `--no-progress-bar`)
- **Comprehensive Code Analysis**: Functions, classes, structs, and symbols are listed in the Markdown output under each file's analysis section for full visibility.
- **File Reconstruction**: Reconstruct original source files from any CodeConCat output format (markdown, XML, JSON) using the `--reconstruct` command.
- **Advanced Language Support**: Dual-parser system with both regex-based and Tree-sitter parsers (select with `--parser-engine={tree_sitter,regex}`):
  - **Tree-sitter Parsers**: High-accuracy parsing for 10 major languages with modern language feature support:
    - Python (type hints, async functions, dataclasses)
    - JavaScript/TypeScript (JSX/TSX, decorators, modern ES features)
    - Java (generics, annotations, lambdas, records)
    - C/C++ (templates, namespaces, operator overloading)
    - C# (generics, attributes, async/await)
    - Go (interfaces, embedded types, generics)

## Parser Strategies & Capabilities

CodeConCat features a parser architecture designed for robustness, accuracy, and flexibility across multiple programming languages.

### Parser Types

The codebase includes three types of parsers, each with specific strengths and use cases:

1. **Legacy Parsers** - The original regex-based parsers that formed the foundation of CodeConCat:
   - Simple pattern matching against language constructs
   - Limited support for complex language features
   - Being phased out in favor of enhanced and tree-sitter parsers
   - Located in `codeconcat/parser/language_parsers/{language}_parser.py`

2. **Enhanced Parsers** - Improved regex-based parsers with better recognition capabilities:
   - More sophisticated regex patterns and state tracking
   - Better support for nested declarations and complex syntax
   - Improved docstring extraction and handling
   - Located in `codeconcat/parser/language_parsers/enhanced_{language}_parser.py`

3. **Tree-sitter Parsers** - Modern parsers using the Tree-sitter parsing library:
   - Full syntax tree parsing for accurate code structure recognition
   - Support for advanced language features and precise source locations
   - Best handling of nested declarations and complex constructs
   - Located in `codeconcat/parser/language_parsers/tree_sitter_{language}_parser.py`

### Parser Engine Selection

```bash
# Use Tree-sitter (default, recommended for most use cases)
codeconcat --parser-engine tree_sitter

# Use enhanced regex-based parsers
codeconcat --parser-engine enhanced

# Use legacy regex-based parsers (not recommended)
codeconcat --parser-engine regex
```

### Fallback Mechanism

When Tree-sitter mode is enabled (default), CodeConCat employs a sophisticated fallback strategy for maximum compatibility:

1. First attempts to use a Tree-sitter grammar if available for the language
2. If Tree-sitter parsing fails or is unavailable, falls back to the enhanced regex parser
3. Processing continues without interruption for the remainder of the codebase

### Testing Structure

Each parser type has corresponding test files to ensure correct functionality:

1. **Legacy Parser Tests** - Located in `tests/unit/parser/test_{language}_parser.py`
   - These tests validate the basic functionality of the original parsers
   - Being maintained for backwards compatibility but will eventually be removed

2. **Enhanced Parser Tests** - Located in `tests/unit/parser/test_enhanced_{language}_parser.py`
   - Comprehensive tests for the improved regex-based parsers
   - Test nested declarations, docstring extraction, and language-specific features
   - Use the modern `Declaration` class with direct `start_line`/`end_line` attributes

3. **Tree-sitter Parser Tests** - Located in `tests/unit/parser/test_tree_sitter_{language}_parser.py`
   - Tests for the Tree-sitter-based parsers
   - Validate accurate syntax tree parsing and handling of complex language constructs
   - Mock Tree-sitter dependencies for consistent test results
   - Use the modern `Declaration` class with direct attributes

### Diagnostic Commands

For troubleshooting parsing issues:

```bash
# Verify Tree-sitter dependencies are correctly installed
codeconcat --verify-dependencies

# Diagnose parsing issues with a specific file
codeconcat --diagnose-parser /path/to/problem/file.py
```

### Development Guidelines

When extending or maintaining parsers:

1. **Focus on Tree-sitter and Enhanced Parsers** - Legacy parsers are being phased out
2. **Follow Modern Declaration API** - Use the `Declaration` class directly with `start_line`/`end_line` attributes
3. **Test Edge Cases** - Ensure robust handling of complex language constructs
4. **Provide Fallbacks** - Allow graceful degradation when specific features are unavailable

### Auto-Fallback Mechanism

When a Tree-sitter parser encounters parsing issues:

1. The system logs detailed diagnostics about the error
2. It automatically falls back to the regex parser for that specific file
3. Processing continues without interruption for the remainder of the codebase

### Diagnostic Commands

For troubleshooting parsing issues:

```bash
# Verify Tree-sitter dependencies are correctly installed
codeconcat --verify-dependencies

# Diagnose parsing issues with a specific file
codeconcat --diagnose-parser /path/to/problem/file.py
```

## Configuration System

CodeConCat features a structured configuration system with a clear precedence order:

### Configuration Precedence

1. **Defaults**: Built-in default values from the `CodeConCatConfig` model
2. **Preset**: Predefined configuration sets ('lean', 'medium', 'full')
3. **YAML**: Values from `.codeconcat.yml` file in project root (or `.codeconcat.yaml`)
4. **CLI arguments**: Command-line options (highest priority)

### Configuration Transparency

View the exact source of each configuration setting:

```bash
codeconcat --show-config-detail
```

Output example:
```
Configuration Details:
======================

DEFAULT settings:
----------------
  target_path: .
  format: markdown
  output: output.md
  ...

PRESET settings:
---------------
  parser_engine: tree_sitter
  include_file_summary: true
  include_repo_overview: true
  ...

YAML settings:
-------------
  include_paths: ['**/*.py', '**/*.js']
  exclude_paths: ['**/test/**']
  ...

CLI settings:
-----------
  format: json
  output: custom_output.json
  ...
```

### Configuration Builder API

For programmatic use, the `ConfigBuilder` class provides a fluent interface:

```python
from codeconcat.config.config_builder import ConfigBuilder

# Create and customize configuration
config_builder = ConfigBuilder()
config_builder.with_defaults()
config_builder.with_preset("medium")  # lean, medium, or full
config_builder.with_yaml_config("path/to/.codeconcat.yml")  # Optional
config_builder.with_cli_args({"format": "json", "parser_engine": "regex"})

# Build final configuration
config = config_builder.build()
```

## Advanced Compression

CodeConCat's compression feature intelligently reduces output size by omitting less important code segments while preserving critical metadata and important code. This is particularly useful when working with large codebases where sending the entire codebase to an AI assistant would exceed token limits.

### Enabling Compression

```bash
# Enable compression with default settings (medium level)
codeconcat --enable-compression

# Specify compression level
codeconcat --enable-compression --compression-level high

# Customize placeholder text
codeconcat --enable-compression --compression-placeholder "[...{lines} lines omitted...]"
```

### Compression Mechanics

Compression works by scoring line importance based on factors like:
- Code complexity and nesting level
- Presence of comments and docstrings
- Special tags in comments (e.g., `#important`, `#keep`)  
- Declarations and function definitions
- Security issues flagged by security processor

### Controlling Preserved Content

You can control which segments are always preserved regardless of their score:

```python
# This function will always be kept in output due to the #important tag
def utility_function():
    # important: This is crucial for error handling
    pass
```

### Compression Configuration

Compression settings can be configured in `.codeconcat.yml`:

```yaml
# Compression Configuration
enable_compression: true
compression_level: medium  # low, medium, high, or aggressive
compression_placeholder: "[...code omitted ({lines} lines, {issues} issues)...]"
compression_keep_threshold: 3  # Minimum lines to consider a segment for omission
compression_keep_tags: ["important", "keep", "security"]  # Tags that mark segments to always keep
```

### Output Format Support

All four output formats (Markdown, JSON, XML, Text) support compression:

- **Markdown**: Displays placeholders in code blocks
- **JSON**: Includes metadata about omitted segments 
- **XML**: Preserves the full segment structure with type and metadata
- **Text**: Simple omission with placeholder text

## Interactive Configuration

CodeConCat provides an interactive setup experience to help you create a customized configuration file:

```bash
# Start the interactive setup
codeconcat --init
```

The interactive setup guides you through:
- Output preset selection (lean, medium, full)
- Language selection for your project
- Excluded paths configuration
- Output format selection
- Parser engine selection
- Compression settings

This creates a `.codeconcat.yml` file in your project directory that you can further customize as needed.

## REST API

CodeConCat now includes a FastAPI-based REST API server that allows you to process code remotely via HTTP requests. This is ideal for integrating CodeConCat into web applications, workflows, or services.

### Starting the API server

```bash
# Start the API server with default settings (port 8000)
codeconcat-api

# Specify host and port
codeconcat-api --host 127.0.0.1 --port 9000

# Development mode with auto-reload
codeconcat-api --reload
```

### API Endpoints

The API provides several endpoints:

- **POST /api/concat**: Process code based on JSON configuration
- **POST /api/upload**: Upload and process a zip file containing code
- **GET /api/ping**: Check if the API is running
- **GET /api/config/presets**: Get available configuration presets
- **GET /api/config/formats**: Get available output formats
- **GET /api/config/languages**: Get supported programming languages

Documentation is available at `/api/docs` when the server is running.

### Example API Usage

```python
import requests

# Process a GitHub repository
response = requests.post(
    "http://localhost:8000/api/concat",
    json={
        "source_url": "username/repo",
        "format": "json",
        "parser_engine": "tree_sitter",
        "enable_compression": True,
        "compression_level": "medium"
    }
)

# Get the processed output
result = response.json()
print(result["content"])
```

### Programmatic API

For direct integration with Python code:

```python
from codeconcat import run_codeconcat_in_memory, CodeConCatConfig

# Basic usage
config = CodeConCatConfig(
    target_path="path/to/code",
    format="markdown"
)
output = run_codeconcat_in_memory(config)

# Advanced configuration
config = CodeConCatConfig(
    target_path="path/to/code",
    format="json",
    parser_engine="tree_sitter",  # tree_sitter or regex
    include_paths=["**/*.py", "**/*.js"],
    exclude_paths=["**/tests/**"],
    enable_compression=True,
    compression_level="medium"
)
output = run_codeconcat_in_memory(config)
```

## Architecture & Design

CodeConCat follows modern software design principles for maintainability and extensibility:

### SOLID Design Principles

- **Single Responsibility**: Each component has one clear purpose
- **Open/Closed**: System is open for extension without modification
- **Liskov Substitution**: Writers use polymorphism via the `WritableItem` interface
- **Interface Segregation**: Focused interfaces with minimal dependencies
- **Dependency Inversion**: High-level modules depend on abstractions

### Component Architecture

The system consists of several key components:

- **Collectors**: Gather files from local or remote sources
- **Parsers**: Extract structure and semantics from code (Tree-sitter and regex)
- **Processors**: Transform and enhance parsed data (security, compression)
- **Writers**: Output data in various formats (Markdown, JSON, XML, text)

### Polymorphic Design

CodeConCat uses a polymorphic architecture for output generation:

- `WritableItem` interface defines the contract for renderable items
- `AnnotatedFileData` and `ParsedDocData` implement this interface
- Writers operate on any `WritableItem` without type checks
- This allows easy extension with new output types

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--target-path` | `.` | Path to code directory |
| `--source-url` | `None` | Remote Git repository URL or shorthand (e.g., `username/repo`) |
| `--format` | `markdown` | Output format (markdown, json, xml, text) |
| `--output` | `output.md` | Output file path |
| `--output-preset` | `medium` | Preset config (lean, medium, full) |
| `--parser-engine` | `tree_sitter` | Parser engine to use (tree_sitter, regex) |
| `--include-paths` | `[]` | Include specific glob patterns |
| `--exclude-paths` | `[]` | Exclude paths/patterns |
| `--enable-compression` | `false` | Enable intelligent code compression |
| `--compression-level` | `medium` | Compression level (low, medium, high, aggressive) |
| `--compression-placeholder` | `[...]` | Template for placeholder text replacing omitted segments |
| `--compression-keep-threshold` | `3` | Minimum lines to consider keeping a segment |
| `--compression-keep-tags` | `important,keep,security` | Special comment tags that mark segments to always keep |
| `--max-workers` | `4` | Number of concurrent threads for processing |
| `--init` | `false` | Interactive setup: create a customized `.codeconcat.yml` and exit |
| `--show-config-detail` | `false` | Display the final merged configuration with sources |
| `--verify-dependencies` | `false` | Verify Tree-sitter language bindings are correctly installed |
| `--diagnose-parser` | `false` | Run detailed parser diagnostics on a single file |
| `--advanced` | `false` | Show all available command-line options |
| `--cross-link-symbols` | `false` | Enable Markdown cross-linking between symbol summaries and definitions |

## Examples

### Basic Usage

```bash
# Process current directory
codeconcat

# Process specific directory with custom output file
codeconcat --target-path ./src --output code_summary.md

# Process a GitHub repository
codeconcat --source-url username/repo
```

### Format Selection

```bash
# Generate markdown output (default)
codeconcat --format markdown

# Generate JSON output
codeconcat --format json

# Generate XML output
codeconcat --format xml

# Generate plain text output
codeconcat --format text
```

### Customizing Content

```bash
# Use lean preset (minimal output)
codeconcat --output-preset lean

# Use full preset (comprehensive output)
codeconcat --output-preset full

# Enable code compression
codeconcat --enable-compression --compression-level high

# Enable symbol cross-linking in markdown
codeconcat --cross-link-symbols
```

### Language Selection

```bash
# Process only Python files
codeconcat --include-languages python

# Process Java, Go, and PHP files
codeconcat --include-languages java go php

# Process all supported languages
codeconcat --include "**/*.{py,js,ts,java,go,php,rb,r,jl,rs,cpp,cs}"
```

### GitHub Integration

```bash
# Process a public repo (default branch)
codeconcat --source-url username/repo

# Process a specific branch
codeconcat --source-url username/repo --source-ref main

# Process a specific commit or tag
codeconcat --source-url username/repo --source-ref v1.0.0

# Use with authentication (for private repos)
codeconcat --source-url username/repo --github-token YOUR_TOKEN
```

### File Filtering

CodeConCat provides multiple ways to control which files are processed:

1. **.gitignore Support**
   - Automatically respects your project's `.gitignore` rules
   - Common patterns (e.g., `__pycache__`, `node_modules`, `tests/`) are always ignored
   - Test directories (`tests/`, `test/`) are excluded by default
   - No configuration needed - just works!

2. **Configuration File**
   ```yaml
   include_paths:
     - "**/*.{py,js,ts}"
     - "**/README*"
     - "**/*.yml"  # YAML files are no longer excluded by default
   exclude_paths:
     - "**/tests/**"
     - "**/build/**"
   ```
   
   **Note:** The `include_paths` option uses glob patterns, not directory paths. For example:
   - ✅ Correct: `"**/*.py"` (matches all Python files)
   - ❌ Incorrect: `"/path/to/directory"` (this won't match files)

3. **Command Line**
   ```bash
   codeconcat --include "**/*.py" --exclude "**/tests/**"
   ```

Priority order for file filtering:
1. .gitignore rules (highest priority)
2. Command line arguments
3. Configuration file
4. Default settings

## Security Scanning

CodeConCat includes built-in security scanning capabilities to help identify potential security issues in your codebase:

### Basic Security Scanning

Basic security scanning is enabled by default and detects common patterns like:
- Hardcoded credentials (API keys, passwords, tokens)
- SQL injection vulnerabilities
- Command injection risks
- Path traversal vulnerabilities

```bash
# Enable security scanning (enabled by default)
codeconcat --enable-security-scanning

# Strict mode - fails processing if security issues are found
codeconcat --enable-security-scanning --strict-security
```

### Advanced Semgrep Integration

For more comprehensive security analysis, CodeConCat integrates with Semgrep and the Apiiro malicious code ruleset:

```bash
# Enable Semgrep security scanning with auto-installation
codeconcat --enable-semgrep --install-semgrep

# Use with strict mode to fail on any findings
codeconcat --enable-semgrep --strict-security

# Specify languages for Semgrep scanning
codeconcat --enable-semgrep --semgrep-languages python,javascript

# Use custom ruleset directory
codeconcat --enable-semgrep --semgrep-ruleset /path/to/custom/rules
```

### Configuration File Options

```yaml
# .codeconcat.yml
enable_security_scanning: true
enable_semgrep: true
install_semgrep: true
strict_security: false
semgrep_languages:
  - python
  - javascript
  - go
```

### Security Features

1. **Pattern-based Detection**: Identifies common security anti-patterns
2. **Comprehensive Attack Patterns**: Language-specific detection for:
   - Buffer overflows, format string bugs, use-after-free (C/C++)
   - Code injection, SQL injection, deserialization (Python, PHP, R, Julia)
   - XSS, prototype pollution, DOM manipulation (JavaScript/TypeScript)
   - Command injection, path traversal, SSRF (Go)
   - Memory safety, race conditions (Rust)
   - Cross-language patterns (hardcoded secrets, crypto wallets, obfuscation)
3. **Semgrep Integration**: Uses industry-standard static analysis with custom rules
4. **Apiiro Ruleset**: Automatically installs and uses the Apiiro malicious code detection rules
5. **Configurable Strictness**: Choose between warning mode and strict failure mode
6. **CWE Mapping**: Security findings are mapped to Common Weakness Enumeration IDs

## Best Practices

1. **Performance**:
   - Start with small directories to test configuration
   - Use include/exclude patterns to limit file processing
   - Disable tree or annotations if not needed

2. **Security**:
   - Keep GitHub tokens secure
   - Review code before processing
   - Check security scan results

3. **Integration**:
   - Use programmatic API for tight integration
   - Use web API for loose coupling
   - Consider using a `.codeconcat.yml` (or `.codeconcat.yaml`) configuration file for consistency and reproducibility

4. **Error Handling**:
   - Always implement proper error handling
   - Check return values and status codes
   - Parsing errors within individual files are now captured as `LanguageParserError` instances and collected, allowing the overall process to continue for other files.
   - Log errors appropriately

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

GitHub Issues: [https://github.com/biostochastics/codeconcat/issues](https://github.com/biostochastics/codeconcat/issues)

---

*Part of the [Biostochastics](https://github.com/biostochastics) collection of tools for translational science and biomarker discovery*
