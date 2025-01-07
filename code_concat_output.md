# CodeConCat Output

# CodeConcat AI-Friendly Code Summary

This document contains a structured representation of a codebase, organized for AI analysis.

## Repository Structure
```
Total code files: 41
Documentation files: 0

File types:
- /LICENSE: 1 files
- egg-info/PKG-INFO: 1 files
- py: 39 files
```

## Code Organization
The code is organized into sections, each prefixed with clear markers:
- Directory markers show file organization
- File headers contain metadata and imports
- Annotations provide context about code purpose
- Documentation sections contain project documentation

## Navigation
- Each file begins with '---FILE:' followed by its path
- Each section is clearly delimited with markdown headers
- Code blocks are formatted with appropriate language tags

## Content Summary

---
Begin code content below:
## Directory Structure
```
└── .
    ├── LICENSE
    ├── setup.py
    ├── codeconcat.egg-info
    │   └── PKG-INFO
    └── codeconcat
        ├── version.py
        ├── __init__.py
        ├── base_types.py
        ├── main.py
        ├── config
        │   ├── config_loader.py
        │   └── __init__.py
        ├── transformer
        │   ├── __init__.py
        │   └── annotator.py
        ├── processor
        │   ├── security_types.py
        │   ├── content_processor.py
        │   ├── token_counter.py
        │   ├── __init__.py
        │   └── security_processor.py
        ├── tests
        │   └── test_end_to_end.py
        ├── collector
        │   ├── github_collector.py
        │   ├── __init__.py
        │   └── local_collector.py
        ├── parser
        │   ├── doc_extractor.py
        │   ├── file_parser.py
        │   ├── __init__.py
        │   └── language_parsers
        │       ├── csharp_parser.py
        │       ├── c_parser.py
        │       ├── julia_parser.py
        │       ├── __init__.py
        │       ├── php_parser.py
        │       ├── rust_parser.py
        │       ├── js_ts_parser.py
        │       ├── python_parser.py
        │       ├── base_parser.py
        │       ├── java_parser.py
        │       ├── cpp_parser.py
        │       ├── r_parser.py
        │       └── go_parser.py
        └── writer
            ├── markdown_writer.py
            ├── __init__.py
            ├── xml_writer.py
            ├── ai_context.py
            └── json_writer.py
```

## Code Files

### File: ./LICENSE
#### Summary
```
File: LICENSE
Language: unknown
```

```unknown
   1 | MIT License
   3 | Copyright (c) 2024 Sergey Kornilov for Biostochastics, LLC
   5 | Permission is hereby granted, free of charge, to any person obtaining a copy
   6 | of this software and associated documentation files (the "Software"), to deal
   7 | in the Software without restriction, including without limitation the rights
   8 | to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   9 | copies of the Software, and to permit persons to whom the Software is
  10 | furnished to do so, subject to the following conditions:
  12 | The above copyright notice and this permission notice shall be included in all
  13 | copies or substantial portions of the Software.
  15 | THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
  16 | IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
  17 | FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
  18 | AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
  19 | LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
  20 | OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
  21 | SOFTWARE.
```

---
### File: ./setup.py
#### Summary
```
File: setup.py
Language: python
```

```python
   1 | import os
   2 | import re
   4 | import setuptools
   8 | def get_version():
   9 |     version_file = os.path.join(
  10 |         os.path.dirname(__file__), "codeconcat", "version.py"
  11 |     )
  12 |     with open(version_file, "r", encoding="utf-8") as f:
  13 |         content = f.read()
  14 |         match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
  15 |         if match:
  16 |             return match.group(1)
  17 |     return "0.0.0"
  20 | setuptools.setup(
  21 |     name="codeconcat",
  22 |     version=get_version(),
  23 |     author="Your Name",
  24 |     author_email="you@example.com",
  25 |     description="An LLM-friendly code aggregator and doc extractor",
  26 |     packages=setuptools.find_packages(),
  27 |     install_requires=[
  28 |         "pyyaml>=5.0",
  29 |         "pyperclip>=1.8.0",
  30 |     ],
  31 |     python_requires=">=3.8",
  32 |     entry_points={
  33 |         "console_scripts": ["codeconcat=codeconcat.main:cli_entry_point"]
  34 |     },
  35 | )
```

---
### File: ./codeconcat.egg-info/PKG-INFO
#### Summary
```
File: PKG-INFO
Language: unknown
```

```unknown
   1 | Metadata-Version: 2.1
   2 | Name: codeconcat
   3 | Version: 0.4.1
   4 | Summary: An LLM-friendly code aggregator and doc extractor
   5 | Author: Your Name
   6 | Author-email: you@example.com
   7 | Requires-Python: >=3.8
   8 | License-File: LICENSE
   9 | Requires-Dist: pyyaml>=5.0
  10 | Requires-Dist: pyperclip>=1.8.0
```

---
### File: ./codeconcat/version.py
#### Summary
```
File: version.py
Language: python
```

```python
   3 | __version__ = "0.5.2"
```

---
### File: ./codeconcat/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/base_types.py
#### Summary
```
File: base_types.py
Language: python
```

```python
   2 | base_types.py
   4 | Holds data classes and typed structures used throughout CodeConCat.
   8 | from dataclasses import dataclass, field
   9 | from typing import Any, Dict, List, Optional
  11 | PROGRAMMING_QUOTES = [
  12 |     '"Clean code always looks like it was written by someone who cares." - Robert C. Martin',
  13 |     '"First, solve the problem. Then write the code." - John Johnson',
  14 |     '"Any fool can write code that a computer can understand. Good programmers write code that humans can understand." - Martin Fowler',
  15 |     "\"Programming isn't about what you know; it's about what you can figure out.\" - Chris Pine",
  16 |     '"Code is like humor. When you have to explain it, it\'s bad." - Cory House',
  17 |     '"The most important property of a program is whether it accomplishes the intention of its user." - C.A.R. Hoare',
  18 |     "\"Good code is its own best documentation. As you're about to add a comment, ask yourself, 'How can I improve the code so that this comment isn't needed?'\" - Steve McConnell",
  19 |     '"Measuring programming progress by lines of code is like measuring aircraft building progress by weight." - Bill Gates',
  20 |     '"Talk is cheap. Show me the code." - Linus Torvalds',
  21 |     '"Truth can only be found in one place: the code." - Robert C. Martin',
  22 |     '"It is not enough for code to work." - Robert C. Martin',
  23 |     '"Debugging is twice as hard as writing the code in the first place. Therefore, if you write the code as cleverly as possible, you are, by definition, not smart enough to debug it." - Brian W. Kernighan',
  24 |     '"Sometimes it pays to stay in bed on Monday rather than spending the rest of the week debugging Monday\'s code." - Dan Salomon',
  25 |     '"Always code as if the guy who ends up maintaining your code will be a violent psychopath who knows where you live." - Rick Osborne',
  26 | ]
  29 | @dataclass
  30 | class SecurityIssue:
  33 |     line_number: int
  34 |     line_content: str
  35 |     issue_type: str
  36 |     severity: str
  37 |     description: str
  40 | @dataclass
  41 | class TokenStats:
  44 |     gpt3_tokens: int
  45 |     gpt4_tokens: int
  46 |     davinci_tokens: int
  47 |     claude_tokens: int
  50 | @dataclass
  51 | class Declaration:
  53 |     Represents a top-level construct in a code file, e.g. a function, class, or symbol.
  54 |     Kinds can be: 'function', 'class', 'struct', 'symbol'
  57 |     kind: str
  58 |     name: str
  59 |     start_line: int
  60 |     end_line: int
  63 | @dataclass
  64 | class ParsedFileData:
  66 |     Parsed output of a single code file.
  69 |     file_path: str
  70 |     language: str
  71 |     content: str
  72 |     declarations: List[Declaration] = field(default_factory=list)
  73 |     token_stats: Optional[TokenStats] = None
  74 |     security_issues: List[SecurityIssue] = field(default_factory=list)
  77 | @dataclass
  78 | class AnnotatedFileData:
  80 |     A file's annotated content, ready to be written (Markdown/JSON).
  83 |     file_path: str
  84 |     language: str
  85 |     annotated_content: str
  86 |     content: str = ""
  87 |     summary: str = ""
  88 |     tags: List[str] = field(default_factory=list)
  91 | @dataclass
  92 | class ParsedDocData:
  94 |     Represents a doc file, storing raw text + file path + doc type (md, rst, etc.).
  97 |     file_path: str
  98 |     doc_type: str
  99 |     content: str
 102 | @dataclass
 103 | class CodeConCatConfig:
 105 |     Global configuration object. Merged from CLI args + .codeconcat.yml.
 107 |     Fields:
 108 |       - target_path: local directory or placeholder for GitHub
 109 |       - github_url: optional GitHub repository URL
 110 |       - github_token: personal access token for private repos
 111 |       - github_ref: optional GitHub reference (branch/tag)
 112 |       - include_languages / exclude_languages
 113 |       - include_paths / exclude_paths: patterns for including/excluding
 114 |       - extract_docs: whether to parse docs
 115 |       - merge_docs: whether to merge doc content into the same output
 116 |       - doc_extensions: list of recognized doc file extensions
 117 |       - custom_extension_map: user-specified extension→language
 118 |       - output: final file name
 119 |       - format: 'markdown' or 'json'
 120 |       - max_workers: concurrency
 121 |       - disable_tree: whether to disable directory structure
 122 |       - disable_copy: whether to disable copying output
 123 |       - disable_annotations: whether to disable annotations
 124 |       - disable_symbols: whether to disable symbol extraction
 125 |       - include_file_summary: whether to include file summaries
 126 |       - include_directory_structure: whether to show directory structure
 127 |       - remove_comments: whether to remove comments from output
 128 |       - remove_empty_lines: whether to remove empty lines
 129 |       - show_line_numbers: whether to show line numbers
 133 |     target_path: str = "."
 134 |     github_url: Optional[str] = None
 135 |     github_token: Optional[str] = None
 136 |     github_ref: Optional[str] = None
 139 |     include_languages: List[str] = field(default_factory=list)
 140 |     exclude_languages: List[str] = field(default_factory=list)
 143 |     include_paths: List[str] = field(default_factory=list)
 144 |     exclude_paths: List[str] = field(default_factory=list)
 147 |     extract_docs: bool = False
 148 |     merge_docs: bool = False
 149 |     doc_extensions: List[str] = field(default_factory=lambda: [".md", ".rst", ".txt", ".rmd"])
 152 |     custom_extension_map: Dict[str, str] = field(default_factory=dict)
 155 |     output: str = "code_concat_output.md"
 156 |     format: str = "markdown"
 157 |     max_workers: int = 4
 160 |     disable_tree: bool = False
 161 |     disable_copy: bool = False
 162 |     disable_annotations: bool = False
 163 |     disable_symbols: bool = False
 164 |     disable_ai_context: bool = False
 167 |     include_file_summary: bool = True
 168 |     include_directory_structure: bool = True
 169 |     remove_comments: bool = False
 170 |     remove_empty_lines: bool = False
 171 |     show_line_numbers: bool = False
```

---
### File: ./codeconcat/main.py
#### Summary
```
File: main.py
Language: python
```

```python
   1 | import argparse
   2 | import logging
   3 | import os
   4 | import sys
   5 | from typing import List
   7 | from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedDocData
   8 | from codeconcat.collector.github_collector import collect_github_files
   9 | from codeconcat.collector.local_collector import (
  10 |     collect_local_files,
  11 |     should_include_file,
  12 |     should_skip_dir,
  13 | )
  14 | from codeconcat.config.config_loader import load_config
  15 | from codeconcat.parser.doc_extractor import extract_docs
  16 | from codeconcat.parser.file_parser import parse_code_files
  17 | from codeconcat.transformer.annotator import annotate
  18 | from codeconcat.writer.json_writer import write_json
  19 | from codeconcat.writer.markdown_writer import write_markdown
  20 | from codeconcat.writer.xml_writer import write_xml
  23 | logger = logging.getLogger("codeconcat")
  24 | logger.setLevel(logging.WARNING)
  27 | def cli_entry_point():
  28 |     parser = argparse.ArgumentParser(
  29 |         prog="codeconcat",
  30 |         description="CodeConCat - An LLM-friendly code aggregator and doc extractor.",
  31 |     )
  33 |     parser.add_argument("target_path", nargs="?", default=".")
  34 |     parser.add_argument(
  35 |         "--github", help="GitHub URL or shorthand (e.g., 'owner/repo')", default=None
  36 |     )
  37 |     parser.add_argument("--github-token", help="GitHub personal access token", default=None)
  38 |     parser.add_argument("--ref", help="Branch, tag, or commit hash for GitHub repo", default=None)
  40 |     parser.add_argument("--docs", action="store_true", help="Enable doc extraction")
  41 |     parser.add_argument(
  42 |         "--merge-docs", action="store_true", help="Merge doc content with code output"
  43 |     )
  45 |     parser.add_argument("--output", default="code_concat_output.md", help="Output file name")
  46 |     parser.add_argument(
  47 |         "--format", choices=["markdown", "json", "xml"], default="markdown", help="Output format"
  48 |     )
  50 |     parser.add_argument("--include", nargs="*", default=[], help="Glob patterns to include")
  51 |     parser.add_argument("--exclude", nargs="*", default=[], help="Glob patterns to exclude")
  52 |     parser.add_argument(
  53 |         "--include-languages", nargs="*", default=[], help="Only include these languages"
  54 |     )
  55 |     parser.add_argument(
  56 |         "--exclude-languages", nargs="*", default=[], help="Exclude these languages"
  57 |     )
  59 |     parser.add_argument("--max-workers", type=int, default=4, help="Number of worker threads")
  60 |     parser.add_argument("--init", action="store_true", help="Initialize default configuration file")
  62 |     parser.add_argument(
  63 |         "--no-tree", action="store_true", help="Disable folder tree generation (enabled by default)"
  64 |     )
  65 |     parser.add_argument(
  66 |         "--no-copy",
  67 |         action="store_true",
  68 |         help="Disable copying output to clipboard (enabled by default)",
  69 |     )
  70 |     parser.add_argument(
  71 |         "--no-ai-context", action="store_true", help="Disable AI context generation"
  72 |     )
  73 |     parser.add_argument("--no-annotations", action="store_true", help="Disable code annotations")
  74 |     parser.add_argument("--no-symbols", action="store_true", help="Disable symbol extraction")
  75 |     parser.add_argument("--debug", action="store_true", help="Enable debug logging")
  77 |     args = parser.parse_args()
  80 |     if args.debug:
  81 |         logger.setLevel(logging.DEBUG)
  83 |         for name in logging.root.manager.loggerDict:
  84 |             if name.startswith("codeconcat"):
  85 |                 logging.getLogger(name).setLevel(logging.DEBUG)
  88 |     if not logger.handlers:
  89 |         ch = logging.StreamHandler()
  90 |         ch.setLevel(logging.DEBUG if args.debug else logging.WARNING)
  91 |         formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  92 |         ch.setFormatter(formatter)
  93 |         logger.addHandler(ch)
  95 |     logger.debug("Debug logging enabled")
  98 |     if args.init:
  99 |         create_default_config()
 100 |         print("[CodeConCat] Created default configuration file: .codeconcat.yml")
 101 |         sys.exit(0)
 104 |     cli_args = vars(args)
 105 |     logging.debug("CLI args: %s", cli_args)  # Debug print
 106 |     config = load_config(cli_args)
 108 |     try:
 109 |         run_codeconcat(config)
 110 |     except Exception as e:
 111 |         print(f"[CodeConCat] Error: {str(e)}", file=sys.stderr)
 112 |         sys.exit(1)
 115 | def create_default_config():
 117 |     if os.path.exists(".codeconcat.yml"):
 118 |         print("Configuration file already exists. Remove it first to create a new one.")
 119 |         return
 121 |     config_content = """# CodeConCat Configuration
 124 | include_paths:
 128 | exclude_paths:
 130 |   - "**/*.{yml,yaml}"
 131 |   - "**/.codeconcat.yml"
 132 |   - "**/.github/*.{yml,yaml}"
 135 |   - "**/tests/**"
 136 |   - "**/test_*.py"
 137 |   - "**/*_test.py"
 140 |   - "**/build/**"
 141 |   - "**/dist/**"
 142 |   - "**/__pycache__/**"
 143 |   - "**/*.{pyc,pyo,pyd}"
 144 |   - "**/.pytest_cache/**"
 145 |   - "**/.coverage"
 146 |   - "**/htmlcov/**"
 149 |   - "**/*.{md,rst,txt}"
 150 |   - "**/LICENSE*"
 151 |   - "**/README*"
 154 | include_languages:
 158 | exclude_languages:
 163 | output: code_concat_output.md
 164 | format: markdown  # or json, xml
 167 | extract_docs: false
 168 | merge_docs: false
 169 | disable_tree: false
 170 | disable_copy: false
 171 | disable_annotations: false
 172 | disable_symbols: false
 175 | include_file_summary: true
 176 | include_directory_structure: true
 177 | remove_comments: true
 178 | remove_empty_lines: true
 179 | show_line_numbers: true
 182 | max_workers: 4
 183 | custom_extension_map:
 188 |     with open(".codeconcat.yml", "w") as f:
 189 |         f.write(config_content)
 191 |     print("[CodeConCat] Created default configuration file: .codeconcat.yml")
 194 | def generate_folder_tree(root_path: str, config: CodeConCatConfig) -> str:
 196 |     Walk the directory tree starting at root_path and return a string that represents the folder structure.
 197 |     Respects exclusion patterns from the config.
 199 |     from codeconcat.collector.local_collector import should_include_file, should_skip_dir
 201 |     lines = []
 202 |     for root, dirs, files in os.walk(root_path):
 204 |         if should_skip_dir(root, config.exclude_paths):
 205 |             dirs[:] = []  # Clear dirs to prevent descending into this directory
 206 |             continue
 208 |         level = root.replace(root_path, "").count(os.sep)
 209 |         indent = "    " * level
 210 |         folder_name = os.path.basename(root) or root_path
 211 |         lines.append(f"{indent}{folder_name}/")
 214 |         included_files = [f for f in files if should_include_file(os.path.join(root, f), config)]
 216 |         sub_indent = "    " * (level + 1)
 217 |         for f in sorted(included_files):
 218 |             lines.append(f"{sub_indent}{f}")
 221 |         dirs[:] = [
 222 |             d for d in dirs if not should_skip_dir(os.path.join(root, d), config.exclude_paths)
 223 |         ]
 224 |         dirs.sort()  # Sort directories for consistent output
 226 |     return "\n".join(lines)
 229 | def run_codeconcat(config: CodeConCatConfig):
 233 |     if config.github_url:
 234 |         code_files = collect_github_files(config)
 235 |     else:
 236 |         code_files = collect_local_files(config.target_path, config)
 239 |     folder_tree_str = ""
 240 |     if not config.disable_tree:
 241 |         folder_tree_str = generate_folder_tree(config.target_path, config)
 244 |     parsed_files = parse_code_files([f.file_path for f in code_files], config)
 247 |     docs = []
 248 |     if config.extract_docs:
 249 |         docs = extract_docs([f.file_path for f in code_files], config)
 252 |     annotated_files = []
 253 |     if not config.disable_annotations:
 255 |         for file in parsed_files:
 256 |             annotated = annotate(file, config)
 257 |             annotated_files.append(annotated)
 258 |     else:
 260 |         for file in parsed_files:
 261 |             annotated_files.append(
 262 |                 AnnotatedFileData(
 263 |                     file_path=file.file_path,
 264 |                     language=file.language,
 265 |                     content=file.content,
 266 |                     annotated_content=file.content,
 267 |                     summary="",
 268 |                     tags=[],
 269 |                 )
 270 |             )
 273 |     if config.format == "markdown":
 274 |         output = write_markdown(annotated_files, docs, config, folder_tree_str)
 275 |     elif config.format == "json":
 276 |         output = write_json(annotated_files, docs, config, folder_tree_str)
 277 |     elif config.format == "xml":
 278 |         output = write_xml(
 279 |             parsed_files, docs, {f.file_path: f for f in annotated_files}, folder_tree_str
 280 |         )
 283 |     if not config.disable_copy:
 284 |         try:
 285 |             import pyperclip
 287 |             pyperclip.copy(output)
 288 |             print("[CodeConCat] Output copied to clipboard")
 289 |         except ImportError:
 290 |             print("[CodeConCat] Warning: pyperclip not installed, skipping clipboard copy")
 291 |         except Exception as e:
 292 |             print(f"[CodeConCat] Warning: Failed to copy to clipboard: {str(e)}")
 295 | def main():
 296 |     cli_entry_point()
 299 | if __name__ == "__main__":
 300 |     main()
```

