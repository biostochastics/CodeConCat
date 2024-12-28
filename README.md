# CodeConCat

CodeConCat is a lightweight command-line tool (CLI) that aggregates code and (optionally) documentation from a local folder (or GitHub in the future). It annotates source files, merges doc files, and produces an LLM-friendly output in Markdown or JSON. The tool supports multiple languages (Python, JavaScript/TypeScript, R, Julia, C/C++, etc.) and can run with concurrency to handle larger projects more efficiently.

## Table of Contents

1. Overview
2. Features
3. Requirements
4. Installation
5. Usage
6. Configuration
7. Concurrency
8. Doc Extraction
9. Examples
10. Testing
11. Project Structure (Example)
12. Contributing
13. License

## Overview

CodeConCat scans your local directory for code files (Python, JS/TS, C/C++, R, Julia, etc.), filters them based on language or ignore patterns, parses them to identify top-level constructs (e.g., functions, classes), and then outputs an annotated version in a single file. If you enable docs mode, it also includes documentation files like .md, .rst, .txt, or .rmd.

Use Case: If you want to feed your code (and possibly docs) to a Large Language Model (LLM) for analysis, CodeConCat can compile them into a single, organized snapshot.

## Features

* **Multi-Language Parsing**: Basic regex-based detection for functions/classes in Python, JS/TS, R, Julia, C/C++ (extendable).
* **Documentation Extraction**: Merge .md, .rst, .txt, .rmd files alongside code into one output.
* **Configurable**: Define includes/excludes, doc extension, concurrency, output format, etc. in .codeconcat.yml or pass CLI flags.
* **Concurrency**: Uses Python's ThreadPoolExecutor to parse files in parallel, improving performance on large projects.
* **Multiple Output Formats**:
  * Markdown: Annotated code blocks with headings and code fences.
  * JSON: Structured data (one object for each file, plus docs if included).
* **GitHub Collector (Planned)**: A placeholder for fetching files from a public GitHub repo and then running the same logic.

## Requirements

* Python 3.8+
* pyyaml (if you want .codeconcat.yml support)
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

This will install the codeconcat CLI command and required dependencies.

## Usage

### Basic Command

```bash
codeconcat <target_path> [options]
```

* `<target_path>` (default = .) is the folder to scan.
* For help, run:
```bash
codeconcat --help
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

### Example

```bash
codeconcat . --docs --merge-docs --format=markdown --output=all_in_one.md
```
* Recursively scans the current directory for code + doc files
* Merges everything into all_in_one.md in Markdown format

## Configuration

CodeConCat merges CLI flags with a local .codeconcat.yml (if present). Example .codeconcat.yml:

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
* custom_extension_map can define extra mappings (e.g., .pyx -> cython)

## Concurrency

To speed up the parsing of large projects, CodeConCat uses multithreading:
* Local Collector uses concurrency to filter out excludes
* File Parsing uses concurrency to parse code
* Doc Extraction uses concurrency to read doc files in parallel

You can adjust the number of threads with `--max-workers <N>`.

*Note: Python's GIL can limit speed gains for CPU-bound tasks, but reading files in parallel often improves I/O throughput on large projects.*

## Doc Extraction

When `--docs` is enabled (or `docs: true` in the config):
1. All files with recognized doc extensions (.md, .rst, .txt, .rmd) are collected
2. They're parsed in parallel to produce doc data
3. If `--merge-docs` is specified (or `merge_docs: true`), the doc content is appended in the same output file after the code sections. Otherwise, you could adapt the code to write them to a separate docs file.

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
This produces a JSON structure with code and docs arrays.

3. Excluding Certain Paths:
```bash
codeconcat . --exclude node_modules build dist
```

## Testing

If you have a tests/ folder (with Pytest-based tests):

```bash
pytest --maxfail=1 --disable-warnings -q
```

* This will run the unit tests (e.g., checking collectors, parsers, writer outputs, etc.)

## Project Structure (Example)

Below is an example layout:

```
codeconcat/
│   main.py                  # CLI entry
│   version.py               # Semantic version
│   types.py                 # Data classes
│
├─ collector/
│   ├─ local_collector.py
│   └─ github_collector.py   # Stub for future GitHub fetching
├─ parser/
│   ├─ file_parser.py
│   ├─ doc_extractor.py
│   └─ language_parsers/
│       ├─ python_parser.py
│       ├─ js_ts_parser.py
│       ├─ r_parser.py
│       └─ julia_parser.py
├─ transformer/
│   └─ annotator.py
├─ writer/
│   ├─ markdown_writer.py
│   └─ json_writer.py
└─ config/
    └─ config_loader.py
```

You can adapt or expand as needed.

## Contributing

1. Fork the repository
2. Create a branch for your feature or bugfix
3. Open a Pull Request explaining your changes, references to issues, etc.
4. Ensure tests pass (pytest)

## License

This project is licensed under the MIT License. See the LICENSE file for details.

Thank you for using CodeConCat! If you have any questions or suggestions, please open an issue or reach out. Happy coding!
