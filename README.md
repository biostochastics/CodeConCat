# CodeConCat

<p align="center">
  <img src="assets/codeconcat_logo.png" alt="CodeConCat Logo" width="300"/>
</p>

> Transform codebases into AI-ready formats with parsing, compression, and security analysis

[![CI](https://github.com/biostochastics/codeconcat/actions/workflows/ci.yml/badge.svg)](https://github.com/biostochastics/codeconcat/actions/workflows/ci.yml)
[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![Poetry](https://img.shields.io/badge/dependency%20management-poetry-blueviolet)](https://python-poetry.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit)
[![Typer](https://img.shields.io/badge/CLI-typer-green)](https://typer.tiangolo.com/)

## Overview

CodeConCat is a Python tool that transforms codebases into formats optimized for AI consumption and analysis. It automatically processes your code to extract functions, classes, imports, and documentation across 11+ programming languages. The tool provides structured output with context generation, making it ideal for sharing code with AI assistants and automated analysis.

### Security Features
- **API access controls**: Configurable path access and authentication
- **Thread-safe operations**: Concurrent request handling with isolated configurations
- **Command injection prevention**: Sanitized external command execution
- **Memory management**: File size limits and resource controls
- **Path validation**: Traversal protection and symlink handling

## Key Features

- **Multi-Language Parsing**: Parsing for 11+ languages using tree-sitter and regex engines
- **Compression**: Intelligent compression with modern pattern recognition and two simplified modes
- **Security Scanning**: Integrated Semgrep support with configurable severity thresholds
- **Multiple Output Formats**: Markdown, JSON, XML, and text outputs
- **Remote Repository Support**: Analyze GitHub repositories directly
- **Parallel Processing**: Configurable worker threads for performance
- **File Reconstruction**: Restore original source files from output
- **REST API**: FastAPI server for programmatic access
- **CLI Interface**: Terminal interface with progress bars and colored output
- **Caching**: TTL-based cache management

## Language Support

### Supported Languages

CodeConCat provides comprehensive parsing for the following languages:

| Language | Tree-sitter Parser | Enhanced Regex Parser | Key Features |
|----------|-------------------|----------------------|--------------|
| **Python** | Yes | Yes | Type hints, async/await, decorators, dataclasses, docstrings |
| **JavaScript/TypeScript** | Yes | Yes | JSX/TSX, ES6+, arrow functions, modules, decorators |
| **Java** | Yes | Yes | Generics, annotations, lambdas, records, streams |
| **C/C++** | Yes | Yes | Templates, namespaces, modern C++ features, preprocessor |
| **C#** | Yes | Yes | Generics, attributes, async/await, LINQ, properties |
| **Go** | Yes | Yes | Interfaces, embedded types, generics, goroutines |
| **Rust** | Yes | Yes | Traits, lifetimes, macros, async, ownership |
| **PHP** | Yes | Yes | Traits, namespaces, attributes, typed properties |
| **Julia** | Yes | Yes | Multiple dispatch, macros, type annotations |
| **R** | Yes | Yes | S3/S4 classes, tidyverse, data.table |
| **TOML** | No | Yes | Configuration parsing, nested tables |

### Parser Features

- **Automatic Fallback**: Seamlessly switches from tree-sitter to regex parsing on errors
- **Unicode Support**: Handles BOM removal, encoding detection, and NFC normalization
- **Error Recovery**: Continues parsing even with syntax errors
- **Docstring Extraction**: Captures documentation in language-specific formats
- **Structure Preservation**: Maintains code hierarchy and relationships

## Parser Architecture

CodeConCat uses a multi-tier parser system for maximum reliability and feature coverage:

### Parser Types

1. **Tree-sitter Parsers** (Primary)
   - Full syntax tree parsing for accurate code structure recognition
   - Support for advanced language features and precise source locations
   - Best handling of nested declarations and complex constructs
   - Located in `codeconcat/parser/language_parsers/tree_sitter_{language}_parser.py`

2. **Enhanced Regex Parsers** (Fallback)
   - Pattern-based parsing with state tracking
   - Better support for edge cases and malformed code
   - Improved docstring extraction and handling
   - Located in `codeconcat/parser/language_parsers/enhanced_{language}_parser.py`

3. **Legacy Parsers** (Being phased out)
   - Original regex-based parsers
   - Limited support for complex language features
   - Located in `codeconcat/parser/language_parsers/{language}_parser.py`

### Parser Selection

Use the `--parser-engine` flag to choose between:
- `tree_sitter` (default): High accuracy with automatic fallback
- `regex`: Force regex-based parsing for compatibility

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        User Interface                        │
│  (CLI, REST API, Python API, Configuration Files)          │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                      Core Pipeline                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Collector │→ │  Parser  │→ │Processor │→ │  Writer  │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    Supporting Services                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │Validation│  │ Security │  │Compression│  │ Language │  │
│  │          │  │ Scanner  │  │          │  │Detection │  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Output Formats

CodeConCat provides four output formats tailored for different use cases:

### XML Format
- Semantic tags for structure understanding
- Hierarchical navigation with file categorization
- Metadata elements for context
- Optional AI processing instructions (`--xml-pi/--no-xml-pi`)
- CDATA sections for content preservation

### Markdown Format
- Table of contents with anchor links
- Summary statistics and project overview
- Collapsible sections for large content
- Syntax highlighting for code blocks
- Cross-references between related files
- Security issue badges with severity indicators

### JSON Format
- Nested structure for traversal
- Indexes by language, type, and directory
- Relationship mapping between files
- Metadata for filtering and searching
- Statistics overview
- Compression segment support

### Text Format
- Box drawing characters for visual hierarchy
- 80-character width for terminal compatibility
- Progress indicators for file processing
- Visual file type indicators (📝 source, 🧪 test, 📄 doc)
- Line wrapping for long content
- Compact metadata display

## Codebase Analysis Features (Optional)

### AI-Powered Code Review Prompts
CodeConCat includes an optional prompt system for preparing codebases for LLM-based analysis. This feature is completely optional and does not affect normal operation:

```bash
# Normal operation (no prompt)
codeconcat run --format markdown -o output.md

# Use the built-in default analysis prompt
codeconcat run --prompt-file default

# Use a custom analysis prompt
codeconcat run --prompt-file ./my-review-prompt.md

# Add context variables to customize the prompt
codeconcat run --prompt-file ./my-review-prompt.md \
               --prompt-var "FOCUS_AREAS=security,performance" \
               --prompt-var "TEAM_SIZE=5"
```

When using a prompt file, the system provides structured analysis guidance across:
- Code quality and maintainability
- Architecture and design patterns
- Security assessment
- Performance optimization
- Testing coverage
- Documentation quality

## Installation

### Prerequisites

- Python 3.10 or higher (tested up to Python 3.13)
- Git (for repository cloning features)
- Poetry 1.8+ (recommended) or pip

### Using Poetry (Recommended)

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/biostochastics/codeconcat.git
cd codeconcat

# Install dependencies
poetry install

# Install with optional dependencies
poetry install --with dev,test,docs

# Run CodeConCat
poetry run codeconcat --help
```

### Using pip

```bash
# Install from PyPI (when published)
pip install codeconcat

# Install from source
git clone https://github.com/biostochastics/codeconcat.git
cd codeconcat
pip install -e .

# Install with extras
pip install -e ".[dev,test]"
```

## Quick Start

### Performance Note

CodeConCat can process large codebases efficiently. For example, processing its own codebase (100+ Python files) takes under 5 seconds with compression enabled, achieving 35-40% token reduction.

### Basic Usage

```bash
# Process current directory
codeconcat run

# Process specific directory
codeconcat run /path/to/project

# Generate JSON output with compression
codeconcat run --format json --compress -o output.json

# Generate XML without AI processing instructions
codeconcat run --format xml --no-xml-pi -o output.xml

# Use lean preset for minimal output
codeconcat run --preset lean

# Process remote GitHub repository
codeconcat run --source-url owner/repo --github-token $GITHUB_TOKEN

# Filter by language and paths
codeconcat run -il python javascript -ep "*/tests/*" "*/node_modules/*"
```

### Initialize Configuration

```bash
# Interactive configuration setup
codeconcat init

# Create config with specific preset
codeconcat init --preset medium --output custom-config.yml

# Non-interactive setup with defaults
codeconcat init --no-interactive

# Validate existing configuration
codeconcat validate .codeconcat.yml

# Force overwrite existing config
codeconcat init --force
```

### Reconstruct Files

```bash
# Reconstruct from output file
codeconcat reconstruct output.md

# Preview without creating files
codeconcat reconstruct output.json --dry-run

# Reconstruct to specific directory
codeconcat reconstruct output.xml -o ./restored

# Force overwrite existing files
codeconcat reconstruct output.md --force

# Verbose reconstruction with progress
codeconcat reconstruct output.json -v
```

### Start API Server

```bash
# Start on default port (8000)
codeconcat api start

# Development mode with auto-reload
codeconcat api start --reload

# Production with multiple workers
codeconcat api start --workers 4 --host 0.0.0.0 --port 8080

# Custom log level
codeconcat api start --log-level warning

# Show API information and endpoints
codeconcat api info
```

### Diagnostics

```bash
# Verify all Tree-sitter dependencies
codeconcat diagnose verify

# Test language parser
codeconcat diagnose parser python

# Test parser with specific file
codeconcat diagnose parser javascript -f test.js

# Show system information
codeconcat diagnose system

# List all supported languages
codeconcat diagnose languages
```

## CLI Reference

### Global Options

Available for all commands:

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-V` | Show version and exit |
| `--verbose` | `-v` | Increase verbosity (-v for INFO, -vv for DEBUG) |
| `--quiet` | `-q` | Quiet mode: suppress progress information |
| `--config` | `-c` | Path to configuration file |
| `--help` | | Show help message and exit |

### Commands

#### `codeconcat run`

Process files and generate AI-optimized output.

**Usage:** `codeconcat run [OPTIONS] [TARGET]`

**Arguments:**
- `TARGET`: Path to process (default: current directory)

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output file path (auto-detected from format if omitted) |
| `--format` | `-f` | Output format: `markdown`, `json`, `xml`, `text` (default: markdown) |
| `--preset` | `-p` | Configuration preset: `lean`, `medium`, `full` |
| `--compress` | | Enable intelligent code compression |
| `--compression-level` | | Compression level: `low`, `medium` (contextual), `high`/`aggressive` (essential) |
| `--source-url` | | GitHub URL or owner/repo for remote repositories |
| `--github-token` | | GitHub PAT for private repositories |
| `--include-path` | `-ip` | Glob patterns to include (repeatable) |
| `--exclude-path` | `-ep` | Glob patterns to exclude (repeatable) |
| `--include-language` | `-il` | Languages to include (e.g., python, java) |
| `--exclude-language` | `-el` | Languages to exclude |
| `--parser-engine` | | Parser engine: `tree_sitter` or `regex` |
| `--max-workers` | | Number of parallel workers (1-32, default: 4) |
| `--docs/--no-docs` | | Extract standalone documentation files |
| `--remove-docstrings` | | Strip docstrings from code |
| `--remove-comments` | | Strip comments from code |
| `--security/--no-security` | | Enable security scanning |
| `--semgrep` | | Enable Semgrep security scanning |
| `--security-threshold` | | Minimum severity: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |

#### `codeconcat init`

Initialize configuration interactively.

**Usage:** `codeconcat init [OPTIONS]`

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output path for config file (default: .codeconcat.yml) |
| `--interactive/--no-interactive` | | Use interactive wizard (default: true) |
| `--force` | `-f` | Overwrite existing configuration |
| `--preset` | `-p` | Use specific preset: `lean`, `medium`, `full` |

#### `codeconcat validate`

Validate a configuration file.

**Usage:** `codeconcat validate CONFIG_FILE`

#### `codeconcat reconstruct`

Reconstruct source files from CodeConCat output.

**Usage:** `codeconcat reconstruct [OPTIONS] INPUT_FILE`

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--output-dir` | `-o` | Directory for reconstructed files (default: ./reconstructed) |
| `--format` | `-f` | Input file format (auto-detected if not specified) |
| `--force` | | Overwrite existing files without confirmation |
| `--dry-run` | | Preview without creating files |
| `--verbose` | `-v` | Show detailed progress |

#### `codeconcat api`

Manage the CodeConCat API server.

**Sub-commands:**

##### `codeconcat api start`

Start the API server.

**Options:**

| Option | Short | Description |
|--------|-------|-------------|
| `--host` | `-h` | Host to bind (default: 127.0.0.1) |
| `--port` | `-p` | Port to bind (default: 8000) |
| `--reload` | | Enable auto-reload for development |
| `--workers` | `-w` | Number of worker processes |
| `--log-level` | `-l` | Logging level |

##### `codeconcat api info`

Display API information and endpoints.

#### `codeconcat diagnose`

Diagnostic and verification tools.

**Sub-commands:**

##### `codeconcat diagnose verify`

Verify Tree-sitter grammar dependencies.

##### `codeconcat diagnose parser`

Test parser for a specific language.

**Usage:** `codeconcat diagnose parser LANGUAGE [OPTIONS]`

**Options:**
- `--test-file, -f PATH`: Test with specific file

##### `codeconcat diagnose system`

Display system information.

##### `codeconcat diagnose languages`

List all supported languages.

## Configuration

### Configuration File

Create a `.codeconcat.yml` file in your project root:

```yaml
version: "1.0"
output_preset: medium
format: markdown

# Filtering
use_gitignore: true
use_default_excludes: true
include_languages:
  - python
  - javascript
exclude_paths:
  - "*/tests/*"
  - "*/node_modules/*"

# Processing
parser_engine: tree_sitter
max_workers: 4

# Compression
enable_compression: false
compression_level: medium

# Security
enable_security_scanning: true
security_scan_severity_threshold: MEDIUM
```

### Presets

CodeConCat includes three built-in presets:

- **Lean**: Minimal output, optimized for token efficiency
- **Medium**: Balanced output with context (default)
- **Full**: Complete output with all metadata and features

### Environment Variables

```bash
# API Configuration
export GITHUB_TOKEN=your_token_here
export CODECONCAT_HOST=0.0.0.0
export CODECONCAT_PORT=8080

# Security Configuration
export CODECONCAT_ALLOW_LOCAL_PATH=false  # Enable local path processing in API (development only)
export ENV=production                     # Environment mode: production, development, or test
```

## Advanced Features

### Compression

Compression reduces token usage by removing repetitive code while preserving structure:

```bash
# Enable compression with contextual mode (keeps important code with context)
codeconcat run --compress --compression-level medium

# Essential compression for maximum reduction (signatures, security, errors only)
codeconcat run --compress --compression-level aggressive
```

Compression effectiveness varies by codebase size and complexity. Larger codebases with more repetitive patterns see better compression ratios.

### Security Features

CodeConCat includes security capabilities integrated into its core:

#### Security Architecture
- **Pattern-based scanning**: Detection of credentials, API keys, and sensitive data patterns
- **Path traversal protection**: Multi-layer validation preventing directory traversal attacks
- **Zip Slip protection**: Secure archive extraction with comprehensive path validation
- **XXE attack prevention**: Safe XML parsing using defusedxml library
- **ReDoS protection**: Regex pattern validation with configurable timeout protection
- **Input sanitization**: Command arguments, URLs, and regex patterns sanitized (1000 char limit)
- **File integrity verification**: SHA-256 based hash verification with configurable size limits
- **Rate limiting**: Built-in API rate limiting for production deployments
- **Secure hashing**: PBKDF2-based password hashing and secure token generation
- **Thread-safe architecture**: Isolated configuration handling for concurrent operations
- **Command execution safety**: Sanitized git and system command execution
- **Production API security**: Configurable access controls with secure defaults

```bash
# Enable Semgrep scanning
codeconcat run --semgrep

# Set security threshold
codeconcat run --security-threshold HIGH

# Strict mode - fail on security issues
codeconcat run --strict-security
```

#### Security Processor Integration
The `SecurityProcessor` class provides unified access to all security features:
- Path validation with symlink control
- Command injection prevention
- URL validation and sanitization
- ReDoS protection for regex patterns
- Binary file detection
- Integrity manifest generation and verification

### File Size Limits

CodeConCat handles file sizes intelligently to optimize performance:

- **20MB limit**: Files larger than 20MB are skipped with a warning
- **5MB binary detection**: Large files checked for binary content
- **100MB hash limit**: Security hashing limited to prevent memory issues
- **Configurable**: Limits can be adjusted in configuration

The system provides detailed logging when files are skipped due to size constraints.

### Shell Completion

Enable auto-completion for your shell (powered by Typer):

```bash
# Bash
codeconcat --install-completion bash
source ~/.bashrc

# Zsh
codeconcat --install-completion zsh
source ~/.zshrc

# Fish
codeconcat --install-completion fish
```

To see the completion script without installing:
```bash
codeconcat --show-completion bash  # or zsh, fish
```

## API Usage

### REST API

Start the API server:

```bash
codeconcat api start --host 0.0.0.0 --port 8000
```

Make requests to the API:

```python
import requests

# Process a GitHub repository
response = requests.post(
    "http://localhost:8000/api/concat",
    json={
        "source_url": "https://github.com/owner/repo",
        "format": "markdown",
        "include_languages": ["python", "javascript"],
        "enable_compression": True,
        "compression_level": "medium"
    }
)

# Process a local directory (requires CODECONCAT_ALLOW_LOCAL_PATH=true)
response = requests.post(
    "http://localhost:8000/api/concat",
    json={
        "target_path": "/path/to/code",  # Available in development mode
        "format": "json",
        "enable_compression": True
    }
)

# Upload and process an archive
with open("code.zip", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/upload",
        files={"file": f},
        data={
            "format": "json",
            "output_preset": "medium",
            "enable_compression": "false"
        }
    )
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/concat` | POST | Process codebase from GitHub URL or local path |
| `/api/upload` | POST | Upload and process a code archive (zip/tar) |
| `/api/ping` | GET | Health check endpoint |
| `/api/config/presets` | GET | Get available configuration presets |
| `/api/config/formats` | GET | Get supported output formats |
| `/api/config/languages` | GET | Get supported programming languages |
| `/api/config/defaults` | GET | Get default configuration values |
| `/docs` | GET | Interactive API documentation (Swagger UI) |
| `/redoc` | GET | Alternative API documentation (ReDoc) |

### Python API

Use CodeConCat programmatically:

```python
from codeconcat.cli import app
from typer.testing import CliRunner

runner = CliRunner()

# Run with various options
result = runner.invoke(app, [
    "run",
    "/path/to/project",
    "--format", "json",
    "--compress",
    "--output", "output.json"
])

# Check result
if result.exit_code == 0:
    print("Success!")
```

## Development

### Setting Up Development Environment

```bash
# Clone repository
git clone https://github.com/biostochastics/codeconcat.git
cd codeconcat

# Install Poetry (if not already installed)
curl -sSL https://install.python-poetry.org | python3 -

# Install all dependencies (including dev, test, docs)
poetry install --all-extras

# Install pre-commit hooks
poetry run pre-commit install

# Activate virtual environment
poetry shell
```

### Code Quality & Testing

```bash
# Run all tests with coverage
poetry run pytest --cov=codeconcat --cov-report=term-missing

# Run specific test file
poetry run pytest tests/unit/test_cli.py -xvs

# Format code (auto-fix)
poetry run black codeconcat tests
poetry run isort codeconcat tests
poetry run ruff check --fix codeconcat tests

# Lint code (check only)
poetry run ruff check codeconcat
poetry run mypy codeconcat

# Run all pre-commit hooks
poetry run pre-commit run --all-files
```

### Code Quality & Security

The codebase follows these practices:

- **Specific Exception Handling**: Exceptions use specific types rather than broad handlers
- **Security Design**: Input validation, path traversal protection, and attack prevention
- **Type Safety**: Type hints with Pydantic validation
- **Centralized Utilities**: Shared functionality in dedicated modules
- **Thread-Safe Operations**: Safe concurrent operation handling

### CI/CD Pipeline

The project uses GitHub Actions for continuous integration:

- **Automated Testing**: Tests run on Python 3.10, 3.11, and 3.12
- **Code Quality**: Linting with ruff, black, isort, and mypy
- **Coverage Reports**: Automatic coverage reporting
- **Pre-commit Hooks**: Ensures code quality before commits
- **Package Publishing**: Automatic PyPI deployment on tagged releases

### Building & Publishing

```bash
# Build package distributions
poetry build

# Check package metadata
poetry check

# Publish to PyPI (requires API token)
poetry publish

# Build and publish in one command
poetry publish --build

# Run tests in parallel
poetry run pytest -n auto
```

## Documentation

Comprehensive documentation is available:

- [CLI Documentation](CLI_DOCUMENTATION.md) - Detailed CLI reference
- [API Documentation](http://localhost:8000/docs) - Interactive API docs (when server is running)
- [Contributing Guide](CONTRIBUTING.md) - How to contribute
- [Security Policy](SECURITY.md) - Security guidelines

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

Key areas for contribution:
- Adding new language parsers
- Improving existing parsers
- Enhancing documentation
- Adding test coverage
- Performance optimizations

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

**GitHub Issues**: [https://github.com/biostochastics/codeconcat/issues](https://github.com/biostochastics/codeconcat/issues)

*Part of the Biostochastics collection of tools for translational science and biomarker discovery*

## Acknowledgments

CodeConCat is built with these open-source tools:

- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Poetry](https://python-poetry.org/) - Dependency management
- [Tree-sitter](https://tree-sitter.github.io/) - Incremental parsing
- [FastAPI](https://fastapi.tiangolo.com/) - Web API framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
