# CodeConCat

<p align="center">
  <img src="assets/codeconcat_logo.png" alt="CodeConCat Logo" width="200"/>
</p>

> A simple code aggregator and documentation extractor optimized for AI comprehension and collaborative workflows

## Overview

CodeConCat is your semi-intelligent companion for preparing codebases. It automatically ingests, processes, and formats your code in a way that's optimized for AI comprehension and collaborative/iterative workflows. The tool provides structured output with smart context generation, making it ideal for sharing code with AI assistants and collaborators.

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

# Install dependencies
pip install -r requirements.txt

# Basic installation
pip install -e .

# Install with web API dependencies
pip install -e ".[web]"

# Install with all optional dependencies
pip install -e ".[all]"
```

## Features

- **AI-Optimized Output**: Structured content with smart context generation
- **Smart File Collection**: Intelligent filtering and organization of your codebase
- **Documentation Extraction**: Automatically extract and process documentation
- **Directory Tree**: Visual representation of your project structure
- **Multiple Formats**: Output in Markdown, JSON, or XML
- **Language Detection**: Automatic language detection and syntax highlighting
- **Clipboard Integration**: One-click copy to clipboard
- **Token Counting**: Accurate GPT-4 token counting for all processed content
- **Progress Tracking**: Real-time progress indication during processing
- **Multi-Language Support**: Regex-based parsing for multiple languages:
  - Python, JavaScript/TypeScript, Java, Go, PHP, Ruby, R, Julia, Rust, C/C++, C#
- **Programmatic API**: Use CodeConCat directly in your Python code
- **Web API**: Built-in FastAPI web server for HTTP access

## Usage

### Command Line Interface (CLI)

The CLI is the simplest way to use CodeConCat:

```bash
# Process current directory with default settings
codeconcat

# Process a specific directory
codeconcat path/to/your/code

# Change output format (markdown, json, or xml)
codeconcat path/to/code --format json

# Extract and include documentation
codeconcat path/to/code --docs

# Process a GitHub repository
codeconcat --github username/repo --github-token YOUR_TOKEN

# Specify files to include/exclude
codeconcat --include "*.py" "*.js" --exclude "test_*" "*.pyc"
```

### CLI Configuration

Create a `.codeconcat.yml` configuration file for persistent settings:

```bash
# Initialize default configuration
codeconcat --init
```

Example configuration:
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
disable_tree: false
disable_annotations: false
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
    disable_tree=False,
    disable_annotations=False,
    github_url=None,  # Optional: Process from GitHub
    github_token=None,  # Optional: GitHub authentication
    ref=None  # Optional: GitHub branch/tag/commit
)

# Error handling
try:
    output = run_codeconcat_in_memory(config)
except Exception as e:
    print(f"Error processing code: {e}")
```

### Web API

CodeConCat includes a FastAPI-based web server for HTTP access:

1. Start the server:
```bash
# Install web dependencies if not already installed
pip install "codeconcat[web]"

# Start the server
uvicorn app:app --reload
```

2. Access the API:

```python
import requests

# Basic usage
response = requests.post("http://localhost:8000/concat", 
    json={
        "target_path": "path/to/code",
        "format": "markdown"
    }
)
output = response.json()["output"]

# Advanced configuration
payload = {
    "target_path": "path/to/code",
    "format": "json",
    "extract_docs": True,
    "merge_docs": True,
    "include": ["*.py", "*.js"],
    "exclude": ["test_*", "*.pyc"],
    "disable_tree": False,
    "disable_annotations": False
}
response = requests.post("http://localhost:8000/concat", json=payload)
```

#### API Endpoints

- `GET /` - API information and version
- `POST /concat` - Process code and return output
  - Request body: JSON with configuration options
  - Response: JSON with processed output

#### API Documentation

Access the auto-generated API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuration

Create a `.codeconcat.yml` in your project root or use `codeconcat --init`:

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
```

### Configuration Priority Order

1. Command line arguments (highest priority)
2. Local `.codeconcat.yml` file
3. Default settings (lowest priority)

## Output Formats

### Markdown (Default)
- Clean, readable format
- Syntax highlighting
- Directory tree visualization
- AI-friendly structure

### JSON
- Machine-readable format
- Perfect for automation
- Preserves all metadata

### XML
- Structured format
- Compatible with XML tools
- Detailed metadata

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
| `--format` | `markdown` | Output format: `markdown`, `json`, or `xml` |
| `--output` | `code_concat_output.md` | Output file name |
| `--include-languages` | `[]` | Limit to specific languages (e.g., `python javascript java go php`) |
| `--exclude-languages` | `[]` | Exclude specific languages (e.g., `cpp`) |
| `--include` | `[]` | Include specific glob patterns (e.g., `**/*.{py,js,ts,java,go}`) |
| `--exclude` | `[]` | Exclude paths/patterns (e.g., `node_modules`, `__pycache__`) |
| `--max-workers` | `4` | Number of concurrent threads for processing |
| `--github` | `None` | GitHub repository URL or shorthand (e.g., `username/repo`) |
| `--github-token` | `None` | Personal access token for private GitHub repos |
| `--ref` | `None` | Branch, tag, or commit hash for GitHub repos |
| `--no-tree` | `false` | Disable folder tree generation |
| `--no-copy` | `false` | Disable copying output to clipboard |
| `--no-ai-context` | `false` | Disable AI context generation |
| `--no-annotations` | `false` | Disable code annotations |
| `--no-symbols` | `false` | Disable symbol extraction |
| `--debug` | `false` | Enable detailed logging |
| `--init` | `false` | Initialize default configuration file |

### Language Support

CodeConcat provides comprehensive parsing for multiple languages:

```bash
# Process Python and JavaScript files
codeconcat --include-languages python javascript

# Process Java, Go, and PHP files
codeconcat --include-languages java go php

# Process all supported languages
codeconcat --include "**/*.{py,js,ts,java,go,php,rb,r,jl,rs,cpp,cs}"
```

### GitHub Integration

```bash
# Process specific branch
codeconcat --github username/repo/main

# Use with authentication
codeconcat --github username/repo --github-token YOUR_TOKEN

# Process specific commit or tag
codeconcat --github username/repo --ref v1.0.0
```

### File Filtering

CodeConCat provides multiple ways to control which files are processed:

1. **.gitignore Support**
   - Automatically respects your project's `.gitignore` rules
   - Common patterns (e.g., `__pycache__`, `node_modules`) are always ignored
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
   - Consider using configuration files for consistency

4. **Error Handling**:
   - Always implement proper error handling
   - Check return values and status codes
   - Parsing errors within individual files are now captured as `LanguageParserError` instances and collected, allowing the overall process to continue for other files.
   - Log errors appropriately

## Contributing

We welcome contributions! Check out our [Contributing Guide](CONTRIBUTING.md) to get started.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contact

GitHub Issues: [https://github.com/biostochastics/codeconcat/issues](https://github.com/biostochastics/codeconcat/issues)

---

*Part of the [Biostochastics](https://github.com/biostochastics) collection of tools for translational science and biomarker discovery*