---
### File: ./codeconcat/config/config_loader.py
#### Summary
```
File: config_loader.py
Language: python
```

```python
   1 | import logging
   2 | import os
   3 | from typing import Any, Dict
   5 | import yaml
   7 | from codeconcat.base_types import CodeConCatConfig
  10 | def load_config(cli_args: Dict[str, Any]) -> CodeConCatConfig:
  12 |     Load and merge configuration from .codeconcat.yml (if exists) and CLI args.
  13 |     CLI args take precedence over the config file.
  16 |     config_dict = {
  17 |         "target_path": cli_args.get("target_path", "."),
  18 |         "github_url": cli_args.get("github"),
  19 |         "github_token": cli_args.get("github_token"),
  20 |         "github_ref": cli_args.get("ref"),
  21 |         "include_languages": cli_args.get("include_languages", []),
  22 |         "exclude_languages": cli_args.get("exclude_languages", []),
  23 |         "include_paths": cli_args.get("include", []),
  24 |         "exclude_paths": cli_args.get("exclude", []),
  25 |         "extract_docs": cli_args.get("docs", False),
  26 |         "merge_docs": cli_args.get("merge_docs", False),
  27 |         "output": cli_args.get("output", "code_concat_output.md"),
  28 |         "format": cli_args.get("format", "markdown"),
  29 |         "max_workers": cli_args.get("max_workers", 4),
  30 |         "disable_tree": cli_args.get("no_tree", False),
  31 |         "disable_copy": cli_args.get("no_copy", False),
  32 |         "disable_annotations": cli_args.get("no_annotations", False),
  33 |         "disable_symbols": cli_args.get("no_symbols", False),
  34 |         "disable_ai_context": cli_args.get("no_ai_context", False),
  35 |     }
  38 |     yaml_config = {}
  39 |     target_path = cli_args.get("target_path", ".")
  40 |     config_path = os.path.join(target_path, ".codeconcat.yml")
  41 |     if os.path.exists(config_path):
  42 |         try:
  43 |             with open(config_path, "r", encoding="utf-8") as f:
  44 |                 yaml_config = yaml.safe_load(f) or {}
  45 |         except Exception as e:
  46 |             logging.error(f"Failed to load .codeconcat.yml: {e}")
  47 |             yaml_config = {}
  50 |     merged = {**yaml_config, **config_dict}
  52 |     try:
  53 |         return CodeConCatConfig(**merged)
  54 |     except TypeError as e:
  55 |         logging.error(f"Failed to create config: {e}")
  56 |         logging.error(
  57 |             f"Available fields in CodeConCatConfig: {CodeConCatConfig.__dataclass_fields__.keys()}"
  58 |         )
  59 |         logging.error(f"Attempted fields: {merged.keys()}")
  60 |         raise
  63 | def read_config_file(path: str) -> Dict[str, Any]:
  64 |     if not os.path.exists(path):
  65 |         return {}
  66 |     try:
  67 |         with open(path, "r", encoding="utf-8") as f:
  68 |             data = yaml.safe_load(f)
  69 |             if isinstance(data, dict):
  70 |                 return data
  71 |     except Exception:
  72 |         pass
  73 |     return {}
  76 | def apply_dict_to_config(data: Dict[str, Any], config: CodeConCatConfig) -> None:
  77 |     for key, value in data.items():
  78 |         if hasattr(config, key):
  79 |             if key == "custom_extension_map" and isinstance(value, dict):
  80 |                 config.custom_extension_map.update(value)
  81 |             else:
  82 |                 setattr(config, key, value)
```

---
### File: ./codeconcat/config/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/transformer/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/transformer/annotator.py
#### Summary
```
File: annotator.py
Language: python
```

```python
   1 | from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedFileData
   4 | def annotate(parsed_data: ParsedFileData, config: CodeConCatConfig) -> AnnotatedFileData:
   5 |     pieces = []
   6 |     pieces.append(f"## File: {parsed_data.file_path}\n")
   9 |     functions = []
  10 |     classes = []
  11 |     structs = []
  12 |     symbols = []
  14 |     for decl in parsed_data.declarations:
  15 |         if decl.kind == "function":
  16 |             functions.append(decl.name)
  17 |         elif decl.kind == "class":
  18 |             classes.append(decl.name)
  19 |         elif decl.kind == "struct":
  20 |             structs.append(decl.name)
  21 |         elif decl.kind == "symbol":
  22 |             symbols.append(decl.name)
  25 |     if functions:
  26 |         pieces.append("### Functions\n")
  27 |         for name in functions:
  28 |             pieces.append(f"- {name}\n")
  30 |     if classes:
  31 |         pieces.append("### Classes\n")
  32 |         for name in classes:
  33 |             pieces.append(f"- {name}\n")
  35 |     if structs:
  36 |         pieces.append("### Structs\n")
  37 |         for name in structs:
  38 |             pieces.append(f"- {name}\n")
  40 |     if symbols:
  41 |         pieces.append("### Symbols\n")
  42 |         for name in symbols:
  43 |             pieces.append(f"- {name}\n")
  45 |     pieces.append(f"```{parsed_data.language}\n{parsed_data.content}\n```\n")
  48 |     summary_parts = []
  49 |     if functions:
  50 |         summary_parts.append(f"{len(functions)} functions")
  51 |     if classes:
  52 |         summary_parts.append(f"{len(classes)} classes")
  53 |     if structs:
  54 |         summary_parts.append(f"{len(structs)} structs")
  55 |     if symbols:
  56 |         summary_parts.append(f"{len(symbols)} symbols")
  58 |     summary = f"Contains {', '.join(summary_parts)}" if summary_parts else "No declarations found"
  61 |     tags = []
  62 |     if functions:
  63 |         tags.append("has_functions")
  64 |     if classes:
  65 |         tags.append("has_classes")
  66 |     if structs:
  67 |         tags.append("has_structs")
  68 |     if symbols:
  69 |         tags.append("has_symbols")
  70 |     tags.append(parsed_data.language)
  72 |     return AnnotatedFileData(
  73 |         file_path=parsed_data.file_path,
  74 |         language=parsed_data.language,
  75 |         content=parsed_data.content,
  76 |         annotated_content="".join(pieces),
  77 |         summary=summary,
  78 |         tags=tags,
  79 |     )
```

---
### File: ./codeconcat/processor/security_types.py
#### Summary
```
File: security_types.py
Language: python
```

```python
   3 | from dataclasses import dataclass
   6 | @dataclass
   7 | class SecurityIssue:
  10 |     line_number: int
  11 |     line_content: str
  12 |     issue_type: str
  13 |     severity: str
  14 |     description: str
```

---
### File: ./codeconcat/processor/content_processor.py
#### Summary
```
File: content_processor.py
Language: python
```

```python
   3 | import os
   4 | from typing import List
   6 | from codeconcat.base_types import CodeConCatConfig, ParsedFileData, SecurityIssue
   7 | from codeconcat.processor.token_counter import TokenStats
  10 | def process_file_content(content: str, config: CodeConCatConfig) -> str:
  12 |     lines = content.split("\n")
  13 |     processed_lines = []
  15 |     for i, line in enumerate(lines):
  17 |         if config.remove_empty_lines and not line.strip():
  18 |             continue
  21 |         if config.remove_comments:
  22 |             stripped = line.strip()
  23 |             if (
  24 |                 stripped.startswith("#")
  25 |                 or stripped.startswith("//")
  26 |                 or stripped.startswith("/*")
  27 |                 or stripped.startswith("*")
  28 |                 or stripped.startswith('"""')
  29 |                 or stripped.startswith("'''")
  30 |                 or stripped.endswith("*/")
  31 |             ):
  32 |                 continue
  35 |         if config.show_line_numbers:
  36 |             line = f"{i+1:4d} | {line}"
  38 |         processed_lines.append(line)
  40 |     return "\n".join(processed_lines)
  43 | def generate_file_summary(file_data: ParsedFileData) -> str:
  45 |     summary = []
  46 |     summary.append(f"File: {os.path.basename(file_data.file_path)}")
  47 |     summary.append(f"Language: {file_data.language}")
  49 |     if file_data.token_stats:
  50 |         summary.append("Token Counts:")
  51 |         summary.append(f"  - GPT-3.5: {file_data.token_stats.gpt3_tokens:,}")
  52 |         summary.append(f"  - GPT-4: {file_data.token_stats.gpt4_tokens:,}")
  53 |         summary.append(f"  - Davinci: {file_data.token_stats.davinci_tokens:,}")
  54 |         summary.append(f"  - Claude: {file_data.token_stats.claude_tokens:,}")
  56 |     if file_data.security_issues:
  57 |         summary.append("\nSecurity Issues:")
  58 |         for issue in file_data.security_issues:
  59 |             summary.append(f"  - {issue.issue_type} (Line {issue.line_number})")
  60 |             summary.append(f"    {issue.line_content}")
  62 |     if file_data.declarations:
  63 |         summary.append("\nDeclarations:")
  64 |         for decl in file_data.declarations:
  65 |             summary.append(
  66 |                 f"  - {decl.kind}: {decl.name} (lines {decl.start_line}-{decl.end_line})"
  67 |             )
  69 |     return "\n".join(summary)
  72 | def generate_directory_structure(file_paths: List[str]) -> str:
  74 |     structure = {}
  75 |     for path in file_paths:
  76 |         parts = path.split(os.sep)
  77 |         current = structure
  78 |         for part in parts[:-1]:
  79 |             if part not in current:
  80 |                 current[part] = {}
  81 |             current = current[part]
  82 |         current[parts[-1]] = None
  84 |     def print_tree(node: dict, prefix: str = "", is_last: bool = True) -> List[str]:
  85 |         lines = []
  86 |         if node is None:
  87 |             return lines
  89 |         items = list(node.items())
  90 |         for i, (name, subtree) in enumerate(items):
  91 |             is_last_item = i == len(items) - 1
  92 |             lines.append(f"{prefix}{'└── ' if is_last_item else '├── '}{name}")
  93 |             if subtree is not None:
  94 |                 extension = "    " if is_last_item else "│   "
  95 |                 lines.extend(print_tree(subtree, prefix + extension, is_last_item))
  96 |         return lines
  98 |     return "\n".join(print_tree(structure))
```

---
### File: ./codeconcat/processor/token_counter.py
#### Summary
```
File: token_counter.py
Language: python
```

```python
   3 | from dataclasses import dataclass
   4 | from typing import Dict
   6 | import tiktoken
   9 | @dataclass
  10 | class TokenStats:
  13 |     gpt3_tokens: int
  14 |     gpt4_tokens: int
  15 |     davinci_tokens: int
  16 |     claude_tokens: int
  20 | _ENCODER_CACHE: Dict[str, tiktoken.Encoding] = {}
  23 | def get_encoder(model: str = "gpt-3.5-turbo") -> tiktoken.Encoding:
  25 |     if model not in _ENCODER_CACHE:
  26 |         _ENCODER_CACHE[model] = tiktoken.encoding_for_model(model)
  27 |     return _ENCODER_CACHE[model]
  30 | def count_tokens(text: str, model: str = "gpt-3.5-turbo") -> int:
  32 |     encoder = get_encoder(model)
  33 |     return len(encoder.encode(text))
  36 | def get_token_stats(text: str) -> TokenStats:
  38 |     return TokenStats(
  39 |         gpt3_tokens=count_tokens(text, "gpt-3.5-turbo"),
  40 |         gpt4_tokens=count_tokens(text, "gpt-4"),
  41 |         davinci_tokens=count_tokens(text, "text-davinci-003"),
  42 |         claude_tokens=int(len(text.encode("utf-8")) / 4),  # Rough approximation for Claude
  43 |     )
```

---
### File: ./codeconcat/processor/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python
   3 | from codeconcat.processor.content_processor import (
   4 |     generate_directory_structure,
   5 |     generate_file_summary,
   6 |     process_file_content,
   7 | )
   9 | __all__ = ["process_file_content", "generate_file_summary", "generate_directory_structure"]
