# 🐱 CodeConCat

🚀 A simple code aggregator and documentation extractor 

CodeConCat is your intelligent companion for preparing codebases. It automatically ingests/collects, processes, and formats your code in a way that's optimized for AI comprehension and collaborative/iterative workflows.

## ✨ Features

- 🤖 **AI-Optimized Output**: Structured content with smart context generation
- 📁 **Smart File Collection**: Intelligent filtering and organization of your codebase
- 📝 **Documentation Extraction**: Automatically extract and process documentation
- 🌳 **Directory Tree**: Visual representation of your project structure
- 🔄 **Multiple Formats**: Output in Markdown, JSON, or XML
- 🔍 **Language Detection**: Automatic language detection and syntax highlighting
- 📋 **Clipboard Integration**: One-click copy to clipboard
- 🌐 **Multi-Language Support**: Comprehensive parsing for:
  - Python: Classes, functions, decorators, imports
  - JavaScript/TypeScript: Classes, functions, interfaces, types, decorators
  - Java: Classes, interfaces, enums, methods, annotations
  - Go: Packages, interfaces, structs, functions
  - PHP: Classes, interfaces, traits, methods
  - Ruby: Classes, modules, methods
  - R: Functions, S3/S4 classes, packages
  - Julia: Functions, structs, types, modules
  - Rust: Traits, impls, structs, enums
  - C/C++: Classes, functions, structs, namespaces
  - C#: Classes, interfaces, methods, properties

## 🚀 Quick Start

### Installation

```bash
pip install codeconcat
```

### Basic Usage

```bash
# Process current directory
codeconcat

# Process specific directory
codeconcat path/to/your/code

# Process GitHub repository
codeconcat --github username/repo
```

### Using Configuration File

Initialize a default configuration:
```bash
codeconcat --init
```

This creates a `.codeconcat.yml` with smart defaults for common use cases.

## 📊 Advanced Usage

### 🎯 Command Line Options

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

```bash
# Include specific patterns
codeconcat --include "**/*.{py,js,ts,java,go,php}"

# Exclude patterns
codeconcat --exclude "**/tests/**" "**/build/**"

# Filter by language
codeconcat --include-languages python javascript java

# Combine filters
codeconcat --include "**/*.py" --exclude "**/tests/**" --include-languages python
```

## ⚙️ Configuration

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

### Configuration Priority

1. Command line arguments (highest priority)
2. Local `.codeconcat.yml` file
3. Default settings (lowest priority)

## 🎨 Output Formats

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

## 📊 Code Summaries

### Output Summaries

CodeConcat generates comprehensive summaries of your codebase:

1. **File Statistics**
   - File name and language
   - Number of lines
   - Number and types of declarations
   - Line ranges for each declaration

2. **Directory Structure**
   - Tree view of project layout
   - Hierarchical file organization
   - File grouping by type/module

3. **Code Declarations**
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

## 🤝 Contributing

We welcome contributions! Check out our [Contributing Guide](CONTRIBUTING.md) to get started.

## 📝 License

MIT License - see the [LICENSE](LICENSE) file for details.

---

<b align="center">
  Made with ❤️ by Sergey Kornilov for Biostochastics, LLC
</b>
