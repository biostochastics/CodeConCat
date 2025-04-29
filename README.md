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
- **Markdown Cross-Linking**: When using `--format markdown` and the `--cross-link-symbols` flag, symbol summaries in the Markdown output will link to their corresponding definitions via HTML anchors for easier navigation.
- **Token Counting**: Accurate GPT-4 token counting for all processed content
- **Progress Tracking**: Real-time progress indication during processing (multi-stage progress bars for file collection, parsing, annotation, doc extraction, output writing; toggle with `--no-progress-bar`)
- **Comprehensive Code Analysis**: Functions, classes, structs, and symbols are listed in the Markdown output under each file's analysis section for full visibility.
- **Advanced Language Support**: Dual-parser system with both regex-based and Tree-sitter parsers (select with `--parser-engine={tree_sitter,regex}`):
  - **Tree-sitter Parsers**: High-accuracy parsing for 10 major languages with modern language feature support:
    - Python (type hints, async functions, dataclasses)
    - JavaScript/TypeScript (JSX/TSX, decorators, modern ES features)
    - Java (generics, annotations, lambdas, records)
    - C/C++ (templates, namespaces, operator overloading)
    - C# (generics, attributes, async/await)
    - Go (interfaces, embedded types, generics)
    - PHP (attributes, enums, constructor promotion)
    - Rust (traits, generics, macros)
    - R (S3/S4/R6 classes, Roxygen docs)
    - Julia (macros, structs, types)
  - **Enhanced Regex Parsers**: Improved parsing for nested declarations and parent-child relationships:
    - Python (nested functions, methods, and classes)
    - JavaScript/TypeScript (nested functions and classes)
    - Julia (nested modules, structs, and functions)
    - Ruby and other languages without Tree-sitter support
- **Programmatic API**: Use CodeConCat directly in your Python code with the new ConfigBuilder:

```python
from codeconcat import run_codeconcat_in_memory
from codeconcat.config.config_builder import ConfigBuilder

# Create a configuration with the builder pattern
config_builder = ConfigBuilder()
config_builder.with_defaults()
config_builder.with_preset("medium")  # Use the 'medium' preset
config_builder.with_yaml_config("path/to/.codeconcat.yml")  # Optional
config_builder.with_cli_args({"format": "json", "parser_engine": "regex"})

# Build the final configuration
config = config_builder.build()

# Run CodeConCat with the configuration
output = run_codeconcat_in_memory(config)
```

- **Web API (Coming Soon)**: FastAPI web server for HTTP access (currently under development)

## Usage

### Command Line Interface (CLI)

The CLI is the simplest way to use CodeConCat. Basic options are shown by default, while advanced options can be viewed with the `--advanced` flag:

```bash
# Process current directory with default settings
codeconcat

# Process a specific directory
codeconcat path/to/your/code

# Change output format (markdown, json, xml, or text)
codeconcat path/to/code --format json
codeconcat path/to/code --format text

# Choose parser engine (tree_sitter for better accuracy, regex for speed)
codeconcat --parser-engine=regex

# Extract and include documentation
codeconcat path/to/code --docs

# Process a remote Git repository (e.g., GitHub)
codeconcat --source-url username/repo --github-token YOUR_TOKEN
# Optionally specify a branch/tag/commit:
# codeconcat --source-url username/repo --source-ref main --github-token YOUR_TOKEN

# Specify files to include/exclude
codeconcat --include-paths "*.py" "*.js" --exclude-paths "test_*" "*.pyc"

# Display advanced options
codeconcat --advanced

# Show detailed configuration information
codeconcat --show-config-detail

# Disable automatic .gitignore handling (it's enabled by default)
codeconcat --no-use-gitignore

# Disable built-in default excludes (they're enabled by default)
codeconcat --no-use-default-excludes

# Enable verbose logging (increase levels with -v, -vv)
codeconcat --verbose
codeconcat -vv  # Debug level logging

# Control progress display
codeconcat --disable-progress-bar

# Show skipped files in verbose mode
codeconcat --verbose --show-skip

# Mask potentially sensitive output content
codeconcat --mask-output-content

# Configure output features
codeconcat --no-ai-context     # Skip AI-specific preamble
codeconcat --no-annotations    # Skip code annotation/augmentation
codeconcat --no-symbols        # Skip generating symbol index

# Enable cross-linking in Markdown output
codeconcat --format markdown --cross-link-symbols

# Apply predefined configuration presets
codeconcat --preset lean      # Minimal output (no comments, docstrings)
codeconcat --preset medium    # Balanced output (default)
codeconcat --preset full      # Comprehensive output
```