```

---
### File: ./codeconcat/processor/security_processor.py
#### Summary
```
File: security_processor.py
Language: python
```

```python
   3 | import re
   4 | from typing import Any, Dict, List, Tuple
   6 | from codeconcat.processor.security_types import SecurityIssue
   9 | class SecurityProcessor:
  13 |     PATTERNS = {
  14 |         "aws_key": (
  15 |             r'(?i)aws[_\-\s]*(?:access)?[_\-\s]*key[_\-\s]*(?:id)?["\'\s:=]+[A-Za-z0-9/\+=]{20,}',
  16 |             "AWS Key",
  17 |         ),
  18 |         "aws_secret": (
  19 |             r'(?i)aws[_\-\s]*secret[_\-\s]*(?:access)?[_\-\s]*key["\'\s:=]+[A-Za-z0-9/\+=]{40,}',
  20 |             "AWS Secret Key",
  21 |         ),
  22 |         "github_token": (
  23 |             r'(?i)(?:github|gh)[_\-\s]*(?:token|key)["\'\s:=]+[A-Za-z0-9_\-]{36,}',
  24 |             "GitHub Token",
  25 |         ),
  26 |         "generic_api_key": (r'(?i)api[_\-\s]*key["\'\s:=]+[A-Za-z0-9_\-]{16,}', "API Key"),
  27 |         "generic_secret": (
  28 |             r'(?i)(?:secret|token|key|password|pwd)["\'\s:=]+[A-Za-z0-9_\-]{16,}',
  29 |             "Generic Secret",
  30 |         ),
  31 |         "private_key": (
  32 |             r"(?i)-----BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY[^-]*-----.*?-----END",
  33 |             "Private Key",
  34 |         ),
  35 |         "basic_auth": (
  36 |             r'(?i)(?:authorization|auth)\s*[:=]\s*["\']*basic\s+[A-Za-z0-9+/=]+["\']*',
  37 |             "Basic Authentication",
  38 |         ),
  39 |         "bearer_token": (
  40 |             r'(?i)(?:authorization|auth)\s*[:=]\s*["\']*bearer\s+[A-Za-z0-9._\-]+["\']*',
  41 |             "Bearer Token",
  42 |         ),
  43 |     }
  46 |     IGNORE_PATTERNS = [
  47 |         r"(?i)example|sample|test|dummy|fake|mock",
  48 |         r"your.*key.*here",
  49 |         r"xxx+",
  50 |         r"[A-Za-z0-9]{16,}\.example\.com",
  51 |     ]
  53 |     @classmethod
  54 |     def scan_content(cls, content: str, file_path: str) -> List[SecurityIssue]:
  56 |         Scan content for potential security issues.
  58 |         Args:
  59 |             content: The content to scan
  60 |             file_path: Path to the file being scanned (for context)
  62 |         Returns:
  63 |             List of SecurityIssue instances
  65 |         issues = []
  66 |         lines = content.split("\n")
  68 |         for line_num, line in enumerate(lines, 1):
  70 |             if not line.strip():
  71 |                 continue
  74 |             if any(re.search(pattern, line) for pattern in cls.IGNORE_PATTERNS):
  75 |                 continue
  78 |             for pattern_name, (pattern, issue_type) in cls.PATTERNS.items():
  79 |                 if re.search(pattern, line):
  81 |                     masked_line = cls._mask_sensitive_data(line, pattern)
  83 |                     issues.append(
  84 |                         SecurityIssue(
  85 |                             line_number=line_num,
  86 |                             line_content=masked_line,
  87 |                             issue_type=issue_type,
  88 |                             severity="HIGH",
  89 |                             description=f"Potential {issue_type} found in {file_path}",
  90 |                         )
  91 |                     )
  93 |         return issues
  95 |     @staticmethod
  96 |     def _mask_sensitive_data(line: str, pattern: str) -> str:
  99 |         def mask_match(match):
 100 |             return match.group()[:4] + "*" * (len(match.group()) - 8) + match.group()[-4:]
 102 |         return re.sub(pattern, mask_match, line)
 104 |     @classmethod
 105 |     def format_issues(cls, issues: List[SecurityIssue]) -> str:
 107 |         if not issues:
 108 |             return "No security issues found."
 110 |         formatted = ["Security Scan Results:", "=" * 20]
 111 |         for issue in issues:
 112 |             formatted.extend(
 113 |                 [
 114 |                     f"\nIssue Type: {issue.issue_type}",
 115 |                     f"Severity: {issue.severity}",
 116 |                     f"Line {issue.line_number}: {issue.line_content}",
 117 |                     f"Description: {issue.description}",
 118 |                     "-" * 20,
 119 |                 ]
 120 |             )
 122 |         return "\n".join(formatted)
```

---
### File: ./codeconcat/tests/test_end_to_end.py
#### Summary
```
File: test_end_to_end.py
Language: python
```

```python
   1 | import os
   3 | import pytest
   5 | from codeconcat.base_types import CodeConCatConfig
   6 | from codeconcat.main import run_codeconcat
   9 | @pytest.fixture
  10 | def sample_dir(tmp_path):
  11 |     py_file = tmp_path / "script.py"
  12 |     py_file.write_text("def foo(): pass\n")
  13 |     doc_file = tmp_path / "README.md"
  14 |     doc_file.write_text("# This is documentation.")
  15 |     return tmp_path
  18 | def test_run_codeconcat(sample_dir):
  19 |     config = CodeConCatConfig(
  20 |         target_path=str(sample_dir),
  21 |         docs=True,
  22 |         merge_docs=True,
  23 |         format="markdown",
  24 |         output=str(sample_dir / "output.md"),
  25 |     )
  26 |     run_codeconcat(config)
  28 |     output_path = sample_dir / "output.md"
  29 |     assert output_path.exists()
  30 |     content = output_path.read_text()
  31 |     assert "def foo" in content
  32 |     assert "# This is documentation." in content
```

---
### File: ./codeconcat/collector/github_collector.py
#### Summary
```
File: github_collector.py
Language: python
```

```python
   1 | import os
   2 | import re
   3 | import shutil
   4 | import subprocess
   5 | import tempfile
   6 | from typing import List, Optional, Tuple
   8 | from github import Github
   9 | from github.ContentFile import ContentFile
  10 | from github.Repository import Repository
  12 | from codeconcat.base_types import CodeConCatConfig
  13 | from codeconcat.collector.local_collector import collect_local_files
  16 | def parse_github_url(url: str) -> Tuple[str, str, Optional[str]]:
  19 |     if "/" in url and not url.startswith("http"):
  20 |         parts = url.split("/")
  21 |         owner = parts[0]
  22 |         repo = parts[1]
  23 |         ref = parts[2] if len(parts) > 2 else None
  24 |         return owner, repo, ref
  27 |     match = re.match(r"https?://github\.com/([^/]+)/([^/]+)(?:/tree/([^/]+))?", url)
  28 |     if match:
  29 |         return match.group(1), match.group(2), match.group(3)
  31 |     raise ValueError(
  32 |         "Invalid GitHub URL or shorthand. Use format 'owner/repo', 'owner/repo/branch', "
  33 |         "or 'https://github.com/owner/repo'"
  34 |     )
  37 | def collect_github_files(github_url: str, config: CodeConCatConfig) -> List[str]:
  38 |     owner, repo_name, url_ref = parse_github_url(github_url)
  41 |     target_ref = config.ref or url_ref or "main"
  43 |     g = Github(config.github_token) if config.github_token else Github()
  44 |     repo = g.get_repo(f"{owner}/{repo_name}")
  46 |     try:
  48 |         repo.get_commit(target_ref)
  49 |     except:
  50 |         try:
  52 |             branches = [b.name for b in repo.get_branches()]
  53 |             tags = [t.name for t in repo.get_tags()]
  54 |             if target_ref not in branches + tags:
  55 |                 raise ValueError(
  56 |                     f"Reference '{target_ref}' not found. Available branches: {branches}, "
  57 |                     f"tags: {tags}"
  58 |                 )
  59 |         except Exception as e:
  60 |             raise ValueError(f"Error accessing repository: {str(e)}")
  62 |     contents = []
  63 |     for content in repo.get_contents("", ref=target_ref):
  64 |         if content.type == "file":
  65 |             contents.append(content.decoded_content.decode("utf-8"))
  66 |         elif content.type == "dir":
  67 |             contents.extend(_collect_dir_contents(repo, content.path, target_ref))
  69 |     return contents
  72 | def _collect_dir_contents(repo: Repository, path: str, ref: str) -> List[str]:
  74 |     contents = []
  75 |     for content in repo.get_contents(path, ref=ref):
  76 |         if content.type == "file":
  77 |             contents.append(content.decoded_content.decode("utf-8"))
  78 |         elif content.type == "dir":
  79 |             contents.extend(_collect_dir_contents(repo, content.path, ref))
  80 |     return contents
  83 | def collect_github_files_legacy(github_url: str, config: CodeConCatConfig) -> List[str]:
  84 |     temp_dir = tempfile.mkdtemp(prefix="codeconcat_github_")
  85 |     try:
  86 |         clone_url = build_clone_url(github_url, config.github_token)
  87 |         print(f"[CodeConCat] Cloning from {clone_url} into {temp_dir}")
  88 |         subprocess.run(["git", "clone", "--depth=1", clone_url, temp_dir], check=True)
  90 |         file_paths = collect_local_files(temp_dir, config)
  91 |         return file_paths
  93 |     except subprocess.CalledProcessError as e:
  94 |         raise RuntimeError(f"Failed to clone GitHub repo: {e}") from e
  95 |     finally:
  98 |         pass
 101 | def build_clone_url(github_url: str, token: str) -> str:
 102 |     if token and "https://" in github_url:
 103 |         parts = github_url.split("https://", 1)
 104 |         return f"https://{token}@{parts[1]}"
 105 |     return github_url
```

---
### File: ./codeconcat/collector/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/collector/local_collector.py
#### Summary
```
File: local_collector.py
Language: python
```

```python
   1 | import fnmatch
   2 | import logging
   3 | import os
   4 | import re
   5 | from concurrent.futures import ThreadPoolExecutor
   6 | from typing import List
   8 | from codeconcat.base_types import CodeConCatConfig, ParsedFileData
  11 | logger = logging.getLogger(__name__)
  12 | logger.setLevel(logging.WARNING)
  15 | ch = logging.StreamHandler()
  16 | ch.setLevel(logging.DEBUG)
  19 | formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  20 | ch.setFormatter(formatter)
  23 | logger.addHandler(ch)
  25 | DEFAULT_EXCLUDES = [
  27 |     ".git/",  # Match the .git directory itself
  28 |     ".git/**",  # Match contents of .git directory
  29 |     "**/.git/",  # Match .git directory anywhere in tree
  30 |     "**/.git/**",  # Match contents of .git directory anywhere in tree
  31 |     ".gitignore",
  32 |     "**/.gitignore",
  34 |     ".DS_Store",
  35 |     "**/.DS_Store",
  36 |     "Thumbs.db",
  37 |     "**/*.swp",
  38 |     "**/*.swo",
  39 |     ".idea/**",
  40 |     ".vscode/**",
  42 |     "*.yml",
  43 |     "./*.yml",
  44 |     "**/*.yml",
  45 |     "*.yaml",
  46 |     "./*.yaml",
  47 |     "**/*.yaml",
  48 |     ".codeconcat.yml",
  50 |     "node_modules/",
  51 |     "**/node_modules/",
  52 |     "**/node_modules/**",
  53 |     "build/",
  54 |     "**/build/",
  55 |     "**/build/**",
  56 |     "dist/",
  57 |     "**/dist/",
  58 |     "**/dist/**",
  60 |     ".next/",
  61 |     "**/.next/",
  62 |     "**/.next/**",
  63 |     "**/static/chunks/**",
  64 |     "**/server/chunks/**",
  65 |     "**/BUILD_ID",
  66 |     "**/trace",
  67 |     "**/*.map",
  68 |     "**/webpack-*.js",
  69 |     "**/manifest*.js",
  70 |     "**/server-reference-manifest.js",
  71 |     "**/middleware-manifest.js",
  72 |     "**/client-reference-manifest.js",
  73 |     "**/webpack-runtime.js",
  74 |     "**/server-reference-manifest.js",
  75 |     "**/middleware-build-manifest.js",
  76 |     "**/middleware-react-loadable-manifest.js",
  77 |     "**/server-reference-manifest.js",
  78 |     "**/interception-route-rewrite-manifest.js",
  79 |     "**/next-font-manifest.js",
  80 |     "**/polyfills-*.js",
  81 |     "**/main-*.js",
  82 |     "**/framework-*.js",
  84 |     "package-lock.json",
  85 |     "**/package-lock.json",
  86 |     "yarn.lock",
  87 |     "**/yarn.lock",
  88 |     "pnpm-lock.yaml",
  89 |     "**/pnpm-lock.yaml",
  91 |     ".cache/",
  92 |     "**/.cache/",
  93 |     "**/.cache/**",
  94 |     "tmp/",
  95 |     "**/tmp/",
  96 |     "**/tmp/**",
  98 |     "coverage/",
  99 |     "**/coverage/",
 100 |     "**/coverage/**",
 102 |     ".env",
 103 |     "**/.env",
 104 |     ".env.*",
 105 |     "**/.env.*",
 106 | ]
 109 | def collect_local_files(root_path: str, config: CodeConCatConfig):
 112 |     logger.debug(f"[CodeConCat] Collecting files from: {root_path}")
 115 |     if not os.path.exists(root_path):
 116 |         raise FileNotFoundError(f"Path does not exist: {root_path}")
 119 |     with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
 120 |         futures = []
 122 |         for dirpath, dirnames, filenames in os.walk(root_path):
 124 |             if should_skip_dir(dirpath, config.exclude_paths):
 125 |                 dirnames.clear()  # Clear dirnames to skip subdirectories
 126 |                 continue
 129 |             for filename in filenames:
 130 |                 file_path = os.path.join(dirpath, filename)
 131 |                 futures.append(executor.submit(process_file, file_path, config))
 134 |         results = [f.result() for f in futures if f.result()]
 136 |     if not results:
 137 |         logger.warning("[CodeConCat] No files found matching the criteria")
 138 |     else:
 139 |         logger.info(f"[CodeConCat] Collected {len(results)} files")
 141 |     return results
 144 | def process_file(file_path: str, config: CodeConCatConfig):
 146 |     try:
 147 |         if not should_include_file(file_path, config):
 148 |             return None
 150 |         if is_binary_file(file_path):
 151 |             logger.debug(f"[CodeConCat] Skipping binary file: {file_path}")
 152 |             return None
 154 |         with open(file_path, "r", encoding="utf-8") as f:
 155 |             content = f.read()
 157 |         ext = os.path.splitext(file_path)[1].lstrip(".")
 158 |         language = ext_map(ext, config)
 160 |         logger.debug(f"[CodeConCat] Processed file: {file_path} ({language})")
 161 |         return ParsedFileData(
 162 |             file_path=file_path,
 163 |             language=language,
 164 |             content=content,
 165 |             declarations=[],  # We'll fill this in during parsing phase
 166 |         )
 168 |     except UnicodeDecodeError:
 169 |         logger.debug(f"[CodeConCat] Skipping non-text file: {file_path}")
 170 |         return None
 171 |     except Exception as e:
 172 |         logger.error(f"[CodeConCat] Error processing {file_path}: {str(e)}")
 173 |         return None
 176 | def should_skip_dir(dirpath: str, user_excludes: List[str]) -> bool:
 178 |     all_excludes = DEFAULT_EXCLUDES + (user_excludes or [])
 179 |     logger.debug(f"Checking directory: {dirpath} against patterns: {all_excludes}")
 182 |     if os.path.isabs(dirpath):
 183 |         try:
 184 |             rel_path = os.path.relpath(dirpath, os.getcwd())
 185 |         except ValueError:
 186 |             rel_path = dirpath
 187 |     else:
 188 |         rel_path = dirpath
 191 |     rel_path = rel_path.replace(os.sep, "/").strip("/")
 194 |     for pattern in all_excludes:
 195 |         if matches_pattern(rel_path, pattern):
 196 |             logger.debug(f"Excluding directory {rel_path} due to pattern {pattern}")
 197 |             return True
 200 |     path_parts = [p for p in rel_path.split("/") if p]
 201 |     current_path = ""
 202 |     for part in path_parts:
 203 |         if current_path:
 204 |             current_path += "/"
 205 |         current_path += part
 207 |         for pattern in all_excludes:
 209 |             if matches_pattern(current_path, pattern) or matches_pattern(
 210 |                 current_path + "/", pattern
 211 |             ):
 212 |                 logger.debug(
 213 |                     f"Excluding directory {rel_path} due to parent {current_path} matching pattern {pattern}"
 214 |                 )
 215 |                 return True
 217 |     return False
 220 | def should_include_file(path_str: str, config: CodeConCatConfig) -> bool:
 223 |     all_excludes = DEFAULT_EXCLUDES + (config.exclude_paths or [])
 224 |     logger.debug(f"Checking file: {path_str} against patterns: {all_excludes}")
 227 |     if os.path.isabs(path_str):
 228 |         try:
 229 |             rel_path = os.path.relpath(path_str, os.getcwd())
 230 |         except ValueError:
 231 |             rel_path = path_str
 232 |     else:
 233 |         rel_path = path_str
 236 |     rel_path = rel_path.replace(os.sep, "/").strip("/")
 239 |     path_parts = [p for p in rel_path.split("/") if p]
 240 |     current_path = ""
 241 |     for part in path_parts[:-1]:  # Don't check the file itself yet
 242 |         if current_path:
 243 |             current_path += "/"
 244 |         current_path += part
 246 |         for pattern in all_excludes:
 248 |             if matches_pattern(current_path, pattern) or matches_pattern(
 249 |                 current_path + "/", pattern
 250 |             ):
 251 |                 logger.debug(
 252 |                     f"Excluding file {rel_path} due to parent directory {current_path} matching pattern {pattern}"
 253 |                 )
 254 |                 return False
 257 |     for pattern in all_excludes:
 258 |         if matches_pattern(rel_path, pattern):
 259 |             logger.debug(f"Excluding file {rel_path} due to pattern {pattern}")
 260 |             return False
 263 |     ext = os.path.splitext(path_str)[1].lower().lstrip(".")
 264 |     if "." in os.path.basename(path_str):  # Only check extension if file has one
 265 |         language_label = ext_map(ext, config)
 266 |         if language_label in ("non-code", "unknown"):
 267 |             logger.debug(f"Excluding file {rel_path} due to non-code extension: {ext}")
 268 |             return False
 271 |     if config.include_paths:
 272 |         included = False
 273 |         for pattern in config.include_paths:
 274 |             if matches_pattern(rel_path, pattern):
 275 |                 included = True
 276 |                 break
 277 |         if not included:
 278 |             logger.debug(f"Excluding file {rel_path} as it doesn't match any include patterns")
 279 |             return False
 282 |     if config.include_languages:
 283 |         ext = os.path.splitext(path_str)[1].lower().lstrip(".")
 284 |         language_label = ext_map(ext, config)
 285 |         include_result = language_label in config.include_languages
 286 |         logger.debug(
 287 |             f"Language check for {path_str}: ext={ext}, label={language_label}, included={include_result}"
 288 |         )
 289 |         return include_result
 291 |     return True
 294 | def matches_pattern(path_str: str, pattern: str) -> bool:
 297 |     path_str = path_str.replace(os.sep, "/").strip("/")
 298 |     pattern = pattern.replace(os.sep, "/").strip("/")
 301 |     if pattern == "":
 302 |         return path_str == ""
 305 |     pattern = pattern.replace(".", "\\.")  # Escape dots
 306 |     pattern = pattern.replace("**", "__DOUBLE_STAR__")  # Preserve **
 307 |     pattern = pattern.replace("*", "[^/]*")  # Single star doesn't cross directories
 308 |     pattern = pattern.replace("__DOUBLE_STAR__", ".*")  # ** can cross directories
 309 |     pattern = pattern.replace("?", "[^/]")  # ? matches single character
 312 |     if pattern.endswith("/"):
 313 |         pattern = pattern + ".*"  # Match anything after directory
 316 |     if pattern.startswith("/"):
 317 |         pattern = "^" + pattern[1:]  # Keep absolute path requirement
 318 |     elif pattern.startswith("**/"):
 319 |         pattern = ".*" + pattern[2:]  # Allow matching anywhere in path
 320 |     else:
 321 |         pattern = "^" + pattern  # Anchor to start by default
 323 |     if not pattern.endswith("$"):
 324 |         pattern += "$"  # Always anchor to end
 327 |     try:
 328 |         return bool(re.match(pattern, path_str))
 329 |     except re.error as e:
 330 |         logger.warning(f"Invalid pattern {pattern}: {str(e)}")
 331 |         return False
 334 | def ext_map(ext: str, config: CodeConCatConfig) -> str:
 336 |     if ext in config.custom_extension_map:
 337 |         return config.custom_extension_map[ext]
 340 |     non_code_exts = {
 342 |         "svg",
 343 |         "png",
 344 |         "jpg",
 345 |         "jpeg",
 346 |         "gif",
 347 |         "ico",
 348 |         "webp",
 350 |         "woff",
 351 |         "woff2",
 352 |         "ttf",
 353 |         "eot",
 354 |         "otf",
 356 |         "pdf",
 357 |         "doc",
 358 |         "docx",
 359 |         "xls",
 360 |         "xlsx",
 362 |         "zip",
 363 |         "tar",
 364 |         "gz",
 365 |         "tgz",
 366 |         "7z",
 367 |         "rar",
 369 |         "map",
 370 |         "min.js",
 371 |         "min.css",
 372 |         "bundle.js",
 373 |         "bundle.css",
 374 |         "chunk.js",
 375 |         "chunk.css",
 376 |         "nft.json",
 377 |         "rsc",
 378 |         "meta",
 380 |         "mp3",
 381 |         "mp4",
 382 |         "wav",
 383 |         "avi",
 384 |         "mov",
 385 |     }
 387 |     if ext.lower() in non_code_exts:
 388 |         return "non-code"
 391 |     code_exts = {
 393 |         "py": "python",
 394 |         "pyi": "python",
 396 |         "js": "javascript",
 397 |         "jsx": "javascript",
 398 |         "ts": "typescript",
 399 |         "tsx": "typescript",
 400 |         "mjs": "javascript",
 402 |         "r": "r",
 403 |         "jl": "julia",
 404 |         "cpp": "cpp",
 405 |         "hpp": "cpp",
 406 |         "cxx": "cpp",
 407 |         "c": "c",
 408 |         "h": "c",
 410 |         "md": "doc",
 411 |         "rst": "doc",
 412 |         "txt": "doc",
 413 |         "rmd": "doc",
 414 |     }
 416 |     return code_exts.get(ext.lower(), "unknown")
 419 | def is_binary_file(file_path: str) -> bool:
 421 |     try:
 422 |         with open(file_path, "tr") as check_file:
 423 |             check_file.readline()
 424 |             return False
 425 |     except UnicodeDecodeError:
 426 |         return True
