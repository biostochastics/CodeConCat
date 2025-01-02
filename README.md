# CodeConCat

CodeConCat is a lightweight command-line tool (CLI) that aggregates code and (optionally) documentation from a local folder or (optionally) from GitHub (with private token support). It creates a folder tree, annotates source files, merges doc files, and produces an LLM-friendly output in Markdown or JSON; allows for automatic copying to the buffer. The tool supports multiple languages (Python, JavaScript/TypeScript, R, Julia, C/C++, etc.) and can run with concurrency to handle larger projects more efficiently.

## Table of Contents

1. [Overview](#overview)
2. [Features](#features)
3. [Requirements](#requirements)
4. [Installation](#installation)
5. [Usage](#usage)
6. [Configuration](#configuration)
7. [Concurrency](#concurrency)
8. [Doc Extraction](#doc-extraction)
9. [Examples](#examples)
10. [Testing](#testing)
11. [Project Structure](#project-structure-example)
12. [Contributing](#contributing)
13. [License](#license)

## Overview

CodeConCat scans your local directory (or a GitHub repo, if configured) for code files (Python, JS/TS, C/C++, R, Julia, etc.), filters them based on language or ignore patterns, parses them to identify top-level constructs (e.g., functions, classes), and then outputs an annotated version in a single file. If you enable docs mode, it also includes documentation files like .md, .rst, .txt, or .rmd.

**Use Case**: If you want to feed your code and docs to a Large Language Model (LLM) for analysis, CodeConCat can compile them into a single, organized snapshot.

## Features

* **Multi-Language Parsing**: Basic regex-based detection for functions/classes in Python, JS/TS, R, Julia, C/C++ (extendable)
* **Documentation Extraction**: Merge .md, .rst, .txt, .rmd files alongside code into one output
* **Configurable**: Define includes/excludes, doc extension, concurrency, output format, etc. in .codeconcat.yml or pass CLI flags
* **Concurrency**: Uses Python's ThreadPoolExecutor to parse files in parallel, improving performance on large projects
* **Multiple Output Formats**:
  * Markdown: Annotated code blocks with headings and code fences
  * JSON: Structured data (one object for each file, plus docs if included)
* **GitHub Collector**: Optionally clone from a public or private GitHub repo (via token) and run the same logic
* **Default Ignores**: By default, CodeConCat skips .DS_Store, .git/, and other system files to keep your output clean
* **Symbol Extraction**: Extracts and organizes constants and variables (symbols) from code files

## Requirements

* Python 3.8+
* pyyaml (if you want .codeconcat.yml support)
* pyperclip (for clipboard support)
* (Optional) pytest for running tests

## Installation

1. Clone the repository:
```bash
git clone https://github.com/biostochastics/CodeConCat.git
cd CodeConCat
```

2. Install either using a modern (PyPI-friendly) approach or a classic setup:
   * With pyproject.toml (recommended):
   ```bash
   pip install .
   ```
   * Or with setup.py:
   ```bash
   python setup.py install
   ```

## Usage

### Basic Command
```bash
codeconcat <target_path> [options]
```
* `<target_path>` (default = .) is the folder to scan
* For help:
```bash
codeconcat --help
```

### GitHub Usage (Optional)

If you want to clone and parse a GitHub repo (public or private):
```bash
codeconcat --github https://github.com/User/Repo.git --docs --merge-docs
```

If it's a private repo, you can provide a token:
```bash
codeconcat --github https://github.com/User/PrivateRepo.git \
           --github-token MY_PERSONAL_TOKEN
```

### Common Flags

| Flag | Description |
|------|-------------|
| --docs | Enable doc extraction (.md, .rst, .txt, .rmd) |
| --merge-docs | Merge docs into the same output file as code |
| --format | markdown (default) or json |
| --output | Output file name (default: code_concat_output.md) |
| --include-languages | Limit to certain languages (e.g., python javascript) |
| --exclude-languages | Exclude certain languages (e.g., cpp) |
| --exclude | Ignore paths/patterns (e.g., node_modules __pycache__) |
| --max-workers | Concurrency threads (default 4) |
| --github | Clone and parse a GitHub repo |
| --github-token | Personal access token if it's a private GitHub repo |
| --no-tree | Disable folder tree generation (enabled by default) |
| --no-copy | Disable copying output to clipboard (enabled by default) |

### Example
```bash
codeconcat . --docs --merge-docs --format=markdown --output=all_in_one.md
```
* Recursively scans the current directory for code + doc files
* Generates a folder tree of the project structure
* Merges everything into all_in_one.md in Markdown format
* Copies the final output to your system clipboard

## Configuration

CodeConCat merges CLI flags with a local .codeconcat.yml (if present). Example:

```yaml
exclude_paths:
  - "*.test.*"
  - "node_modules"

include_languages:
  - python
  - r

docs: true
merge_docs: false

output: "my_concat_output.md"
format: "markdown"

custom_extension_map:
  pyx: "cython"

max_workers: 4
```

* CLI arguments override the .codeconcat.yml values if they conflict
* custom_extension_map can define extra mappings (e.g., .pyx → cython)

## Concurrency

To speed up the parsing of large projects, CodeConCat uses multithreading:
* Local Collector uses concurrency to filter out excludes
* File Parsing uses concurrency to parse code
* Doc Extraction uses concurrency to read doc files in parallel

You can adjust the number of threads with `--max-workers <N>`.

## Doc Extraction

When --docs is enabled (or docs: true in the config):
1. All files with recognized doc extensions (.md, .rst, .txt, .rmd) are collected
2. They're parsed in parallel to produce doc data
3. If --merge-docs is specified (or merge_docs: true), the doc content is appended in the same output file after the code sections

## Examples

1. Only Python and JS:
```bash
codeconcat my_project/ \
  --include-languages python javascript \
  --docs --output=code_and_docs.md
```

2. JSON Output:
```bash
codeconcat . --format=json --output=project.json
```

3. Excluding Certain Paths:
```bash
codeconcat . --exclude node_modules build dist
```

4. GitHub + Token:
```bash
codeconcat --github https://github.com/YourUser/PrivateRepo.git \
           --github-token YOUR_GITHUB_PAT \
           --docs
```

## Testing

If you have a tests/ folder (with Pytest-based tests):
```bash
pytest --maxfail=1 --disable-warnings -q
```
* This runs the unit tests (e.g., checking collectors, parsers, writer outputs, etc.)

## Project Structure

```
codeconcat/
├─ main.py
├─ version.py
├─ types.py
├─ collector/
│   ├─ local_collector.py
│   └─ github_collector.py
├─ parser/
│   ├─ file_parser.py
│   ├─ doc_extractor.py
│   └─ language_parsers/
├─ transformer/
│   └─ annotator.py
├─ writer/
│   ├─ markdown_writer.py
│   └─ json_writer.py
└─ config/
    └─ config_loader.py
```

## Contributing

1. Fork the repository
2. Create a branch for your feature or bugfix
3. Open a Pull Request referencing issues or describing your changes
4. Ensure tests pass (pytest)

## License

This project is licensed under the MIT License. See the LICENSE file for details.

---
Thank you for using CodeConCat! If you have any questions or suggestions, please open an issue or reach out. Happy coding!