### CLI Configuration

#### Configuration Precedence

CodeConCat now uses a strict four-stage configuration loading process:

1. **Defaults** - Built-in default values from the `CodeConCatConfig` model
2. **Preset** - Predefined configuration sets ('lean', 'medium', 'full')
3. **YAML** - Values from `.codeconcat.yml` file in project root (or `.codeconcat.yaml`)
4. **CLI arguments** - Command-line options (highest priority)

Each stage builds upon the previous, with later stages overriding earlier ones. You can view the source of each setting with:

```bash
# Show where each configuration setting comes from
codeconcat --show-config-detail
```

#### Advanced vs Basic Options

The CLI now groups options into two categories:

- **Basic options**: Always shown in help output, covering common use cases
- **Advanced options**: Hidden by default, shown when using `--advanced`

This makes the tool more approachable for new users while still providing power users with all available options.

Create a `.codeconcat.yml (YAML syntax; .yaml also supported, but .yml is recommended)` configuration file for persistent settings:

```bash
# Initialize default configuration
codeconcat --init  # creates a .codeconcat.yml template file
```

Example configuration (YAML):
```yaml
# .codeconcat.yml
format: markdown
extract_docs: true
include_patterns:
  - "*.py"
  - "*.js"
exclude_patterns:
  - "*.test.js"
  - "__pycache__"
parser_engine: tree_sitter  # Use 'regex' for faster, simpler parsing
disable_annotations: false
# Control filtering behavior (defaults are true)
use_gitignore: true
use_default_excludes: true
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
    extract_docs=True,
    merge_docs=True,
    include_paths=["*.py", "*.js"],
    exclude_paths=["test_*", "*.pyc"],
    parser_engine="tree_sitter",  # Use 'regex' for faster, simpler parsing
    disable_annotations=False,
    # Optional: Process from a remote source URL (Git repo, potentially ZIP in future)
    source_url=None,
    github_token=None,  # Optional: Git authentication (e.g., GitHub PAT)
    # Optional: Git branch/tag/commit for source_url
    source_ref=None
)

# Error handling
try:
    output = run_codeconcat_in_memory(config)
except Exception as e:
    print(f"Error processing code: {e}")
```

### Web API (Coming Soon)

> **Note**: The Web API is currently under development and not yet available in the main release.

A FastAPI-based HTTP API is planned for a future release, which will allow you to integrate CodeConCat with other services:

```python
# Example of planned API usage (not yet implemented)
import requests

# Future API endpoint
response = requests.post(
    "http://localhost:8000/concat",
    json={
        "target_path": "path/to/code",
        "format": "json",
        "parser_engine": "tree_sitter",
        "include_paths": ["*.py", "*.js"],
        "exclude_paths": ["test_*", "*.pyc"]
    }
)
```


## Configuration

Create a `.codeconcat.yml` (YAML syntax; .yaml also supported, but .yml is recommended) in your project root or use `codeconcat --init  # creates a .codeconcat.yml template file`:

```yaml
# Documentation settings
docs: true
merge_docs: false

# Output settings
output: "my_concat_output.md"
format: "markdown"
generate_tree: true
copy_to_clipboard: true
generate_ai_context: true

# Language settings
include_languages:
  - python
  - javascript
  - java
  - go
  - php
  - ruby
  - r
  - julia
  - rust
  - c
  - cpp
  - csharp

exclude_languages:
  - cpp

# File patterns
include_paths:
  - "**/*.{py,js,ts,java,go,php,rb,r,jl,rs,cpp,cs}"
  - "**/README*"
  - "**/LICENSE*"

exclude_paths:
  - "**/*.{yml,yaml}"
  - "**/tests/**"
  - "**/build/**"
  - "**/node_modules/**"
  - "**/__pycache__/**"

# Performance settings
max_workers: 4

# Custom language mappings
custom_extension_map:
  pyx: "cython"
  jsx: "javascript"
  tsx: "typescript"

# Control filtering behavior (defaults are true)
use_gitignore: true
use_default_excludes: true
```

### Configuration Priority Order

CodeConCat uses a strict configuration priority order to ensure predictable behavior:

1. CLI arguments (highest priority)
2. Local `.codeconcat.yml` configuration file (YAML syntax)
3. Preset configuration (lean, medium, or full)
4. Default settings (lowest priority)

This merging order ensures that command-line arguments always take precedence over any other settings, while still providing sensible defaults. Use `--show-config-detail` to see the source of each active configuration setting.

## Output Formats

CodeConCat supports multiple output formats, selectable via the `--format` flag:

### Markdown (Default)
- Clean, readable format with syntax highlighting
- Directory tree visualization
- Structured declarations and imports
- Security issue highlighting with severity indicators
- Token counting statistics (when enabled)
- AI-friendly structure

### JSON
- Machine-readable format for automation
- Complete structured data representation
- Preserves all metadata (declarations, imports, security issues, token stats)
- Suitable for downstream processing

### XML
- Structured hierarchical format
- Full metadata preservation
- Compatible with XML processing tools

### Text
- Simple plain text output
- Line numbers (when enabled)
- Minimal formatting
- Simple and lightweight
- Suitable for basic use cases

## Code Summaries

CodeConcat generates comprehensive summaries of your codebase:

### File Statistics
- File name and language
- Number of lines
- Number and types of declarations
- Line ranges for each declaration

### Directory Structure
- Tree view of project layout
- Hierarchical file organization
- File grouping by type/module

### Code Declarations
- Functions and classes with line numbers
- Methods and properties
- Imports and dependencies
- Language-specific constructs (e.g., interfaces, traits)

Example output:
```
File: main.py
Language: python
Declarations:
  - class: CodeParser (lines 10-45)
  - function: parse_file (lines 15-30)
  - function: process_content (lines 32-40)
```

### Directory Summary Example
```
project/
├── src/
│   ├── parser/
│   │   ├── python_parser.py
│   │   └── javascript_parser.py
│   └── utils/
│       └── helpers.py
└── tests/
    └── test_parser.py
```

## Advanced Usage

### Command Line Options