```

---
### File: ./codeconcat/parser/doc_extractor.py
#### Summary
```
File: doc_extractor.py
Language: python
```

```python
   1 | import os
   2 | from concurrent.futures import ThreadPoolExecutor
   3 | from typing import List
   5 | from codeconcat.base_types import CodeConCatConfig, ParsedDocData
   8 | def extract_docs(file_paths: List[str], config: CodeConCatConfig) -> List[ParsedDocData]:
   9 |     doc_paths = [fp for fp in file_paths if is_doc_file(fp, config.doc_extensions)]
  11 |     with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
  12 |         results = list(executor.map(lambda fp: parse_doc_file(fp), doc_paths))
  13 |     return results
  16 | def is_doc_file(file_path: str, doc_exts: List[str]) -> bool:
  17 |     ext = os.path.splitext(file_path)[1].lower()
  18 |     return ext in doc_exts
  21 | def parse_doc_file(file_path: str) -> ParsedDocData:
  22 |     ext = os.path.splitext(file_path)[1].lower()
  23 |     content = read_doc_content(file_path)
  24 |     doc_type = ext.lstrip(".")
  25 |     return ParsedDocData(file_path=file_path, doc_type=doc_type, content=content)
  28 | def read_doc_content(file_path: str) -> str:
  29 |     try:
  30 |         with open(file_path, "r", encoding="utf-8", errors="replace") as f:
  31 |             return f.read()
  32 |     except Exception:
  33 |         return ""
```

---
### File: ./codeconcat/parser/file_parser.py
#### Summary
```
File: file_parser.py
Language: python
```

```python
   1 | import os
   2 | from concurrent.futures import ThreadPoolExecutor
   3 | from typing import Callable, List, Optional, Tuple
   5 | from codeconcat.base_types import CodeConCatConfig, ParsedFileData
   6 | from codeconcat.parser.language_parsers.c_parser import parse_c_code
   7 | from codeconcat.parser.language_parsers.cpp_parser import parse_cpp_code
   8 | from codeconcat.parser.language_parsers.csharp_parser import parse_csharp_code
   9 | from codeconcat.parser.language_parsers.go_parser import parse_go
  10 | from codeconcat.parser.language_parsers.java_parser import parse_java
  11 | from codeconcat.parser.language_parsers.js_ts_parser import parse_javascript_or_typescript
  12 | from codeconcat.parser.language_parsers.julia_parser import parse_julia
  13 | from codeconcat.parser.language_parsers.php_parser import parse_php
  14 | from codeconcat.parser.language_parsers.python_parser import parse_python
  15 | from codeconcat.parser.language_parsers.r_parser import parse_r
  16 | from codeconcat.parser.language_parsers.rust_parser import parse_rust_code
  17 | from codeconcat.processor.token_counter import get_token_stats
  20 | def parse_code_files(file_paths: List[str], config: CodeConCatConfig) -> List[ParsedFileData]:
  21 |     code_paths = [fp for fp in file_paths if not is_doc_file(fp, config.doc_extensions)]
  23 |     with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
  24 |         results = list(executor.map(lambda fp: parse_single_file(fp, config), code_paths))
  25 |     return results
  28 | def parse_single_file(file_path: str, config: CodeConCatConfig) -> ParsedFileData:
  29 |     ext = os.path.splitext(file_path)[1].lower().lstrip(".")
  30 |     content = read_file_content(file_path)
  33 |     token_stats = get_token_stats(content)
  35 |     parser_info = get_language_parser(file_path)
  36 |     if parser_info:
  37 |         language, parser_func = parser_info
  38 |         if parser_func == parse_javascript_or_typescript:
  39 |             parsed_data = parser_func(file_path, content, language)
  40 |         else:
  41 |             parsed_data = parser_func(file_path, content)
  42 |         parsed_data.token_stats = token_stats
  43 |         return parsed_data
  44 |     else:
  45 |         return ParsedFileData(
  46 |             file_path=file_path,
  47 |             language=get_language_name(file_path),
  48 |             content=content,
  49 |             token_stats=token_stats,
  50 |         )
  53 | def get_language_parser(file_path: str) -> Optional[Tuple[str, Callable]]:
  55 |     ext = file_path.split(".")[-1].lower() if "." in file_path else ""
  57 |     extension_map = {
  59 |         ".py": ("python", parse_python),
  60 |         ".js": ("javascript", parse_javascript_or_typescript),
  61 |         ".ts": ("typescript", parse_javascript_or_typescript),
  62 |         ".jsx": ("javascript", parse_javascript_or_typescript),
  63 |         ".tsx": ("typescript", parse_javascript_or_typescript),
  64 |         ".r": ("r", parse_r),
  65 |         ".jl": ("julia", parse_julia),
  67 |         ".rs": ("rust", parse_rust_code),
  68 |         ".cpp": ("cpp", parse_cpp_code),
  69 |         ".cxx": ("cpp", parse_cpp_code),
  70 |         ".cc": ("cpp", parse_cpp_code),
  71 |         ".hpp": ("cpp", parse_cpp_code),
  72 |         ".hxx": ("cpp", parse_cpp_code),
  73 |         ".h": ("c", parse_c_code),  # Note: .h could be C or C++
  74 |         ".c": ("c", parse_c_code),
  75 |         ".cs": ("csharp", parse_csharp_code),
  76 |         ".java": ("java", parse_java),
  77 |         ".go": ("go", parse_go),
  78 |         ".php": ("php", parse_php),
  79 |     }
  81 |     ext_with_dot = f".{ext}" if not ext.startswith(".") else ext
  82 |     return extension_map.get(ext_with_dot)
  85 | def get_language_name(file_path: str) -> str:
  87 |     parser_info = get_language_parser(file_path)
  88 |     if parser_info:
  89 |         return parser_info[0]
  90 |     return "unknown"
  93 | def is_doc_file(file_path: str, doc_exts: List[str]) -> bool:
  94 |     ext = os.path.splitext(file_path)[1].lower()
  95 |     return ext in doc_exts
  98 | def read_file_content(file_path: str) -> str:
  99 |     try:
 100 |         with open(file_path, "r", encoding="utf-8", errors="replace") as f:
 101 |             return f.read()
 102 |     except Exception:
 103 |         return ""
```

---
### File: ./codeconcat/parser/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/parser/language_parsers/csharp_parser.py
#### Summary
```
File: csharp_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Tuple
   7 | def parse_csharp_code(content: str) -> List[Tuple[str, int, int]]:
  10 |     Returns:
  11 |         List of tuples (symbol_name, start_line, end_line)
  13 |     symbols = []
  14 |     lines = content.split("\n")
  17 |     patterns = {
  18 |         "class": r"^\s*(?:public|private|protected|internal)?\s*(?:static|abstract|sealed)?\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)",
  19 |         "interface": r"^\s*(?:public|private|protected|internal)?\s*interface\s+([a-zA-Z_][a-zA-Z0-9_]*)",
  20 |         "method": r"^\s*(?:public|private|protected|internal)?\s*(?:static|virtual|abstract|override)?\s*(?:async\s+)?(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)",
  21 |         "property": r"^\s*(?:public|private|protected|internal)?\s*(?:static|virtual|abstract|override)?\s*(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*{\s*(?:get|set)",
  22 |         "enum": r"^\s*(?:public|private|protected|internal)?\s*enum\s+([a-zA-Z_][a-zA-Z0-9_]*)",
  23 |         "struct": r"^\s*(?:public|private|protected|internal)?\s*struct\s+([a-zA-Z_][a-zA-Z0-9_]*)",
  24 |         "delegate": r"^\s*(?:public|private|protected|internal)?\s*delegate\s+(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(",
  25 |         "event": r"^\s*(?:public|private|protected|internal)?\s*event\s+(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)",
  26 |         "namespace": r"^\s*namespace\s+([a-zA-Z_][a-zA-Z0-9_.]*)",
  27 |     }
  29 |     in_block = False
  30 |     block_start = 0
  31 |     block_name = ""
  32 |     brace_count = 0
  33 |     in_comment = False
  35 |     for i, line in enumerate(lines):
  37 |         if "/*" in line:
  38 |             in_comment = True
  39 |         if "*/" in line:
  40 |             in_comment = False
  41 |             continue
  42 |         if in_comment or line.strip().startswith("//"):
  43 |             continue
  46 |         if line.strip().startswith("["):
  47 |             continue
  50 |         if not in_block:
  51 |             for construct, pattern in patterns.items():
  52 |                 match = re.match(pattern, line)
  53 |                 if match:
  54 |                     block_name = match.group(1)
  55 |                     block_start = i
  56 |                     in_block = True
  57 |                     brace_count = line.count("{") - line.count("}")
  59 |                     if brace_count == 0 and ";" in line:
  60 |                         symbols.append((block_name, i, i))
  61 |                         in_block = False
  62 |                     break
  63 |         else:
  64 |             brace_count += line.count("{") - line.count("}")
  67 |         if in_block and brace_count == 0 and ("}" in line or ";" in line):
  68 |             symbols.append((block_name, block_start, i))
  69 |             in_block = False
  71 |     return symbols
