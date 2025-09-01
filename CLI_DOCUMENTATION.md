# CodeConCat CLI Documentation

## Overview

CodeConCat uses a modern CLI architecture based on [Typer](https://typer.tiangolo.com/), providing an intuitive command-line interface with rich terminal output, type safety, and excellent user experience. Version 0.8.0 introduced this complete rewrite from argparse to Typer, bringing significant improvements in usability and maintainability.

## Installation

### Using Poetry (Recommended)

```bash
# Install Poetry if you haven't already
curl -sSL https://install.python-poetry.org | python3 -

# Clone the repository
git clone https://github.com/biostochastics/codeconcat.git
cd codeconcat

# Install dependencies
poetry install

# Run CodeConCat
poetry run codeconcat --help
```

### Using pip

```bash
pip install codeconcat

# Or install from source
pip install git+https://github.com/biostochastics/codeconcat.git
```

## Command Structure

CodeConCat uses a hierarchical command structure with sub-commands for different operations:

```
codeconcat [OPTIONS] COMMAND [ARGS]...
```

### Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-V` | Show version information and exit |
| `--verbose` | `-v` | Increase verbosity (-v for INFO, -vv for DEBUG) |
| `--quiet` | `-q` | Quiet mode: suppress progress information |
| `--config PATH` | `-c` | Path to configuration file |
| `--help` | | Show help message and exit |

### Rich Terminal Features

CodeConCat leverages Typer's rich terminal capabilities:
- **Organized Help Panels**: Options are grouped into logical sections (Output, Source, Filtering, etc.)
- **Beautiful Formatting**: Colored output, progress bars, and styled panels
- **Smart Validation**: Type checking, path validation, and range constraints
- **Interactive Prompts**: Confirmation dialogs and input prompts when needed

## Commands

### `codeconcat run`

Process files and generate LLM-friendly output. This is the main command for processing your codebase.

#### Usage

```bash
codeconcat run [OPTIONS] [TARGET]
```

#### Arguments

- `TARGET`: Target directory or file to process (default: current directory)

#### Options

**Output Options:**
- `--output PATH`, `-o PATH`: Output file path (auto-detected from format if omitted)
- `--format FORMAT`, `-f FORMAT`: Output format (markdown, json, xml, text) [default: markdown]
- `--preset PRESET`, `-p PRESET`: Configuration preset (lean, medium, full)

**Source Options:**
- `--source-url URL`: URL or owner/repo for remote repositories
- `--github-token TOKEN`: GitHub PAT for private repositories [env: GITHUB_TOKEN]
- `--source-ref REF`: Branch, tag, or commit hash for Git source

**Filtering Options:**
- `--include-path PATTERN`, `-ip`: Glob patterns for files to include (can be repeated)
- `--exclude-path PATTERN`, `-ep`: Glob patterns for files to exclude (can be repeated)
- `--include-language LANG`, `-il`: Languages to include (e.g., python, java)
- `--exclude-language LANG`, `-el`: Languages to exclude
- `--use-gitignore/--no-gitignore`: Respect .gitignore files [default: true]
- `--use-default-excludes/--no-default-excludes`: Use built-in excludes [default: true]

**Processing Options:**
- `--parser-engine ENGINE`: Parser engine (tree_sitter, regex)
- `--max-workers N`: Number of parallel workers (1-32) [default: 4]

**Feature Options:**
- `--docs/--no-docs`: Extract standalone documentation files [default: false]
- `--merge-docs/--no-merge-docs`: Merge docs into main output [default: false]
- `--no-annotations`: Skip code annotation
- `--remove-docstrings`: Strip docstrings from code
- `--remove-comments`: Strip comments from code

**Compression Options:**
- `--compress/--no-compress`: Enable intelligent code compression [default: false]
- `--compression-level LEVEL`: Compression mode:
  - `low`/`medium`: Contextual mode (keeps important code with surrounding context)
  - `high`/`aggressive`: Essential mode (keeps only signatures, security, and error handling)
  [default: medium]

**Security Options:**
- `--security/--no-security`: Enable security scanning [default: true]
- `--security-threshold LEVEL`: Minimum severity for findings [default: MEDIUM]
- `--semgrep/--no-semgrep`: Enable Semgrep security scanning [default: false]

**Display Options:**
- `--show-config`: Print configuration and exit
- `--no-progress`: Disable progress bars

**XML Options:**
- `--xml-pi/--no-xml-pi`: Include AI processing instructions in XML output

**Analysis Options:**
- `--prompt-file PATH`: Custom prompt file for codebase review
- `--prompt-var KEY=value`: Prompt variables (can be repeated)

#### Examples

```bash
# Process current directory with default settings
codeconcat run

# Process specific directory with JSON output
codeconcat run /path/to/project -f json -o output.json

# Use lean preset with compression
codeconcat run --preset lean --compress

# Process remote GitHub repository
codeconcat run --source-url owner/repo --github-token $GITHUB_TOKEN

# Filter by language and paths
codeconcat run -il python javascript -ep "*/tests/*" "*/node_modules/*"

# Advanced filtering with multiple patterns
codeconcat run \
    --include-path "src/**/*.py" "lib/**/*.py" \
    --exclude-path "**/test_*.py" "**/__pycache__/*" \
    --include-language python rust \
    --no-use-default-excludes

# Production build with security scanning
codeconcat run \
    --format json \
    --compress --compression-level high \
    --security --security-threshold HIGH \
    --semgrep \
    --output production-audit.json

# Quick documentation extraction
codeconcat run \
    --docs --merge-docs \
    --remove-docstrings --remove-comments \
    --preset lean \
    --output docs-only.md

# Parallel processing for large codebases
codeconcat run /large/codebase \
    --max-workers 16 \
    --parser-engine tree_sitter \
    --quiet \
    --output large-output.json
```

### `codeconcat init`

Initialize a CodeConCat configuration file interactively or with presets.

#### Usage

```bash
codeconcat init [OPTIONS]
```

#### Options

- `--output PATH`, `-o`: Output path for configuration file [default: .codeconcat.yml]
- `--interactive/--no-interactive`, `-i/-n`: Use interactive setup wizard [default: true]
- `--force`, `-f`: Overwrite existing configuration file
- `--preset PRESET`, `-p`: Use a specific preset (lean, medium, full)

#### Sub-commands

##### `codeconcat init validate`

Validate an existing configuration file.

```bash
codeconcat init validate [CONFIG_FILE]
```

#### Examples

```bash
# Interactive configuration setup
codeconcat init

# Create config with lean preset
codeconcat init --preset lean

# Create default config non-interactively
codeconcat init --no-interactive

# Validate existing config
codeconcat init validate .codeconcat.yml
```

### `codeconcat reconstruct`

Reconstruct source files from CodeConCat output.

#### Usage

```bash
codeconcat reconstruct [OPTIONS] INPUT_FILE
```

#### Arguments

- `INPUT_FILE`: CodeConCat output file to reconstruct from

#### Options

- `--output-dir PATH`, `-o`: Directory for reconstructed files [default: ./reconstructed]
- `--format FORMAT`, `-f`: Input file format (auto-detected if not specified)
- `--force`: Overwrite existing files without confirmation
- `--dry-run`: Preview without creating files
- `--verbose`, `-v`: Show detailed progress

#### Sub-commands

##### `codeconcat reconstruct preview`

Preview files without reconstructing them.

```bash
codeconcat reconstruct preview [OPTIONS] INPUT_FILE
```

Options:
- `--limit N`, `-l`: Maximum number of files to show [default: 10]

#### Examples

```bash
# Reconstruct from markdown output
codeconcat reconstruct output.md

# Reconstruct to custom directory
codeconcat reconstruct output.json -o ./restored

# Preview without creating files
codeconcat reconstruct output.xml --dry-run

# Preview file list
codeconcat reconstruct preview output.md --limit 20
```

### `codeconcat api`

Manage the CodeConCat API server.

#### Usage

```bash
codeconcat api [OPTIONS] COMMAND
```

#### Sub-commands

##### `codeconcat api start`

Start the API server.

Options:
- `--host HOST`, `-h`: Host to bind to [default: 127.0.0.1]
- `--port PORT`, `-p`: Port to bind to [default: 8000]
- `--reload/--no-reload`, `-r/-R`: Enable auto-reload for development
- `--workers N`, `-w`: Number of worker processes [default: 1]
- `--log-level LEVEL`, `-l`: Logging level [default: info]

##### `codeconcat api info`

Display API server information and endpoints.

#### Examples

```bash
# Start API server on localhost:8000
codeconcat api start

# Start on all interfaces with reload
codeconcat api start --host 0.0.0.0 --reload

# Production mode with multiple workers
codeconcat api start --workers 4 --log-level warning

# Show API information
codeconcat api info
```

### `codeconcat diagnose`

Diagnostic and verification tools for troubleshooting.

#### Usage

```bash
codeconcat diagnose [OPTIONS] COMMAND
```

#### Sub-commands

##### `codeconcat diagnose verify`

Verify Tree-sitter grammar dependencies.

```bash
codeconcat diagnose verify
```

##### `codeconcat diagnose parser`

Test parser for a specific language.

```bash
codeconcat diagnose parser LANGUAGE [OPTIONS]
```

Options:
- `--test-file PATH`, `-f`: Test file to parse

##### `codeconcat diagnose system`

Display system information.

```bash
codeconcat diagnose system
```

##### `codeconcat diagnose languages`

List all supported programming languages.

```bash
codeconcat diagnose languages
```

#### Examples

```bash
# Verify all dependencies
codeconcat diagnose verify

# Test Python parser
codeconcat diagnose parser python

# Test JavaScript parser with file
codeconcat diagnose parser javascript -f test.js

# Show system information
codeconcat diagnose system
```

## Configuration

### Configuration File Format

CodeConCat uses YAML configuration files (`.codeconcat.yml`):

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

# Features
extract_docs: false
remove_comments: false
remove_docstrings: false

# Compression
enable_compression: false
compression_level: medium

# Security
enable_security_scanning: true
security_scan_severity_threshold: MEDIUM

# Feature Flags (via environment variables)
# CODECONCAT_ENABLE_PATH_VALIDATION=true  # Enable path traversal protection
# CODECONCAT_ENABLE_UNICODE_HANDLER=true  # Enable unicode normalization
# CODECONCAT_ENABLE_ERROR_RECOVERY=true   # Enable parser error recovery
# CODECONCAT_ENABLE_RATE_LIMITING=true    # Enable API rate limiting
```

### Presets

CodeConCat includes three built-in presets:

#### Lean Preset
- Minimal output for token efficiency
- Regex parser for speed
- Removes comments and docstrings
- No AI context or summaries

#### Medium Preset (Default)
- Balanced output with useful context
- Tree-sitter parser for accuracy
- Includes file summaries and indices
- Retains comments and docstrings

#### Full Preset
- Complete output with all features
- Tree-sitter parser with full analysis
- Includes imports and declarations
- Token counting and security analysis

### Environment Variables

CodeConCat supports environment variables for configuration:

- `CODECONCAT_CONFIG`: Default configuration file path
- `CODECONCAT_HOST`: API server host
- `CODECONCAT_PORT`: API server port
- `GITHUB_TOKEN`: GitHub personal access token

## Shell Completion

Enable shell completion for better CLI experience:

### Bash
```bash
codeconcat --install-completion bash
source ~/.bashrc
```

### Zsh
```bash
codeconcat --install-completion zsh
source ~/.zshrc
```

### Fish
```bash
codeconcat --install-completion fish
```

## Advanced Features

### Rich Terminal Output

CodeConCat uses Rich for beautiful terminal output:
- Colored and formatted text
- Progress bars with live updates
- Tables for structured data
- Panels for important messages
- Syntax highlighting for code

### Type Safety

All CLI commands use Python type hints and Pydantic models:
- Automatic validation of inputs
- Clear error messages for invalid arguments
- IDE autocompletion support
- Runtime type checking

### Async Support

The API server and certain operations support async execution:
- Concurrent file processing
- Non-blocking I/O operations
- Better performance for large codebases

### Compression

Intelligent compression reduces output size while preserving important code:
- **Two compression modes**:
  - **Contextual** (`low`/`medium`): Keeps important code with surrounding context
  - **Essential** (`high`/`aggressive`): Keeps only signatures, security patterns, and error handling
- **Modern pattern recognition**: Detects database operations, API calls, async patterns, testing code
- **Fixed data loss bug**: Preserves all original content when merging segments
- **Syntactic validation**: Ensures compressed code maintains structural integrity
- Special tag support for always-keep sections

**Examples:**
```bash
# Enable compression with default contextual mode
codeconcat run --compress

# Essential mode for maximum reduction (keeps only critical code)
codeconcat run --compress --compression-level aggressive

# Custom placeholder text
codeconcat run --compress --compression-placeholder "// Code removed for brevity"

# Keep specific sections from compression
codeconcat run --compress --compression-keep-tags IMPORTANT CRITICAL SECURITY
```

## Troubleshooting

### Common Issues

#### Missing Dependencies
```bash
# Install Tree-sitter grammars
pip install tree-sitter-languages

# Install specific language grammar
pip install tree-sitter-python
```

#### Permission Errors
```bash
# Use sudo for global installation
sudo pip install codeconcat

# Or use user installation
pip install --user codeconcat
```

#### Parser Issues
```bash
# Verify parser installation
codeconcat diagnose verify

# Test specific language
codeconcat diagnose parser python
```

### Debug Mode

Enable debug output for troubleshooting:
```bash
codeconcat -vv run  # Very verbose output
```

## API Integration

### Python API

```python
from codeconcat.cli import app
from typer.testing import CliRunner

runner = CliRunner()
result = runner.invoke(app, ["run", "--format", "json"])
```

### REST API

```python
import requests

response = requests.post(
    "http://localhost:8000/process",
    json={
        "target_path": "/path/to/code",
        "format": "json",
        "enable_compression": True
    }
)
```

## Migration from Legacy CLI

### Command Mapping

| Old Command | New Command |
|-------------|-------------|
| `codeconcat --init` | `codeconcat init` |
| `codeconcat --reconstruct FILE` | `codeconcat reconstruct FILE` |
| `codeconcat --verify-dependencies` | `codeconcat diagnose verify` |
| `codeconcat --diagnose-parser LANG` | `codeconcat diagnose parser LANG` |
| `codeconcat PATH` | `codeconcat run PATH` |

### Configuration Changes

The configuration format remains largely the same, but with improved validation and type checking. Existing `.codeconcat.yml` files are compatible with the new CLI.

## Contributing

CodeConCat welcomes contributions! The new CLI architecture makes it easier to:
- Add new commands
- Extend existing functionality
- Improve documentation
- Add tests

See [CONTRIBUTING.md](https://github.com/biostochastics/codeconcat/blob/main/CONTRIBUTING.md) for guidelines.

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/biostochastics/codeconcat/issues
- Documentation: https://github.com/biostochastics/codeconcat#readme

## License

MIT License - see [LICENSE](https://github.com/biostochastics/codeconcat/blob/main/LICENSE) for details.
