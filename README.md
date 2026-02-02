# CodeConCat

<p align="center">
  <img src="assets/codeconcat_logo.png" alt="CodeConCat Logo" width="300"/>
</p>

<p align="center">
  <strong>Transform codebases into AI-ready formats with intelligent parsing, compression, and security analysis</strong>
</p>

[![Version](https://img.shields.io/badge/version-0.9.3-blue)](https://github.com/biostochastics/codeconcat) [![Tests](https://img.shields.io/badge/tests-1550%2B%20passing-brightgreen)](https://github.com/biostochastics/codeconcat) [![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT) [![DeepWiki](https://img.shields.io/badge/DeepWiki-Documentation-purple)](https://deepwiki.com/biostochastics/CodeConCat) [![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Type checked: mypy](https://img.shields.io/badge/type%20checked-mypy-blue.svg)](http://mypy-lang.org/) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit)](https://github.com/pre-commit/pre-commit) [![Poetry](https://img.shields.io/badge/dependency%20management-poetry-blueviolet)](https://python-poetry.org/) [![Typer](https://img.shields.io/badge/CLI-typer-green)](https://typer.tiangolo.com/)

## Table of Contents

- [What is CodeConCat?](#what-is-codeconcat)
- [Quick Start](#quick-start)
- [Core Features](#core-features)
- [Language Support](#language-support)
- [Usage Guide](#usage-guide)
- [Configuration](#configuration)
- [CLI Reference](#cli-reference)
- [Advanced Features](#advanced-features)
- [API Access](#api-access)
- [Development](#development)
- [Security](#security)
- [Reference](#reference)

## What is CodeConCat?

CodeConCat is a Python tool that transforms codebases into formats optimized for AI consumption and analysis. It automatically processes your code to extract functions, classes, imports, and documentation across 25+ programming languages, providing structured output that makes code analysis intuitive and efficient.

**Why CodeConCat?**
- **Multi-Language Intelligence**: Parse 25+ languages including smart contracts
- **AI-Optimized Output**: Optional compression and AI summarization
- **Production-Grade Security**: Path traversal protection, XXE prevention, Semgrep integration
- **High Performance**: 5-7x speedup with parallel parsing using ProcessPoolExecutor

**Primary Use Cases:**
- Preparing codebases for AI assistant analysis
- Code review and documentation generation
- Repository migration and refactoring planning
- Security auditing and vulnerability scanning

## Quick Start

### Installation

<details>
<summary>Using Poetry (Recommended)</summary>

```bash
# Install Poetry if needed
curl -sSL https://install.python-poetry.org | python3 -

# Clone and install
git clone https://github.com/biostochastics/codeconcat.git
cd codeconcat
poetry install

# Run CodeConCat
poetry run codeconcat --help
```
</details>

<details>
<summary>Using pip</summary>

```bash
# Install from source
git clone https://github.com/biostochastics/codeconcat.git
cd codeconcat
pip install -e .

# Or install from PyPI (when published)
pip install codeconcat
```
</details>

### Your First Command

```bash
# Process current directory with default settings
codeconcat run

# Generate markdown output
codeconcat run --format markdown --output my-code.md
```

**Expected output:** Structured file with code analysis, function signatures, and documentation.

### Common Examples

```bash
# Process with filtering
codeconcat run --include-language python javascript --exclude-path "*/tests/*"

# With AI summarization (requires API key)
codeconcat run --ai-summary --ai-provider anthropic --output analyzed-code.md

# Security scanning with compression
codeconcat run --security --semgrep --compress --output secure-report.json
```

> **⚠️ Security Note**
> CodeConCat processes code for AI model consumption. While built-in security features protect against common threats, always review output before sharing with AI assistants or third parties. See the [Security](#security) section for detailed information.

**Next Steps:**
- See [Usage Guide](#usage-guide) for detailed workflows
- Check [Configuration](#configuration) for customization options
- Review [Advanced Features](#advanced-features) for AI and compression capabilities

## Core Features

- **Multi-Language Parsing** - 25+ languages using tree-sitter and regex engines with intelligent result merging
- **AI Summarization** *(Optional)* - Code summaries via OpenAI, Anthropic, OpenRouter, or local models (Ollama, llama.cpp)
- **Differential Outputs** - Generate diffs between Git refs with AI-powered change summaries
- **Code Compression** - Pattern recognition reduces token usage by 35-40% with configurable levels
- **Security Scanning** - Integrated Semgrep support with configurable thresholds and comprehensive validation
- **Multiple Output Formats** - Markdown, JSON, XML, and text with format-specific optimizations
- **Remote Repository Support** - Analyze GitHub repositories directly via URL or shorthand notation
- **Parallel Processing** - Configurable worker threads for optimal performance
- **File Reconstruction** - Restore source files from output with path traversal protection
- **REST API** - FastAPI-based server for programmatic access
- **Modern CLI** - Typer-powered interface with shell completion and rich help
- **Smart Caching** - TTL-based cache management for repeated operations
- **Graceful Interrupts** - Ctrl+C handling with double-press force quit support
- **Unified Progress Display** - Flicker-free Rich Live dashboard with stage tracking

## Language Support

CodeConCat provides comprehensive parsing for 25+ programming languages with industry-validated accuracy:

| Language | Parser Type | Key Features | Documentation |
|----------|-------------|--------------|---------------|
| **Python** | Tree-sitter + Enhanced Regex | Type hints, async/await, decorators, dataclasses | ✓ Docstrings |
| **JavaScript/TypeScript** | Tree-sitter + Enhanced Regex | JSX/TSX, ES6+, decorators, modules | ✓ JSDoc |
| **Java** | Tree-sitter + Enhanced Regex | Generics, annotations, lambdas, records | ✓ Javadoc |
| **C/C++** | Tree-sitter + Enhanced Regex | Templates, modern C++ features, preprocessor | ✓ Doxygen |
| **C#** | Tree-sitter + Enhanced Regex | Generics, attributes, async/await, LINQ | ✓ XML docs |
| **Go** | Tree-sitter + Enhanced Regex | Interfaces, embedded types, generics | ✓ GoDoc |
| **Rust** | Tree-sitter + Enhanced Regex | Traits, lifetimes, const generics, GATs | ✓ Rustdoc |
| **PHP** | Tree-sitter + Enhanced Regex | Traits, attributes, typed properties | ✓ PHPDoc |
| **Julia** | Tree-sitter + Enhanced Regex | Multiple dispatch, parametric types, macros | ✓ Docstrings |
| **R** | Tree-sitter + Enhanced Regex | S3/S4 OOP, functions, tidyverse patterns | ✓ Roxygen |
| **Swift** | Tree-sitter + Enhanced Regex | Property wrappers, actors, async/await | ✓ SwiftDoc |
| **Kotlin** | Tree-sitter | Extension functions, suspend functions, sealed classes | ✓ KDoc |
| **Ruby** | Tree-sitter | Modules, classes, blocks, metaprogramming, mixins | ✓ RDoc |
| **Solidity** | Tree-sitter | Smart contracts, inheritance, modifiers, events, security patterns | ✓ NatSpec |
| **Crystal** | Tree-sitter | Type annotations, union types, C bindings, macros | ✓ Comments |
| **Dart** | Tree-sitter | Null safety, Flutter patterns, mixins | ✓ Dartdoc |
| **Elixir** | Tree-sitter | GenServer, LiveView, pattern matching, pipe operators, macros | ✓ @doc/@moduledoc |
| **Zig** | Tree-sitter | Comptime blocks, async/await (suspend/resume), error unions, inline for, struct methods | ✓ /// comments |
| **SQL** | Tree-sitter | Multi-dialect (PostgreSQL, MySQL, SQLite), CTEs | ✓ Comments |
| **HCL/Terraform** | Tree-sitter | Resources, modules, providers, variables | ✓ Comments |
| **GraphQL** | Tree-sitter | Schema definitions, operations, directives | ✓ Descriptions |
| **GLSL** | Tree-sitter | Vertex/fragment/compute shaders, uniforms, samplers, textures, in/out variables, layout qualifiers | ✓ Comments |
| **HLSL** | Tree-sitter | Compute/vertex/pixel shaders, cbuffer/tbuffer, RWTextures, structured buffers, typedefs, semantics | ✓ Comments |
| **Bash/Shell** | Tree-sitter | Functions, variables, source imports | ✓ Comments |
| **TOML** | Enhanced Regex | Configuration parsing, nested tables | ✓ Comments |
| **WAT (WebAssembly Text)** | Tree-sitter | Modules, functions, imports/exports, memory, types | ✓ Comments |

**Crystal Support:** CodeConCat provides comprehensive parsing for Crystal using a dynamically-compiled tree-sitter grammar from [crystal-lang-tools/tree-sitter-crystal](https://github.com/crystal-lang-tools/tree-sitter-crystal). The grammar is automatically downloaded and compiled on first use, with configurable cache directory via `CODECONCAT_CACHE_DIR` environment variable. The parser extracts classes, modules, structs, methods, macros, type aliases, and C library bindings (lib blocks). It tracks Crystal-specific features including type annotations, union types, nilable types, and generic type parameters. All security features include file locking to prevent race conditions, atomic file operations to prevent TOCTOU vulnerabilities, and automatic caching for improved performance.

**WebAssembly Support:** CodeConCat provides comprehensive parsing for WebAssembly Text (WAT) format using a dynamically-compiled tree-sitter grammar from [wasm-lsp/tree-sitter-wasm](https://github.com/wasm-lsp/tree-sitter-wasm). The grammar is automatically downloaded and compiled on first use, with configurable cache directory via `CODECONCAT_CACHE_DIR` environment variable. The parser extracts module structure, function signatures with parameter/result types, import/export statements, type definitions, and global/table declarations. All security features include file locking to prevent race conditions, commit hash pinning for reproducible builds, and atomic file operations to prevent TOCTOU vulnerabilities.

### Parser Architecture

CodeConCat uses an intelligent multi-tier parser system with **result merging** for maximum reliability:

1. **Tree-sitter Parsers** (Primary) - Full syntax tree parsing for accurate structure recognition
2. **Enhanced Regex Parsers** (Fallback) - Pattern-based parsing with state tracking for edge cases
3. **Intelligent Merging** (v0.8.4+) - Combines results from multiple parsers with confidence scoring

**Key Capabilities:**
- Automatic fallback between parser engines on errors
- Unicode support with BOM removal and NFC normalization
- Error recovery continues parsing even with syntax errors
- Signature extraction for functions/methods with full parameter lists
- Docstring extraction in language-specific formats

For detailed parser implementation history, architecture decisions, and refactoring documentation, see [docs/PARSER_DETAILS.md](./docs/PARSER_DETAILS.md).

## Usage Guide

### Basic Usage

**Process Files and Directories**

```bash
# Process current directory
codeconcat run

# Process specific directory or file
codeconcat run /path/to/project
codeconcat run src/main.py

# Process GitHub repository (NEW in v0.8.3)
codeconcat run https://github.com/owner/repo
codeconcat run owner/repo  # Shorthand notation
codeconcat run git@github.com:owner/repo.git  # SSH URL
```

**Output Formats**

```bash
# Markdown (default) - Best for human readability
codeconcat run --format markdown --output code.md

# JSON - Best for programmatic access
codeconcat run --format json --output code.json

# XML - Best for structured processing
codeconcat run --format xml --output code.xml

# Text - Best for terminal output
codeconcat run --format text --output code.txt
```

**Filtering Options**

```bash
# Include specific languages
codeconcat run --include-language python javascript rust

# Exclude paths (glob patterns)
codeconcat run --exclude-path "*/tests/*" "*/node_modules/*" "*/__pycache__/*"

# Include specific paths
codeconcat run --include-path "src/**/*.py" "lib/**/*.py"

# Combine filters
codeconcat run \
    --include-language python \
    --exclude-path "**/test_*.py" \
    --output filtered-code.md
```

For complete command reference and all available options, see the [CLI Reference](#cli-reference) section.

### Advanced Workflows

**Differential Analysis**

Compare Git branches, tags, or commits to see only changed files:

```bash
# Compare branches
codeconcat run --diff-from main --diff-to feature-branch --output changes.md

# Compare commits with AI summaries
codeconcat run \
    --diff-from HEAD~10 \
    --diff-to HEAD \
    --ai-summary \
    --ai-provider anthropic \
    --output recent-changes.md

# Compare tags for release notes
codeconcat run --diff-from v1.0.0 --diff-to v2.0.0 --output release-diff.md
```

**AI-Powered Summarization**

Generate intelligent code summaries for better understanding:

```bash
# Enable AI summarization with default provider
codeconcat run --ai-summary --ai-provider openai

# Use specific model
codeconcat run \
    --ai-summary \
    --ai-provider anthropic \
    --ai-model claude-sonnet-4-20250514

# Generate meta-overview of entire codebase
codeconcat run \
    --ai-summary \
    --ai-meta-overview \
    --ai-provider anthropic \
    --output full-analysis.md

# Save summaries for caching
codeconcat run \
    --ai-summary \
    --ai-save-summaries \
    --ai-provider openai \
    --output analyzed-code.md
```

See [Advanced Features - AI Summarization](#ai-summarization) for detailed AI configuration.

**Code Compression**

Reduce token usage while preserving structure:

```bash
# Enable compression with contextual mode
codeconcat run --compress --compression-level medium --output compressed.md

# Aggressive compression (signatures and essential code only)
codeconcat run --compress --compression-level aggressive --output minimal.json
```

**Smart Contract Analysis (Solidity)**

Analyze Ethereum/blockchain smart contracts with security pattern detection:

```bash
# Process Solidity contracts with security pattern flagging
codeconcat run contracts/ --include-language solidity --output contracts-analysis.md

# Combine with security scanning for comprehensive analysis
codeconcat run \
    --include-language solidity \
    --security \
    --output smart-contract-audit.md

# Process DeFi protocol with AI summarization
codeconcat run defi-protocol/ \
    --include-language solidity javascript \
    --ai-summary \
    --ai-provider anthropic \
    --output protocol-analysis.md
```

The Solidity parser automatically flags security-relevant patterns including:
- `selfdestruct` and `delegatecall` usage
- Assembly blocks requiring manual review
- External calls (potential reentrancy points)
- Inheritance hierarchies and modifier chains

**Security Scanning**

Scan code for security issues and sensitive data:

```bash
# Basic security scanning
codeconcat run --security --output secure-report.md

# With Semgrep integration
codeconcat run --security --semgrep --output detailed-security.json

# Set severity threshold
codeconcat run --security --security-threshold HIGH --output critical-only.md
```

### Common Recipes

**Production Build with Full Analysis**

```bash
codeconcat run \
    --format json \
    --compress \
    --compression-level high \
    --security \
    --semgrep \
    --security-threshold HIGH \
    --test-security-report \
    --output production-audit.json
```

**Quick Documentation Extraction**

```bash
codeconcat run \
    --docs \
    --merge-docs \
    --remove-docstrings \
    --remove-comments \
    --preset lean \
    --output docs-only.md
```

**GitHub Repository Analysis**

```bash
# Public repository
codeconcat run owner/repo --ai-summary --output analysis.md

# Private repository (requires token)
codeconcat run \
    --source-url owner/private-repo \
    --github-token $GITHUB_TOKEN \
    --output private-analysis.md
```

<details>
<summary><strong>GitHub Token Best Practices</strong></summary>

GitHub recommends **fine-grained personal access tokens** over classic PATs for better security:

| Token Type | Format | Recommendation |
|------------|--------|----------------|
| **Fine-grained PAT** | `github_pat_*` | Recommended - scoped to specific repos |
| **Classic PAT** | `ghp_*` | Legacy - grants broader access |
| **GitHub App** | `ghs_*` | Best for organizational/production use |

**Creating a Fine-Grained Token (Recommended):**

1. Go to [GitHub Settings → Developer settings → Personal access tokens → Fine-grained tokens](https://github.com/settings/tokens?type=beta)
2. Click "Generate new token"
3. Configure:
   - **Token name**: `codeconcat-access` (or descriptive name)
   - **Expiration**: Set appropriate expiration (GitHub allows up to 1 year)
   - **Repository access**: Select "Only select repositories" and choose specific repos
   - **Permissions**:
     - `Contents`: **Read** (required for cloning)
     - `Metadata`: **Read** (automatically included)
4. Click "Generate token" and save it securely

**Minimum Required Permissions:**
- For public repos: No token needed
- For private repos: `Contents: Read` permission only

**Security Benefits of Fine-Grained Tokens:**
- Scoped to specific repositories (not all repos you can access)
- Minimum required permissions (principle of least privilege)
- Built-in expiration (enterprises can enforce max 90-366 days)
- Better audit trail in organization settings

**Using the Token:**
```bash
# Set as environment variable (recommended)
export GITHUB_TOKEN=github_pat_11AAAA...

# Or pass directly (avoid in shell history)
codeconcat run --source-url owner/private-repo --github-token "github_pat_..."
```

</details>

## Configuration

### Configuration File

Create `.codeconcat.yml` in your project root for persistent settings:

```yaml
version: "1.0"

# Output settings
output_preset: medium  # Options: lean, medium, full
format: markdown       # Options: markdown, json, xml, text

# Filtering
use_gitignore: true
use_default_excludes: true
include_languages:
  - python
  - javascript
  - rust
exclude_paths:
  - "*/tests/*"
  - "*/node_modules/*"
  - "*/__pycache__/*"

# Processing
parser_engine: tree_sitter  # Options: tree_sitter, regex
max_workers: 4              # Parallel processing threads (1-32)
enable_result_merging: true # Intelligent parser result merging
merge_strategy: confidence  # Options: confidence, union, fast_fail, best_of_breed

# Compression
enable_compression: false
compression_level: medium  # Options: low, medium, high/aggressive

# Security
enable_security_scanning: true
security_scan_severity_threshold: MEDIUM  # Options: LOW, MEDIUM, HIGH, CRITICAL

# AI Features (optional)
enable_ai_summary: false
ai_provider: anthropic           # Options: openai, anthropic, openrouter, google, deepseek,
                                 #          minimax, qwen, zhipu, ollama, local_server, vllm,
                                 #          lmstudio, llamacpp_server
ai_model: ""                     # Optional, uses provider defaults
ai_meta_overview: false          # Generate project-wide overview
ai_meta_prompt: ""               # Custom prompt for meta-overview
ai_save_summaries: false         # Save summaries to disk for caching
ai_summaries_dir: "codeconcat_summaries"  # Directory for saved summaries
ai_min_file_lines: 20            # Skip small files
ai_max_concurrent: 25            # Max concurrent AI requests
```

Initialize configuration interactively:

```bash
codeconcat init                    # Interactive setup
codeconcat init --preset medium    # Use specific preset
codeconcat validate .codeconcat.yml  # Validate existing config
```

### Configuration Presets

| Preset | Use Case | Features |
|--------|----------|----------|
| **lean** | Minimal output for quick reviews | Basic parsing, no metadata, compressed output |
| **medium** | Balanced analysis (default) | Standard parsing with context, moderate detail |
| **full** | Comprehensive documentation | Complete parsing, all metadata, full features |

### Environment Variables

```bash
# GitHub Token (see "GitHub Token Best Practices" above for creating tokens)
# Fine-grained tokens (github_pat_*) are recommended over classic tokens (ghp_*)
export GITHUB_TOKEN=github_pat_11AAAA...

# AI Provider Keys (optional, see AI Summarization section)
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export OPENROUTER_API_KEY=sk-or-...
export GOOGLE_API_KEY=...         # Google Gemini
export DEEPSEEK_API_KEY=...       # DeepSeek
export MINIMAX_API_KEY=...        # MiniMax
export DASHSCOPE_API_KEY=...      # Qwen/DashScope
export ZHIPUAI_API_KEY=...        # Zhipu GLM
export LOCAL_LLM_API_KEY=""       # Optional: generic OpenAI-compatible local servers
export VLLM_API_KEY=""            # Optional: vLLM preset
export LMSTUDIO_API_KEY=""        # Optional: LM Studio preset
export LLAMACPP_SERVER_API_KEY="" # Optional: llama.cpp server preset

# API Server Configuration
export CODECONCAT_HOST=127.0.0.1
export CODECONCAT_PORT=8000
export CODECONCAT_ALLOW_LOCAL_PATH=false  # Enable local paths in API (dev only)

# Environment Mode
export ENV=production  # Options: production, development, test
```

## CLI Reference

### Global Options

| Option | Short | Description |
|--------|-------|-------------|
| `--version` | `-V` | Show version and exit |
| `--verbose` | `-v` | Increase verbosity (-v for INFO, -vv for DEBUG) |
| `--quiet` | `-q` | Suppress progress information |
| `--config` | `-c` | Path to configuration file |
| `--install-completion` | | Install shell completion |
| `--show-completion` | | Show shell completion script |
| `--help` | | Show help message |

### `codeconcat run`

Process files and generate AI-optimized output.

**Usage:** `codeconcat run [OPTIONS] [TARGET]`

**Arguments:**
- `TARGET` - Path to process, GitHub URL, or owner/repo shorthand (default: current directory)

<details>
<summary><strong>Output Options</strong></summary>

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output file path (default: `ccc_{folder}_{mmddyy}.{ext}`) |
| `--format` | `-f` | Output format: `markdown`, `json`, `xml`, `text` |
| `--preset` | `-p` | Configuration preset: `lean`, `medium`, `full` |

</details>

<details>
<summary><strong>Processing Options</strong></summary>

| Option | Description |
|--------|-------------|
| `--parser-engine` | Parser engine: `tree_sitter`, `regex` |
| `--max-workers` | Parallel workers (1-32, default: 4) |
| `--show-config` | Print configuration and exit |
| `--no-progress` | Disable progress bars |
| `--redact-paths` / `--no-redact-paths` | Redact absolute filesystem paths in output |

</details>

<details>
<summary><strong>Filtering Options</strong></summary>

| Option | Short | Description |
|--------|-------|-------------|
| `--include-path` | `-ip` | Glob patterns to include (repeatable) |
| `--exclude-path` | `-ep` | Glob patterns to exclude (repeatable) |
| `--include-language` | `-il` | Languages to include |
| `--exclude-language` | `-el` | Languages to exclude |
| `--use-gitignore` / `--no-gitignore` | | Respect .gitignore files (default: true) |
| `--use-default-excludes` / `--no-default-excludes` | | Use built-in default excludes (default: true) |

</details>

<details>
<summary><strong>Feature Options</strong></summary>

| Option | Description |
|--------|-------------|
| `--docs` / `--no-docs` | Extract standalone documentation files |
| `--merge-docs` / `--no-merge-docs` | Merge docs into main output |
| `--no-annotations` | Skip code annotation |
| `--remove-docstrings` | Strip docstrings from code |
| `--remove-comments` | Strip comments from code |
| `--xml-pi` / `--no-xml-pi` | Include AI processing instructions in XML output |
| `--prompt-file` | Custom prompt file for codebase review |
| `--prompt-var` | Prompt variables (format: KEY=value, repeatable) |
| `--unsupported-report` | Write unsupported/skipped files report to JSON |

</details>

<details>
<summary><strong>Compression Options</strong></summary>

| Option | Description |
|--------|-------------|
| `--compress` / `--no-compress` | Enable intelligent code compression |
| `--compression-level` | Level: `low`, `medium`, `high`/`aggressive` |

</details>

<details>
<summary><strong>Security Options</strong></summary>

| Option | Description |
|--------|-------------|
| `--security` / `--no-security` | Enable security scanning (default: true) |
| `--semgrep` / `--no-semgrep` | Enable Semgrep security scanning |
| `--security-threshold` | Severity: `LOW`, `MEDIUM`, `HIGH`, `CRITICAL` |
| `--test-security-report` | Write test file security findings to separate file |

</details>

<details>
<summary><strong>Git Differential Options</strong></summary>

| Option | Description |
|--------|-------------|
| `--diff-from` | Starting Git ref (branch, tag, commit) |
| `--diff-to` | Ending Git ref (branch, tag, commit) |

</details>

<details>
<summary><strong>AI Summarization Options</strong></summary>

| Option | Description |
|--------|-------------|
| `--ai-summary` / `--no-ai-summary` | Enable AI-powered code summarization |
| `--ai-provider` | Provider: `openai`, `anthropic`, `openrouter`, `google`, `deepseek`, `minimax`, `qwen`, `zhipu`, `ollama`, `local_server`, `vllm`, `lmstudio`, `llamacpp_server` |
| `--ai-model` | Specific model (uses provider defaults if omitted) |
| `--ai-api-key` | API key (alternative to environment variable) |
| `--ai-api-base` | Override the API base URL for local servers |
| `--ai-functions` / `--no-ai-functions` | Also summarize individual functions/methods |
| `--ai-meta-overview` / `--no-ai-meta-overview` | Generate meta-overview from all file summaries |
| `--ai-meta-prompt` | Custom prompt for meta-overview generation |
| `--ai-meta-higher-tier` / `--no-ai-meta-higher-tier` | Use higher-tier models for meta-overview (default: true) |
| `--ai-meta-model` | Override model for meta-overview generation |
| `--ai-save-summaries` / `--no-ai-save-summaries` | Save summaries to separate files |
| `--ai-summaries-dir` | Directory for saving AI summaries |

</details>

<details>
<summary><strong>Local LLM Performance Options</strong></summary>

| Option | Description |
|--------|-------------|
| `--llama-gpu-layers` | Number of layers to offload to GPU (0=CPU only) |
| `--llama-context-size` | Context window size (default: 2048) |
| `--llama-threads` | Number of CPU threads |
| `--llama-batch-size` | Batch size for prompt processing |

</details>

<details>
<summary><strong>Remote Repository Options</strong></summary>

| Option | Description |
|--------|-------------|
| `--source-url` | GitHub URL or owner/repo shorthand |
| `--github-token` | GitHub PAT for private repos (env: `GITHUB_TOKEN`) |
| `--source-ref` | Branch, tag, or commit hash for Git source |

</details>

### `codeconcat init`

Initialize configuration interactively.

**Usage:** `codeconcat init [OPTIONS]`

| Option | Short | Description |
|--------|-------|-------------|
| `--output` | `-o` | Output path (default: .codeconcat.yml) |
| `--interactive` / `--no-interactive` | | Use interactive wizard (default: true) |
| `--force` | `-f` | Overwrite existing configuration |
| `--preset` | `-p` | Use preset: `lean`, `medium`, `full` |

### `codeconcat config local-llm`

Interactive wizard for configuring local OpenAI-compatible servers (vLLM,
LM Studio, llama.cpp server, or generic runtimes).

**Usage:** `codeconcat config local-llm`

| Step | What happens |
|------|---------------|
| Preset selection | Choose vLLM, LM Studio, llama.cpp server, or generic |
| Auto-detect | Probes common ports and health endpoints |
| Model discovery | Lists models from `/v1/models` or `/models` |
| Config update | Writes `enable_ai_summary`, `ai_provider`, `ai_api_base`, `ai_model`, and `ai_api_key` |

Refer to [`docs/LOCAL_MODELS.md`](docs/LOCAL_MODELS.md) for a detailed guide.

### `codeconcat validate`

Validate a configuration file.

**Usage:** `codeconcat validate [CONFIG_FILE]`

**Arguments:**
- `CONFIG_FILE` - Configuration file to validate (default: `.codeconcat.yml`)

### `codeconcat reconstruct`

Reconstruct source files from CodeConCat output with security validation.

**Usage:** `codeconcat reconstruct [OPTIONS] INPUT_FILE`

**Security:** All reconstructed files are validated to prevent path traversal attacks.

| Option | Short | Description |
|--------|-------|-------------|
| `--output-dir` | `-o` | Directory for files (default: ./reconstructed) |
| `--format` | `-f` | Input format (auto-detected if not specified) |
| `--strict` / `--lenient` | | Strict parsing (default: `--strict`) or lenient repair mode |
| `--force` | | Overwrite existing files |
| `--dry-run` | | Preview without creating files |
| `--verbose` | `-v` | Show detailed progress |

**Supported Formats:** Markdown v2.0, XML v2.0, JSON v2.0

### `codeconcat api`

Manage the CodeConCat API server.

**Sub-commands:**

#### `codeconcat api start`

Start the API server.

| Option | Short | Description |
|--------|-------|-------------|
| `--host` | `-h` | Host to bind (default: 127.0.0.1) |
| `--port` | `-p` | Port to bind (default: 8000) |
| `--reload` | | Enable auto-reload (development) |
| `--workers` | `-w` | Number of worker processes |
| `--log-level` | `-l` | Logging level |

#### `codeconcat api info`

Display API information and endpoints.

### `codeconcat diagnose`

Diagnostic and verification tools.

**Sub-commands:**

- `codeconcat diagnose verify` - Verify tree-sitter dependencies
- `codeconcat diagnose parser LANGUAGE [-f FILE]` - Test language parser
- `codeconcat diagnose system` - Display system information
- `codeconcat diagnose languages` - List supported languages

### `codeconcat keys`

Manage API keys for AI providers with secure storage.

**Sub-commands:**

- `codeconcat keys setup` - Interactive key setup with encryption
- `codeconcat keys list [--show-values]` - List configured keys
- `codeconcat keys set PROVIDER [API_KEY]` - Set or update key
- `codeconcat keys delete PROVIDER` - Delete key
- `codeconcat keys reset [--force]` - Reset all keys
- `codeconcat keys test PROVIDER` - Test key validity
- `codeconcat keys change-password` - Change master password for encrypted storage
- `codeconcat keys export [-o FILE] [--show-keys]` - Export configuration

**Storage Methods:** Encrypted file (default), system keyring, environment variables

### Shell Completion

Enable tab completion for your shell:

```bash
# Bash
codeconcat --install-completion bash

# Zsh
codeconcat --install-completion zsh

# Fish
codeconcat --install-completion fish
```

## Advanced Features

### AI Summarization

Generate intelligent code summaries to enhance understanding and reduce context size.

#### Supported Providers

| Provider | Default Model (Files) | Default Model (Meta) | Notes |
|----------|----------------------|---------------------|-------|
| **OpenAI** | gpt-5-mini-2025-08-07 | gpt-5-2025-08-07 | Fast with reasoning capabilities |
| **Anthropic** | claude-sonnet-4-20250514 | claude-opus-4-20250514 | Fast with extended thinking |
| **OpenRouter** | qwen/qwen3-coder | z-ai/glm-4.6 | Access to 100+ models |
| **Google Gemini** | gemini-2.0-flash | gemini-2.5-pro | Free tier available, 1M+ context |
| **DeepSeek** | deepseek-coder | deepseek-chat | Extremely cost-effective |
| **MiniMax** | MiniMax-Text-01 | MiniMax-Text-01 | 1M context window |
| **Qwen/DashScope** | qwen-coder-plus | qwen3-235b-instruct | Alibaba's code models |
| **Zhipu GLM** | glm-4-flash | glm-4-plus | Strong multilingual support |
| **Ollama** | llama3.2 | llama3.2 | Local, private, no API needed |

#### Quick Start

```bash
# Enable AI summarization
codeconcat run --ai-summary --ai-provider openai

# Use specific model
codeconcat run --ai-summary --ai-provider anthropic --ai-model claude-sonnet-4-20250514

# Local model with Ollama (privacy-focused)
ollama run llama3.2  # First-time setup
codeconcat run --ai-summary --ai-provider ollama --ai-model llama3.2
```

#### AI Meta-Overview

Generate a comprehensive project-wide overview:

```bash
# Enable meta-overview with default prompt
codeconcat run --ai-summary --ai-meta-overview --ai-provider openai

# Custom prompt for focused analysis
codeconcat run --ai-summary --ai-meta-overview \
  --ai-meta-prompt "Focus on security architecture and data flow" \
  --ai-provider anthropic

# Save summaries to disk for caching
codeconcat run --ai-summary --ai-meta-overview --ai-save-summaries \
  --ai-provider anthropic \
  --output report.md
```

The meta-overview synthesizes all file summaries into:
- High-level architectural understanding
- Key components and relationships
- Design patterns and technologies used
- Onboarding insights for new developers

#### Summary Persistence

Save AI-generated summaries for caching and reuse:

```bash
codeconcat run --ai-summary --ai-save-summaries --ai-provider openai

# Summaries saved to {output_dir}/codeconcat_summaries/
# ├── individual/      # Per-file summaries (JSON)
# └── meta_overview.json  # Project-wide overview
```

#### API Key Configuration

API keys are resolved in the following **priority order**:

1. **CLI flag** (`--ai-api-key`) - Highest priority, overrides all others
2. **Environment variable** - Provider-specific env vars (see table below)
3. **Encrypted storage** - Keys stored via `codeconcat keys setup`
4. **Config file** - Keys in `.codeconcat.yml` (not recommended for secrets)

<details>
<summary><strong>Environment Variables (Recommended)</strong></summary>

| Provider | Environment Variable | Notes |
|----------|---------------------|-------|
| OpenAI | `OPENAI_API_KEY` | GPT-4, GPT-5, o-series models |
| Anthropic | `ANTHROPIC_API_KEY` | Claude models |
| Google Gemini | `GOOGLE_API_KEY` or `GEMINI_API_KEY` | Gemini 1.5/2.0/2.5 models |
| OpenRouter | `OPENROUTER_API_KEY` | Multi-provider gateway |
| DeepSeek | `DEEPSEEK_API_KEY` | DeepSeek Coder, Chat, Reasoner |
| MiniMax | `MINIMAX_API_KEY` | MiniMax-Text-01, abab models |
| Qwen/DashScope | `DASHSCOPE_API_KEY` | Qwen Coder models |
| Zhipu GLM | `ZHIPUAI_API_KEY` or `ZHIPU_API_KEY` | GLM-4, CodeGeeX models |
| Ollama | *(none required)* | Local, no API key needed |
| vLLM | `VLLM_API_KEY` | Optional, for authenticated servers |
| LM Studio | `LMSTUDIO_API_KEY` | Optional, usually not needed |
| llama.cpp | `LLAMACPP_SERVER_API_KEY` | Optional, for authenticated servers |
| Generic local | `LOCAL_LLM_API_KEY` | Fallback for any OpenAI-compatible server |

```bash
# Example: Set up cloud providers
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."
export GOOGLE_API_KEY="AIza..."
export DEEPSEEK_API_KEY="sk-..."
export DASHSCOPE_API_KEY="sk-..."
export ZHIPUAI_API_KEY="..."
```

</details>

<details>
<summary><strong>Encrypted Storage (Interactive)</strong></summary>

Store keys securely with password-protected encryption in `~/.codeconcat/`:

```bash
# Interactive setup wizard
codeconcat keys setup

# Prompts for:
# 1. Master password (for encryption)
# 2. Provider selection
# 3. API key entry

# Or set keys directly
codeconcat keys set openai sk-...
codeconcat keys set anthropic sk-ant-...
codeconcat keys set google AIza...

# List configured keys
codeconcat keys list

# Get a specific key
codeconcat keys get openai
```

</details>

<details>
<summary><strong>CLI Flag (Per-Command)</strong></summary>

```bash
# Pass API key directly (useful for CI/CD or one-off runs)
codeconcat run --ai-summary --ai-provider openai --ai-api-key "sk-..."
```

**Note:** Avoid this method for interactive use as keys may appear in shell history.

</details>

#### Local LLM Support

- Run `codeconcat config local-llm` to configure vLLM, LM Studio, llama.cpp
  server, or any OpenAI-compatible runtime. The wizard probes common ports,
  auto-discovers models, and writes updated fields to `.codeconcat.yml`.
- See [`docs/LOCAL_MODELS.md`](docs/LOCAL_MODELS.md) for a full integration
  guide and troubleshooting tips.

**Ollama (Easiest)**
```bash
# Install and start Ollama
ollama serve
ollama pull codellama  # or deepseek-coder, mistral, etc.

# Use with CodeConCat (auto-discovers best model)
codeconcat run --ai-summary --ai-provider ollama

# Or specify model explicitly
codeconcat run --ai-summary --ai-provider ollama --ai-model deepseek-coder
```

**OpenAI-compatible servers (vLLM / LM Studio / llama.cpp server)**
```bash
# Start your preferred server first (examples)
python -m vllm.entrypoints.openai.api_server --model path/to/model --port 8000
./llama-server -m models/llama-2-7b-chat.gguf -c 4096 -ngl 35
# In LM Studio: Start the "OpenAI Compatible Server" from the UI

# Run the configuration wizard
codeconcat config local-llm

# Then use CodeConCat with the saved settings
codeconcat run --ai-summary
```

> ⚠️ The legacy `--ai-provider llamacpp` integration is deprecated and will be
> removed in a future version. Run the llama.cpp HTTP server and use the wizard
> instead for better compatibility and auto-discovery.

**Recommended Models:**
- **Code-specific**: DeepSeek-Coder, CodeLlama, StarCoder, WizardCoder
- **General**: Mistral/Mixtral, Llama 3, Phi-3

#### Configuration

```yaml
# In .codeconcat.yml
enable_ai_summary: true
ai_provider: openai
ai_model: gpt-5-mini-2025-08-07  # Optional, uses provider default

# Meta-overview settings
ai_meta_overview: false
ai_meta_prompt: ""  # Custom prompt for meta-overview
ai_meta_overview_use_higher_tier: true  # Use premium models
ai_save_summaries: false
ai_summaries_dir: "codeconcat_summaries"

# Processing limits
ai_min_file_lines: 20
ai_summarize_functions: true
ai_max_functions_per_file: 10

# Performance
ai_max_concurrent: 25  # Concurrent AI requests (cloud APIs handle high concurrency)
ai_cache_enabled: true
ai_timeout: 600  # 10 minutes for AI operations
```

> **Note:** AI summaries are saved in the `codeconcat_summaries/` directory adjacent to your output file. Cache TTL is 7 days by default. Content is normalized (comments/whitespace stripped) for cache key hashing to improve hit rate.

#### Cost Optimization

```bash
# Use free local models
codeconcat run --ai-summary --ai-provider ollama --ai-model llama3.2

# Use low-cost cloud models
codeconcat run --ai-summary --ai-provider openai --ai-model gpt-5-mini-2025-08-07

# Limit scope
codeconcat run --ai-summary --ai-min-file-lines 50

# Enable caching (enabled by default)
codeconcat run --ai-summary --ai-cache-enabled
```

#### Security Considerations

⚠️ **Important:**
- API keys encrypted using Fernet (AES-128) with PBKDF2 key derivation
- Keys stored in `~/.codeconcat/keys.enc` with 0600 permissions
- Never commit API keys to version control
- Code sent to third-party services (except Ollama/llama.cpp)
- Use local models for sensitive/proprietary code

### Code Compression

Reduce token usage while preserving code structure:

```bash
# Contextual compression (keeps important code with context)
codeconcat run --compress --compression-level medium

# Essential compression (signatures, security, errors only)
codeconcat run --compress --compression-level aggressive
```

**Compression Levels:**
- **low**: Remove obvious redundancy, keep most context
- **medium**: Contextual compression, balance of reduction and readability
- **high/aggressive**: Essential code only, maximum token reduction

Typical results: 35-40% token reduction on large codebases.

### Security Scanning

Built-in security features protect against common vulnerabilities:

```bash
# Basic pattern-based scanning
codeconcat run --security --output secure-report.md

# Advanced Semgrep integration
codeconcat run --security --semgrep --security-threshold HIGH

# Separate test file security report
codeconcat run --security --test-security-report --output analysis.json
```

**Security Features:**
- Pattern-based credential detection
- Path traversal protection (CWE-22)
- XXE attack prevention
- ReDoS protection
- Command injection prevention
- Zip Slip protection
- File integrity verification (SHA-256)

See the [Security](#security) section for detailed architecture and best practices.

### File Reconstruction

Restore original source files from CodeConCat output:

```bash
# Reconstruct from output file
codeconcat reconstruct output.md

# Preview without creating files
codeconcat reconstruct output.json --dry-run

# Reconstruct to specific directory
codeconcat reconstruct output.xml -o ./restored

# Force overwrite existing files
codeconcat reconstruct output.md --force
```

**Security Features:**
- Path traversal protection prevents `../../../etc/passwd` attacks
- All file writes validated against target directory boundary
- XML parsing uses `defusedxml` for XXE-safe reconstruction
- Supports Markdown, XML, and JSON formats

### Differential Outputs

Generate diffs between Git references:

```bash
# Compare branches
codeconcat run --diff-from main --diff-to feature-branch -o changes.md

# Compare commits with AI summaries
codeconcat run \
  --diff-from HEAD~10 \
  --diff-to HEAD \
  --ai-summary \
  --ai-provider anthropic \
  --output recent-changes.md

# Compare tags for release notes
codeconcat run --diff-from v1.0.0 --diff-to v2.0.0 -o release-diff.md
```

**Features:**
- Works with branches, tags, and commit hashes
- Shows file-level changes with unified diff format
- AI summaries explain change impact
- Supports all output formats

## API Access

### REST API

Start the API server:

```bash
# Default settings (localhost:8000)
codeconcat api start

# Production with workers
codeconcat api start --host 0.0.0.0 --port 8080 --workers 4

# Development with auto-reload
codeconcat api start --reload
```

**API Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/concat` | POST | Process codebase from URL or local path |
| `/api/upload` | POST | Upload and process archive (zip/tar) |
| `/api/ping` | GET | Health check |
| `/api/config/presets` | GET | Available presets |
| `/api/config/formats` | GET | Supported formats |
| `/api/config/languages` | GET | Supported languages |
| `/api/config/defaults` | GET | Default configuration |
| `/docs` | GET | Interactive API docs (Swagger UI) |
| `/redoc` | GET | Alternative docs (ReDoc) |

**Example Usage:**

```python
import requests

# Process GitHub repository
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

# Upload and process archive
with open("code.zip", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/upload",
        files={"file": f},
        data={
            "format": "json",
            "output_preset": "medium"
        }
    )
```

### Python API

Use CodeConCat programmatically:

```python
from codeconcat.cli import app
from typer.testing import CliRunner

runner = CliRunner()

result = runner.invoke(app, [
    "run",
    "/path/to/project",
    "--format", "json",
    "--compress",
    "--output", "output.json"
])

if result.exit_code == 0:
    print("Success!")
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/biostochastics/codeconcat.git
cd codeconcat

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies (including dev, test, docs)
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
poetry run ruff format codeconcat tests
poetry run ruff check codeconcat tests --fix

# Lint code (check only)
poetry run ruff check codeconcat
poetry run mypy codeconcat

# Run all pre-commit hooks
poetry run pre-commit run --all-files
```

### CI/CD Pipeline

GitHub Actions runs on every push:
- **Testing**: Python 3.10, 3.11, 3.12
- **Code Quality**: Ruff linting and formatting, mypy type checking
- **Coverage**: Automatic coverage reporting
- **Pre-commit**: All hooks enforced
- **Publishing**: Automatic PyPI deployment on tagged releases

### Building & Publishing

```bash
# Build package
poetry build

# Check package
poetry check

# Publish to PyPI (requires token)
poetry publish

# Build and publish together
poetry publish --build
```

### Contributing

We welcome contributions! Please ensure:
- All tests pass (`pytest`)
- Code is formatted (`ruff format`)
- Type hints are complete (`mypy`)
- Pre-commit hooks pass
- New features include tests and documentation

## Security

### Security Architecture

CodeConCat implements defense-in-depth security with multiple protection layers:

**Path Traversal Prevention (CWE-22)**
- Canonical path resolution with `os.path.realpath()`
- Strict boundary enforcement via `os.path.commonpath()`
- Symlink escape detection and blocking
- Null byte injection prevention
- Cross-platform path normalization

**Content Sanitization**
- Dangerous content replaced with `[REDACTED]` placeholders
- Never exposes original secret values
- API keys, tokens, and credentials detected and removed

**Supply Chain Security**
- Semgrep pinned to tested version (1.52.0)
- Apiiro ruleset pinned to verified commit hash
- Uses `sys.executable -m pip` to prevent PATH hijacking
- Network timeouts prevent hanging attacks
- Post-install version verification

**Additional Protections**
- XXE attack prevention using defusedxml
- ReDoS protection with regex timeout limits
- Command injection prevention with sanitized inputs
- Zip Slip protection for archive extraction
- File integrity verification (SHA-256)
- Rate limiting for API deployments
- Thread-safe concurrent operations

### Security Features

- **API Access Controls**: Configurable path access and authentication
- **Thread-Safe Operations**: Concurrent request handling with isolated configurations
- **Memory Management**: File size limits (10MB max) and resource controls
- **Path Validation**: Traversal protection and symlink handling
- **Secure Git Operations**: All repository URLs and tokens sanitized

### ⚠️ Important Security Warnings

#### Prompt Injection Risks

This tool processes code for AI model consumption. Malicious code comments, docstrings, or file contents could potentially manipulate AI behavior when the output is used as LLM input.

#### Recommended Security Practices

1. **Review Output** - Always review generated output before sharing with AI models or third parties
2. **Sanitize Sensitive Data** - Use security scanning features (`--security`, `--semgrep`) to identify sensitive information
3. **Validate AI Responses** - Treat all AI-generated code suggestions as untrusted input requiring validation
4. **Restrict Access** - Use API access controls and authentication in production
5. **Environment Isolation** - Process untrusted codebases in isolated environments

### Security Disclosure

To report security vulnerabilities, please open a GitHub issue with the `security` label or contact maintainers directly. We follow responsible disclosure practices and credit reporters.

### Liability Disclaimer

**NO WARRANTY**: This software is provided "as is" without warranty of any kind, express or implied.

**NO LIABILITY**: In no event shall the authors be liable for any claim, damages, or other liability arising from the use of this software.

**USE AT YOUR OWN RISK**: Users assume all responsibility for security implications, validation of AI responses, protection of sensitive information, and compliance with applicable regulations.

## Reference

### Output Formats

**Markdown Format**
- Table of contents with anchor links
- Summary statistics and project overview
- Collapsible sections for large content
- Syntax highlighting
- Security issue badges

**JSON Format**
- Nested structure for traversal
- Indexes by language, type, directory
- Relationship mapping
- Metadata for filtering

**XML Format**
- Semantic tags for structure
- Hierarchical navigation
- Optional processing instructions (`--xml-pi`)
- CDATA sections for content preservation

**Text Format**
- Box drawing for visual hierarchy
- 80-character width for terminals
- Visual file type indicators
- Compact metadata display

### Parser Architecture Details

For comprehensive documentation on parser implementation, historical refactoring, and architectural decisions, see:

**[docs/PARSER_DETAILS.md](./docs/PARSER_DETAILS.md)**

Includes:
- Multi-tier parser system design
- Tree-sitter and regex integration
- Result merging algorithms (v0.8.4+)
- Phase-by-phase refactoring history (v0.9.4-dev)
- Modern tree-sitter API migration details
- Language-specific implementation notes

#### Recent Parser Improvements (v0.8.6+)

The parser system has undergone comprehensive security and performance improvements with critical bug fixes:

**Critical Bug Fixes:**
- **Cross-Platform Compatibility**: Removed POSIX-only signal timeout that caused AttributeError on Windows systems
- **Tree-sitter Version Compatibility**: Fixed QueryCursor API compatibility across tree-sitter 0.23.x and 0.24.0+ versions
- **Query Performance**: Optimized LRU cache eviction from O(n) to O(1) using deque.popleft() (128x improvement)
- **Error Search Performance**: Reduced BFS complexity from O(n²) to O(n) for deeply nested AST structures

**Security Enhancements:**
- **ReDoS Protection**: All regex patterns now include timeout limits and input sanitization
- **Path Traversal Prevention**: Robust validation prevents directory traversal attacks
- **Memory Exhaustion Protection**: Content size limits (10MB) prevent resource exhaustion attacks
- **Input Sanitization**: Comprehensive sanitization of all user inputs

**Performance Optimizations:**
- **LRU Cache Implementation**: Query caching with configurable size limits prevents memory leaks
- **Memory Management**: Automatic cache eviction using collections.deque for O(1) operations
- **Content Size Validation**: Two-tier approach (character count then UTF-8 encoding) for efficiency
- **C++ Parser**: Direct lookup for access specifiers and modifiers (reduced tree traversals)
- **Rust Parser**: Dict-based deduplication for O(1) lookup performance

**Error Handling Improvements:**
- **Standardized Error Reporting**: Unified error handling across all parsers with consistent error flags
- **Partial Parse Recovery**: Graceful handling of syntax errors with continued parsing
- **Quality Indicators**: Parser quality metrics for result reliability assessment

**Type System Standardization:**
- **Unified Type Mapping**: Consistent type classification across 25+ programming languages
- **Declaration Type Hierarchy**: Standardized type relationships (function, class, module, etc.)
- **Language-Agnostic Interface**: Consistent API regardless of source language

**Documentation Extraction:**
- **Unified Docstring Parsing**: Consistent extraction across all documentation formats
- **Multi-Language Support**: Support for Python docstrings, JSDoc, Javadoc, Rustdoc, etc.
- **Smart Context Detection**: Automatic detection of docstring location (preceding, internal, following)

**Enhanced Parser Implementations:**
- **Modern Tree-sitter API**: Full compatibility with tree-sitter 0.23.x and 0.24.0+ (handles both dict and tuple capture formats)
- **Improved Error Recovery**: Better handling of malformed code and syntax errors
- **Optimized Query Processing**: Efficient AST traversal with memory-safe operations

For detailed technical documentation of all fixes, see **[PARSER_FIXES_SUMMARY.md](./PARSER_FIXES_SUMMARY.md)**.

### Version History

See [CHANGELOG.md](./CHANGELOG.md) for complete version history and release notes.

**Current Version:** 0.9.3

### Troubleshooting

**Tree-sitter Grammar Issues**
```bash
codeconcat diagnose verify  # Verify all grammars
codeconcat diagnose parser python  # Test specific parser
```

**Performance Issues**
```bash
# Increase workers for large codebases
codeconcat run --max-workers 8

# Enable compression to reduce output size
codeconcat run --compress --compression-level medium
```

**API Connection Issues**
```bash
# Check API server status
codeconcat api info

# Start with debug logging
codeconcat api start --log-level debug
```

**AI Summary Failures**
```bash
# Test API key validity
codeconcat keys test openai

# Use local model as fallback
codeconcat run --ai-summary --ai-provider ollama
```

### Acknowledgments

CodeConCat is built with these open-source tools:

- [Typer](https://typer.tiangolo.com/) - CLI framework
- [Rich](https://rich.readthedocs.io/) - Terminal formatting
- [Poetry](https://python-poetry.org/) - Dependency management
- [Tree-sitter](https://tree-sitter.github.io/) - Incremental parsing
- [FastAPI](https://fastapi.tiangolo.com/) - Web API framework
- [Pydantic](https://pydantic-docs.helpmanual.io/) - Data validation
- [GitPython](https://gitpython.readthedocs.io/) - Git integration
- [Semgrep](https://semgrep.dev/) - Security scanning

### License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Contact

**GitHub Issues**: [https://github.com/biostochastics/codeconcat/issues](https://github.com/biostochastics/codeconcat/issues)

*Part of the Biostochastics collection of tools for translational science and biomarker discovery*