```

---
### File: ./codeconcat/parser/language_parsers/c_parser.py
#### Summary
```
File: c_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Tuple
   7 | def parse_c_code(content: str) -> List[Tuple[str, int, int]]:
  10 |     Returns:
  11 |         List of tuples (symbol_name, start_line, end_line)
  13 |     symbols = []
  14 |     lines = content.split("\n")
  17 |     patterns = {
  18 |         "function": r"^\s*(?:static\s+)?(?:inline\s+)?(?:[a-zA-Z_][a-zA-Z0-9_]*\s+)+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^;]*$",
  19 |         "struct": r"^\s*struct\s+([a-zA-Z_][a-zA-Z0-9_]*)",
  20 |         "union": r"^\s*union\s+([a-zA-Z_][a-zA-Z0-9_]*)",
  21 |         "enum": r"^\s*enum\s+([a-zA-Z_][a-zA-Z0-9_]*)",
  22 |         "typedef": r"^\s*typedef\s+(?:struct|union|enum)?\s*(?:[a-zA-Z_][a-zA-Z0-9_]*\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*;",
  23 |         "define": r"^\s*#define\s+([A-Z_][A-Z0-9_]*)",
  24 |     }
  26 |     in_block = False
  27 |     block_start = 0
  28 |     block_name = ""
  29 |     brace_count = 0
  30 |     in_comment = False
  31 |     in_macro = False
  33 |     for i, line in enumerate(lines):
  35 |         if "/*" in line:
  36 |             in_comment = True
  37 |         if "*/" in line:
  38 |             in_comment = False
  39 |             continue
  40 |         if in_comment or line.strip().startswith("//"):
  41 |             continue
  44 |         if line.strip().endswith("\\"):
  45 |             in_macro = True
  46 |             continue
  47 |         if in_macro:
  48 |             if not line.strip().endswith("\\"):
  49 |                 in_macro = False
  50 |             continue
  53 |         if line.strip().startswith("#") and not line.strip().startswith("#define"):
  54 |             continue
  57 |         if not in_block:
  58 |             for construct, pattern in patterns.items():
  59 |                 match = re.match(pattern, line)
  60 |                 if match:
  61 |                     block_name = match.group(1)
  62 |                     block_start = i
  63 |                     in_block = True
  64 |                     brace_count = line.count("{") - line.count("}")
  66 |                     if construct in ["typedef", "define"] or (brace_count == 0 and ";" in line):
  67 |                         symbols.append((block_name, i, i))
  68 |                         in_block = False
  69 |                     break
  70 |         else:
  71 |             brace_count += line.count("{") - line.count("}")
  74 |         if in_block and brace_count == 0 and ("}" in line or ";" in line):
  75 |             symbols.append((block_name, block_start, i))
  76 |             in_block = False
  78 |     return symbols
```

---
### File: ./codeconcat/parser/language_parsers/julia_parser.py
#### Summary
```
File: julia_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import Dict, List, Pattern
   6 | from codeconcat.base_types import Declaration, ParsedFileData
   7 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
  10 | class JuliaParser(BaseParser):
  13 |     def _setup_patterns(self):
  15 |         self.patterns = {
  16 |             "function": re.compile(
  17 |                 r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
  18 |                 r"function\s+(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Function name
  19 |                 r"\s*\((?P<parameters>[^)]*)\)"  # Parameters
  20 |                 r"(?:\s*::\s*(?P<return_type>[^{;]+))?"  # Optional return type
  21 |             ),
  22 |             "struct": re.compile(
  23 |                 r"^(?P<modifiers>(?:export\s+)?(?:mutable\s+)?)"  # Modifiers
  24 |                 r"struct\s+(?P<struct_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Struct name
  25 |                 r"(?:\s*<:\s*(?P<supertype>[^{]+))?"  # Optional supertype
  26 |             ),
  27 |             "abstract": re.compile(
  28 |                 r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
  29 |                 r"abstract\s+type\s+(?P<type_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Type name
  30 |                 r"(?:\s*<:\s*(?P<supertype>[^{]+))?"  # Optional supertype
  31 |             ),
  32 |             "module": re.compile(
  33 |                 r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
  34 |                 r"module\s+(?P<module_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Module name
  35 |             ),
  36 |             "const": re.compile(
  37 |                 r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
  38 |                 r"const\s+(?P<const_name>[A-Z][A-Z0-9_]*)"  # Constant name
  39 |                 r"(?:\s*::\s*(?P<type>[^=]+))?"  # Optional type annotation
  40 |                 r"\s*="  # Assignment
  41 |             ),
  42 |             "macro": re.compile(
  43 |                 r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
  44 |                 r"macro\s+(?P<macro_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Macro name
  45 |                 r"\s*\((?P<parameters>[^)]*)\)"  # Parameters
  46 |             ),
  47 |             "variable": re.compile(
  48 |                 r"^(?P<var_name>[a-z][a-z0-9_]*)"  # Variable name
  49 |                 r"(?:\s*::\s*(?P<type>[^=]+))?"  # Optional type annotation
  50 |                 r"\s*=\s*(?!.*(?:function|struct|mutable|module|macro))"  # Assignment, not a definition
  51 |             ),
  52 |         }
  54 |         self.modifiers = {"export", "mutable"}
  55 |         self.block_start = "begin"
  56 |         self.block_end = "end"
  57 |         self.line_comment = "#"
  58 |         self.block_comment_start = "#="
  59 |         self.block_comment_end = "=#"
  61 |     def parse(self, content: str) -> List[Declaration]:
  63 |         lines = content.split("\n")
  64 |         symbols = []
  65 |         brace_count = 0
  66 |         in_comment = False
  67 |         current_module = None
  69 |         i = 0
  70 |         while i < len(lines):
  71 |             line = lines[i].strip()
  74 |             if not line:
  75 |                 i += 1
  76 |                 continue
  79 |             if line.startswith("#="):
  80 |                 in_comment = True
  81 |                 if "=#" in line[2:]:
  82 |                     in_comment = False
  83 |                 i += 1
  84 |                 continue
  86 |             if in_comment:
  87 |                 if "=#" in line:
  88 |                     in_comment = False
  89 |                 i += 1
  90 |                 continue
  93 |             if line.startswith("#"):
  94 |                 i += 1
  95 |                 continue
  98 |             for kind, pattern in self.patterns.items():
  99 |                 match = pattern.match(line)
 100 |                 if match:
 101 |                     name = match.group(f"{kind}_name")
 102 |                     modifiers = set()
 103 |                     if "modifiers" in match.groupdict() and match.group("modifiers"):
 104 |                         modifiers = {m.strip() for m in match.group("modifiers").split()}
 107 |                     symbol = CodeSymbol(
 108 |                         name=name,
 109 |                         kind=kind,
 110 |                         start_line=i,
 111 |                         end_line=i,
 112 |                         modifiers=modifiers,
 113 |                         parent=current_module,
 114 |                     )
 117 |                     if kind in ("function", "struct", "abstract", "module", "macro"):
 118 |                         j = i + 1
 119 |                         block_level = 1
 120 |                         while j < len(lines) and block_level > 0:
 121 |                             if "begin" in lines[j] or kind in lines[j]:
 122 |                                 block_level += 1
 123 |                             if "end" in lines[j]:
 124 |                                 block_level -= 1
 125 |                             j += 1
 126 |                         symbol.end_line = j - 1
 127 |                         i = j - 1
 130 |                         if kind == "module":
 131 |                             current_module = symbol
 133 |                     symbols.append(symbol)
 134 |                     break
 136 |             i += 1
 139 |         return [
 140 |             Declaration(symbol.kind, symbol.name, symbol.start_line + 1, symbol.end_line + 1)
 141 |             for symbol in symbols
 142 |         ]
 145 | def parse_julia(file_path: str, content: str) -> ParsedFileData:
 147 |     parser = JuliaParser()
 148 |     declarations = parser.parse(content)
 149 |     return ParsedFileData(
 150 |         file_path=file_path, language="julia", content=content, declarations=declarations
 151 |     )
```

---
### File: ./codeconcat/parser/language_parsers/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/parser/language_parsers/php_parser.py
#### Summary
```
File: php_parser.py
Language: python
```

```python
   3 | from typing import List
   5 | from codeconcat.base_types import Declaration
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser
   9 | class PhpParser(BaseParser):
  12 |     def _setup_patterns(self):
  15 |         self.namespace_pattern = self._create_pattern(r"namespace\s+([\w\\]+);")
  18 |         self.use_pattern = self._create_pattern(r"use\s+([\w\\]+)(?:\s+as\s+(\w+))?;")
  21 |         self.class_pattern = self._create_pattern(
  22 |             r"(?:abstract\s+|final\s+)?"
  23 |             r"(?:class|interface|trait)\s+"
  24 |             r"(\w+)"
  25 |             r"(?:\s+extends\s+[\w\\]+)?"
  26 |             r"(?:\s+implements\s+[\w\\,\s]+)?"
  27 |             r"\s*{"
  28 |         )
  31 |         self.method_pattern = self._create_pattern(
  32 |             r"(?:public\s+|protected\s+|private\s+)?"
  33 |             r"(?:static\s+|final\s+|abstract\s+)*"
  34 |             r"function\s+"
  35 |             r"(?:&\s*)?"  # Reference return
  36 |             r"(\w+)"  # Method name
  37 |             r"\s*\([^)]*\)"  # Parameters
  38 |             r"(?:\s*:\s*\??[\w\\|]+)?"  # Return type hint
  39 |             r"\s*(?:{|;)"  # Body or abstract method
  40 |         )
  43 |         self.property_pattern = self._create_pattern(
  44 |             r"(?:public\s+|protected\s+|private\s+)?"
  45 |             r"(?:static\s+|readonly\s+)*"
  46 |             r"(?:var\s+)?"
  47 |             r"\$(\w+)"  # Property name
  48 |             r"(?:\s*=\s*[^;]+)?;"  # Optional initialization
  49 |         )
  52 |         self.const_pattern = self._create_pattern(
  53 |             r"const\s+"
  54 |             r"(\w+)"  # Constant name
  55 |             r"\s*=\s*[^;]+;"  # Value required
  56 |         )
  58 |     def parse(self, content: str) -> List[Declaration]:
  60 |         lines = content.split("\n")
  61 |         symbols = []
  62 |         brace_count = 0
  63 |         in_comment = False
  64 |         current_namespace = None
  65 |         current_class = None
  67 |         i = 0
  68 |         while i < len(lines):
  69 |             line = lines[i].strip()
  72 |             if not line:
  73 |                 i += 1
  74 |                 continue
  77 |             if line.startswith("/*"):
  78 |                 in_comment = True
  79 |                 if "*/" in line[2:]:
  80 |                     in_comment = False
  81 |                 i += 1
  82 |                 continue
  83 |             if in_comment:
  84 |                 if "*/" in line:
  85 |                     in_comment = False
  86 |                 i += 1
  87 |                 continue
  90 |             if line.startswith("//") or line.startswith("#"):
  91 |                 i += 1
  92 |                 continue
  95 |             brace_count += line.count("{") - line.count("}")
  98 |             if namespace_match := self.namespace_pattern.search(line):
  99 |                 current_namespace = namespace_match.group(1)
 100 |                 i += 1
 101 |                 continue
 104 |             if class_match := self.class_pattern.search(line):
 105 |                 class_name = class_match.group(1)
 106 |                 qualified_name = (
 107 |                     f"{current_namespace}\\{class_name}" if current_namespace else class_name
 108 |                 )
 109 |                 current_class = qualified_name
 110 |                 symbols.append(
 111 |                     Declaration(kind="class", name=qualified_name, start_line=i, end_line=i)
 112 |                 )
 113 |                 i += 1
 114 |                 continue
 117 |             if method_match := self.method_pattern.search(line):
 118 |                 method_name = method_match.group(1)
 119 |                 qualified_name = f"{current_class}::{method_name}" if current_class else method_name
 120 |                 symbols.append(
 121 |                     Declaration(kind="function", name=qualified_name, start_line=i, end_line=i)
 122 |                 )
 123 |                 i += 1
 124 |                 continue
 127 |             if property_match := self.property_pattern.search(line):
 128 |                 property_name = property_match.group(1)
 129 |                 qualified_name = (
 130 |                     f"{current_class}::{property_name}" if current_class else property_name
 131 |                 )
 132 |                 symbols.append(
 133 |                     Declaration(kind="symbol", name=qualified_name, start_line=i, end_line=i)
 134 |                 )
 137 |             if const_match := self.const_pattern.search(line):
 138 |                 const_name = const_match.group(1)
 139 |                 qualified_name = f"{current_class}::{const_name}" if current_class else const_name
 140 |                 symbols.append(
 141 |                     Declaration(kind="symbol", name=qualified_name, start_line=i, end_line=i)
 142 |                 )
 144 |             i += 1
 146 |         return symbols
 149 | def parse_php(file_path: str, content: str) -> List[Declaration]:
 151 |     parser = PhpParser()
 152 |     return parser.parse(content)
```

---
### File: ./codeconcat/parser/language_parsers/rust_parser.py
#### Summary
```
File: rust_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import Dict, List, Pattern
   6 | from codeconcat.base_types import Declaration, ParsedFileData
   7 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
  10 | class RustParser(BaseParser):
  13 |     def _setup_patterns(self):
  15 |         self.patterns = {
  16 |             "function": re.compile(
  17 |                 r"^(?P<modifiers>(?:pub\s+)?(?:async\s+)?)"  # Visibility and async
  18 |                 r"fn\s+(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Function name
  19 |                 r"\s*(?:<[^>]*>)?"  # Optional generic parameters
  20 |                 r"\s*\((?P<parameters>[^)]*)\)"  # Parameters
  21 |                 r"(?:\s*->\s*(?P<return_type>[^{;]+))?"  # Optional return type
  22 |             ),
  23 |             "struct": re.compile(
  24 |                 r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
  25 |                 r"struct\s+(?P<struct_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Struct name
  26 |                 r"(?:\s*<[^>]*>)?"  # Optional generic parameters
  27 |             ),
  28 |             "enum": re.compile(
  29 |                 r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
  30 |                 r"enum\s+(?P<enum_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Enum name
  31 |                 r"(?:\s*<[^>]*>)?"  # Optional generic parameters
  32 |             ),
  33 |             "trait": re.compile(
  34 |                 r"^(?P<modifiers>(?:pub\s+)?(?:unsafe\s+)?)"  # Visibility and safety
  35 |                 r"trait\s+(?P<trait_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Trait name
  36 |                 r"(?:\s*<[^>]*>)?"  # Optional generic parameters
  37 |                 r"(?:\s*:\s*(?P<super_traits>[^{]+))?"  # Optional super traits
  38 |             ),
  39 |             "impl": re.compile(
  40 |                 r"^(?P<modifiers>(?:unsafe\s+)?)"  # Safety
  41 |                 r"impl(?:\s*<[^>]*>)?\s*"  # Optional generic parameters
  42 |                 r"(?P<impl_trait>(?:[^{]+)\s+for\s+)?"  # Optional trait being implemented
  43 |                 r"(?P<impl_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Type name
  44 |                 r"(?:\s*<[^>]*>)?"  # Optional generic parameters
  45 |             ),
  46 |             "const": re.compile(
  47 |                 r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
  48 |                 r"const\s+(?P<const_name>[A-Z_][A-Z0-9_]*)"  # Constant name
  49 |                 r"(?::\s*(?P<type>[^=]+))?"  # Type annotation
  50 |                 r"\s*="  # Assignment
  51 |             ),
  52 |             "static": re.compile(
  53 |                 r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
  54 |                 r"static\s+(?:mut\s+)?"  # Mutability
  55 |                 r"(?P<static_name>[A-Z_][A-Z0-9_]*)"  # Static name
  56 |                 r"(?::\s*(?P<type>[^=]+))?"  # Type annotation
  57 |                 r"\s*="  # Assignment
  58 |             ),
  59 |             "type": re.compile(
  60 |                 r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
  61 |                 r"type\s+(?P<type_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Type alias name
  62 |                 r"(?:\s*<[^>]*>)?"  # Optional generic parameters
  63 |                 r"(?:\s*=\s*(?P<type_value>[^;]+))?"  # Type value
  64 |             ),
  65 |             "macro": re.compile(
  66 |                 r"^(?P<modifiers>(?:#\[macro_export\]\s*)?)"  # Export attribute
  67 |                 r"macro_rules!\s+(?P<macro_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Macro name
  68 |             ),
  69 |             "module": re.compile(
  70 |                 r"^(?P<modifiers>(?:pub\s+)?)"  # Visibility
  71 |                 r"mod\s+(?P<module_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Module name
  72 |             ),
  73 |         }
  75 |         self.modifiers = {
  76 |             "pub",
  77 |             "async",
  78 |             "unsafe",
  79 |             "mut",
  80 |             "const",
  81 |             "static",
  82 |             "extern",
  83 |             "default",
  84 |             "#[macro_export]",
  85 |         }
  86 |         self.block_start = "{"
  87 |         self.block_end = "}"
  88 |         self.line_comment = "//"
  89 |         self.block_comment_start = "/*"
  90 |         self.block_comment_end = "*/"
  92 |     def parse(self, content: str) -> List[Declaration]:
  94 |         lines = content.split("\n")
  95 |         symbols = []
  96 |         brace_count = 0
  97 |         in_comment = False
  98 |         current_impl = None
  99 |         pending_attributes = []
 101 |         i = 0
 102 |         while i < len(lines):
 103 |             line = lines[i].strip()
 106 |             if not line:
 107 |                 i += 1
 108 |                 continue
 111 |             if line.startswith("#["):
 112 |                 pending_attributes.append(line)
 113 |                 i += 1
 114 |                 continue
 117 |             if line.startswith("//"):
 118 |                 i += 1
 119 |                 continue
 121 |             if "/*" in line and not in_comment:
 122 |                 in_comment = True
 123 |                 if "*/" in line[line.index("/*") :]:
 124 |                     in_comment = False
 125 |                 i += 1
 126 |                 continue
 128 |             if in_comment:
 129 |                 if "*/" in line:
 130 |                     in_comment = False
 131 |                 i += 1
 132 |                 continue
 135 |             for kind, pattern in self.patterns.items():
 136 |                 match = pattern.match(line)
 137 |                 if match:
 138 |                     name_group = f"{kind}_name"
 139 |                     name = match.group(name_group)
 140 |                     modifiers = set()
 141 |                     if "modifiers" in match.groupdict() and match.group("modifiers"):
 142 |                         modifiers = {m.strip() for m in match.group("modifiers").split()}
 143 |                     modifiers.update(pending_attributes)
 144 |                     pending_attributes = []
 147 |                     symbol = CodeSymbol(
 148 |                         name=name,
 149 |                         kind=kind,
 150 |                         start_line=i,
 151 |                         end_line=i,
 152 |                         modifiers=modifiers,
 153 |                         parent=current_impl if kind == "function" else None,
 154 |                     )
 157 |                     if "{" in line:
 158 |                         brace_count = line.count("{")
 159 |                         j = i + 1
 160 |                         while j < len(lines) and brace_count > 0:
 161 |                             line = lines[j].strip()
 162 |                             if not line.startswith("//"):
 163 |                                 brace_count += line.count("{") - line.count("}")
 164 |                             j += 1
 165 |                         symbol.end_line = j - 1
 166 |                         i = j - 1
 169 |                         if kind == "impl":
 170 |                             current_impl = symbol
 172 |                     symbols.append(symbol)
 173 |                     break
 175 |             i += 1
 178 |         return [
 179 |             Declaration(symbol.kind, symbol.name, symbol.start_line + 1, symbol.end_line + 1)
 180 |             for symbol in symbols
 181 |         ]
 184 | def parse_rust_code(file_path: str, content: str) -> ParsedFileData:
 186 |     parser = RustParser()
 187 |     declarations = parser.parse(content)
 188 |     return ParsedFileData(
 189 |         file_path=file_path, language="rust", content=content, declarations=declarations
 190 |     )