| Flag | Default | Description |
|------|---------|-------------|
| `--docs` | `false` | Enable documentation extraction (.md, .rst, .txt, .rmd) |
| `--merge-docs` | `false` | Merge documentation into the same output file as code |
| `--format` | `markdown` | Output format: `markdown`, `json`, `xml`, or `text` |
| `--output` | `code_concat_output.md` | Output file name |
| `--include-languages` | `[]` | Limit to specific languages (e.g., `python javascript java go php`) |
| `--exclude-languages` | `[]` | Exclude specific languages (e.g., `cpp`) |
| `--include` | `[]` | Include specific glob patterns (e.g., `**/*.{py,js,ts,java,go}`) |
| `--exclude` | `[]` | Exclude paths/patterns (e.g., `node_modules`, `__pycache__`, already excludes `tests/` by default) |
| `--max-workers` | `4` | Number of concurrent threads for processing |
| `--source-url` | `None` | Remote Git repository URL or shorthand (e.g., `username/repo`) |
| `--github-token` | `None` | Personal access token for private Git repos |
| `--source-ref` | `None` | Branch, tag, or commit hash for Git repos |
| `--no-use-gitignore` | `false` | Disable automatic .gitignore handling (default is enabled) |
| `--no-use-default-excludes` | `false` | Disable built-in default excludes (default is enabled) |
| `--no-tree` | `false` | Disable folder tree generation |
| `--no-progress-bar` | `false` | Disable progress bars (use spinner only) |
| `--cross-link-symbols` | `false` | Enable Markdown cross-linking between symbol summaries and definitions |
| `--no-copy` | `false` | Disable copying output to clipboard |
| `--no-ai-context` | `false` | Disable AI context generation |
| `--no-annotations` | `false` | Disable code annotations |
| `--no-symbols` | `false` | Disable symbol extraction |
| `--mask-output` | `false` | Mask sensitive data directly in the output content. |
| `--debug` | `false` | Enable detailed logging |
| `--log-level` | `WARNING` | Set logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `--init` | `false` | Initialize a default `.codeconcat.yml` configuration file from template |
| `--show-config` | `false` | Display the final merged configuration (after applying precedence) and exit |
| `--sort-files` | `false` | Sort files alphabetically by path in the output |
| `--split-output` | `1` | Split the output into X approximately equal files (requires X > 1, Markdown only) |
| `--remove-docstrings` | `false` | Remove docstrings from the code content in the output |
| `--verbose` | `false` | Enable verbose logging for debugging file inclusion/exclusion |
| `--no-use-gitignore` | `false` | Disable automatic .gitignore handling |
| `--no-use-default-excludes` | `false` | Disable built-in default excludes |
| `--parser-engine` | `regex` | Select parsing engine: 'regex' (default) or 'tree_sitter'. |
| `--compress-code` | `false` | Compress code output using Tree-sitter (requires --parser-engine=tree_sitter). |
| `--no-fallback-to-regex` | `true` | Disable fallback to regex parser if Tree-sitter fails. |

### Language Support

CodeConCat provides comprehensive parsing for multiple languages:

```bash
# Process Python and JavaScript files
codeconcat --include-languages python javascript

# Process Java, Go, and PHP files
codeconcat --include-languages java go php

# Process all supported languages
codeconcat --include "**/*.{py,js,ts,java,go,php,rb,r,jl,rs,cpp,cs}"
```

### GitHub Integration

You can process any public or private GitHub repository by specifying either the full URL or the `username/repo` format. By default, CodeConCat will include all code, LICENSE, and README files, and will always respect `.gitignore` rules.

#### Minimal examples
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

#### Custom file filtering
When using `--source-url`, CodeConCat defaults to considering **all files** (`**/*`) in the repository, in addition to `LICENSE*` and `README*`. This ensures broad inclusion unless you specify otherwise. You can still use `--include-paths` and `--exclude-paths` on the command line to customize filtering for a specific run, overriding this default behavior.

```bash
# Only include Python files (and LICENSE/README) - overrides the default broad inclusion
codeconcat --source-url username/repo --include-paths '**/*.py'

# Exclude docs directories (test directories are already excluded by default)
codeconcat --source-url username/repo --exclude-paths '**/docs/**'

# Include test directories (overriding the default exclusion)
codeconcat --source-url username/repo --include-paths '**/tests/**'
```

- **GitHub Default:** Considers all files (`**/*`), plus `LICENSE*` and `README*`.
- `LICENSE*` and `README*` files are always included by default (even if overriding includes).
- `.gitignore` is always respected.

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
   exclude_paths:
     - "**/tests/**"
     - "**/build/**"
   ```

3. **Command Line**
   ```bash
   codeconcat --include "**/*.py" --exclude "**/tests/**"
   ```

Priority order for file filtering:
1. .gitignore rules (highest priority)
2. Command line arguments
3. Configuration file
4. Default settings

## Testing

CodeConCat includes a comprehensive test suite:

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests with coverage report
pytest tests/ -v --cov=codeconcat

# Or run directly using the test file
python tests/test_codeconcat.py
```

The test suite includes:
- Unit tests for parsers and processors
- Integration tests for end-to-end workflows
- Performance tests for concurrent processing
- Edge case tests for special characters and large files
- Security tests for sensitive data detection

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