```

---
### File: ./codeconcat/parser/language_parsers/js_ts_parser.py
#### Summary
```
File: js_ts_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import Dict, List, Pattern
   6 | from codeconcat.base_types import Declaration, ParsedFileData
   7 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
  10 | class JstsParser(BaseParser):
  13 |     def __init__(self, language: str = "javascript"):
  14 |         self.language = language  # Set language before calling super()
  15 |         super().__init__()
  16 |         self._setup_patterns()
  18 |     def _setup_patterns(self):
  21 |         base_patterns = {
  22 |             "class": re.compile(
  23 |                 r"^(?P<modifiers>(?:export\s+)?(?:default\s+)?)"  # Export/default modifiers
  24 |                 r"class\s+(?P<class_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Class name
  25 |                 r"(?:\s+extends\s+(?P<extends_name>[a-zA-Z_$][a-zA-Z0-9_$]*))?"  # Optional extends
  26 |                 r"(?:\s+implements\s+(?P<implements_names>[a-zA-Z_$][a-zA-Z0-9_$]*(?:\s*,\s*[a-zA-Z_$][a-zA-Z0-9_$]*)*))?"  # Optional implements
  27 |             ),
  28 |             "function": re.compile(
  29 |                 r"^(?P<modifiers>(?:export\s+)?(?:default\s+)?(?:async\s+)?)"  # Modifiers
  30 |                 r"(?:function\s+)?(?P<function_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Function name
  31 |                 r"\s*\((?P<parameters>[^)]*)\)"  # Parameters
  32 |                 r"(?:\s*:\s*(?P<return_type>[^{;]+))?"  # Optional return type (TS)
  33 |             ),
  34 |             "method": re.compile(
  35 |                 r"^(?P<modifiers>(?:public|private|protected|static|readonly|async)\s+)*"  # Method modifiers
  36 |                 r"(?P<method_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Method name
  37 |                 r"\s*\((?P<parameters>[^)]*)\)"  # Parameters
  38 |                 r"(?:\s*:\s*(?P<return_type>[^{;]+))?"  # Optional return type (TS)
  39 |             ),
  40 |             "variable": re.compile(
  41 |                 r"^(?P<modifiers>(?:export\s+)?(?:const|let|var)\s+)"  # Variable modifiers
  42 |                 r"(?P<variable_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Variable name
  43 |                 r"(?:\s*:\s*(?P<type_annotation>[^=;]+))?"  # Optional type annotation (TS)
  44 |                 r"\s*=\s*"  # Assignment
  45 |             ),
  46 |             "interface": re.compile(
  47 |                 r"^(?P<modifiers>(?:export\s+)?)"  # Export modifier
  48 |                 r"interface\s+(?P<interface_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Interface name
  49 |                 r"(?:\s+extends\s+(?P<extends_names>[a-zA-Z_$][a-zA-Z0-9_$]*(?:\s*,\s*[a-zA-Z_$][a-zA-Z0-9_$]*)*))?"  # Optional extends
  50 |             ),
  51 |             "type": re.compile(
  52 |                 r"^(?P<modifiers>(?:export\s+)?)"  # Export modifier
  53 |                 r"type\s+(?P<type_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Type name
  54 |                 r"\s*=\s*(?P<type_value>.*)"  # Type assignment
  55 |             ),
  56 |         }
  59 |         if self.language == "typescript":
  60 |             base_patterns.update(
  61 |                 {
  62 |                     "enum": re.compile(
  63 |                         r"^(?P<modifiers>(?:export\s+)?(?:const\s+)?)"  # Modifiers
  64 |                         r"enum\s+(?P<enum_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Enum name
  65 |                     ),
  66 |                     "decorator": re.compile(
  67 |                         r"^@(?P<decorator_name>[a-zA-Z_$][a-zA-Z0-9_$]*)"  # Decorator name
  68 |                         r"(?:\s*\((?P<parameters>[^)]*)\))?"  # Optional parameters
  69 |                     ),
  70 |                 }
  71 |             )
  73 |         self.patterns = base_patterns
  74 |         self.modifiers = {
  75 |             "export",
  76 |             "default",
  77 |             "async",
  78 |             "static",
  79 |             "public",
  80 |             "private",
  81 |             "protected",
  82 |             "readonly",
  83 |             "abstract",
  84 |             "declare",
  85 |         }
  86 |         self.block_start = "{"
  87 |         self.block_end = "}"
  88 |         self.line_comment = "//"
  89 |         self.block_comment_start = "/*"
  90 |         self.block_comment_end = "*/"
  92 |     def parse(self, content: str) -> List[Declaration]:
  94 |         lines = content.split("\n")
  95 |         symbols = []
  96 |         brace_count = 0
  97 |         in_comment = False
  98 |         in_template = False
  99 |         pending_decorators = []
 101 |         i = 0
 102 |         while i < len(lines):
 103 |             line = lines[i].strip()
 106 |             if not line:
 107 |                 i += 1
 108 |                 continue
 111 |             if line.startswith("//"):
 112 |                 i += 1
 113 |                 continue
 115 |             if "/*" in line and not in_template:
 116 |                 in_comment = True
 117 |                 if "*/" in line[line.index("/*") :]:
 118 |                     in_comment = False
 119 |                 i += 1
 120 |                 continue
 122 |             if in_comment:
 123 |                 if "*/" in line:
 124 |                     in_comment = False
 125 |                 i += 1
 126 |                 continue
 129 |             if "`" in line:
 130 |                 in_template = not in_template
 132 |             if in_template:
 133 |                 i += 1
 134 |                 continue
 137 |             if self.language == "typescript" and line.startswith("@"):
 138 |                 pending_decorators.append(line)
 139 |                 i += 1
 140 |                 continue
 143 |             for kind, pattern in self.patterns.items():
 144 |                 match = pattern.match(line)
 145 |                 if match:
 146 |                     try:
 147 |                         name = match.group(f"{kind}_name")
 148 |                         modifiers = set()
 149 |                         if "modifiers" in match.groupdict() and match.group("modifiers"):
 150 |                             modifiers = {m.strip() for m in match.group("modifiers").split()}
 151 |                         modifiers.update(pending_decorators)
 152 |                         pending_decorators = []
 155 |                         brace_count += line.count("{") - line.count("}")
 157 |                         symbol = CodeSymbol(
 158 |                             name=name,
 159 |                             kind=kind,
 160 |                             start_line=i,
 161 |                             end_line=i,
 162 |                             modifiers=modifiers,
 163 |                             parent=None,
 164 |                         )
 167 |                         if "{" in line:
 168 |                             j = i + 1
 169 |                             while j < len(lines) and brace_count > 0:
 170 |                                 brace_count += lines[j].count("{") - lines[j].count("}")
 171 |                                 j += 1
 172 |                             symbol.end_line = j - 1
 173 |                             i = j - 1
 175 |                         symbols.append(symbol)
 176 |                         break
 177 |                     except IndexError:
 179 |                         continue
 181 |             i += 1
 184 |         return [
 185 |             Declaration(symbol.kind, symbol.name, symbol.start_line + 1, symbol.end_line + 1)
 186 |             for symbol in symbols
 187 |         ]
 190 | def parse_javascript_or_typescript(
 191 |     file_path: str, content: str, language: str = "javascript"
 192 | ) -> ParsedFileData:
 194 |     parser = JstsParser(language)
 195 |     declarations = parser.parse(content)
 196 |     return ParsedFileData(
 197 |         file_path=file_path, language=language, content=content, declarations=declarations
 198 |     )
```

---
### File: ./codeconcat/parser/language_parsers/python_parser.py
#### Summary
```
File: python_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import Dict, List, Pattern
   6 | from codeconcat.base_types import Declaration, ParsedFileData
   7 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
  10 | class PythonParser(BaseParser):
  13 |     def _setup_patterns(self):
  15 |         self.patterns = {
  16 |             "class": re.compile(
  17 |                 r"^(?P<modifiers>(?:@\w+\s+)*)"  # Decorators
  18 |                 r"class\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Class name
  19 |                 r"\s*(?:\([^)]*\))?\s*:"  # Optional parent class
  20 |             ),
  21 |             "function": re.compile(
  22 |                 r"^(?P<modifiers>(?:@\w+\s+)*)"  # Decorators
  23 |                 r"(?:async\s+)?def\s+(?P<name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Function name
  24 |                 r"\s*\([^)]*\)\s*(?:->[^:]+)?:"  # Args and optional return type
  25 |             ),
  26 |             "constant": re.compile(r"^(?P<name>[A-Z][A-Z0-9_]*)\s*="),  # Constants (UPPER_CASE)
  27 |             "variable": re.compile(
  28 |                 r"^(?P<name>[a-z][a-z0-9_]*)\s*="  # Variables (lower_case)
  29 |                 r"(?!.*(?:def|class)\s)"  # Not part of function/class definition
  30 |             ),
  31 |         }
  33 |         self.modifiers = {"@classmethod", "@staticmethod", "@property", "@abstractmethod"}
  34 |         self.block_start = ":"
  35 |         self.block_end = None  # Python uses indentation
  36 |         self.line_comment = "#"
  37 |         self.block_comment_start = '"""'
  38 |         self.block_comment_end = '"""'
  40 |     def parse(self, content: str) -> List[Declaration]:
  42 |         lines = content.split("\n")
  43 |         symbols = []
  44 |         indent_stack = [0]
  45 |         current_indent = 0
  46 |         pending_decorators = []
  48 |         i = 0
  49 |         while i < len(lines):
  50 |             line = lines[i]
  51 |             stripped = line.lstrip()
  54 |             if not stripped or stripped.startswith(self.line_comment):
  55 |                 i += 1
  56 |                 continue
  59 |             if stripped.startswith('"""') or stripped.startswith("'''"):
  60 |                 doc_end = self._find_docstring_end(lines, i)
  61 |                 if doc_end > i:
  62 |                     if self.current_symbol and not self.current_symbol.docstring:
  63 |                         self.current_symbol.docstring = "\n".join(lines[i : doc_end + 1])
  64 |                     i = doc_end + 1
  65 |                     continue
  68 |             if stripped.startswith("@"):
  69 |                 pending_decorators.append(stripped)
  70 |                 i += 1
  71 |                 continue
  74 |             current_indent = len(line) - len(stripped)
  77 |             while current_indent < indent_stack[-1]:
  78 |                 indent_stack.pop()
  79 |                 if self.symbol_stack:
  80 |                     symbol = self.symbol_stack.pop()
  81 |                     symbol.end_line = i - 1
  82 |                     symbols.append(symbol)
  85 |             for kind, pattern in self.patterns.items():
  86 |                 match = pattern.match(stripped)
  87 |                 if match:
  88 |                     name = match.group("name")
  89 |                     modifiers = set(pending_decorators)
  90 |                     pending_decorators = []  # Clear pending decorators
  92 |                     symbol = CodeSymbol(
  93 |                         name=name,
  94 |                         kind=kind,
  95 |                         start_line=i - len(modifiers),  # Account for decorators
  96 |                         end_line=i,
  97 |                         modifiers=modifiers,
  98 |                         parent=self.symbol_stack[-1] if self.symbol_stack else None,
  99 |                     )
 101 |                     if kind in ("class", "function"):
 102 |                         indent_stack.append(current_indent)
 103 |                         self.symbol_stack.append(symbol)
 104 |                     else:
 105 |                         symbols.append(symbol)
 106 |                     break
 107 |             else:
 109 |                 pending_decorators = []
 111 |             i += 1
 114 |         while self.symbol_stack:
 115 |             symbol = self.symbol_stack.pop()
 116 |             symbol.end_line = len(lines) - 1
 117 |             symbols.append(symbol)
 120 |         return [
 121 |             Declaration(symbol.kind, symbol.name, symbol.start_line + 1, symbol.end_line + 1)
 122 |             for symbol in symbols
 123 |         ]
 125 |     def _find_docstring_end(self, lines: List[str], start: int) -> int:
 127 |         quote = '"""' if lines[start].strip().startswith('"""') else "'''"
 128 |         for i in range(start + 1, len(lines)):
 129 |             if quote in lines[i]:
 130 |                 return i
 131 |         return start
 134 | def parse_python(file_path: str, content: str) -> ParsedFileData:
 136 |     parser = PythonParser()
 137 |     declarations = parser.parse(content)
 138 |     return ParsedFileData(
 139 |         file_path=file_path, language="python", content=content, declarations=declarations
 140 |     )
```

---
### File: ./codeconcat/parser/language_parsers/base_parser.py
#### Summary
```
File: base_parser.py
Language: python
```

```python
   3 | import re
   4 | from abc import ABC, abstractmethod
   5 | from dataclasses import dataclass
   6 | from typing import Dict, List, Optional, Pattern, Set, Tuple
   9 | @dataclass
  10 | class CodeSymbol:
  13 |     name: str
  14 |     kind: str
  15 |     start_line: int
  16 |     end_line: int
  17 |     modifiers: Set[str]
  18 |     parent: Optional["CodeSymbol"] = None
  19 |     children: List["CodeSymbol"] = None
  20 |     docstring: Optional[str] = None
  22 |     def __post_init__(self):
  23 |         if self.children is None:
  24 |             self.children = []
  27 | class BaseParser(ABC):
  30 |     def __init__(self):
  31 |         self.symbols: List[CodeSymbol] = []
  32 |         self.current_symbol: Optional[CodeSymbol] = None
  33 |         self.symbol_stack: List[CodeSymbol] = []
  34 |         self._setup_patterns()
  36 |     @abstractmethod
  37 |     def _setup_patterns(self):
  39 |         self.patterns: Dict[str, Pattern] = {}
  40 |         self.modifiers: Set[str] = set()
  41 |         self.block_start: str = "{"
  42 |         self.block_end: str = "}"
  43 |         self.line_comment: str = "//"
  44 |         self.block_comment_start: str = "/*"
  45 |         self.block_comment_end: str = "*/"
  47 |     def parse(self, content: str) -> List[Tuple[str, int, int]]:
  49 |         self.symbols = []
  50 |         self.current_symbol = None
  51 |         self.symbol_stack = []
  53 |         lines = content.split("\n")
  54 |         in_comment = False
  55 |         brace_count = 0
  56 |         comment_buffer = []
  58 |         for i, line in enumerate(lines):
  59 |             stripped_line = line.strip()
  62 |             if self.block_comment_start in line and not in_comment:
  63 |                 in_comment = True
  64 |                 comment_start = line.index(self.block_comment_start)
  65 |                 comment_buffer.append(line[comment_start + 2 :])
  66 |                 continue
  68 |             if in_comment:
  69 |                 if self.block_comment_end in line:
  70 |                     in_comment = False
  71 |                     comment_end = line.index(self.block_comment_end)
  72 |                     comment_buffer.append(line[:comment_end])
  73 |                     if self.current_symbol and not self.current_symbol.docstring:
  74 |                         self.current_symbol.docstring = "\n".join(comment_buffer).strip()
  75 |                     comment_buffer = []
  76 |                 else:
  77 |                     comment_buffer.append(line)
  78 |                 continue
  80 |             if stripped_line.startswith(self.line_comment):
  81 |                 continue
  84 |             if not self.current_symbol:
  86 |                 for kind, pattern in self.patterns.items():
  87 |                     match = pattern.match(line)
  88 |                     if match:
  89 |                         name = match.group("name")
  90 |                         modifiers = (
  91 |                             set(m.strip() for m in match.group("modifiers").split())
  92 |                             if "modifiers" in match.groupdict()
  93 |                             else set()
  94 |                         )
  96 |                         symbol = CodeSymbol(
  97 |                             name=name,
  98 |                             kind=kind,
  99 |                             start_line=i,
 100 |                             end_line=i,
 101 |                             modifiers=modifiers & self.modifiers,
 102 |                         )
 104 |                         if self.symbol_stack:
 105 |                             symbol.parent = self.symbol_stack[-1]
 106 |                             self.symbol_stack[-1].children.append(symbol)
 108 |                         self.current_symbol = symbol
 109 |                         self.symbol_stack.append(symbol)
 110 |                         break
 113 |             brace_count += line.count(self.block_start) - line.count(self.block_end)
 116 |             if self.current_symbol and brace_count == 0:
 117 |                 if self.block_end in line or ";" in line:
 118 |                     self.current_symbol.end_line = i
 119 |                     self.symbols.append(self.current_symbol)
 120 |                     self.symbol_stack.pop()
 121 |                     self.current_symbol = self.symbol_stack[-1] if self.symbol_stack else None
 124 |         return [(s.name, s.start_line, s.end_line) for s in self.symbols]
 126 |     def _create_pattern(self, base_pattern: str, modifiers: Optional[List[str]] = None) -> Pattern:
 128 |         if modifiers:
 129 |             modifier_pattern = f"(?:(?:{' |'.join(modifiers)})\\s+)*"
 130 |             return re.compile(f"^\\s*{modifier_pattern}?{base_pattern}")
 131 |         return re.compile(f"^\\s*{base_pattern}")
 133 |     @staticmethod
 134 |     def extract_docstring(lines: List[str], start: int, end: int) -> Optional[str]:
 136 |         for i in range(start, min(end + 1, len(lines))):
 137 |             line = lines[i].strip()
 138 |             if line.startswith('"""') or line.startswith("'''"):
 139 |                 doc_lines = []
 140 |                 quote = line[:3]
 141 |                 if line.endswith(quote) and len(line) > 3:
 142 |                     return line[3:-3].strip()
 143 |                 doc_lines.append(line[3:])
 144 |                 for j in range(i + 1, end + 1):
 145 |                     line = lines[j].strip()
 146 |                     if line.endswith(quote):
 147 |                         doc_lines.append(line[:-3])
 148 |                         return "\n".join(doc_lines).strip()
 149 |                     doc_lines.append(line)
 150 |         return None
```

---
### File: ./codeconcat/parser/language_parsers/java_parser.py
#### Summary
```
File: java_parser.py
Language: python
```

```python
   3 | from typing import List
   5 | from codeconcat.base_types import Declaration
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser
   9 | class JavaParser(BaseParser):
  12 |     def _setup_patterns(self):
  15 |         self.package_pattern = self._create_pattern(r"package\s+([\w.]+);")
  18 |         self.import_pattern = self._create_pattern(r"import\s+(?:static\s+)?([\w.*]+);")
  21 |         self.class_pattern = self._create_pattern(
  22 |             r"(?:public\s+|protected\s+|private\s+)?"
  23 |             r"(?:abstract\s+|final\s+)?"
  24 |             r"(?:class|interface|enum)\s+"
  25 |             r"(\w+)"
  26 |             r"(?:\s+extends\s+\w+)?"
  27 |             r"(?:\s+implements\s+[\w,\s]+)?"
  28 |             r"\s*{"
  29 |         )
  32 |         self.method_pattern = self._create_pattern(
  33 |             r"(?:public\s+|protected\s+|private\s+)?"
  34 |             r"(?:static\s+|final\s+|abstract\s+|synchronized\s+)*"
  35 |             r"(?:<[\w\s,<>]+>\s+)?"  # Generic type parameters
  36 |             r"(?:[\w.<>[\],\s]+\s+)?"  # Return type (optional for constructors)
  37 |             r"(\w+)"  # Method name
  38 |             r"\s*\([^)]*\)"  # Parameters
  39 |             r"(?:\s+throws\s+[\w,\s]+)?"  # Throws clause
  40 |             r"\s*(?:{|;)"  # Body or abstract method
  41 |         )
  44 |         self.field_pattern = self._create_pattern(
  45 |             r"(?:public\s+|protected\s+|private\s+)?"
  46 |             r"(?:static\s+|final\s+|volatile\s+|transient\s+)*"
  47 |             r"[\w.<>[\],\s]+\s+"  # Type
  48 |             r"(\w+)"  # Field name
  49 |             r"(?:\s*=\s*[^;]+)?;"  # Optional initialization
  50 |         )
  53 |         self.annotation_pattern = self._create_pattern(r"@(\w+)(?:\s*\([^)]*\))?")
  55 |     def parse(self, content: str) -> List[Declaration]:
  57 |         lines = content.split("\n")
  58 |         symbols = []
  59 |         brace_count = 0
  60 |         in_comment = False
  61 |         current_package = None
  62 |         current_class = None
  64 |         i = 0
  65 |         while i < len(lines):
  66 |             line = lines[i].strip()
  69 |             if not line:
  70 |                 i += 1
  71 |                 continue
  74 |             if line.startswith("/*"):
  75 |                 in_comment = True
  76 |                 if "*/" in line[2:]:
  77 |                     in_comment = False
  78 |                 i += 1
  79 |                 continue
  80 |             if in_comment:
  81 |                 if "*/" in line:
  82 |                     in_comment = False
  83 |                 i += 1
  84 |                 continue
  87 |             if line.startswith("//"):
  88 |                 i += 1
  89 |                 continue
  92 |             brace_count += line.count("{") - line.count("}")
  95 |             if package_match := self.package_pattern.search(line):
  96 |                 current_package = package_match.group(1)
  97 |                 i += 1
  98 |                 continue
 101 |             if class_match := self.class_pattern.search(line):
 102 |                 class_name = class_match.group(1)
 103 |                 qualified_name = (
 104 |                     f"{current_package}.{class_name}" if current_package else class_name
 105 |                 )
 106 |                 current_class = qualified_name
 107 |                 symbols.append(
 108 |                     Declaration(kind="class", name=qualified_name, start_line=i, end_line=i)
 109 |                 )
 110 |                 i += 1
 111 |                 continue
 114 |             if method_match := self.method_pattern.search(line):
 115 |                 method_name = method_match.group(1)
 116 |                 qualified_name = f"{current_class}.{method_name}" if current_class else method_name
 117 |                 symbols.append(
 118 |                     Declaration(kind="function", name=qualified_name, start_line=i, end_line=i)
 119 |                 )
 120 |                 i += 1
 121 |                 continue
 124 |             if field_match := self.field_pattern.search(line):
 125 |                 field_name = field_match.group(1)
 126 |                 qualified_name = f"{current_class}.{field_name}" if current_class else field_name
 127 |                 symbols.append(
 128 |                     Declaration(kind="symbol", name=qualified_name, start_line=i, end_line=i)
 129 |                 )
 131 |             i += 1
 133 |         return symbols
 136 | def parse_java(file_path: str, content: str) -> List[Declaration]:
 138 |     parser = JavaParser()
 139 |     return parser.parse(content)
```

---
### File: ./codeconcat/parser/language_parsers/cpp_parser.py
#### Summary
```
File: cpp_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Tuple
   7 | def parse_cpp_code(content: str) -> List[Tuple[str, int, int]]:
  10 |     Returns:
  11 |         List of tuples (symbol_name, start_line, end_line)
  13 |     symbols = []
  14 |     lines = content.split("\n")
  17 |     patterns = {
  18 |         "class": r"^\s*(?:template\s*<[^>]*>\s*)?(?:class|struct)\s+([a-zA-Z_][a-zA-Z0-9_]*)",
  19 |         "function": r"^\s*(?:template\s*<[^>]*>\s*)?(?:[a-zA-Z_][a-zA-Z0-9_:]*\s+)?([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*(?:const)?\s*(?:noexcept)?\s*(?:override)?\s*(?:final)?\s*(?:=\s*(?:default|delete))?\s*(?:{\s*)?$",
  20 |         "namespace": r"^\s*namespace\s+([a-zA-Z_][a-zA-Z0-9_]*)",
  21 |         "enum": r"^\s*enum(?:\s+class)?\s+([a-zA-Z_][a-zA-Z0-9_]*)",
  22 |         "typedef": r"^\s*typedef\s+[^;]+\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*;",
  23 |         "using": r"^\s*using\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*=",
  24 |     }
  26 |     in_block = False
  27 |     block_start = 0
  28 |     block_name = ""
  29 |     brace_count = 0
  30 |     in_comment = False
  32 |     for i, line in enumerate(lines):
  34 |         if "/*" in line:
  35 |             in_comment = True
  36 |         if "*/" in line:
  37 |             in_comment = False
  38 |             continue
  39 |         if in_comment or line.strip().startswith("//"):
  40 |             continue
  43 |         if line.strip().startswith("#"):
  44 |             continue
  47 |         if not in_block:
  48 |             for construct, pattern in patterns.items():
  49 |                 match = re.match(pattern, line)
  50 |                 if match:
  51 |                     block_name = match.group(1)
  52 |                     block_start = i
  53 |                     in_block = True
  54 |                     brace_count = line.count("{") - line.count("}")
  56 |                     if brace_count == 0 and ";" in line:
  57 |                         symbols.append((block_name, i, i))
  58 |                         in_block = False
  59 |                     break
  60 |         else:
  61 |             brace_count += line.count("{") - line.count("}")
  64 |         if in_block and brace_count == 0 and ("}" in line or ";" in line):
  65 |             symbols.append((block_name, block_start, i))
  66 |             in_block = False
  68 |     return symbols
```

---
### File: ./codeconcat/parser/language_parsers/r_parser.py
#### Summary
```
File: r_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import Dict, List, Pattern
   6 | from codeconcat.base_types import Declaration, ParsedFileData
   7 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
  10 | class RParser(BaseParser):
  13 |     def _setup_patterns(self):
  15 |         self.patterns = {
  16 |             "function": re.compile(
  17 |                 r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
  18 |                 r"(?P<func_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Function name
  19 |                 r"\s*<?-\s*function\s*\("  # Assignment and function declaration
  20 |             ),
  21 |             "class": re.compile(
  22 |                 r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
  23 |                 r'setClass\s*\(\s*["\'](?P<class_name>[a-zA-Z_][a-zA-Z0-9_]*)["\']'  # S4 class definition
  24 |             ),
  25 |             "method": re.compile(
  26 |                 r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
  27 |                 r'setMethod\s*\(\s*["\'](?P<method_name>[a-zA-Z_][a-zA-Z0-9_]*)["\']'  # S4 method definition
  28 |             ),
  29 |             "constant": re.compile(
  30 |                 r"^(?P<const_name>[A-Z][A-Z0-9_]*)"  # Constant name
  31 |                 r"\s*<?-\s*"  # Assignment
  32 |             ),
  33 |             "variable": re.compile(
  34 |                 r"^(?P<var_name>[a-z][a-z0-9_.]*)"  # Variable name
  35 |                 r"\s*<?-\s*(?!function)"  # Assignment, not a function
  36 |             ),
  37 |             "package": re.compile(
  38 |                 r"^(?P<modifiers>(?:export\s+)?)"  # Optional export
  39 |                 r'(?:library|require)\s*\(\s*["\']?(?P<package_name>[a-zA-Z_][a-zA-Z0-9_]*)["\']?\s*\)'  # Package import
  40 |             ),
  41 |         }
  43 |         self.modifiers = {"export"}
  44 |         self.block_start = "{"
  45 |         self.block_end = "}"
  46 |         self.line_comment = "#"
  47 |         self.block_comment_start = None  # R doesn't have block comments
  48 |         self.block_comment_end = None
  50 |     def parse(self, content: str) -> List[Declaration]:
  52 |         lines = content.split("\n")
  53 |         symbols = []
  54 |         brace_count = 0
  55 |         current_class = None
  57 |         i = 0
  58 |         while i < len(lines):
  59 |             line = lines[i].strip()
  62 |             if not line or line.startswith("#"):
  63 |                 i += 1
  64 |                 continue
  67 |             for kind, pattern in self.patterns.items():
  68 |                 match = pattern.match(line)
  69 |                 if match:
  70 |                     name_group = f"{kind}_name"
  71 |                     name = match.group(name_group)
  72 |                     modifiers = set()
  73 |                     if "modifiers" in match.groupdict() and match.group("modifiers"):
  74 |                         modifiers = {m.strip() for m in match.group("modifiers").split()}
  77 |                     symbol = CodeSymbol(
  78 |                         name=name,
  79 |                         kind=kind,
  80 |                         start_line=i,
  81 |                         end_line=i,
  82 |                         modifiers=modifiers,
  83 |                         parent=current_class,
  84 |                     )
  87 |                     if kind in ("function", "class", "method"):
  89 |                         brace_count = line.count("{")
  90 |                         j = i + 1
  91 |                         while j < len(lines) and (brace_count > 0 or "{" not in line):
  92 |                             line = lines[j].strip()
  93 |                             brace_count += line.count("{") - line.count("}")
  94 |                             j += 1
  96 |                         if j > i + 1:
  97 |                             symbol.end_line = j - 1
  98 |                             i = j - 1
 101 |                         if kind == "class":
 102 |                             current_class = symbol
 104 |                     symbols.append(symbol)
 105 |                     break
 107 |             i += 1
 110 |         return [
 111 |             Declaration(symbol.kind, symbol.name, symbol.start_line + 1, symbol.end_line + 1)
 112 |             for symbol in symbols
 113 |         ]
 116 | def parse_r(file_path: str, content: str) -> ParsedFileData:
 118 |     parser = RParser()
 119 |     declarations = parser.parse(content)
 120 |     return ParsedFileData(
 121 |         file_path=file_path, language="r", content=content, declarations=declarations
 122 |     )
```

---
### File: ./codeconcat/parser/language_parsers/go_parser.py
#### Summary
```
File: go_parser.py
Language: python
```

```python
   3 | from typing import List
   5 | from codeconcat.base_types import Declaration
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser
   9 | class GoParser(BaseParser):
  12 |     def _setup_patterns(self):
  15 |         self.package_pattern = self._create_pattern(r"package\s+(\w+)")
  18 |         self.import_pattern = self._create_pattern(r'import\s+(?:\(\s*|\s*"?)([^"\s]+)"?')
  21 |         self.func_pattern = self._create_pattern(
  22 |             r"func\s+"  # func keyword
  23 |             r"(?:\([^)]+\)\s+)?"  # Optional receiver for methods
  24 |             r"(\w+)"  # Function name
  25 |             r"\s*\([^)]*\)"  # Parameters
  26 |             r"(?:\s*\([^)]*\)|\s+[\w.*\[\]{}<>,\s]+)?"  # Optional return type(s)
  27 |             r"\s*{"  # Function body start
  28 |         )
  31 |         self.type_pattern = self._create_pattern(
  32 |             r"type\s+"
  33 |             r"(\w+)\s+"  # Type name
  34 |             r"(?:struct|interface)\s*{"  # Type kind
  35 |         )
  38 |         self.var_pattern = self._create_pattern(
  39 |             r"(?:var|const)\s+"
  40 |             r"(\w+)"  # Variable name
  41 |             r"(?:\s+[\w.*\[\]{}<>,\s]+)?"  # Optional type
  42 |             r"(?:\s*=\s*[^;]+)?"  # Optional value
  43 |         )
  45 |     def parse(self, content: str) -> List[Declaration]:
  47 |         lines = content.split("\n")
  48 |         symbols = []
  49 |         brace_count = 0
  50 |         in_comment = False
  51 |         current_package = None
  53 |         i = 0
  54 |         while i < len(lines):
  55 |             line = lines[i].strip()
  58 |             if not line:
  59 |                 i += 1
  60 |                 continue
  63 |             if line.startswith("/*"):
  64 |                 in_comment = True
  65 |                 if "*/" in line[2:]:
  66 |                     in_comment = False
  67 |                 i += 1
  68 |                 continue
  69 |             if in_comment:
  70 |                 if "*/" in line:
  71 |                     in_comment = False
  72 |                 i += 1
  73 |                 continue
  76 |             if line.startswith("//"):
  77 |                 i += 1
  78 |                 continue
  81 |             brace_count += line.count("{") - line.count("}")
  84 |             if package_match := self.package_pattern.search(line):
  85 |                 current_package = package_match.group(1)
  86 |                 i += 1
  87 |                 continue
  90 |             if func_match := self.func_pattern.search(line):
  91 |                 func_name = func_match.group(1)
  92 |                 qualified_name = f"{current_package}.{func_name}" if current_package else func_name
  93 |                 symbols.append(
  94 |                     Declaration(kind="function", name=qualified_name, start_line=i, end_line=i)
  95 |                 )
  96 |                 i += 1
  97 |                 continue
 100 |             if type_match := self.type_pattern.search(line):
 101 |                 type_name = type_match.group(1)
 102 |                 qualified_name = f"{current_package}.{type_name}" if current_package else type_name
 103 |                 symbols.append(
 104 |                     Declaration(
 105 |                         kind="class",  # Using class for both struct and interface
 106 |                         name=qualified_name,
 107 |                         start_line=i,
 108 |                         end_line=i,
 109 |                     )
 110 |                 )
 111 |                 i += 1
 112 |                 continue
 115 |             if var_match := self.var_pattern.search(line):
 116 |                 var_name = var_match.group(1)
 117 |                 qualified_name = f"{current_package}.{var_name}" if current_package else var_name
 118 |                 symbols.append(
 119 |                     Declaration(kind="symbol", name=qualified_name, start_line=i, end_line=i)
 120 |                 )
 122 |             i += 1
 124 |         return symbols
 127 | def parse_go(file_path: str, content: str) -> List[Declaration]:
 129 |     parser = GoParser()
 130 |     return parser.parse(content)
```

---
### File: ./codeconcat/writer/markdown_writer.py
#### Summary
```
File: markdown_writer.py
Language: python
```

```python
   1 | import random
   2 | from typing import Dict, List
   4 | import tiktoken
   5 | from halo import Halo
   7 | from codeconcat.base_types import (
   8 |     PROGRAMMING_QUOTES,
   9 |     AnnotatedFileData,
  10 |     CodeConCatConfig,
  11 |     ParsedDocData,
  12 |     ParsedFileData,
  13 | )
  14 | from codeconcat.processor.content_processor import (
  15 |     generate_directory_structure,
  16 |     generate_file_summary,
  17 |     process_file_content,
  18 | )
  19 | from codeconcat.writer.ai_context import generate_ai_preamble
  22 | def count_tokens(text: str) -> int:
  24 |     try:
  25 |         encoder = tiktoken.get_encoding("cl100k_base")
  26 |         return len(encoder.encode(text))
  27 |     except Exception as e:
  28 |         print(f"Warning: Tiktoken encoding failed ({str(e)}), falling back to word count")
  29 |         return len(text.split())
  32 | def print_quote_with_ascii(total_output_tokens: int = None):
  34 |     quote = random.choice(PROGRAMMING_QUOTES)
  35 |     quote_tokens = count_tokens(quote)
  38 |     width = max(len(line) for line in quote.split("\n")) + 4
  41 |     top_border = "+" + "=" * (width - 2) + "+"
  42 |     empty_line = "|" + " " * (width - 2) + "|"
  45 |     output_lines = ["\n[CodeConCat] Meow:", top_border, empty_line]
  48 |     words = quote.split()
  49 |     current_line = "|  "
  50 |     for word in words:
  51 |         if len(current_line) + len(word) + 1 > width - 2:
  52 |             output_lines.append(current_line + " " * (width - len(current_line) - 1) + "|")
  53 |             current_line = "|  " + word
  54 |         else:
  55 |             if current_line == "|  ":
  56 |                 current_line += word
  57 |             else:
  58 |                 current_line += " " + word
  59 |     output_lines.append(current_line + " " * (width - len(current_line) - 1) + "|")
  61 |     output_lines.extend([empty_line, top_border])
  64 |     print("\n".join(output_lines))
  65 |     print(f"\nQuote tokens (GPT-4): {quote_tokens:,}")
  66 |     if total_output_tokens:
  67 |         print(f"Total CodeConcat output tokens (GPT-4): {total_output_tokens:,}")
  70 | def write_markdown(
  71 |     annotated_files: List[AnnotatedFileData],
  72 |     docs: List[ParsedDocData],
  73 |     config: CodeConCatConfig,
  74 |     folder_tree_str: str = "",
  75 | ) -> str:
  76 |     spinner = Halo(text="Generating CodeConcat output", spinner="dots")
  77 |     spinner.start()
  79 |     output_chunks = []
  80 |     output_chunks.append("# CodeConCat Output\n\n")
  83 |     spinner.text = "Generating AI preamble"
  84 |     parsed_files = [
  85 |         ParsedFileData(
  86 |             file_path=ann.file_path, language=ann.language, content=ann.content, declarations=[]
  87 |         )
  88 |         for ann in annotated_files
  89 |     ]
  90 |     output_chunks.append(generate_ai_preamble(parsed_files, docs, {}))
  93 |     if config.include_directory_structure:
  94 |         spinner.text = "Generating directory structure"
  95 |         output_chunks.append("## Directory Structure\n")
  96 |         output_chunks.append("```\n")
  97 |         all_files = [f.file_path for f in annotated_files] + [d.file_path for d in docs]
  98 |         dir_structure = generate_directory_structure(all_files)
  99 |         output_chunks.append(dir_structure)
 100 |         output_chunks.append("\n```\n\n")
 101 |     elif folder_tree_str:  # Fallback to provided folder tree
 102 |         output_chunks.append("## Folder Tree\n")
 103 |         output_chunks.append("```\n")
 104 |         output_chunks.append(folder_tree_str)
 105 |         output_chunks.append("\n```\n\n")
 108 |     if annotated_files:
 109 |         spinner.text = "Processing code files"
 110 |         output_chunks.append("## Code Files\n\n")
 111 |         for i, ann in enumerate(annotated_files, 1):
 112 |             spinner.text = f"Processing code file {i}/{len(annotated_files)}: {ann.file_path}"
 113 |             output_chunks.append(f"### File: {ann.file_path}\n")
 114 |             if config.include_file_summary:
 115 |                 summary = generate_file_summary(
 116 |                     ParsedFileData(
 117 |                         file_path=ann.file_path,
 118 |                         language=ann.language,
 119 |                         content=ann.content,
 120 |                         declarations=[],
 121 |                     )
 122 |                 )
 123 |                 output_chunks.append(f"#### Summary\n```\n{summary}\n```\n\n")
 125 |             processed_content = process_file_content(ann.content, config)
 126 |             output_chunks.append(f"```{ann.language}\n{processed_content}\n```\n")
 127 |             output_chunks.append("\n---\n")
 130 |     if docs:
 131 |         spinner.text = "Processing documentation files"
 132 |         output_chunks.append("## Documentation\n\n")
 133 |         for i, doc in enumerate(docs, 1):
 134 |             spinner.text = f"Processing doc file {i}/{len(docs)}: {doc.file_path}"
 135 |             output_chunks.append(f"### File: {doc.file_path}\n")
 136 |             if config.include_file_summary:
 137 |                 summary = generate_file_summary(
 138 |                     ParsedFileData(
 139 |                         file_path=doc.file_path,
 140 |                         language=doc.doc_type,
 141 |                         content=doc.content,
 142 |                         declarations=[],
 143 |                     )
 144 |                 )
 145 |                 output_chunks.append(f"#### Summary\n```\n{summary}\n```\n\n")
 147 |             processed_content = process_file_content(doc.content, config)
 148 |             output_chunks.append(f"```{doc.doc_type}\n{processed_content}\n```\n")
 149 |             output_chunks.append("\n---\n")
 151 |     spinner.text = "Finalizing output"
 152 |     final_str = "".join(output_chunks)
 155 |     spinner.text = "Counting tokens"
 156 |     output_tokens = count_tokens(final_str)
 158 |     with open(config.output, "w", encoding="utf-8") as f:
 159 |         f.write(final_str)
 161 |         f.write("\n\n## Token Statistics\n")
 162 |         f.write(f"Total CodeConcat output tokens (GPT-4): {output_tokens:,}\n")
 164 |     spinner.succeed("CodeConcat output generated successfully")
 165 |     print(f"[CodeConCat] Markdown output written to: {config.output}")
 168 |     print_quote_with_ascii(output_tokens)
 170 |     return final_str
```

---
### File: ./codeconcat/writer/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python

```

---
### File: ./codeconcat/writer/xml_writer.py
#### Summary
```
File: xml_writer.py
Language: python
```

```python
   3 | import xml.etree.ElementTree as ET
   4 | from typing import Dict, List, Optional
   5 | from xml.dom import minidom
   7 | from codeconcat.base_types import AnnotatedFileData, ParsedDocData, ParsedFileData
  10 | def write_xml(
  11 |     code_files: List[ParsedFileData],
  12 |     doc_files: List[ParsedDocData],
  13 |     file_annotations: Dict[str, AnnotatedFileData],
  14 |     folder_tree: Optional[str] = None,
  15 | ) -> str:
  18 |     root = ET.Element("codeconcat")
  21 |     metadata = ET.SubElement(root, "metadata")
  22 |     ET.SubElement(metadata, "total_files").text = str(len(code_files) + len(doc_files))
  23 |     ET.SubElement(metadata, "code_files").text = str(len(code_files))
  24 |     ET.SubElement(metadata, "doc_files").text = str(len(doc_files))
  27 |     if folder_tree:
  28 |         tree_elem = ET.SubElement(root, "folder_tree")
  29 |         tree_elem.text = folder_tree
  32 |     code_section = ET.SubElement(root, "code_files")
  33 |     for file in code_files:
  34 |         file_elem = ET.SubElement(code_section, "file")
  35 |         ET.SubElement(file_elem, "path").text = file.file_path
  36 |         ET.SubElement(file_elem, "language").text = file.language
  39 |         annotation = file_annotations.get(file.file_path)
  40 |         if annotation:
  41 |             annotations_elem = ET.SubElement(file_elem, "annotations")
  42 |             if annotation.summary:
  43 |                 ET.SubElement(annotations_elem, "summary").text = annotation.summary
  44 |             if annotation.tags:
  45 |                 tags_elem = ET.SubElement(annotations_elem, "tags")
  46 |                 for tag in annotation.tags:
  47 |                     ET.SubElement(tags_elem, "tag").text = tag
  50 |         content_elem = ET.SubElement(file_elem, "content")
  51 |         content_elem.text = f"<![CDATA[{file.content}]]>"
  54 |     if doc_files:
  55 |         docs_section = ET.SubElement(root, "doc_files")
  56 |         for doc in doc_files:
  57 |             doc_elem = ET.SubElement(docs_section, "file")
  58 |             ET.SubElement(doc_elem, "path").text = doc.file_path
  59 |             ET.SubElement(doc_elem, "format").text = doc.format
  60 |             content_elem = ET.SubElement(doc_elem, "content")
  61 |             content_elem.text = f"<![CDATA[{doc.content}]]>"
  64 |     xml_str = ET.tostring(root, encoding="unicode")
  65 |     pretty_xml = minidom.parseString(xml_str).toprettyxml(indent="  ")
  67 |     return pretty_xml
```

---
### File: ./codeconcat/writer/ai_context.py
#### Summary
```
File: ai_context.py
Language: python
```

```python
   3 | from typing import Dict, List
   5 | from codeconcat.base_types import AnnotatedFileData, ParsedDocData, ParsedFileData
   8 | def generate_ai_preamble(
   9 |     code_files: List[ParsedFileData],
  10 |     doc_files: List[ParsedDocData],
  11 |     file_annotations: Dict[str, AnnotatedFileData],
  12 | ) -> str:
  16 |     file_types = {}
  17 |     for file in code_files:
  18 |         ext = file.file_path.split(".")[-1] if "." in file.file_path else "unknown"
  19 |         file_types[ext] = file_types.get(ext, 0) + 1
  22 |     lines = [
  23 |         "# CodeConcat AI-Friendly Code Summary",
  24 |         "",
  25 |         "This document contains a structured representation of a codebase, organized for AI analysis.",
  26 |         "",
  27 |         "## Repository Structure",
  28 |         "```",
  29 |         f"Total code files: {len(code_files)}",
  30 |         f"Documentation files: {len(doc_files)}",
  31 |         "",
  32 |         "File types:",
  33 |     ]
  35 |     for ext, count in sorted(file_types.items()):
  36 |         lines.append(f"- {ext}: {count} files")
  38 |     lines.extend(
  39 |         [
  40 |             "```",
  41 |             "",
  42 |             "## Code Organization",
  43 |             "The code is organized into sections, each prefixed with clear markers:",
  44 |             "- Directory markers show file organization",
  45 |             "- File headers contain metadata and imports",
  46 |             "- Annotations provide context about code purpose",
  47 |             "- Documentation sections contain project documentation",
  48 |             "",
  49 |             "## Navigation",
  50 |             "- Each file begins with '---FILE:' followed by its path",
  51 |             "- Each section is clearly delimited with markdown headers",
  52 |             "- Code blocks are formatted with appropriate language tags",
  53 |             "",
  54 |             "## Content Summary",
  55 |         ]
  56 |     )
  59 |     for file in code_files:
  60 |         annotation = file_annotations.get(file.file_path, AnnotatedFileData(file.file_path, "", []))
  61 |         if annotation.summary:
  62 |             lines.append(f"- `{file.file_path}`: {annotation.summary}")
  64 |     lines.extend(["", "---", "Begin code content below:", ""])
  66 |     return "\n".join(lines)
```

---
### File: ./codeconcat/writer/json_writer.py
#### Summary
```
File: json_writer.py
Language: python
```

```python
   1 | import json
   2 | from typing import List
   4 | from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedDocData
   7 | def write_json(
   8 |     annotated_files: List[AnnotatedFileData],
   9 |     docs: List[ParsedDocData],
  10 |     config: CodeConCatConfig,
  11 |     folder_tree_str: str = "",
  12 | ) -> str:
  13 |     data = {"files": []}  # Single list of all files with clear type indicators
  16 |     if folder_tree_str:
  17 |         data["folder_tree"] = folder_tree_str
  20 |     for ann in annotated_files:
  21 |         data["files"].append(
  22 |             {
  23 |                 "type": "code",
  24 |                 "file_path": ann.file_path,
  25 |                 "language": ann.language,
  26 |                 "content": ann.content,
  27 |                 "annotated_content": ann.annotated_content,
  28 |                 "summary": ann.summary,
  29 |                 "tags": ann.tags,
  30 |             }
  31 |         )
  34 |     for doc in docs:
  35 |         data["files"].append(
  36 |             {
  37 |                 "type": "documentation",
  38 |                 "file_path": doc.file_path,
  39 |                 "doc_type": doc.doc_type,
  40 |                 "content": doc.content,
  41 |             }
  42 |         )
  44 |     final_json = json.dumps(data, indent=2)
  46 |     with open(config.output, "w", encoding="utf-8") as f:
  47 |         f.write(final_json)
  49 |     print(f"[CodeConCat] JSON output written to: {config.output}")
  50 |     return final_json
```

---


## Token Statistics
Total CodeConcat output tokens (GPT-4): 37,767
