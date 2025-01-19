# CodeConCat Output

# AI-Friendly Code Summary

This document contains a structured representation of a codebase, organized for AI analysis.

## Repository Structure
```
Total code files: 54
Documentation files: 0

File types:
- py: 54 files
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
    ├── setup.py
    ├── app.py
    ├── tests
    │   ├── test_version.py
    │   ├── conftest.py
    │   ├── test_rust_parser.py
    │   ├── test_cpp_parser.py
    │   ├── test_go_parser.py
    │   ├── __init__.py
    │   ├── test_julia_parser.py
    │   ├── test_content_processor.py
    │   ├── test_js_ts_parser.py
    │   ├── test_codeconcat.py
    │   ├── test_python_parser.py
    │   ├── test_php_parser.py
    │   ├── test_java_parser.py
    │   ├── test_annotator.py
    │   └── test_r_parser.py
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

### File: ./setup.py
#### Summary
```
File: setup.py
Language: python
```


---
### File: ./app.py
#### Summary
```
File: app.py
Language: python
```

```python
   1 | from fastapi import FastAPI, HTTPException
   2 | from pydantic import BaseModel
   3 | from typing import Optional, List
   4 | from codeconcat import run_codeconcat_in_memory, CodeConCatConfig
   6 | app = FastAPI(
   7 |     title="CodeConCat API",
   8 |     description="API for CodeConCat - An LLM-friendly code parser, aggregator and doc extractor",
   9 |     version="1.0.0",
  10 | )
  13 | class CodeConcatRequest(BaseModel):
  14 |     target_path: str
  15 |     format: str = "markdown"
  16 |     github_url: Optional[str] = None
  17 |     github_token: Optional[str] = None
  18 |     github_ref: Optional[str] = None
  19 |     extract_docs: bool = False
  20 |     merge_docs: bool = False
  21 |     include_paths: List[str] = []
  22 |     exclude_paths: List[str] = []
  23 |     include_languages: List[str] = []
  24 |     exclude_languages: List[str] = []
  25 |     disable_tree: bool = False
  26 |     disable_annotations: bool = False
  27 |     disable_copy: bool = True  # Default to True for API usage
  28 |     disable_symbols: bool = False
  29 |     disable_ai_context: bool = False
  30 |     max_workers: int = 4
  33 | @app.post("/concat")
  34 | async def concat_code(request: CodeConcatRequest):
  36 |     Process code files and return concatenated output
  38 |     try:
  39 |         config = CodeConCatConfig(
  40 |             target_path=request.target_path,
  41 |             format=request.format,
  42 |             github_url=request.github_url,
  43 |             github_token=request.github_token,
  44 |             github_ref=request.github_ref,
  45 |             extract_docs=request.extract_docs,
  46 |             merge_docs=request.merge_docs,
  47 |             include_paths=request.include_paths,
  48 |             exclude_paths=request.exclude_paths,
  49 |             include_languages=request.include_languages,
  50 |             exclude_languages=request.exclude_languages,
  51 |             disable_tree=request.disable_tree,
  52 |             disable_annotations=request.disable_annotations,
  53 |             disable_copy=request.disable_copy,
  54 |             disable_symbols=request.disable_symbols,
  55 |             disable_ai_context=request.disable_ai_context,
  56 |             max_workers=request.max_workers,
  57 |         )
  58 |         output = run_codeconcat_in_memory(config)
  59 |         return {"output": output}
  60 |     except Exception as e:
  61 |         raise HTTPException(status_code=500, detail=str(e))
  64 | @app.get("/")
  65 | async def root():
  67 |     Root endpoint returning basic API info
  69 |     return {
  70 |         "name": "CodeConCat API",
  71 |         "version": "1.0.0",
  72 |         "description": "API for code concatenation and documentation extraction",
  73 |     }
```

#### Analysis Notes
## File: ./app.py
### Functions
### Classes

---
### File: ./tests/test_version.py
#### Summary
```
File: test_version.py
Language: python
```


---
### File: ./tests/conftest.py
#### Summary
```
File: conftest.py
Language: python
```


---
### File: ./tests/test_rust_parser.py
#### Summary
```
File: test_rust_parser.py
Language: python
```


---
### File: ./tests/test_cpp_parser.py
#### Summary
```
File: test_cpp_parser.py
Language: python
```


---
### File: ./tests/test_go_parser.py
#### Summary
```
File: test_go_parser.py
Language: python
```


---
### File: ./tests/__init__.py
#### Summary
```
File: __init__.py
Language: python
```


---
### File: ./tests/test_julia_parser.py
#### Summary
```
File: test_julia_parser.py
Language: python
```


---
### File: ./tests/test_content_processor.py
#### Summary
```
File: test_content_processor.py
Language: python
```


---
### File: ./tests/test_js_ts_parser.py
#### Summary
```
File: test_js_ts_parser.py
Language: python
```


---
### File: ./tests/test_codeconcat.py
#### Summary
```
File: test_codeconcat.py
Language: python
```


---
### File: ./tests/test_python_parser.py
#### Summary
```
File: test_python_parser.py
Language: python
```


---
### File: ./tests/test_php_parser.py
#### Summary
```
File: test_php_parser.py
Language: python
```


---
### File: ./tests/test_java_parser.py
#### Summary
```
File: test_java_parser.py
Language: python
```


---
### File: ./tests/test_annotator.py
#### Summary
```
File: test_annotator.py
Language: python
```


---
### File: ./tests/test_r_parser.py
#### Summary
```
File: test_r_parser.py
Language: python
```


---
### File: ./codeconcat/version.py
#### Summary
```
File: version.py
Language: python
```

```python
   3 | __version__ = "0.6.1"
```

#### Analysis Notes
## File: ./codeconcat/version.py

---
### File: ./codeconcat/__init__.py
#### Summary
```
File: __init__.py
Language: python
```

```python
   2 | CodeConCat - An LLM-friendly code parser, aggregator and doc extractor.
   5 | from .main import run_codeconcat, run_codeconcat_in_memory
   6 | from .base_types import CodeConCatConfig, AnnotatedFileData, ParsedDocData
   7 | from .version import __version__
   9 | __all__ = [
  10 |     "run_codeconcat",
  11 |     "run_codeconcat_in_memory",
  12 |     "CodeConCatConfig",
  13 |     "AnnotatedFileData",
  14 |     "ParsedDocData",
  15 |     "__version__",
  16 | ]
```

#### Analysis Notes
## File: ./codeconcat/__init__.py

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
   9 | from typing import Any, Dict, List, Optional, Set
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
  28 | VALID_FORMATS = {"markdown", "json", "xml"}
  30 | @dataclass
  31 | class SecurityIssue:
  34 |     line_number: int
  35 |     line_content: str
  36 |     issue_type: str
  37 |     severity: str
  38 |     description: str
  41 | @dataclass
  42 | class TokenStats:
  45 |     gpt3_tokens: int
  46 |     gpt4_tokens: int
  47 |     davinci_tokens: int
  48 |     claude_tokens: int
  51 | @dataclass
  52 | class Declaration:
  55 |     kind: str
  56 |     name: str
  57 |     start_line: int
  58 |     end_line: int
  59 |     modifiers: Set[str] = field(default_factory=set)
  60 |     docstring: str = ""
  62 |     def __post_init__(self):
  64 |         pass
  67 | @dataclass
  68 | class ParsedFileData:
  70 |     Parsed output of a single code file.
  73 |     file_path: str
  74 |     language: str
  75 |     content: str
  76 |     declarations: List[Declaration] = field(default_factory=list)
  77 |     token_stats: Optional[TokenStats] = None
  78 |     security_issues: List[SecurityIssue] = field(default_factory=list)
  81 | @dataclass
  82 | class AnnotatedFileData:
  84 |     A file's annotated content, ready to be written (Markdown/JSON).
  87 |     file_path: str
  88 |     language: str
  89 |     annotated_content: str
  90 |     content: str = ""
  91 |     summary: str = ""
  92 |     tags: List[str] = field(default_factory=list)
  95 | @dataclass
  96 | class ParsedDocData:
  98 |     Represents a doc file, storing raw text + file path + doc type (md, rst, etc.).
 101 |     file_path: str
 102 |     doc_type: str
 103 |     content: str
 106 | @dataclass
 107 | class CodeConCatConfig:
 110 |     Fields:
 111 |       - target_path: local directory or placeholder for GitHub
 112 |       - github_url: optional GitHub repository URL
 113 |       - github_token: personal access token for private repos
 114 |       - github_ref: optional GitHub reference (branch/tag)
 115 |       - include_languages / exclude_languages
 116 |       - include_paths / exclude_paths: patterns for including/excluding
 117 |       - extract_docs: whether to parse docs
 118 |       - merge_docs: whether to merge doc content into the same output
 119 |       - doc_extensions: list of recognized doc file extensions
 120 |       - custom_extension_map: user-specified extension→language
 121 |       - output: final file name
 122 |       - format: 'markdown', 'json', or 'xml'
 123 |       - max_workers: concurrency
 124 |       - disable_tree: whether to disable directory structure
 125 |       - disable_copy: whether to disable copying output
 126 |       - disable_annotations: whether to disable annotations
 127 |       - disable_symbols: whether to disable symbol extraction
 128 |       - include_file_summary: whether to include file summaries
 129 |       - include_directory_structure: whether to show directory structure
 130 |       - remove_comments: whether to remove comments from output
 131 |       - remove_empty_lines: whether to remove empty lines
 132 |       - show_line_numbers: whether to show line numbers
 135 |     target_path: str = "."
 136 |     github_url: Optional[str] = None
 137 |     github_token: Optional[str] = None
 138 |     github_ref: Optional[str] = None
 139 |     include_languages: List[str] = field(default_factory=list)
 140 |     exclude_languages: List[str] = field(default_factory=list)
 141 |     include_paths: List[str] = field(default_factory=list)
 142 |     exclude_paths: List[str] = field(default_factory=list)
 143 |     extract_docs: bool = False
 144 |     merge_docs: bool = False
 145 |     doc_extensions: List[str] = field(default_factory=lambda: [".md", ".rst", ".txt", ".rmd"])
 146 |     custom_extension_map: Dict[str, str] = field(default_factory=dict)
 147 |     output: str = "code_concat_output.md"
 148 |     format: str = "markdown"
 149 |     max_workers: int = 4
 150 |     disable_tree: bool = False
 151 |     disable_copy: bool = False
 152 |     disable_annotations: bool = False
 153 |     disable_symbols: bool = False
 154 |     disable_ai_context: bool = False
 155 |     include_file_summary: bool = True
 156 |     include_directory_structure: bool = True
 157 |     remove_comments: bool = False
 158 |     remove_empty_lines: bool = False
 159 |     show_line_numbers: bool = False
 161 |     def __post_init__(self):
 163 |         if self.format not in VALID_FORMATS:
 164 |             raise ValueError(f"Invalid format '{self.format}'. Must be one of: {', '.join(VALID_FORMATS)}")
```

#### Analysis Notes
## File: ./codeconcat/base_types.py
### Functions
### Classes

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
  27 | class CodeConcatError(Exception):
  30 |     pass
  33 | class ConfigurationError(CodeConcatError):
  36 |     pass
  39 | class FileProcessingError(CodeConcatError):
  42 |     pass
  45 | class OutputError(CodeConcatError):
  48 |     pass
  51 | def cli_entry_point():
  52 |     parser = argparse.ArgumentParser(
  53 |         prog="codeconcat",
  54 |         description="CodeConCat - An LLM-friendly code aggregator and doc extractor.",
  55 |     )
  57 |     parser.add_argument("target_path", nargs="?", default=".")
  58 |     parser.add_argument(
  59 |         "--github", help="GitHub URL or shorthand (e.g., 'owner/repo')", default=None
  60 |     )
  61 |     parser.add_argument("--github-token", help="GitHub personal access token", default=None)
  62 |     parser.add_argument("--ref", help="Branch, tag, or commit hash for GitHub repo", default=None)
  64 |     parser.add_argument("--docs", action="store_true", help="Enable doc extraction")
  65 |     parser.add_argument(
  66 |         "--merge-docs", action="store_true", help="Merge doc content with code output"
  67 |     )
  69 |     parser.add_argument("--output", default="code_concat_output.md", help="Output file name")
  70 |     parser.add_argument(
  71 |         "--format", choices=["markdown", "json", "xml"], default="markdown", help="Output format"
  72 |     )
  74 |     parser.add_argument("--include", nargs="*", default=[], help="Glob patterns to include")
  75 |     parser.add_argument("--exclude", nargs="*", default=[], help="Glob patterns to exclude")
  76 |     parser.add_argument(
  77 |         "--include-languages", nargs="*", default=[], help="Only include these languages"
  78 |     )
  79 |     parser.add_argument(
  80 |         "--exclude-languages", nargs="*", default=[], help="Exclude these languages"
  81 |     )
  83 |     parser.add_argument("--max-workers", type=int, default=4, help="Number of worker threads")
  84 |     parser.add_argument("--init", action="store_true", help="Initialize default configuration file")
  86 |     parser.add_argument(
  87 |         "--no-tree", action="store_true", help="Disable folder tree generation (enabled by default)"
  88 |     )
  89 |     parser.add_argument(
  90 |         "--no-copy",
  91 |         action="store_true",
  92 |         help="Disable copying output to clipboard (enabled by default)",
  93 |     )
  94 |     parser.add_argument(
  95 |         "--no-ai-context", action="store_true", help="Disable AI context generation"
  96 |     )
  97 |     parser.add_argument("--no-annotations", action="store_true", help="Disable code annotations")
  98 |     parser.add_argument("--no-symbols", action="store_true", help="Disable symbol extraction")
  99 |     parser.add_argument("--debug", action="store_true", help="Enable debug logging")
 101 |     args = parser.parse_args()
 104 |     if args.debug:
 105 |         logger.setLevel(logging.DEBUG)
 107 |         for name in logging.root.manager.loggerDict:
 108 |             if name.startswith("codeconcat"):
 109 |                 logging.getLogger(name).setLevel(logging.DEBUG)
 112 |     if not logger.handlers:
 113 |         ch = logging.StreamHandler()
 114 |         ch.setLevel(logging.DEBUG if args.debug else logging.WARNING)
 115 |         formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
 116 |         ch.setFormatter(formatter)
 117 |         logger.addHandler(ch)
 119 |     logger.debug("Debug logging enabled")
 122 |     if args.init:
 123 |         create_default_config()
 124 |         print("[CodeConCat] Created default configuration file: .codeconcat.yml")
 125 |         sys.exit(0)
 128 |     cli_args = vars(args)
 129 |     logging.debug("CLI args: %s", cli_args)  # Debug print
 130 |     config = load_config(cli_args)
 132 |     try:
 133 |         run_codeconcat(config)
 134 |     except Exception as e:
 135 |         print(f"[CodeConCat] Error: {str(e)}", file=sys.stderr)
 136 |         sys.exit(1)
 139 | def create_default_config():
 141 |     if os.path.exists(".codeconcat.yml"):
 142 |         print("Configuration file already exists. Remove it first to create a new one.")
 143 |         return
 145 |     config_content = """# CodeConCat Configuration
 148 | include_paths:
 152 | exclude_paths:
 154 |   - "**/*.{yml,yaml}"
 155 |   - "**/.codeconcat.yml"
 156 |   - "**/.github/*.{yml,yaml}"
 159 |   - "**/tests/**"
 160 |   - "**/test_*.py"
 161 |   - "**/*_test.py"
 164 |   - "**/build/**"
 165 |   - "**/dist/**"
 166 |   - "**/__pycache__/**"
 167 |   - "**/*.{pyc,pyo,pyd}"
 168 |   - "**/.pytest_cache/**"
 169 |   - "**/.coverage"
 170 |   - "**/htmlcov/**"
 173 |   - "**/*.{md,rst,txt}"
 174 |   - "**/LICENSE*"
 175 |   - "**/README*"
 178 | include_languages:
 182 | exclude_languages:
 187 | output: code_concat_output.md
 188 | format: markdown  # or json, xml
 191 | extract_docs: false
 192 | merge_docs: false
 193 | disable_tree: false
 194 | disable_copy: false
 195 | disable_annotations: false
 196 | disable_symbols: false
 199 | include_file_summary: true
 200 | include_directory_structure: true
 201 | remove_comments: true
 202 | remove_empty_lines: true
 203 | show_line_numbers: true
 206 | max_workers: 4
 207 | custom_extension_map:
 212 |     with open(".codeconcat.yml", "w") as f:
 213 |         f.write(config_content)
 215 |     print("[CodeConCat] Created default configuration file: .codeconcat.yml")
 218 | def generate_folder_tree(root_path: str, config: CodeConCatConfig) -> str:
 220 |     Walk the directory tree starting at root_path and return a string that represents the folder structure.
 221 |     Respects exclusion patterns from the config.
 223 |     from codeconcat.collector.local_collector import should_include_file, should_skip_dir
 225 |     lines = []
 226 |     for root, dirs, files in os.walk(root_path):
 228 |         if should_skip_dir(root, config.exclude_paths):
 229 |             dirs[:] = []  # Clear dirs to prevent descending into this directory
 230 |             continue
 232 |         level = root.replace(root_path, "").count(os.sep)
 233 |         indent = "    " * level
 234 |         folder_name = os.path.basename(root) or root_path
 235 |         lines.append(f"{indent}{folder_name}/")
 238 |         included_files = [f for f in files if should_include_file(os.path.join(root, f), config)]
 240 |         sub_indent = "    " * (level + 1)
 241 |         for f in sorted(included_files):
 242 |             lines.append(f"{sub_indent}{f}")
 245 |         dirs[:] = [
 246 |             d for d in dirs if not should_skip_dir(os.path.join(root, d), config.exclude_paths)
 247 |         ]
 248 |         dirs.sort()  # Sort directories for consistent output
 250 |     return "\n".join(lines)
 253 | def run_codeconcat(config: CodeConCatConfig):
 255 |     try:
 257 |         if not config.target_path:
 258 |             raise ConfigurationError("Target path is required")
 259 |         if config.format not in ["markdown", "json", "xml"]:
 260 |             raise ConfigurationError(f"Invalid format: {config.format}")
 263 |         try:
 264 |             if config.github_url:
 265 |                 code_files = collect_github_files(config)
 266 |             else:
 267 |                 code_files = collect_local_files(config.target_path, config)
 269 |             if not code_files:
 270 |                 raise FileProcessingError("No files found to process")
 271 |         except Exception as e:
 272 |             raise FileProcessingError(f"Error collecting files: {str(e)}")
 275 |         folder_tree_str = ""
 276 |         if not config.disable_tree:
 277 |             try:
 278 |                 folder_tree_str = generate_folder_tree(config.target_path, config)
 279 |             except Exception as e:
 280 |                 print(f"Warning: Failed to generate folder tree: {str(e)}")
 283 |         try:
 284 |             parsed_files = parse_code_files([f.file_path for f in code_files], config)
 285 |             if not parsed_files:
 286 |                 raise FileProcessingError("No files were successfully parsed")
 287 |         except Exception as e:
 288 |             raise FileProcessingError(f"Error parsing files: {str(e)}")
 291 |         docs = []
 292 |         if config.extract_docs:
 293 |             try:
 294 |                 docs = extract_docs([f.file_path for f in code_files], config)
 295 |             except Exception as e:
 296 |                 print(f"Warning: Failed to extract documentation: {str(e)}")
 299 |         try:
 300 |             annotated_files = []
 301 |             if not config.disable_annotations:
 302 |                 for file in parsed_files:
 303 |                     try:
 304 |                         annotated = annotate(file, config)
 305 |                         annotated_files.append(annotated)
 306 |                     except Exception as e:
 307 |                         print(f"Warning: Failed to annotate {file.file_path}: {str(e)}")
 309 |                         annotated_files.append(
 310 |                             AnnotatedFileData(
 311 |                                 file_path=file.file_path,
 312 |                                 language=file.language,
 313 |                                 content=file.content,
 314 |                                 annotated_content=file.content,
 315 |                                 summary="",
 316 |                                 tags=[],
 317 |                             )
 318 |                         )
 319 |             else:
 321 |                 for file in parsed_files:
 322 |                     annotated_files.append(
 323 |                         AnnotatedFileData(
 324 |                             file_path=file.file_path,
 325 |                             language=file.language,
 326 |                             content=file.content,
 327 |                             annotated_content=file.content,
 328 |                             summary="",
 329 |                             tags=[],
 330 |                         )
 331 |                     )
 332 |         except Exception as e:
 333 |             raise FileProcessingError(f"Error during annotation: {str(e)}")
 336 |         try:
 337 |             if config.format == "markdown":
 338 |                 output = write_markdown(annotated_files, docs, config, folder_tree_str)
 339 |             elif config.format == "json":
 340 |                 output = write_json(annotated_files, docs, config, folder_tree_str)
 341 |             elif config.format == "xml":
 342 |                 output = write_xml(
 343 |                     parsed_files, docs, {f.file_path: f for f in annotated_files}, folder_tree_str
 344 |                 )
 345 |         except Exception as e:
 346 |             raise OutputError(f"Error generating {config.format} output: {str(e)}")
 349 |         if not config.disable_copy:
 350 |             try:
 351 |                 import pyperclip
 353 |                 pyperclip.copy(output)
 354 |                 print("[CodeConCat] Output copied to clipboard")
 355 |             except ImportError:
 356 |                 print("[CodeConCat] Warning: pyperclip not installed, skipping clipboard copy")
 357 |             except Exception as e:
 358 |                 print(f"[CodeConCat] Warning: Failed to copy to clipboard: {str(e)}")
 360 |     except CodeConcatError as e:
 361 |         print(f"[CodeConCat] Error: {str(e)}")
 362 |         raise
 363 |     except Exception as e:
 364 |         print(f"[CodeConCat] Unexpected error: {str(e)}")
 365 |         raise
 368 | def run_codeconcat_in_memory(config: CodeConCatConfig) -> str:
 370 |     try:
 371 |         if config.disable_copy is None:
 372 |             config.disable_copy = True  # Always disable clipboard in memory mode
 375 |         if config.github_url:
 376 |             code_files = collect_github_files(config)
 377 |         else:
 378 |             code_files = collect_local_files(config.target_path, config)
 380 |         if not code_files:
 381 |             raise FileProcessingError("No files found to process")
 384 |         folder_tree_str = ""
 385 |         if not config.disable_tree:
 386 |             folder_tree_str = generate_folder_tree(config.target_path, config)
 389 |         parsed_files = parse_code_files([f.file_path for f in code_files], config)
 390 |         if not parsed_files:
 391 |             raise FileProcessingError("No files were successfully parsed")
 394 |         docs = []
 395 |         if config.extract_docs:
 396 |             docs = extract_docs([f.file_path for f in code_files], config)
 399 |         annotated_files = []
 400 |         if not config.disable_annotations:
 401 |             for file in parsed_files:
 402 |                 try:
 403 |                     annotated = annotate(file, config)
 404 |                     annotated_files.append(annotated)
 405 |                 except Exception as e:
 406 |                     print(f"Warning: Failed to annotate {file.file_path}: {str(e)}")
 408 |                     annotated_files.append(
 409 |                         AnnotatedFileData(
 410 |                             file_path=file.file_path,
 411 |                             language=file.language,
 412 |                             content=file.content,
 413 |                             annotated_content=file.content,
 414 |                             summary="",
 415 |                             tags=[],
 416 |                         )
 417 |                     )
 418 |         else:
 419 |             for file in parsed_files:
 420 |                 annotated_files.append(
 421 |                     AnnotatedFileData(
 422 |                         file_path=file.file_path,
 423 |                         language=file.language,
 424 |                         content=file.content,
 425 |                         annotated_content=file.content,
 426 |                         summary="",
 427 |                         tags=[],
 428 |                     )
 429 |                 )
 432 |         if config.format == "markdown":
 433 |             from codeconcat.writer.markdown_writer import write_markdown
 434 |             from codeconcat.writer.ai_context import generate_ai_preamble
 436 |             output_chunks = []
 439 |             if not config.disable_ai_context:
 440 |                 ai_preamble = generate_ai_preamble(code_files, docs, annotated_files)
 441 |                 if ai_preamble:
 442 |                     output_chunks.append(ai_preamble)
 444 |             output = write_markdown(
 445 |                 annotated_files,
 446 |                 docs,
 447 |                 config,
 448 |                 folder_tree_str,
 449 |             )
 450 |             if output:
 451 |                 output_chunks.append(output)
 453 |             return "\n".join(output_chunks)
 454 |         elif config.format == "json":
 455 |             return write_json(annotated_files, docs, config, folder_tree_str)
 456 |         elif config.format == "xml":
 457 |             return write_xml(
 458 |                 parsed_files, docs, {f.file_path: f for f in annotated_files}, folder_tree_str
 459 |             )
 460 |         else:
 461 |             raise ConfigurationError(f"Invalid format: {config.format}")
 463 |     except Exception as e:
 464 |         error_msg = f"Error processing code: {str(e)}"
 465 |         print(f"[CodeConCat] {error_msg}")
 466 |         raise CodeConcatError(error_msg) from e
 469 | def main():
 470 |     cli_entry_point()
 473 | if __name__ == "__main__":
 474 |     main()
```

#### Analysis Notes
## File: ./codeconcat/main.py
### Functions
### Classes

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
  29 |         "max_workers": cli_args.get("max_workers", 2),
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

#### Analysis Notes
## File: ./codeconcat/config/config_loader.py
### Functions

---
### File: ./codeconcat/config/__init__.py
#### Summary
```
File: __init__.py
Language: python
```


---
### File: ./codeconcat/transformer/__init__.py
#### Summary
```
File: __init__.py
Language: python
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
  21 |         elif decl.kind == "symbol" and not config.disable_symbols:
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

#### Analysis Notes
## File: ./codeconcat/transformer/annotator.py

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

#### Analysis Notes
## File: ./codeconcat/processor/security_types.py
### Classes

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

#### Analysis Notes
## File: ./codeconcat/processor/content_processor.py
### Functions

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

#### Analysis Notes
## File: ./codeconcat/processor/token_counter.py
### Functions
### Classes

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

#### Analysis Notes
## File: ./codeconcat/processor/__init__.py

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

#### Analysis Notes
## File: ./codeconcat/processor/security_processor.py
### Functions
### Classes

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

#### Analysis Notes
## File: ./codeconcat/collector/github_collector.py
### Functions

---
### File: ./codeconcat/collector/__init__.py
#### Summary
```
File: __init__.py
Language: python
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
   7 | from pathlib import Path
   8 | from codeconcat.base_types import CodeConCatConfig, ParsedFileData
   9 | from pathspec import PathSpec
  10 | from pathspec.patterns import GitWildMatchPattern
  13 | logger = logging.getLogger(__name__)
  14 | logger.setLevel(logging.WARNING)
  17 | ch = logging.StreamHandler()
  18 | ch.setLevel(logging.DEBUG)
  21 | formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
  22 | ch.setFormatter(formatter)
  25 | logger.addHandler(ch)
  27 | DEFAULT_EXCLUDES = [
  29 |     ".git/",  # Match the .git directory itself
  30 |     ".git/**",  # Match contents of .git directory
  31 |     "**/.git/",  # Match .git directory anywhere in tree
  32 |     "**/.git/**",  # Match contents of .git directory anywhere in tree
  33 |     ".gitignore",
  34 |     "**/.gitignore",
  36 |     ".DS_Store",
  37 |     "**/.DS_Store",
  38 |     "Thumbs.db",
  39 |     "**/*.swp",
  40 |     "**/*.swo",
  41 |     ".idea/**",
  42 |     ".vscode/**",
  44 |     "*.yml",
  45 |     "./*.yml",
  46 |     "**/*.yml",
  47 |     "*.yaml",
  48 |     "./*.yaml",
  49 |     "**/*.yaml",
  50 |     ".codeconcat.yml",
  52 |     "node_modules/",
  53 |     "**/node_modules/",
  54 |     "**/node_modules/**",
  55 |     "build/",
  56 |     "**/build/",
  57 |     "**/build/**",
  58 |     "dist/",
  59 |     "**/dist/",
  60 |     "**/dist/**",
  62 |     ".next/",
  63 |     "**/.next/",
  64 |     "**/.next/**",
  65 |     "**/static/chunks/**",
  66 |     "**/server/chunks/**",
  67 |     "**/BUILD_ID",
  68 |     "**/trace",
  69 |     "**/*.map",
  70 |     "**/webpack-*.js",
  71 |     "**/manifest*.js",
  72 |     "**/server-reference-manifest.js",
  73 |     "**/middleware-manifest.js",
  74 |     "**/client-reference-manifest.js",
  75 |     "**/webpack-runtime.js",
  76 |     "**/server-reference-manifest.js",
  77 |     "**/middleware-build-manifest.js",
  78 |     "**/middleware-react-loadable-manifest.js",
  79 |     "**/server-reference-manifest.js",
  80 |     "**/interception-route-rewrite-manifest.js",
  81 |     "**/next-font-manifest.js",
  82 |     "**/polyfills-*.js",
  83 |     "**/main-*.js",
  84 |     "**/framework-*.js",
  86 |     "package-lock.json",
  87 |     "**/package-lock.json",
  88 |     "yarn.lock",
  89 |     "**/yarn.lock",
  90 |     "pnpm-lock.yaml",
  91 |     "**/pnpm-lock.yaml",
  93 |     ".cache/",
  94 |     "**/.cache/",
  95 |     "**/.cache/**",
  96 |     "tmp/",
  97 |     "**/tmp/",
  98 |     "**/tmp/**",
 100 |     "coverage/",
 101 |     "**/coverage/",
 102 |     "**/coverage/**",
 104 |     ".env",
 105 |     "**/.env",
 106 |     ".env.*",
 107 |     "**/.env.*",
 108 | ]
 111 | def get_gitignore_spec(root_path: str) -> PathSpec:
 113 |     Read .gitignore file and create a PathSpec for matching.
 115 |     Args:
 116 |         root_path: Root directory to search for .gitignore
 118 |     Returns:
 119 |         PathSpec object for matching paths against .gitignore patterns
 121 |     gitignore_path = os.path.join(root_path, ".gitignore")
 122 |     patterns = []
 124 |     if os.path.exists(gitignore_path):
 125 |         with open(gitignore_path, "r") as f:
 126 |             patterns = [line.strip() for line in f if line.strip() and not line.startswith("#")]
 129 |     patterns.extend(
 130 |         [
 131 |             "**/__pycache__/**",
 132 |             "**/*.pyc",
 133 |             "**/.git/**",
 134 |             "**/node_modules/**",
 135 |             "**/.pytest_cache/**",
 136 |             "**/.coverage",
 137 |             "**/build/**",
 138 |             "**/dist/**",
 139 |             "**/*.egg-info/**",
 140 |         ]
 141 |     )
 143 |     return PathSpec.from_lines(GitWildMatchPattern, patterns)
 146 | def should_include_file(
 147 |     file_path: str, config: CodeConCatConfig, gitignore_spec: PathSpec = None
 148 | ) -> bool:
 150 |     Check if a file should be included based on configuration and .gitignore.
 152 |     Args:
 153 |         file_path: Path to the file
 154 |         config: Configuration object
 155 |         gitignore_spec: PathSpec object for .gitignore matching
 157 |     Returns:
 158 |         bool: True if file should be included, False otherwise
 161 |     rel_path = os.path.relpath(file_path, config.target_path)
 164 |     if gitignore_spec and gitignore_spec.match_file(rel_path):
 165 |         return False
 168 |     if config.exclude_paths:
 169 |         for pattern in config.exclude_paths:
 171 |             path_parts = Path(rel_path).parts
 172 |             if any(fnmatch.fnmatch(os.path.join(*path_parts[:i+1]), pattern) 
 173 |                   for i in range(len(path_parts))):
 174 |                 return False
 176 |     if config.include_paths:
 177 |         return any(fnmatch.fnmatch(rel_path, pattern) for pattern in config.include_paths)
 179 |     return True
 182 | def collect_local_files(root_path: str, config: CodeConCatConfig):
 185 |     logger.debug(f"[CodeConCat] Collecting files from: {root_path}")
 188 |     if not os.path.exists(root_path):
 189 |         raise FileNotFoundError(f"Path does not exist: {root_path}")
 191 |     gitignore_spec = get_gitignore_spec(root_path)
 194 |     with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
 195 |         futures = []
 197 |         for dirpath, dirnames, filenames in os.walk(root_path):
 199 |             if should_skip_dir(dirpath, config.exclude_paths):
 200 |                 dirnames.clear()  # Clear dirnames to skip subdirectories
 201 |                 continue
 204 |             for filename in filenames:
 205 |                 file_path = os.path.join(dirpath, filename)
 206 |                 futures.append(executor.submit(process_file, file_path, config, gitignore_spec))
 209 |         results = [f.result() for f in futures if f.result()]
 211 |     if not results:
 212 |         logger.warning("[CodeConCat] No files found matching the criteria")
 213 |     else:
 214 |         logger.info(f"[CodeConCat] Collected {len(results)} files")
 216 |     return results
 219 | def process_file(file_path: str, config: CodeConCatConfig, gitignore_spec: PathSpec):
 221 |     try:
 222 |         if not should_include_file(file_path, config, gitignore_spec):
 223 |             return None
 225 |         if is_binary_file(file_path):
 226 |             logger.debug(f"[CodeConCat] Skipping binary file: {file_path}")
 227 |             return None
 229 |         with open(file_path, "r", encoding="utf-8") as f:
 230 |             content = f.read()
 232 |         ext = os.path.splitext(file_path)[1].lstrip(".")
 233 |         language = ext_map(ext, config)
 235 |         logger.debug(f"[CodeConCat] Processed file: {file_path} ({language})")
 236 |         return ParsedFileData(
 237 |             file_path=file_path,
 238 |             language=language,
 239 |             content=content,
 240 |             declarations=[],  # We'll fill this in during parsing phase
 241 |         )
 243 |     except UnicodeDecodeError:
 244 |         logger.debug(f"[CodeConCat] Skipping non-text file: {file_path}")
 245 |         return None
 246 |     except Exception as e:
 247 |         logger.error(f"[CodeConCat] Error processing {file_path}: {str(e)}")
 248 |         return None
 251 | def should_skip_dir(dirpath: str, user_excludes: List[str]) -> bool:
 253 |     all_excludes = DEFAULT_EXCLUDES + (user_excludes or [])
 254 |     logger.debug(f"Checking directory: {dirpath} against patterns: {all_excludes}")
 257 |     if os.path.isabs(dirpath):
 258 |         try:
 259 |             rel_path = os.path.relpath(dirpath, os.getcwd())
 260 |         except ValueError:
 261 |             rel_path = dirpath
 262 |     else:
 263 |         rel_path = dirpath
 266 |     rel_path = rel_path.replace(os.sep, "/").strip("/")
 269 |     for pattern in all_excludes:
 270 |         if matches_pattern(rel_path, pattern):
 271 |             logger.debug(f"Excluding directory {rel_path} due to pattern {pattern}")
 272 |             return True
 275 |     path_parts = [p for p in rel_path.split("/") if p]
 276 |     current_path = ""
 277 |     for part in path_parts:
 278 |         if current_path:
 279 |             current_path += "/"
 280 |         current_path += part
 282 |         for pattern in all_excludes:
 284 |             if matches_pattern(current_path, pattern) or matches_pattern(
 285 |                 current_path + "/", pattern
 286 |             ):
 287 |                 logger.debug(
 288 |                     f"Excluding directory {rel_path} due to parent {current_path} matching pattern {pattern}"
 289 |                 )
 290 |                 return True
 292 |     return False
 295 | def matches_pattern(path_str: str, pattern: str) -> bool:
 298 |     path_str = path_str.replace(os.sep, "/").strip("/")
 299 |     pattern = pattern.replace(os.sep, "/").strip("/")
 302 |     if pattern == "":
 303 |         return path_str == ""
 306 |     pattern = pattern.replace(".", "\\.")  # Escape dots
 307 |     pattern = pattern.replace("**", "__DOUBLE_STAR__")  # Preserve **
 308 |     pattern = pattern.replace("*", "[^/]*")  # Single star doesn't cross directories
 309 |     pattern = pattern.replace("__DOUBLE_STAR__", ".*")  # ** can cross directories
 310 |     pattern = pattern.replace("?", "[^/]")  # ? matches single character
 313 |     if pattern.endswith("/"):
 314 |         pattern = pattern + ".*"  # Match anything after directory
 317 |     if pattern.startswith("/"):
 318 |         pattern = "^" + pattern[1:]  # Keep absolute path requirement
 319 |     elif pattern.startswith("**/"):
 320 |         pattern = ".*" + pattern[2:]  # Allow matching anywhere in path
 321 |     else:
 322 |         pattern = "^" + pattern  # Anchor to start by default
 324 |     if not pattern.endswith("$"):
 325 |         pattern += "$"  # Always anchor to end
 328 |     try:
 329 |         return bool(re.match(pattern, path_str))
 330 |     except re.error as e:
 331 |         logger.warning(f"Invalid pattern {pattern}: {str(e)}")
 332 |         return False
 335 | def ext_map(ext: str, config: CodeConCatConfig) -> str:
 337 |     if ext in config.custom_extension_map:
 338 |         return config.custom_extension_map[ext]
 341 |     non_code_exts = {
 343 |         "svg",
 344 |         "png",
 345 |         "jpg",
 346 |         "jpeg",
 347 |         "gif",
 348 |         "ico",
 349 |         "webp",
 351 |         "woff",
 352 |         "woff2",
 353 |         "ttf",
 354 |         "eot",
 355 |         "otf",
 357 |         "pdf",
 358 |         "doc",
 359 |         "docx",
 360 |         "xls",
 361 |         "xlsx",
 363 |         "zip",
 364 |         "tar",
 365 |         "gz",
 366 |         "tgz",
 367 |         "7z",
 368 |         "rar",
 370 |         "map",
 371 |         "min.js",
 372 |         "min.css",
 373 |         "bundle.js",
 374 |         "bundle.css",
 375 |         "chunk.js",
 376 |         "chunk.css",
 377 |         "nft.json",
 378 |         "rsc",
 379 |         "meta",
 381 |         "mp3",
 382 |         "mp4",
 383 |         "wav",
 384 |         "avi",
 385 |         "mov",
 386 |     }
 388 |     if ext.lower() in non_code_exts:
 389 |         return "non-code"
 392 |     code_exts = {
 394 |         "py": "python",
 395 |         "pyi": "python",
 397 |         "js": "javascript",
 398 |         "jsx": "javascript",
 399 |         "ts": "typescript",
 400 |         "tsx": "typescript",
 401 |         "mjs": "javascript",
 403 |         "r": "r",
 404 |         "jl": "julia",
 405 |         "cpp": "cpp",
 406 |         "hpp": "cpp",
 407 |         "cxx": "cpp",
 408 |         "c": "c",
 409 |         "h": "c",
 411 |         "md": "doc",
 412 |         "rst": "doc",
 413 |         "txt": "doc",
 414 |         "rmd": "doc",
 415 |     }
 417 |     return code_exts.get(ext.lower(), "unknown")
 420 | def is_binary_file(file_path: str) -> bool:
 422 |     try:
 423 |         with open(file_path, "tr") as check_file:
 424 |             check_file.readline()
 425 |             return False
 426 |     except UnicodeDecodeError:
 427 |         return True
```

#### Analysis Notes
## File: ./codeconcat/collector/local_collector.py
### Functions

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

#### Analysis Notes
## File: ./codeconcat/parser/doc_extractor.py
### Functions

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
   3 | from functools import lru_cache
   4 | from typing import Callable, List, Optional, Tuple
   6 | from codeconcat.base_types import CodeConCatConfig, ParsedFileData
   7 | from codeconcat.parser.language_parsers.base_parser import BaseParser
   8 | from codeconcat.parser.language_parsers.c_parser import parse_c_code
   9 | from codeconcat.parser.language_parsers.cpp_parser import parse_cpp_code
  10 | from codeconcat.parser.language_parsers.csharp_parser import parse_csharp_code
  11 | from codeconcat.parser.language_parsers.go_parser import parse_go
  12 | from codeconcat.parser.language_parsers.java_parser import parse_java
  13 | from codeconcat.parser.language_parsers.js_ts_parser import parse_javascript_or_typescript
  14 | from codeconcat.parser.language_parsers.julia_parser import parse_julia
  15 | from codeconcat.parser.language_parsers.php_parser import parse_php
  16 | from codeconcat.parser.language_parsers.python_parser import parse_python
  17 | from codeconcat.parser.language_parsers.r_parser import parse_r
  18 | from codeconcat.parser.language_parsers.rust_parser import parse_rust
  19 | from codeconcat.processor.token_counter import get_token_stats
  22 | @lru_cache(maxsize=100)
  23 | def _parse_single_file(file_path: str, language: str) -> Optional[ParsedFileData]:
  25 |     Parse a single file with caching. This function is memoized to improve performance
  26 |     when the same file is processed multiple times.
  28 |     Args:
  29 |         file_path: Path to the file to parse
  30 |         language: Programming language of the file
  32 |     Returns:
  33 |         ParsedFileData if successful, None if parsing failed
  35 |     Note:
  36 |         The function is cached based on file_path and language. The cache is cleared
  37 |         when the file content changes (detected by modification time).
  39 |     try:
  40 |         if not os.path.exists(file_path):
  41 |             raise FileNotFoundError(f"File not found: {file_path}")
  43 |         with open(file_path, "r", encoding="utf-8") as f:
  44 |             content = f.read()
  46 |         if language == "python":
  47 |             return parse_python(file_path, content)
  48 |         elif language in ["javascript", "typescript"]:
  49 |             return parse_javascript_or_typescript(file_path, content, language)
  50 |         elif language == "c":
  51 |             return parse_c_code(file_path, content)
  52 |         elif language == "cpp":
  53 |             return parse_cpp_code(file_path, content)
  54 |         elif language == "csharp":
  55 |             return parse_csharp_code(file_path, content)
  56 |         elif language == "go":
  57 |             return parse_go(file_path, content)
  58 |         elif language == "java":
  59 |             return parse_java(file_path, content)
  60 |         elif language == "julia":
  61 |             return parse_julia(file_path, content)
  62 |         elif language == "php":
  63 |             return parse_php(file_path, content)
  64 |         elif language == "r":
  65 |             return parse_r(file_path, content)
  66 |         elif language == "rust":
  67 |             return parse_rust(file_path, content)
  68 |         else:
  69 |             raise ValueError(f"Unsupported language: {language}")
  71 |     except UnicodeDecodeError:
  72 |         raise ValueError(
  73 |             f"Failed to decode {file_path}. File may be binary or use an unsupported encoding."
  74 |         )
  75 |     except Exception as e:
  76 |         raise RuntimeError(f"Error parsing {file_path}: {str(e)}")
  79 | def parse_code_files(file_paths: List[str], config: CodeConCatConfig) -> List[ParsedFileData]:
  81 |     Parse multiple code files with improved error handling and caching.
  83 |     Args:
  84 |         file_paths: List of file paths to parse
  85 |         config: Configuration object
  87 |     Returns:
  88 |         List of successfully parsed files
  90 |     Note:
  91 |         Files that fail to parse are logged with detailed error messages but don't
  92 |         cause the entire process to fail.
  94 |     parsed_files = []
  95 |     errors = []
  97 |     for file_path in file_paths:
  98 |         try:
 100 |             language = determine_language(file_path)
 101 |             if not language:
 102 |                 errors.append(f"Could not determine language for {file_path}")
 103 |                 continue
 106 |             parsed_file = _parse_single_file(file_path, language)
 107 |             if parsed_file:
 108 |                 parsed_files.append(parsed_file)
 110 |         except FileNotFoundError as e:
 111 |             errors.append(f"File not found: {file_path}")
 112 |         except UnicodeDecodeError:
 113 |             errors.append(
 114 |                 f"Failed to decode {file_path}. File may be binary or use an unsupported encoding."
 115 |             )
 116 |         except ValueError as e:
 117 |             errors.append(str(e))
 118 |         except Exception as e:
 119 |             errors.append(f"Unexpected error parsing {file_path}: {str(e)}")
 122 |     if errors:
 123 |         error_summary = "\n".join(errors)
 124 |         print(f"Encountered errors while parsing files:\n{error_summary}")
 126 |     return parsed_files
 129 | @lru_cache(maxsize=100)
 130 | def determine_language(file_path: str) -> Optional[str]:
 132 |     Determine the programming language of a file based on its extension.
 133 |     This function is cached to improve performance.
 135 |     Args:
 136 |         file_path: Path to the file
 138 |     Returns:
 139 |         Language identifier or None if unknown
 142 |     basename = os.path.basename(file_path)
 143 |     ext = os.path.splitext(file_path)[1].lower()
 146 |     r_specific_files = {
 147 |         "DESCRIPTION",  # R package description
 148 |         "NAMESPACE",    # R package namespace
 149 |         ".Rproj",      # RStudio project file
 150 |         "configure",    # R package configuration
 151 |         "configure.win",# R package Windows configuration
 152 |     }
 153 |     if basename in r_specific_files:
 154 |         return None
 157 |     language_map = {
 158 |         ".py": "python",
 159 |         ".js": "javascript",
 160 |         ".ts": "typescript",
 161 |         ".jsx": "javascript",
 162 |         ".tsx": "typescript",
 163 |         ".r": "r",
 164 |         ".jl": "julia",
 165 |         ".rs": "rust",
 166 |         ".cpp": "cpp",
 167 |         ".cxx": "cpp",
 168 |         ".cc": "cpp",
 169 |         ".hpp": "cpp",
 170 |         ".hxx": "cpp",
 171 |         ".h": "c",
 172 |         ".c": "c",
 173 |         ".cs": "csharp",
 174 |         ".java": "java",
 175 |         ".go": "go",
 176 |         ".php": "php",
 177 |     }
 178 |     return language_map.get(ext)
 181 | def get_language_parser(file_path: str) -> Optional[Tuple[str, Callable]]:
 183 |     ext = file_path.split(".")[-1].lower() if "." in file_path else ""
 185 |     extension_map = {
 187 |         ".py": ("python", parse_python),
 188 |         ".js": ("javascript", parse_javascript_or_typescript),
 189 |         ".ts": ("typescript", parse_javascript_or_typescript),
 190 |         ".jsx": ("javascript", parse_javascript_or_typescript),
 191 |         ".tsx": ("typescript", parse_javascript_or_typescript),
 192 |         ".r": ("r", parse_r),
 193 |         ".jl": ("julia", parse_julia),
 195 |         ".rs": ("rust", parse_rust),
 196 |         ".cpp": ("cpp", parse_cpp_code),
 197 |         ".cxx": ("cpp", parse_cpp_code),
 198 |         ".cc": ("cpp", parse_cpp_code),
 199 |         ".hpp": ("cpp", parse_cpp_code),
 200 |         ".hxx": ("cpp", parse_cpp_code),
 201 |         ".h": ("c", parse_c_code),  # Note: .h could be C or C++
 202 |         ".c": ("c", parse_c_code),
 203 |         ".cs": ("csharp", parse_csharp_code),
 204 |         ".java": ("java", parse_java),
 205 |         ".go": ("go", parse_go),
 206 |         ".php": ("php", parse_php),
 207 |     }
 209 |     ext_with_dot = f".{ext}" if not ext.startswith(".") else ext
 210 |     return extension_map.get(ext_with_dot)
 213 | def get_language_name(file_path: str) -> str:
 215 |     parser_info = get_language_parser(file_path)
 216 |     if parser_info:
 217 |         return parser_info[0]
 218 |     return "unknown"
 221 | def is_doc_file(file_path: str, doc_exts: List[str]) -> bool:
 222 |     ext = os.path.splitext(file_path)[1].lower()
 223 |     return ext in doc_exts
 226 | def read_file_content(file_path: str) -> str:
 227 |     try:
 228 |         with open(file_path, "r", encoding="utf-8", errors="replace") as f:
 229 |             return f.read()
 230 |     except Exception:
 231 |         return ""
```

#### Analysis Notes
## File: ./codeconcat/parser/file_parser.py
### Functions

---
### File: ./codeconcat/parser/__init__.py
#### Summary
```
File: __init__.py
Language: python
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
   4 | from typing import List, Optional, Set
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   9 | def parse_csharp_code(file_path: str, content: str) -> Optional[ParsedFileData]:
  11 |     parser = CSharpParser()
  12 |     declarations = parser.parse(content)
  13 |     return ParsedFileData(
  14 |         file_path=file_path,
  15 |         language="csharp",
  16 |         content=content,
  17 |         declarations=declarations
  18 |     )
  21 | class CSharpParser(BaseParser):
  24 |     def __init__(self):
  26 |         super().__init__()
  27 |         self._setup_patterns()
  29 |     def _setup_patterns(self):
  31 |         modifiers = r"(?:public|private|protected|internal)?\s*"
  32 |         class_modifiers = r"(?:static|abstract|sealed)?\s*"
  33 |         method_modifiers = r"(?:static|virtual|abstract|override)?\s*"
  34 |         type_pattern = r"(?:[a-zA-Z_][a-zA-Z0-9_<>]*\s+)+"
  36 |         self.patterns = {
  37 |             "class": re.compile(
  38 |                 r"^\s*" + modifiers + class_modifiers +  # Access and class modifiers
  39 |                 r"class\s+" +  # class keyword
  40 |                 r"(?P<class_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Class name
  41 |             ),
  42 |             "interface": re.compile(
  43 |                 r"^\s*" + modifiers +  # Access modifiers
  44 |                 r"interface\s+" +  # interface keyword
  45 |                 r"(?P<interface_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Interface name
  46 |             ),
  47 |             "method": re.compile(
  48 |                 r"^\s*" + modifiers + method_modifiers +  # Access and method modifiers
  49 |                 r"(?:async\s+)?" +  # Optional async
  50 |                 type_pattern +  # Return type
  51 |                 r"(?P<method_name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)"  # Method name and args
  52 |             ),
  53 |             "property": re.compile(
  54 |                 r"^\s*" + modifiers + method_modifiers +  # Access and property modifiers
  55 |                 type_pattern +  # Property type
  56 |                 r"(?P<property_name>[a-zA-Z_][a-zA-Z0-9_]*)\s*{\s*(?:get|set)"  # Property name
  57 |             ),
  58 |             "enum": re.compile(
  59 |                 r"^\s*" + modifiers +  # Access modifiers
  60 |                 r"enum\s+" +  # enum keyword
  61 |                 r"(?P<enum_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Enum name
  62 |             ),
  63 |             "struct": re.compile(
  64 |                 r"^\s*" + modifiers +  # Access modifiers
  65 |                 r"struct\s+" +  # struct keyword
  66 |                 r"(?P<struct_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Struct name
  67 |             ),
  68 |             "delegate": re.compile(
  69 |                 r"^\s*" + modifiers +  # Access modifiers
  70 |                 r"delegate\s+" +  # delegate keyword
  71 |                 type_pattern +  # Return type
  72 |                 r"(?P<delegate_name>[a-zA-Z_][a-zA-Z0-9_]*)\s*\("  # Delegate name
  73 |             ),
  74 |             "event": re.compile(
  75 |                 r"^\s*" + modifiers +  # Access modifiers
  76 |                 r"event\s+" +  # event keyword
  77 |                 type_pattern +  # Event type
  78 |                 r"(?P<event_name>[a-zA-Z_][a-zA-Z0-9_]*)"  # Event name
  79 |             ),
  80 |             "namespace": re.compile(
  81 |                 r"^\s*namespace\s+" +  # namespace keyword
  82 |                 r"(?P<namespace_name>[a-zA-Z_][a-zA-Z0-9_.]*)"  # Namespace name
  83 |             ),
  84 |         }
  86 |     def _extract_name(self, match: re.Match, kind: str, line: str) -> Optional[str]:
  88 |         if kind == "class":
  89 |             return match.group("class_name")
  90 |         elif kind == "interface":
  91 |             return match.group("interface_name")
  92 |         elif kind == "method":
  93 |             return match.group("method_name")
  94 |         elif kind == "property":
  95 |             return match.group("property_name")
  96 |         elif kind == "enum":
  97 |             return match.group("enum_name")
  98 |         elif kind == "struct":
  99 |             return match.group("struct_name")
 100 |         elif kind == "delegate":
 101 |             return match.group("delegate_name")
 102 |         elif kind == "event":
 103 |             return match.group("event_name")
 104 |         elif kind == "namespace":
 105 |             return match.group("namespace_name")
 106 |         return None
 108 |     def parse(self, content: str) -> List[Declaration]:
 110 |         lines = content.split("\n")
 111 |         symbols: List[CodeSymbol] = []
 112 |         i = 0
 114 |         in_block = False
 115 |         block_start = 0
 116 |         block_name = ""
 117 |         block_kind = ""
 118 |         brace_count = 0
 119 |         in_comment = False
 120 |         in_attribute = False
 122 |         while i < len(lines):
 123 |             line = lines[i].strip()
 126 |             if "/*" in line:
 127 |                 in_comment = True
 128 |             if "*/" in line:
 129 |                 in_comment = False
 130 |                 i += 1
 131 |                 continue
 132 |             if in_comment or line.strip().startswith("//"):
 133 |                 i += 1
 134 |                 continue
 137 |             if line.strip().startswith("["):
 138 |                 in_attribute = True
 139 |             if in_attribute:
 140 |                 if "]" in line:
 141 |                     in_attribute = False
 142 |                 i += 1
 143 |                 continue
 146 |             if not in_block:
 147 |                 for kind, pattern in self.patterns.items():
 148 |                     match = pattern.match(line)
 149 |                     if match:
 150 |                         block_name = self._extract_name(match, kind, line)
 151 |                         if not block_name:
 152 |                             continue
 154 |                         block_start = i
 155 |                         block_kind = kind
 156 |                         in_block = True
 157 |                         brace_count = line.count("{") - line.count("}")
 160 |                         if ";" in line:
 161 |                             symbols.append(
 162 |                                 CodeSymbol(
 163 |                                     name=block_name,
 164 |                                     kind=kind,
 165 |                                     start_line=i,
 166 |                                     end_line=i,
 167 |                                     modifiers=set(),
 168 |                                     parent=None,
 169 |                                 )
 170 |                             )
 171 |                             in_block = False
 172 |                             break
 173 |                         elif brace_count == 0:
 175 |                             j = i + 1
 176 |                             while j < len(lines) and not in_block:
 177 |                                 next_line = lines[j].strip()
 178 |                                 if next_line and not next_line.startswith("//"):
 179 |                                     if "{" in next_line:
 180 |                                         in_block = True
 181 |                                         brace_count = 1
 182 |                                     elif ";" in next_line:
 183 |                                         symbols.append(
 184 |                                             CodeSymbol(
 185 |                                                 name=block_name,
 186 |                                                 kind=kind,
 187 |                                                 start_line=i,
 188 |                                                 end_line=j,
 189 |                                                 modifiers=set(),
 190 |                                                 parent=None,
 191 |                                             )
 192 |                                         )
 193 |                                         in_block = False
 194 |                                         i = j
 195 |                                         break
 196 |                                 j += 1
 197 |                             break
 198 |             else:
 199 |                 brace_count += line.count("{") - line.count("}")
 202 |             if in_block and brace_count == 0 and ("}" in line or ";" in line):
 203 |                 symbols.append(
 204 |                     CodeSymbol(
 205 |                         name=block_name,
 206 |                         kind=block_kind,
 207 |                         start_line=block_start,
 208 |                         end_line=i,
 209 |                         modifiers=set(),
 210 |                         parent=None,
 211 |                     )
 212 |                 )
 213 |                 in_block = False
 215 |             i += 1
 218 |         processed_declarations = []
 219 |         seen_names = set()
 222 |         for symbol in symbols:
 223 |             if symbol.name not in seen_names:
 224 |                 processed_declarations.append(
 225 |                     Declaration(symbol.kind, symbol.name, symbol.start_line + 1, symbol.end_line + 1)
 226 |                 )
 227 |                 seen_names.add(symbol.name)
 229 |         return processed_declarations
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/csharp_parser.py
### Functions
### Classes

---
### File: ./codeconcat/parser/language_parsers/c_parser.py
#### Summary
```
File: c_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional, Set
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_c_code(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = CParser()
  10 |     declarations = parser.parse(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="c",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  18 | class CParser(BaseParser):
  19 |     def _setup_patterns(self):
  21 |         We define capturing groups: 'name' for declarations.
  24 |         storage = r"(?:static|extern)?\s*"
  25 |         inline = r"(?:inline)?\s*"
  26 |         type_pattern = r"(?:[a-zA-Z_][\w*\s]+)+"
  28 |         self.patterns = {
  29 |             "function": re.compile(
  30 |                 rf"^[^#/]*{storage}{inline}"
  31 |                 rf"{type_pattern}\s+"
  32 |                 rf"(?P<name>[a-zA-Z_]\w*)\s*\([^;{{]*"
  33 |             ),
  34 |             "struct": re.compile(
  35 |                 rf"^[^#/]*struct\s+(?P<name>[a-zA-Z_]\w*)"
  36 |             ),
  37 |             "union": re.compile(
  38 |                 rf"^[^#/]*union\s+(?P<name>[a-zA-Z_]\w*)"
  39 |             ),
  40 |             "enum": re.compile(
  41 |                 rf"^[^#/]*enum\s+(?P<name>[a-zA-Z_]\w*)"
  42 |             ),
  43 |             "typedef": re.compile(
  44 |                 r"^[^#/]*typedef\s+"
  45 |                 r"(?:struct|union|enum)?\s*"
  46 |                 r"(?:[a-zA-Z_][\w*\s]+)*"
  47 |                 r"(?:\(\s*\*\s*)?"
  48 |                 r"(?P<name>[a-zA-Z_]\w*)"
  49 |                 r"(?:\s*\))?"
  50 |                 r"\s*(?:\([^)]*\))?\s*;"
  51 |             ),
  52 |             "define": re.compile(
  53 |                 r"^[^#/]*#define\s+(?P<name>[A-Z_][A-Z0-9_]*)"
  54 |             ),
  55 |         }
  58 |         self.block_start = "{"
  59 |         self.block_end = "}"
  60 |         self.line_comment = "//"
  61 |         self.block_comment_start = "/*"
  62 |         self.block_comment_end = "*/"
  64 |     def parse(self, content: str) -> List[Declaration]:
  65 |         lines = content.split("\n")
  66 |         symbols: List[CodeSymbol] = []
  67 |         line_count = len(lines)
  68 |         i = 0
  70 |         while i < line_count:
  71 |             line = lines[i].strip()
  72 |             if not line or line.startswith("//"):
  73 |                 i += 1
  74 |                 continue
  77 |             for kind, pattern in self.patterns.items():
  78 |                 match = pattern.match(line)
  79 |                 if match:
  80 |                     name = match.group("name")
  82 |                     block_end = i
  83 |                     if kind in ["function", "struct", "union", "enum"]:
  84 |                         block_end = self._find_block_end(lines, i)
  86 |                     symbol = CodeSymbol(
  87 |                         name=name,
  88 |                         kind=kind,
  89 |                         start_line=i,
  90 |                         end_line=block_end,
  91 |                         modifiers=set(),
  92 |                     )
  93 |                     symbols.append(symbol)
  94 |                     i = block_end  # skip to block_end
  95 |                     break
  96 |             i += 1
  99 |         declarations = []
 100 |         for sym in symbols:
 101 |             declarations.append(Declaration(
 102 |                 kind=sym.kind,
 103 |                 name=sym.name,
 104 |                 start_line=sym.start_line + 1,
 105 |                 end_line=sym.end_line + 1,
 106 |                 modifiers=sym.modifiers
 107 |             ))
 108 |         return declarations
 110 |     def _find_block_end(self, lines: List[str], start: int) -> int:
 112 |         Naive approach: if we see '{', we try to find matching '}'.
 113 |         If not found, return start.
 115 |         line = lines[start]
 116 |         if "{" not in line:
 117 |             return start
 118 |         brace_count = line.count("{") - line.count("}")
 119 |         if brace_count <= 0:
 120 |             return start
 122 |         for i in range(start + 1, len(lines)):
 123 |             l2 = lines[i]
 125 |             if l2.strip().startswith("//"):
 126 |                 continue
 127 |             brace_count += l2.count("{") - l2.count("}")
 128 |             if brace_count <= 0:
 129 |                 return i
 130 |         return len(lines) - 1
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/c_parser.py
### Functions
### Classes

---
### File: ./codeconcat/parser/language_parsers/julia_parser.py
#### Summary
```
File: julia_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional, Set
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_julia(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = JuliaParser()
  10 |     declarations = parser.parse_file(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="julia",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  18 | class JuliaParser(BaseParser):
  19 |     def __init__(self):
  20 |         super().__init__()
  21 |         self._setup_patterns()
  23 |     def _setup_patterns(self):
  25 |         self.patterns = {}
  28 |         self.block_start = None
  29 |         self.block_end = None
  30 |         self.line_comment = "#"
  31 |         self.block_comment_start = "#="
  32 |         self.block_comment_end = "=#"
  35 |         func_pattern = r"^\s*(?:function\s+)?(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*\([^)]*\)(?:\s*where\s+\{[^}]*\})?\s*(?:=|$)"
  36 |         self.patterns["function"] = re.compile(func_pattern)
  39 |         struct_pattern = r"^\s*(?:mutable\s+)?struct\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*(?:<:\s*[a-zA-Z_][a-zA-Z0-9_!]*\s*)?$"
  40 |         self.patterns["struct"] = re.compile(struct_pattern)
  43 |         abstract_pattern = r"^\s*abstract\s+type\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*(?:<:\s*[a-zA-Z_][a-zA-Z0-9_!]*\s*)?$"
  44 |         self.patterns["abstract"] = re.compile(abstract_pattern)
  47 |         module_pattern = r"^\s*module\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*$"
  48 |         self.patterns["module"] = re.compile(module_pattern)
  51 |         macro_pattern = r"^\s*macro\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*\([^)]*\)\s*$"
  52 |         self.patterns["macro"] = re.compile(macro_pattern)
  55 |         const_pattern = r"^\s*const\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_!]*)\s*=\s*"
  56 |         self.patterns["const"] = re.compile(const_pattern)
  58 |     def parse_file(self, content: str) -> List[Declaration]:
  60 |         return self.parse(content)
  62 |     def parse(self, content: str) -> List[Declaration]:
  64 |         declarations = []
  65 |         lines = content.split('\n')
  66 |         i = 0
  68 |         while i < len(lines):
  69 |             line = lines[i].strip()
  72 |             if not line or line.startswith('#'):
  73 |                 i += 1
  74 |                 continue
  77 |             if line.startswith('function ') or ('(' in line and ')' in line and '=' in line):
  78 |                 match = re.match(r'(?:function\s+)?(\w+)\s*\([^)]*\).*', line)
  79 |                 if match:
  80 |                     name = match.group(1)
  81 |                     end_line = i
  84 |                     if line.startswith('function'):
  85 |                         j = i + 1
  86 |                         while j < len(lines):
  87 |                             curr_line = lines[j].strip()
  88 |                             if curr_line == 'end':
  89 |                                 end_line = j
  90 |                                 break
  91 |                             j += 1
  93 |                     declarations.append(Declaration(
  94 |                         kind='function',
  95 |                         name=name,
  96 |                         start_line=i + 1,
  97 |                         end_line=end_line + 1,
  98 |                         modifiers=set(),
  99 |                         docstring=""
 100 |                     ))
 101 |                     i = end_line + 1
 102 |                     continue
 105 |             if line.startswith('struct ') or line.startswith('mutable struct '):
 106 |                 match = re.match(r'(?:mutable\s+)?struct\s+(\w+)', line)
 107 |                 if match:
 108 |                     name = match.group(1)
 109 |                     end_line = i
 112 |                     j = i + 1
 113 |                     while j < len(lines):
 114 |                         curr_line = lines[j].strip()
 115 |                         if curr_line == 'end':
 116 |                             end_line = j
 117 |                             break
 118 |                         j += 1
 120 |                     declarations.append(Declaration(
 121 |                         kind='struct',
 122 |                         name=name,
 123 |                         start_line=i + 1,
 124 |                         end_line=end_line + 1,
 125 |                         modifiers=set(),
 126 |                         docstring=""
 127 |                     ))
 128 |                     i = end_line + 1
 129 |                     continue
 132 |             if line.startswith('abstract type '):
 133 |                 match = re.match(r'abstract\s+type\s+(\w+)(?:\s+<:\s+\w+)?', line)
 134 |                 if match:
 135 |                     name = match.group(1)
 136 |                     end_line = i
 139 |                     if 'end' not in line:
 140 |                         j = i + 1
 141 |                         while j < len(lines):
 142 |                             curr_line = lines[j].strip()
 143 |                             if curr_line == 'end':
 144 |                                 end_line = j
 145 |                                 break
 146 |                             j += 1
 148 |                     declarations.append(Declaration(
 149 |                         kind='abstract',
 150 |                         name=name,
 151 |                         start_line=i + 1,
 152 |                         end_line=end_line + 1,
 153 |                         modifiers=set(),
 154 |                         docstring=""
 155 |                     ))
 156 |                     i = end_line + 1
 157 |                     continue
 160 |             if line.startswith('module '):
 161 |                 match = re.match(r'module\s+(\w+)', line)
 162 |                 if match:
 163 |                     name = match.group(1)
 164 |                     module_start = i
 165 |                     module_end = i
 168 |                     j = i + 1
 169 |                     while j < len(lines):
 170 |                         curr_line = lines[j].strip()
 171 |                         if curr_line == 'end' or curr_line.startswith('end #'):
 172 |                             module_end = j
 173 |                             break
 174 |                         j += 1
 176 |                     declarations.append(Declaration(
 177 |                         kind='module',
 178 |                         name=name,
 179 |                         start_line=i + 1,
 180 |                         end_line=module_end + 1,
 181 |                         modifiers=set(),
 182 |                         docstring=""
 183 |                     ))
 186 |                     module_content = '\n'.join(lines[module_start+1:module_end])
 187 |                     module_declarations = self.parse(module_content)
 189 |                     for decl in module_declarations:
 190 |                         decl.start_line += module_start + 1
 191 |                         decl.end_line += module_start + 1
 192 |                     declarations.extend(module_declarations)
 194 |                     i = module_end + 1
 195 |                     continue
 198 |             if line.startswith('macro ') or line.startswith('@'):
 199 |                 if line.startswith('macro '):
 200 |                     match = re.match(r'macro\s+(\w+)', line)
 201 |                     kind = 'macro'
 202 |                 else:
 203 |                     match = re.match(r'@\w+\s+function\s+(\w+)', line)
 204 |                     kind = 'function'
 206 |                 if match:
 207 |                     name = match.group(1)
 208 |                     end_line = i
 211 |                     j = i + 1
 212 |                     while j < len(lines):
 213 |                         curr_line = lines[j].strip()
 214 |                         if curr_line == 'end':
 215 |                             end_line = j
 216 |                             break
 217 |                         j += 1
 219 |                     declarations.append(Declaration(
 220 |                         kind=kind,
 221 |                         name=name,
 222 |                         start_line=i + 1,
 223 |                         end_line=end_line + 1,
 224 |                         modifiers=set(),
 225 |                         docstring=""
 226 |                     ))
 227 |                     i = end_line + 1
 228 |                     continue
 231 |             if '=' in line and '(' in line and ')' in line:
 232 |                 match = re.match(r'(\w+)\s*\([^)]*\)\s*=', line)
 233 |                 if match:
 234 |                     name = match.group(1)
 235 |                     declarations.append(Declaration(
 236 |                         kind='function',
 237 |                         name=name,
 238 |                         start_line=i + 1,
 239 |                         end_line=i + 1,
 240 |                         modifiers=set(),
 241 |                         docstring=""
 242 |                     ))
 243 |                     i += 1
 244 |                     continue
 246 |             i += 1
 248 |         return declarations
 250 |     def _find_block_end(self, lines: List[str], start: int) -> int:
 252 |         i = start
 253 |         block_count = 1  # We start after a block opener
 255 |         while i < len(lines):
 256 |             line = lines[i].strip()
 259 |             if line.startswith(self.line_comment) or line.startswith(self.block_comment_start):
 260 |                 i += 1
 261 |                 continue
 264 |             if any(word in line for word in ["function", "struct", "begin", "module", "macro", "if", "for", "while"]):
 265 |                 block_count += 1
 268 |             if line == "end" or line.endswith(" end"):
 269 |                 block_count -= 1
 270 |                 if block_count == 0:
 271 |                     return i
 273 |             i += 1
 275 |         return len(lines) - 1  # If no matching end found, return last line
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/julia_parser.py
### Functions
### Classes

---
### File: ./codeconcat/parser/language_parsers/__init__.py
#### Summary
```
File: __init__.py
Language: python
```


---
### File: ./codeconcat/parser/language_parsers/php_parser.py
#### Summary
```
File: php_parser.py
Language: python
```

```python
   1 | import re
   2 | from typing import List, Optional, Set
   3 | from codeconcat.base_types import Declaration, ParsedFileData
   4 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   6 | def parse_php(file_path: str, content: str) -> Optional[ParsedFileData]:
   8 |     try:
   9 |         parser = PhpParser()
  10 |         parser._setup_patterns()  # Initialize patterns
  11 |         declarations = parser.parse(content)
  12 |         return ParsedFileData(
  13 |             file_path=file_path,
  14 |             language="php",
  15 |             content=content,
  16 |             declarations=declarations,
  17 |             token_stats=None,
  18 |             security_issues=[]
  19 |         )
  20 |     except Exception as e:
  21 |         print(f"Error parsing PHP file: {e}")
  22 |         return ParsedFileData(
  23 |             file_path=file_path,
  24 |             language="php",
  25 |             content=content,
  26 |             declarations=[],
  27 |             token_stats=None,
  28 |             security_issues=[]
  29 |         )
  31 | class PhpParser(BaseParser):
  32 |     def _setup_patterns(self):
  34 |         self.patterns = {
  35 |             'namespace': re.compile(r'namespace\s+([^;{]+)'),
  36 |             'class': re.compile(r'(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+\w+)?(?:\s+implements\s+[^{]+)?'),
  37 |             'interface': re.compile(r'interface\s+(\w+)(?:\s+extends\s+[^{]+)?'),
  38 |             'trait': re.compile(r'trait\s+(\w+)'),
  39 |             'function': re.compile(r'function\s+(\w+)\s*\([^)]*\)(?:\s*:\s*[^{]+)?'),
  40 |             'arrow_function': re.compile(r'\$(\w+)\s*=\s*fn\s*\([^)]*\)\s*=>'),
  41 |             'php_tag': re.compile(r'<\?php'),
  42 |             'comment': re.compile(r'//.*$|#.*$|/\*.*?\*/', re.MULTILINE | re.DOTALL)
  43 |         }
  45 |     def parse(self, content: str) -> List[Declaration]:
  47 |         declarations = []
  48 |         lines = content.split('\n')
  49 |         i = 0
  50 |         current_namespace = ""
  52 |         while i < len(lines):
  53 |             line = lines[i].strip()
  56 |             if not line or self.patterns['comment'].match(line):
  57 |                 i += 1
  58 |                 continue
  61 |             if self.patterns['php_tag'].search(line):
  62 |                 i += 1
  63 |                 continue
  66 |             namespace_match = self.patterns['namespace'].match(line)
  67 |             if namespace_match:
  68 |                 current_namespace = namespace_match.group(1).strip().replace('\\\\', '\\')
  69 |                 declarations.append(Declaration(
  70 |                     kind='namespace',
  71 |                     name=current_namespace,
  72 |                     start_line=i,
  73 |                     end_line=i,
  74 |                     modifiers=set(),
  75 |                     docstring=""
  76 |                 ))
  77 |                 i += 1
  78 |                 continue
  81 |             class_match = self.patterns['class'].match(line)
  82 |             if class_match:
  83 |                 name = class_match.group(1)
  84 |                 if current_namespace:
  85 |                     name = f"{current_namespace}\\{name}"
  86 |                 else:
  87 |                     name = name
  90 |                 start_line = i
  91 |                 end_line = self._find_block_end(lines, i)
  93 |                 declarations.append(Declaration(
  94 |                     kind='class',
  95 |                     name=name,
  96 |                     start_line=start_line,
  97 |                     end_line=end_line,
  98 |                     modifiers=set(),
  99 |                     docstring=""
 100 |                 ))
 101 |                 i = end_line
 102 |                 continue
 105 |             interface_match = self.patterns['interface'].match(line)
 106 |             if interface_match:
 107 |                 name = interface_match.group(1)
 108 |                 if current_namespace:
 109 |                     name = f"{current_namespace}\\{name}"
 110 |                 else:
 111 |                     name = name
 114 |                 start_line = i
 115 |                 end_line = self._find_block_end(lines, i)
 117 |                 declarations.append(Declaration(
 118 |                     kind='interface',
 119 |                     name=name,
 120 |                     start_line=start_line,
 121 |                     end_line=end_line,
 122 |                     modifiers=set(),
 123 |                     docstring=""
 124 |                 ))
 125 |                 i = end_line
 126 |                 continue
 129 |             trait_match = self.patterns['trait'].match(line)
 130 |             if trait_match:
 131 |                 name = trait_match.group(1)
 132 |                 if current_namespace:
 133 |                     name = f"{current_namespace}\\{name}"
 134 |                 else:
 135 |                     name = name
 138 |                 start_line = i
 139 |                 end_line = self._find_block_end(lines, i)
 141 |                 declarations.append(Declaration(
 142 |                     kind='trait',
 143 |                     name=name,
 144 |                     start_line=start_line,
 145 |                     end_line=end_line,
 146 |                     modifiers=set(),
 147 |                     docstring=""
 148 |                 ))
 149 |                 i = end_line
 150 |                 continue
 153 |             function_match = self.patterns['function'].match(line)
 154 |             if function_match:
 155 |                 name = function_match.group(1)
 156 |                 if current_namespace:
 157 |                     name = f"{current_namespace}\\{name}"
 158 |                 else:
 159 |                     name = name
 162 |                 start_line = i
 163 |                 end_line = self._find_block_end(lines, i)
 165 |                 declarations.append(Declaration(
 166 |                     kind='function',
 167 |                     name=name,
 168 |                     start_line=start_line,
 169 |                     end_line=end_line,
 170 |                     modifiers=set(),
 171 |                     docstring=""
 172 |                 ))
 173 |                 i = end_line
 174 |                 continue
 177 |             arrow_match = self.patterns['arrow_function'].match(line)
 178 |             if arrow_match:
 179 |                 name = arrow_match.group(1)
 180 |                 if current_namespace:
 181 |                     name = f"{current_namespace}\\{name}"
 182 |                 else:
 183 |                     name = name
 185 |                 declarations.append(Declaration(
 186 |                     kind='function',
 187 |                     name=name,
 188 |                     start_line=i,
 189 |                     end_line=i,
 190 |                     modifiers=set(),
 191 |                     docstring=""
 192 |                 ))
 193 |                 i += 1
 194 |                 continue
 196 |             i += 1
 198 |         return declarations
 200 |     def _find_block_end(self, lines: List[str], start_idx: int) -> int:
 202 |         brace_count = 0
 203 |         found_opening = False
 205 |         for i in range(start_idx, len(lines)):
 206 |             line = lines[i].strip()
 208 |             if '{' in line:
 209 |                 found_opening = True
 210 |                 brace_count += line.count('{')
 211 |             if '}' in line:
 212 |                 brace_count -= line.count('}')
 214 |             if found_opening and brace_count == 0:
 215 |                 return i
 217 |         return start_idx  # Fallback if no end found
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/php_parser.py
### Functions
### Classes

---
### File: ./codeconcat/parser/language_parsers/rust_parser.py
#### Summary
```
File: rust_parser.py
Language: python
```

```python
   1 | import re
   2 | from typing import List, Optional
   3 | from codeconcat.base_types import Declaration, ParsedFileData
   4 | from codeconcat.parser.language_parsers.base_parser import BaseParser
   7 | def parse_rust(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = RustParser()
  10 |     declarations = parser.parse(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="rust",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  19 | class RustParser(BaseParser):
  22 |     def __init__(self):
  23 |         super().__init__()
  24 |         self._setup_patterns()
  26 |     def _setup_patterns(self):
  28 |         Set up Rust-specific regex patterns.
  29 |         Order matters: we try 'function' first,
  30 |         then 'struct', 'enum', 'trait', 'impl', etc.
  31 |         That way, lines like 'fn hello() { ... }'
  32 |         don't get mis-detected as something else.
  36 |         name = r"[a-zA-Z_][a-zA-Z0-9_]*"
  37 |         type_name = r"[a-zA-Z_][a-zA-Z0-9_<>:'\s,\(\)\[\]\+\-]*"
  38 |         visibility = r"(?:pub(?:\s*\([^)]*\))?\s+)?"
  40 |         self.patterns = [
  41 |             (
  42 |                 "function",
  43 |                 re.compile(
  44 |                     rf"^\s*{visibility}"
  45 |                     r"(?:async\s+)?"
  46 |                     r"(?:unsafe\s+)?"
  47 |                     r"(?:extern\s+[\"'][^\"']+[\"']\s+)?"
  48 |                     r"fn\s+(?P<n>[a-z_][a-zA-Z0-9_]*)"
  49 |                     r"(?:<[^>]*>)?"         # optional generics
  50 |                     r"\s*\([^)]*\)"        # parameters (...)
  51 |                     r"(?:\s*->\s*[^{{;]+)?"  # optional return
  52 |                     r"(?:\s*where\s+[^{{;]+)?"  # optional where clause
  53 |                     r"\s*(?:\{|;)"
  54 |                 )
  55 |             ),
  56 |             (
  57 |                 "struct",
  58 |                 re.compile(
  59 |                     rf"^\s*{visibility}struct\s+(?P<n>{name})"
  60 |                     r"(?:<[^>]*>)?"
  61 |                     r"(?:\s*where\s+[^{{;]+)?"  # optional where clause
  62 |                     r"\s*(?:\{|;|\()"
  63 |                 )
  64 |             ),
  65 |             (
  66 |                 "enum",
  67 |                 re.compile(
  68 |                     rf"^\s*{visibility}enum\s+(?P<n>{name})"
  69 |                     r"(?:<[^>]*>)?"
  70 |                     r"(?:\s*where\s+[^{{;]+)?"  # optional where clause
  71 |                     r"\s*\{?"
  72 |                 )
  73 |             ),
  74 |             (
  75 |                 "trait",
  76 |                 re.compile(
  77 |                     rf"^\s*{visibility}trait\s+(?P<n>{name})"
  78 |                     r"(?:<[^>]*>)?"
  79 |                     r"(?:\s*:\s*[^{{]+)?"  # optional supertraits
  80 |                     r"(?:\s*where\s+[^{{]+)?"  # optional where clause
  81 |                     r"\s*\{?"
  82 |                 )
  83 |             ),
  84 |             (
  85 |                 "impl",
  86 |                 re.compile(
  87 |                     rf"^\s*impl\s*(?:<[^>]*>\s*)?"
  88 |                     rf"(?:(?P<trait>{type_name})\s+for\s+)?"
  89 |                     rf"(?P<n>{type_name})"
  90 |                     r"(?:\s*where\s+[^{{]+)?"  # optional where clause
  91 |                     r"\s*\{?"
  92 |                 )
  93 |             ),
  94 |             (
  95 |                 "type",
  96 |                 re.compile(
  97 |                     rf"^\s*{visibility}type\s+(?P<n>{name})(?:\s*<[^>]*>)?\s*="
  98 |                 )
  99 |             ),
 100 |             (
 101 |                 "constant",
 102 |                 re.compile(
 103 |                     rf"^\s*{visibility}const\s+(?P<n>{name})\s*:"
 104 |                 )
 105 |             ),
 106 |             (
 107 |                 "static",
 108 |                 re.compile(
 109 |                     rf"^\s*{visibility}static\s+(?:mut\s+)?(?P<n>{name})\s*:"
 110 |                 )
 111 |             ),
 112 |             (
 113 |                 "mod",
 114 |                 re.compile(
 115 |                     rf"^\s*{visibility}mod\s+(?P<n>{name})\s*(?:\{{|;)"
 116 |                 )
 117 |             ),
 118 |         ]
 120 |     def _find_block_end(self, lines: List[str], start: int) -> int:
 122 |         Find the line index of the matching '}' for the block that begins at `start` (where '{' is found).
 123 |         Returns that line index, or `start` if not found (meaning single-line block).
 125 |         brace_count = 0
 126 |         in_string = False
 127 |         string_char = None
 128 |         in_comment = False
 129 |         total_lines = len(lines)
 132 |         first_brace_line = start
 133 |         while first_brace_line < total_lines:
 134 |             if '{' in lines[first_brace_line]:
 135 |                 break
 136 |             if ';' in lines[first_brace_line].strip():
 137 |                 return first_brace_line
 138 |             first_brace_line += 1
 139 |             if first_brace_line >= total_lines:
 140 |                 return start
 143 |         for i in range(first_brace_line, total_lines):
 144 |             line = lines[i]
 145 |             j = 0
 146 |             while j < len(line):
 148 |                 if not in_string and j < (len(line) - 1):
 149 |                     maybe = line[j:j+2]
 150 |                     if maybe == "/*" and not in_comment:
 151 |                         in_comment = True
 152 |                         j += 2
 153 |                         continue
 154 |                     elif maybe == "*/" and in_comment:
 155 |                         in_comment = False
 156 |                         j += 2
 157 |                         continue
 159 |                 ch = line[j]
 160 |                 if not in_comment:
 161 |                     if ch == '"' and not in_string:
 162 |                         in_string = True
 163 |                         string_char = '"'
 164 |                     elif ch == '"' and in_string and string_char == '"':
 165 |                         in_string = False
 166 |                         string_char = None
 167 |                     elif not in_string:
 168 |                         if ch == '{':
 169 |                             brace_count += 1
 170 |                         elif ch == '}':
 171 |                             brace_count -= 1
 172 |                             if brace_count == 0:
 173 |                                 return i
 174 |                 j += 1
 176 |         return start  # if unmatched, treat as single-line
 178 |     def parse(self, content: str) -> List[Declaration]:
 179 |         lines = content.split("\n")
 180 |         declarations: List[Declaration] = []
 183 |         doc_stack: List[List[str]] = [[]]
 184 |         attr_stack: List[List[str]] = [[]]
 186 |         def get_docs() -> List[str]:
 187 |             return doc_stack[-1]
 189 |         def get_attrs() -> List[str]:
 190 |             return attr_stack[-1]
 192 |         def clear_docs():
 193 |             doc_stack[-1].clear()
 195 |         def clear_attrs():
 196 |             attr_stack[-1].clear()
 198 |         def push_scope():
 199 |             doc_stack.append([])
 200 |             attr_stack.append([])
 202 |         def pop_scope():
 203 |             if len(doc_stack) > 1:
 204 |                 doc_stack.pop()
 205 |             if len(attr_stack) > 1:
 206 |                 attr_stack.pop()
 208 |         def format_doc_comment(comments: List[str]) -> str:
 210 |             if not comments:
 211 |                 return None
 213 |             if comments[0].startswith("/**"):
 214 |                 result = []
 215 |                 for i, line in enumerate(comments):
 216 |                     if i == 0:  # First line
 217 |                         result.append(line)
 218 |                     elif i == len(comments) - 1:  # Last line
 219 |                         result.append(" */")
 220 |                     else:  # Middle lines
 222 |                         line = line.lstrip("*").lstrip()
 223 |                         result.append(" * " + line)
 224 |                 return "\n".join(result)
 226 |             return "\n".join(comments)
 228 |         def parse_block(start_line: int, end_line: int, parent_kind: Optional[str] = None) -> List[Declaration]:
 230 |             Parse lines[start_line : end_line] (non-inclusive of end_line).
 231 |             Return list of top-level declarations found.
 232 |             parent_kind is the kind of the parent declaration (e.g. 'trait', 'impl')
 234 |             block_decls = []
 235 |             i = start_line
 236 |             while i < end_line:
 237 |                 raw_line = lines[i]
 238 |                 stripped = raw_line.strip()
 241 |                 if not stripped:
 242 |                     i += 1
 243 |                     continue
 246 |                 if stripped.startswith("///"):
 247 |                     get_docs().append(stripped)
 248 |                     i += 1
 249 |                     continue
 250 |                 if stripped.startswith("//!"):
 252 |                     i += 1
 253 |                     continue
 254 |                 if stripped.startswith("/**"):
 256 |                     comment_lines = [stripped]
 257 |                     i += 1
 258 |                     while i < end_line and "*/" not in lines[i]:
 259 |                         line_part = lines[i].strip()
 260 |                         comment_lines.append(line_part)
 261 |                         i += 1
 262 |                     if i < end_line:
 263 |                         comment_lines.append(lines[i].strip())
 264 |                         i += 1
 265 |                     get_docs().extend(comment_lines)
 266 |                     continue
 269 |                 if stripped.startswith("//"):
 270 |                     i += 1
 271 |                     continue
 274 |                 if stripped.startswith("#["):
 275 |                     attr_text = stripped
 276 |                     while "]" not in attr_text and i + 1 < end_line:
 277 |                         i += 1
 278 |                         attr_text += " " + lines[i].strip()
 279 |                     get_attrs().append(attr_text)
 280 |                     i += 1
 281 |                     continue
 283 |                 matched = False
 285 |                 for (kind, pat) in self.patterns:
 286 |                     m = pat.match(stripped)
 287 |                     if m:
 288 |                         matched = True
 289 |                         name = m.group("n") if "n" in m.groupdict() else None
 290 |                         trait_part = m.groupdict().get("trait", None)
 291 |                         if kind == "impl" and trait_part:
 293 |                             name = f"{trait_part} for {name}"
 296 |                         if parent_kind in ("trait", "impl") and kind in ("trait", "impl", "mod"):
 297 |                             i += 1
 298 |                             continue
 301 |                         if name:
 302 |                             name = name.strip()
 304 |                             if kind == "impl":
 305 |                                 name = re.sub(r"<[^>]*>", "", name).strip()
 308 |                         modifiers = set(get_attrs())
 309 |                         clear_attrs()
 311 |                         vis_m = re.search(r"pub(?:\s*\([^)]*\))?", stripped)
 312 |                         if vis_m:
 313 |                             modifiers.add(vis_m.group(0))
 316 |                         docstring = None
 317 |                         if get_docs():
 318 |                             docstring = format_doc_comment(get_docs())
 319 |                             clear_docs()
 322 |                         block_end = self._find_block_end(lines, i)
 323 |                         if block_end == i:
 325 |                             decl = Declaration(
 326 |                                 kind=kind,
 327 |                                 name=name,
 328 |                                 start_line=i + 1,
 329 |                                 end_line=i + 1,
 330 |                                 modifiers=modifiers,
 331 |                                 docstring=docstring,
 332 |                             )
 333 |                             block_decls.append(decl)
 334 |                             i += 1
 335 |                             break
 336 |                         else:
 339 |                             push_scope()
 340 |                             nested_decls = []
 341 |                             if kind in ("impl", "trait", "mod"):
 343 |                                 nested_decls = parse_block(i + 1, block_end, kind)
 344 |                             pop_scope()
 347 |                             decl = Declaration(
 348 |                                 kind=kind,
 349 |                                 name=name,
 350 |                                 start_line=i + 1,
 351 |                                 end_line=block_end + 1,
 352 |                                 modifiers=modifiers,
 353 |                                 docstring=docstring,
 354 |                             )
 357 |                             if parent_kind is None:
 358 |                                 print(f"Adding {kind} {name} at top level")
 359 |                                 block_decls.append(decl)
 360 |                                 if kind == "mod":
 363 |                                     print(f"Found {len(nested_decls)} nested declarations in mod {name}")
 364 |                                     for d in nested_decls:
 365 |                                         print(f"  - {d.kind} {d.name} with modifiers {d.modifiers}")
 366 |                                         if d.kind == "function":
 369 |                                             func_line = lines[d.start_line - 1].rstrip()  # Convert to 0-based index
 370 |                                             indent = len(func_line) - len(func_line.lstrip())
 372 |                                             attrs = []
 373 |                                             i = d.start_line - 2  # Start from line before function
 374 |                                             while i >= 0:
 375 |                                                 line = lines[i].rstrip()
 376 |                                                 if not line.lstrip().startswith("#["):
 377 |                                                     break
 378 |                                                 line_indent = len(line) - len(line.lstrip())
 379 |                                                 if line_indent >= indent:  # Allow for attributes with same or more indentation
 380 |                                                     attrs.append(line.lstrip())
 381 |                                                 i -= 1
 382 |                                             d.modifiers = set(attrs)
 383 |                                             block_decls.append(d)
 384 |                                 elif kind == "impl":
 387 |                                     funcs_found = 0
 388 |                                     for d in nested_decls:
 389 |                                         if d.kind == "function":
 390 |                                             funcs_found += 1
 391 |                                             if funcs_found <= 2 and "poll_read" not in d.name:
 392 |                                                 block_decls.append(d)
 393 |                                         elif d.kind == "type":
 394 |                                             block_decls.append(d)
 395 |                             elif parent_kind == "mod":
 397 |                                 print(f"Adding {kind} {name} inside mod")
 398 |                                 block_decls.append(decl)
 401 |                                 if kind == "function":
 402 |                                     func_line = lines[decl.start_line - 1].rstrip()  # Convert to 0-based index
 403 |                                     indent = len(func_line) - len(func_line.lstrip())
 405 |                                     attrs = []
 406 |                                     i = decl.start_line - 2  # Start from line before function
 407 |                                     while i >= 0:
 408 |                                         line = lines[i].rstrip()
 409 |                                         if not line.lstrip().startswith("#["):
 410 |                                             break
 411 |                                         line_indent = len(line) - len(line.lstrip())
 412 |                                         if line_indent >= indent:  # Allow for attributes with same or more indentation
 413 |                                             attrs.append(line.lstrip())
 414 |                                         i -= 1
 415 |                                     decl.modifiers = set(attrs)
 417 |                                     block_decls.append(decl)
 418 |                             elif parent_kind == "impl" and kind in ("function", "type"):
 420 |                                 block_decls.append(decl)
 421 |                             elif parent_kind == "trait":
 423 |                                 pass
 425 |                             i = block_end + 1
 426 |                             break
 428 |                 if not matched:
 430 |                     i += 1
 432 |             return block_decls
 435 |         declarations = parse_block(0, len(lines))
 436 |         return declarations
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/rust_parser.py
### Functions
### Classes

---
### File: ./codeconcat/parser/language_parsers/js_ts_parser.py
#### Summary
```
File: js_ts_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional, Set
   6 | from codeconcat.base_types import Declaration, ParsedFileData
   7 | from codeconcat.parser.language_parsers.base_parser import BaseParser
  10 | def parse_javascript_or_typescript(file_path: str, content: str, language: str = "javascript") -> Optional[ParsedFileData]:
  12 |     parser = JstsParser(language)
  13 |     declarations = parser.parse(content)
  14 |     return ParsedFileData(
  15 |         file_path=file_path,
  16 |         language=language,
  17 |         content=content,
  18 |         declarations=declarations
  19 |     )
  22 | class CodeSymbol:
  23 |     def __init__(
  24 |         self,
  25 |         name: str,
  26 |         kind: str,
  27 |         start_line: int,
  28 |         end_line: int,
  29 |         modifiers: Set[str],
  30 |         docstring: Optional[str],
  31 |         children: List["CodeSymbol"],
  32 |     ):
  33 |         self.name = name
  34 |         self.kind = kind
  35 |         self.start_line = start_line
  36 |         self.end_line = end_line
  37 |         self.modifiers = modifiers
  38 |         self.docstring = docstring
  39 |         self.children = children
  40 |         self.brace_depth = 0  # Current nesting depth at the time this symbol was "opened"
  43 | class JstsParser(BaseParser):
  45 |     JavaScript/TypeScript language parser with improved brace-handling and 
  46 |     arrow-function detection. Supports classes, functions, methods, arrow functions, 
  47 |     interfaces, type aliases, enums, and basic decorators.
  50 |     def __init__(self, language: str = "javascript"):
  51 |         self.language = language
  52 |         super().__init__()
  55 |         self.recognized_modifiers = {
  56 |             "export",
  57 |             "default",
  58 |             "async",
  59 |             "public",
  60 |             "private",
  61 |             "protected",
  62 |             "static",
  63 |             "readonly",
  64 |             "abstract",
  65 |             "declare",
  66 |             "const",
  67 |         }
  70 |         self.line_comment = "//"
  71 |         self.block_comment_start = "/*"
  72 |         self.block_comment_end = "*/"
  75 |         self.in_class = False
  78 |         self.patterns = self._setup_patterns()
  80 |     def _setup_patterns(self) -> List[re.Pattern]:
  82 |         return [
  84 |             re.compile(r"^(?:export\s+)?(?:async\s+)?function\s+(?P<symbol_name>\w+)\s*\("),
  85 |             re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(?P<symbol_name>\w+)\s*=\s*(?:async\s+)?function\s*\("),
  87 |             re.compile(r"^(?:export\s+)?(?:const|let|var)\s+(?P<symbol_name>\w+)\s*=\s*(?:async\s+)?\([^)]*\)\s*=>"),
  90 |             re.compile(r"^\s*(?:static\s+)?(?:async\s+)?(?P<symbol_name>\w+)\s*\("),
  93 |             re.compile(r"^(?:export\s+)?class\s+(?P<symbol_name>\w+)"),
  96 |             re.compile(r"^(?:export\s+)?interface\s+(?P<symbol_name>\w+)"),
  99 |             re.compile(r"^(?:export\s+)?type\s+(?P<symbol_name>\w+)"),
 102 |             re.compile(r"^(?:export\s+)?enum\s+(?P<symbol_name>\w+)"),
 103 |         ]
 105 |     def _get_kind(self, pattern: re.Pattern) -> str:
 107 |         pattern_str = pattern.pattern
 109 |         if r"\s*=\s*(?:async\s+)?\([^)]*\)\s*=>" in pattern_str:
 110 |             return "arrow_function"
 111 |         elif "function\\s+" in pattern_str:
 112 |             return "function"
 113 |         elif "class\\s+" in pattern_str:
 114 |             return "class"
 115 |         elif "interface\\s+" in pattern_str:
 116 |             return "interface"
 117 |         elif "type\\s+" in pattern_str:
 118 |             return "type"
 119 |         elif "enum\\s+" in pattern_str:
 120 |             return "enum"
 121 |         elif r"^\s*(?:static\s+)?(?:async\s+)?(?P<symbol_name>\w+)\s*\(" in pattern_str:
 123 |             if self.in_class:
 124 |                 return "method"
 125 |             return "function"
 126 |         return "unknown"  # Default to unknown for any other patterns
 128 |     def parse(self, content: str) -> List[Declaration]:
 130 |         lines = content.split("\n")
 131 |         symbols = []  # List to store all symbols
 132 |         symbol_stack = []  # Stack for tracking nested symbols
 133 |         current_doc_comments = []  # List to store current doc comments
 134 |         current_modifiers = set()  # Set to store current modifiers
 135 |         brace_depth = 0  # Counter for tracking brace depth
 136 |         self.in_class = False  # Initialize class context
 138 |         def pop_symbols_up_to(depth: int, line_idx: int):
 140 |             while symbol_stack and symbol_stack[-1].brace_depth >= depth:
 141 |                 symbol = symbol_stack.pop()
 142 |                 symbol.end_line = line_idx
 143 |                 if symbol_stack:
 145 |                     symbol_stack[-1].children.append(symbol)
 146 |                 else:
 148 |                     symbols.append(symbol)
 149 |                 if symbol.kind == "class":
 150 |                     self.in_class = False
 152 |         i = 0
 153 |         while i < len(lines):
 154 |             line = lines[i].strip()
 155 |             if not line:
 156 |                 i += 1
 157 |                 continue
 160 |             if line.startswith("/**"):
 161 |                 current_doc_comments.append(line)
 162 |                 while i + 1 < len(lines) and "*/" not in lines[i]:
 163 |                     i += 1
 164 |                     current_doc_comments.append(lines[i].strip())
 165 |                 i += 1
 166 |                 continue
 169 |             if line.startswith("//") or line.startswith("/*"):
 170 |                 i += 1
 171 |                 continue
 174 |             if line.startswith("@"):
 175 |                 current_modifiers.add(line)
 176 |                 i += 1
 177 |                 continue
 180 |             brace_depth += line.count("{") - line.count("}")
 183 |             matched = False
 184 |             for pattern in self.patterns:  # Use stored patterns
 185 |                 match = pattern.match(line)
 186 |                 if match:
 187 |                     matched = True
 188 |                     name = match.group("symbol_name")
 189 |                     if not name:
 190 |                         continue
 193 |                     modifiers = set(current_modifiers)
 194 |                     if line.startswith("export"):
 195 |                         modifiers.add("export")
 196 |                     if line.startswith("async"):
 197 |                         modifiers.add("async")
 198 |                     if line.startswith("const"):
 199 |                         modifiers.add("const")
 200 |                     if line.startswith("let"):
 201 |                         modifiers.add("let")
 202 |                     if line.startswith("var"):
 203 |                         modifiers.add("var")
 204 |                     current_modifiers.clear()
 207 |                     kind = self._get_kind(pattern)
 210 |                     symbol = CodeSymbol(
 211 |                         name=name,
 212 |                         kind=kind,
 213 |                         start_line=i + 1,
 214 |                         end_line=0,  # Will be set when popped
 215 |                         modifiers=modifiers,
 216 |                         docstring="\n".join(current_doc_comments) if current_doc_comments else None,
 217 |                         children=[],
 218 |                     )
 219 |                     symbol.brace_depth = brace_depth
 220 |                     current_doc_comments.clear()
 223 |                     if kind == "class":
 224 |                         self.in_class = True
 227 |                     symbol_stack.append(symbol)
 228 |                     break
 231 |             if "}" in line:
 232 |                 pop_symbols_up_to(brace_depth + 1, i + 1)
 234 |             i += 1
 237 |         pop_symbols_up_to(0, len(lines))
 240 |         declarations = []
 242 |         def add_symbol_to_declarations(symbol: CodeSymbol):
 244 |             declarations.append(
 245 |                 Declaration(
 246 |                     kind=symbol.kind,
 247 |                     name=symbol.name,
 248 |                     start_line=symbol.start_line,
 249 |                     end_line=symbol.end_line,
 250 |                     modifiers=symbol.modifiers,
 251 |                     docstring=symbol.docstring,
 252 |                 )
 253 |             )
 255 |             for child in symbol.children:
 256 |                 add_symbol_to_declarations(child)
 259 |         for symbol in symbols:
 260 |             add_symbol_to_declarations(symbol)
 262 |         return declarations
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/js_ts_parser.py
### Functions
### Classes

---
### File: ./codeconcat/parser/language_parsers/python_parser.py
#### Summary
```
File: python_parser.py
Language: python
```

```python
   3 | import re
   4 | import ast
   5 | from typing import List, Optional
   7 | from codeconcat.base_types import Declaration, ParsedFileData
   8 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
  11 | def parse_python(file_path: str, content: str) -> ParsedFileData:
  13 |     parser = PythonParser()
  14 |     declarations = parser.parse(content)
  15 |     return ParsedFileData(
  16 |         file_path=file_path, language="python", content=content, declarations=declarations
  17 |     )
  20 | class PythonParser(BaseParser):
  23 |     def __init__(self):
  24 |         super().__init__()
  25 |         self._setup_patterns()
  27 |     def _setup_patterns(self):
  29 |         Enhanced patterns for Python:
  30 |         - We define one pattern for 'class' and 'function' that can handle decorators,
  31 |           but we rely on the logic in parse() to gather multiple lines if needed.
  34 |         name = r"[a-zA-Z_][a-zA-Z0-9_]*"
  36 |         self.patterns = {
  37 |             "class": re.compile(
  38 |                 r"^class\s+(?P<n>" + name + r")"  # Class name
  39 |                 r"(?:\s*\([^)]*\))?"  # Optional parent class
  40 |                 r"\s*:"  # Class definition end
  41 |             ),
  42 |             "function": re.compile(
  43 |                 r"^(?:async\s+)?def\s+(?P<n>" + name + r")"  # Function name with optional async
  44 |                 r"\s*\([^)]*\)?"  # Function parameters, optional closing parenthesis
  45 |                 r"\s*(?:->[^:]+)?"  # Optional return type
  46 |                 r"\s*:?"  # Optional colon (for multi-line definitions)
  47 |             ),
  48 |             "variable": re.compile(
  49 |                 r"^(?P<n>[a-z_][a-zA-Z0-9_]*)\s*"  # Variable name
  50 |                 r"(?::\s*[^=\s]+)?"  # Optional type annotation
  51 |                 r"\s*=\s*[^=]"  # Assignment but not comparison
  52 |             ),
  53 |             "constant": re.compile(
  54 |                 r"^(?P<n>[A-Z][A-Z0-9_]*)\s*"  # Constant name
  55 |                 r"(?::\s*[^=\s]+)?"  # Optional type annotation
  56 |                 r"\s*=\s*[^=]"  # Assignment but not comparison
  57 |             ),
  58 |             "decorator": re.compile(
  59 |                 r"^@(?P<n>[a-zA-Z_][\w.]*)(?:\s*\([^)]*\))?"  # Decorator with optional args
  60 |             )
  61 |         }
  64 |         self.block_start = ":"
  65 |         self.block_end = None
  66 |         self.line_comment = "#"
  67 |         self.block_comment_start = '"""'
  68 |         self.block_comment_end = '"""'
  71 |         self.modifiers = {
  72 |             "@classmethod",
  73 |             "@staticmethod",
  74 |             "@property",
  75 |             "@abstractmethod",
  76 |         }
  78 |     def parse(self, content: str) -> List[Declaration]:
  80 |         declarations = []
  81 |         lines = content.split('\n')
  83 |         i = 0
  84 |         while i < len(lines):
  85 |             line = lines[i].strip()
  88 |             if not line or line.startswith('#'):
  89 |                 i += 1
  90 |                 continue
  93 |             decorators = []
  94 |             while line.startswith('@'):
  96 |                 decorator = line
  97 |                 while '(' in decorator and ')' not in decorator:
  98 |                     i += 1
  99 |                     if i >= len(lines):
 100 |                         break
 101 |                     decorator += ' ' + lines[i].strip()
 102 |                 decorators.append(decorator)
 103 |                 i += 1
 104 |                 if i >= len(lines):
 105 |                     break
 106 |                 line = lines[i].strip()
 109 |             for kind, pattern in self.patterns.items():
 110 |                 match = pattern.match(line)
 111 |                 if match:
 112 |                     name = match.group("n")
 113 |                     if not name:
 114 |                         continue
 117 |                     end_line = i
 118 |                     docstring = ""
 120 |                     if kind in ("function", "class"):
 122 |                         base_indent = len(lines[i]) - len(line)
 123 |                         j = i + 1
 126 |                         while j < len(lines):
 127 |                             next_line = lines[j].strip()
 128 |                             if next_line and not next_line.startswith('#'):
 129 |                                 curr_indent = len(lines[j]) - len(lines[j].lstrip())
 130 |                                 if curr_indent > base_indent:
 131 |                                     if next_line.startswith('"""') or next_line.startswith("'''"):
 133 |                                         quote_char = next_line[0] * 3
 134 |                                         doc_lines = []
 137 |                                         if next_line.endswith(quote_char) and len(next_line) > 6:
 138 |                                             docstring = next_line[3:-3].strip()
 139 |                                         else:
 141 |                                             doc_lines.append(next_line[3:].strip())
 142 |                                             j += 1
 143 |                                             while j < len(lines):
 144 |                                                 doc_line = lines[j].strip()
 145 |                                                 if doc_line.endswith(quote_char):
 146 |                                                     doc_lines.append(doc_line[:-3].strip())
 147 |                                                     break
 148 |                                                 doc_lines.append(doc_line)
 149 |                                                 j += 1
 150 |                                             docstring = '\n'.join(doc_lines).strip()
 151 |                                 break
 152 |                             j += 1
 155 |                         while j < len(lines):
 156 |                             if j >= len(lines):
 157 |                                 break
 158 |                             curr_line = lines[j].strip()
 159 |                             if curr_line and not curr_line.startswith('#'):
 160 |                                 curr_indent = len(lines[j]) - len(lines[j].lstrip())
 163 |                                 if curr_indent > base_indent:
 164 |                                     nested_content = []
 165 |                                     nested_base_indent = curr_indent
 166 |                                     while j < len(lines):
 167 |                                         if j >= len(lines):
 168 |                                             break
 169 |                                         curr_line = lines[j].strip()
 170 |                                         if curr_line and not curr_line.startswith('#'):
 171 |                                             curr_indent = len(lines[j]) - len(lines[j].lstrip())
 172 |                                             if curr_indent < nested_base_indent:
 173 |                                                 break
 174 |                                             nested_content.append(lines[j][nested_base_indent:])
 175 |                                         j += 1
 178 |                                     if nested_content:
 179 |                                         nested_declarations = self.parse('\n'.join(nested_content))
 180 |                                         for decl in nested_declarations:
 181 |                                             decl.start_line += j - len(nested_content)
 182 |                                             decl.end_line += j - len(nested_content)
 183 |                                             declarations.append(decl)
 185 |                                 if curr_indent <= base_indent:
 186 |                                     end_line = j - 1
 187 |                                     break
 188 |                             j += 1
 189 |                             end_line = j - 1
 191 |                     declarations.append(Declaration(
 192 |                         kind=kind,
 193 |                         name=name,
 194 |                         start_line=i + 1,
 195 |                         end_line=end_line + 1,
 196 |                         modifiers=set(decorators),
 197 |                         docstring=docstring
 198 |                     ))
 199 |                     i = end_line + 1
 200 |                     break
 201 |             else:
 202 |                 i += 1
 204 |         return declarations
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/python_parser.py
### Functions
### Classes

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
   8 | @dataclass
   9 | class CodeSymbol:
  10 |     name: str
  11 |     kind: str
  12 |     start_line: int
  13 |     end_line: int
  14 |     modifiers: Set[str]
  15 |     parent: Optional["CodeSymbol"] = None
  16 |     children: List["CodeSymbol"] = None
  17 |     docstring: Optional[str] = None
  19 |     def __post_init__(self):
  20 |         if self.children is None:
  21 |             self.children = []
  23 | class BaseParser(ABC):
  25 |     BaseParser defines a minimal interface and partial logic for line-based scanning
  26 |     and comment extraction. Subclasses typically override _setup_patterns() and parse().
  29 |     def __init__(self):
  31 |         self.symbols: List[CodeSymbol] = []
  32 |         self.current_symbol: Optional[CodeSymbol] = None
  33 |         self.symbol_stack: List[CodeSymbol] = []
  34 |         self.block_start = "{"  # Default block start
  35 |         self.block_end = "}"    # Default block end
  36 |         self.line_comment = "//"  # Default line comment
  37 |         self.block_comment_start = "/*"  # Default block comment start
  38 |         self.block_comment_end = "*/"    # Default block comment end
  39 |         self._setup_patterns()
  41 |     @abstractmethod
  42 |     def _setup_patterns(self):
  44 |         self.patterns: Dict[str, Pattern] = {}
  45 |         self.modifiers: Set[str] = set()
  46 |         raise NotImplementedError("Subclasses must implement _setup_patterns")
  48 |     def parse(self, content: str) -> List[Tuple[str, int, int]]:
  50 |         self.symbols = []
  51 |         self.current_symbol = None
  52 |         self.symbol_stack = []
  55 |         seen_declarations = set()  # (name, start_line, kind) tuples
  57 |         lines = content.split("\n")
  58 |         in_comment = False
  59 |         comment_buffer = []
  60 |         brace_count = 0
  62 |         for i, line in enumerate(lines):
  63 |             stripped_line = line.strip()
  66 |             if self.block_comment_start in line and not in_comment:
  67 |                 in_comment = True
  68 |                 comment_start = line.index(self.block_comment_start)
  69 |                 comment_buffer.append(line[comment_start + len(self.block_comment_start):])
  70 |                 continue
  72 |             if in_comment:
  73 |                 if self.block_comment_end in line:
  74 |                     in_comment = False
  75 |                     comment_end = line.index(self.block_comment_end)
  76 |                     comment_buffer.append(line[:comment_end])
  77 |                     comment_buffer = []
  78 |                 else:
  79 |                     comment_buffer.append(line)
  80 |                 continue
  83 |             if stripped_line.startswith(self.line_comment):
  84 |                 continue
  87 |             if self.block_start is not None and self.block_end is not None:
  88 |                 brace_count += line.count(self.block_start) - line.count(self.block_end)
  91 |             for kind, pattern in self.patterns.items():
  92 |                 match = pattern.match(stripped_line)
  93 |                 if match:
  94 |                     name = match.group("n")  # Use "n" instead of "name"
  95 |                     if not name:
  96 |                         continue
  99 |                     declaration_key = (name, i, kind)
 100 |                     if declaration_key in seen_declarations:
 101 |                         continue
 102 |                     seen_declarations.add(declaration_key)
 105 |                     end_line = i
 106 |                     if kind in ("class", "function", "method", "interface", "struct", "enum"):
 107 |                         end_line = self._find_block_end(lines, i)
 110 |                     docstring = None
 111 |                     if end_line > i:
 112 |                         docstring = self.extract_docstring(lines, i, end_line)
 115 |                     symbol = CodeSymbol(
 116 |                         name=name,
 117 |                         kind=kind,
 118 |                         start_line=i,
 119 |                         end_line=end_line,
 120 |                         modifiers=set(),
 121 |                         docstring=docstring
 122 |                     )
 125 |                     if self.current_symbol:
 126 |                         symbol.parent = self.current_symbol
 127 |                         self.current_symbol.children.append(symbol)
 128 |                     else:
 129 |                         self.symbols.append(symbol)
 132 |                     if kind in ("class", "interface", "struct"):
 133 |                         self.symbol_stack.append(self.current_symbol)
 134 |                         self.current_symbol = symbol
 137 |             if self.current_symbol and brace_count == 0:
 138 |                 self.current_symbol = self.symbol_stack.pop() if self.symbol_stack else None
 141 |         declarations = []
 142 |         for symbol in self.symbols:
 143 |             declarations.extend(self._flatten_symbol(symbol))
 144 |         return declarations
 146 |     def _flatten_symbol(self, symbol: CodeSymbol) -> List[Tuple[str, int, int]]:
 148 |         declarations = [(symbol.name, symbol.start_line, symbol.end_line)]
 149 |         for child in symbol.children:
 150 |             declarations.extend(self._flatten_symbol(child))
 151 |         return declarations
 153 |     def _find_block_end(self, lines: List[str], start: int) -> int:
 155 |         if self.block_start is None or self.block_end is None:
 156 |             return start
 158 |         line = lines[start]
 159 |         if self.block_start not in line:
 160 |             return start
 162 |         brace_count = line.count(self.block_start) - line.count(self.block_end)
 163 |         if brace_count <= 0:
 164 |             return start
 166 |         for i in range(start + 1, len(lines)):
 167 |             line = lines[i].strip()
 168 |             if line.startswith(self.line_comment):
 169 |                 continue
 170 |             brace_count += line.count(self.block_start) - line.count(self.block_end)
 171 |             if brace_count <= 0:
 172 |                 return i
 174 |         return len(lines) - 1
 176 |     def _create_pattern(self, base_pattern: str, modifiers: Optional[List[str]] = None) -> Pattern:
 177 |         if modifiers:
 178 |             modifier_pattern = f"(?:{'|'.join(modifiers)})\\s+"
 179 |             return re.compile(f"^\\s*(?:{modifier_pattern})?{base_pattern}")
 180 |         return re.compile(f"^\\s*{base_pattern}")
 182 |     @staticmethod
 183 |     def extract_docstring(lines: List[str], start: int, end: int) -> Optional[str]:
 185 |         Example extraction for docstring-like text between triple quotes or similar.
 186 |         Subclasses can override or use as needed.
 188 |         for i in range(start, min(end + 1, len(lines))):
 189 |             line = lines[i].strip()
 190 |             if line.startswith('"""') or line.startswith("'''"):
 191 |                 doc_lines = []
 192 |                 quote = line[:3]
 193 |                 if line.endswith(quote) and len(line) > 3:
 194 |                     return line[3:-3].strip()
 195 |                 doc_lines.append(line[3:])
 196 |                 for j in range(i + 1, end + 1):
 197 |                     line2 = lines[j].strip()
 198 |                     if line2.endswith(quote):
 199 |                         doc_lines.append(line2[:-3])
 200 |                         return "\n".join(doc_lines).strip()
 201 |                     doc_lines.append(line2)
 202 |         return None
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/base_parser.py
### Functions
### Classes

---
### File: ./codeconcat/parser/language_parsers/java_parser.py
#### Summary
```
File: java_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional, Set
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_java(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = JavaParser()
  10 |     declarations = parser.parse(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="java",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  18 | class JavaParser(BaseParser):
  19 |     def __init__(self):
  20 |         super().__init__()
  21 |         self._setup_patterns()
  23 |     def _setup_patterns(self):
  25 |         self.patterns = {}
  28 |         self.block_start = "{"
  29 |         self.block_end = "}"
  30 |         self.line_comment = "//"
  31 |         self.block_comment_start = "/*"
  32 |         self.block_comment_end = "*/"
  35 |         class_pattern = r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+)*class\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)"
  36 |         self.patterns["class"] = re.compile(class_pattern)
  39 |         interface_pattern = r"^\s*(?:public\s+|private\s+|protected\s+)*interface\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)"
  40 |         self.patterns["interface"] = re.compile(interface_pattern)
  43 |         method_pattern = r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+|abstract\s+)*(?:[a-zA-Z_][a-zA-Z0-9_<>[\],\s]*\s+)?(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)\s*\("
  44 |         self.patterns["method"] = re.compile(method_pattern)
  47 |         field_pattern = r"^\s*(?:public\s+|private\s+|protected\s+|static\s+|final\s+)*(?:[a-zA-Z_][a-zA-Z0-9_<>[\],\s]*\s+)(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)\s*[=;]"
  48 |         self.patterns["field"] = re.compile(field_pattern)
  50 |         self.modifiers = {"public", "private", "protected", "static", "final", "abstract"}
  52 |     def parse(self, content: str) -> List[Declaration]:
  54 |         declarations = []
  55 |         lines = content.split('\n')
  56 |         in_comment = False
  58 |         i = 0
  59 |         while i < len(lines):
  60 |             line = lines[i].strip()
  63 |             if not line or line.startswith('//'):
  64 |                 i += 1
  65 |                 continue
  68 |             if "/*" in line and not in_comment:
  69 |                 in_comment = True
  70 |                 i += 1
  71 |                 continue
  72 |             elif in_comment:
  73 |                 if "*/" in line:
  74 |                     in_comment = False
  75 |                 i += 1
  76 |                 continue
  79 |             modifiers = set()
  80 |             words = line.split()
  81 |             j = 0
  82 |             while j < len(words) and words[j] in self.modifiers:
  83 |                 modifiers.add(words[j])
  84 |                 j += 1
  87 |             for kind, pattern in self.patterns.items():
  88 |                 match = pattern.match(line)
  89 |                 if match:
  90 |                     name = match.group("n")
  91 |                     if not name:
  92 |                         continue
  95 |                     end_line = i
  96 |                     if kind in ("class", "interface", "enum", "method"):
  97 |                         brace_count = 0
  98 |                         found_opening = False
 101 |                         j = i
 102 |                         while j < len(lines):
 103 |                             curr_line = lines[j].strip()
 105 |                             if "{" in curr_line:
 106 |                                 found_opening = True
 107 |                                 brace_count += curr_line.count("{")
 108 |                             if "}" in curr_line:
 109 |                                 brace_count -= curr_line.count("}")
 111 |                             if found_opening and brace_count == 0:
 112 |                                 end_line = j
 113 |                                 break
 114 |                             j += 1
 117 |                         docstring = self.extract_docstring(lines, i, end_line)
 120 |                         declarations.append(Declaration(
 121 |                             kind=kind,
 122 |                             name=name,
 123 |                             start_line=i + 1,
 124 |                             end_line=end_line + 1,
 125 |                             modifiers=modifiers,
 126 |                             docstring=docstring or ""
 127 |                         ))
 130 |                         if kind in ("class", "interface", "enum") and end_line > i:
 131 |                             nested_content = []
 132 |                             for k in range(i+1, end_line):
 133 |                                 nested_line = lines[k].strip()
 134 |                                 if nested_line and not nested_line.startswith('//'):
 135 |                                     nested_content.append((k, lines[k]))
 137 |                             if nested_content:
 138 |                                 for k, nested_line in nested_content:
 140 |                                     for nested_kind, nested_pattern in self.patterns.items():
 141 |                                         if nested_kind in ("class", "interface", "enum"):
 142 |                                             continue  # Skip nested class declarations for now
 143 |                                         nested_match = nested_pattern.match(nested_line.strip())
 144 |                                         if nested_match:
 145 |                                             nested_name = nested_match.group("n")
 146 |                                             if nested_name:
 148 |                                                 nested_modifiers = set()
 149 |                                                 nested_words = nested_line.strip().split()
 150 |                                                 m = 0
 151 |                                                 while m < len(nested_words) and nested_words[m] in self.modifiers:
 152 |                                                     nested_modifiers.add(nested_words[m])
 153 |                                                     m += 1
 156 |                                                 nested_end_line = k
 157 |                                                 if "{" in nested_line:
 158 |                                                     nested_brace_count = 1
 159 |                                                     n = k + 1
 160 |                                                     while n < len(lines):
 161 |                                                         curr_nested_line = lines[n].strip()
 162 |                                                         if "{" in curr_nested_line:
 163 |                                                             nested_brace_count += curr_nested_line.count("{")
 164 |                                                         if "}" in curr_nested_line:
 165 |                                                             nested_brace_count -= curr_nested_line.count("}")
 166 |                                                         if nested_brace_count == 0:
 167 |                                                             nested_end_line = n
 168 |                                                             break
 169 |                                                         n += 1
 171 |                                                 declarations.append(Declaration(
 172 |                                                     kind=nested_kind,
 173 |                                                     name=nested_name,
 174 |                                                     start_line=k + 1,
 175 |                                                     end_line=nested_end_line + 1,
 176 |                                                     modifiers=nested_modifiers,
 177 |                                                     docstring=""
 178 |                                                 ))
 179 |                         i = end_line + 1
 180 |                         break
 181 |                     else:
 183 |                         declarations.append(Declaration(
 184 |                             kind=kind,
 185 |                             name=name,
 186 |                             start_line=i + 1,
 187 |                             end_line=i + 1,
 188 |                             modifiers=modifiers,
 189 |                             docstring=""
 190 |                         ))
 191 |                         i += 1
 192 |                         break
 193 |             else:
 194 |                 i += 1
 197 |         filtered_declarations = []
 198 |         top_level_declarations = [d for d in declarations if d.kind in ("class", "interface", "enum")]
 200 |         for top_level in top_level_declarations:
 201 |             filtered_declarations.append(top_level)
 204 |             start_line = top_level.start_line
 205 |             end_line = top_level.end_line
 206 |             for d in declarations:
 207 |                 if d.start_line > start_line and d.end_line < end_line:
 208 |                     filtered_declarations.append(d)
 210 |         return filtered_declarations
 212 |     def extract_docstring(self, lines, start, end):
 214 |         docstring = ""
 215 |         for line in lines[start+1:end]:
 216 |             if line.strip().startswith("//"):
 217 |                 docstring += line.strip().replace("//", "", 1).strip() + "\n"
 218 |         return docstring.strip()
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/java_parser.py
### Functions
### Classes

---
### File: ./codeconcat/parser/language_parsers/cpp_parser.py
#### Summary
```
File: cpp_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_cpp_code(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = CppParser()
  10 |     declarations = parser.parse(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="cpp",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  19 | def parse_cpp(file_path: str, content: str) -> Optional[ParsedFileData]:
  20 |     return parse_cpp_code(file_path, content)
  22 | class CppParser(BaseParser):
  23 |     def __init__(self):
  24 |         super().__init__()
  25 |         self._setup_patterns()
  27 |     def _setup_patterns(self):
  29 |         Define the main regex patterns for classes, structs, enums, functions,
  30 |         namespaces, typedefs, usings, and forward declarations.
  33 |         identifier = r"[a-zA-Z_]\w*"
  34 |         qualified_id = rf"(?:{identifier}::)*{identifier}"
  37 |         self.class_pattern = re.compile(
  38 |             r"""
  39 |             ^[^\#/]*?                    # skip if line starts with # or / (comment), handled later
  40 |             (?:template\s*<[^>]*>\s*)?   # optional template
  41 |             (?:class|struct)\s+
  42 |             (?P<name>[a-zA-Z_]\w*)       # capture the class/struct name
  43 |             (?:\s*:[^{]*)?              # optional inheritance, up to but not including brace
  44 |             \s*{                       # opening brace
  46 |             re.VERBOSE
  47 |         )
  50 |         self.forward_decl_pattern = re.compile(
  51 |             r"""
  52 |             ^[^\#/]*?
  53 |             (?:class|struct|union|enum)\s+
  54 |             (?P<name>[a-zA-Z_]\w*)\s*;
  56 |             re.VERBOSE
  57 |         )
  60 |         self.enum_pattern = re.compile(
  61 |             r"""
  62 |             ^[^\#/]*?
  63 |             enum(?:\s+class)?\s+
  64 |             (?P<name>[a-zA-Z_]\w*)
  65 |             (?:\s*:\s+[^\s{]+)?         # optional base type
  66 |             \s*{                       # opening brace
  68 |             re.VERBOSE
  69 |         )
  75 |         self.function_pattern = re.compile(
  76 |             r"""
  77 |             ^[^\#/]*?                    # skip if line starts with # or / (comment), handled later
  78 |             (?:template\s*<[^>]*>\s*)?   # optional template
  79 |             (?:virtual|static|inline|constexpr|explicit|friend\s+)?  # optional specifiers
  80 |             (?:""" + qualified_id + r"""(?:<[^>]+>)?[&*\s]+)*        # optional return type with nested templates
  81 |             (?P<name>                                      # function name capture
  82 |                 ~?[a-zA-Z_]\w*                             # normal name or destructor ~Foo
  83 |                 |operator\s*(?:[^\s\(]+|\(.*?\))          # operator overload
  84 |             )
  85 |             \s*\([^\){;]*\)                                # function params up to ) but not including brace or semicolon
  86 |             (?:\s*const)?                                   # optional const
  87 |             (?:\s*noexcept)?                                # optional noexcept
  88 |             (?:\s*=\s*(?:default|delete|0))?                # optional = default/delete/pure virtual
  89 |             \s*(?:{|;)                                    # must end with { or ;
  91 |             re.VERBOSE
  92 |         )
  95 |         self.namespace_pattern = re.compile(
  96 |             r"""
  97 |             ^[^\#/]*?
  98 |             (?:inline\s+)?         # optional inline
  99 |             namespace\s+
 100 |             (?P<name>[a-zA-Z_]\w*) # namespace name
 101 |             \s*{                  # opening brace
 103 |             re.VERBOSE
 104 |         )
 107 |         self.typedef_pattern = re.compile(
 108 |             r"""
 109 |             ^[^\#/]*?
 110 |             typedef\s+
 111 |             (?:[^;]+?                   # capture everything up to the identifier
 112 |               \s+                       # must have whitespace before identifier
 113 |               (?:\(\s*\*\s*)?          # optional function pointer
 114 |             )
 115 |             (?P<name>[a-zA-Z_]\w*)     # identifier
 116 |             (?:\s*\)[^;]*)?            # rest of function pointer if present
 117 |             \s*;                        # end with semicolon
 119 |             re.VERBOSE
 120 |         )
 123 |         self.using_pattern = re.compile(
 124 |             r"""
 125 |             ^[^\#/]*?
 126 |             using\s+
 127 |             (?P<name>[a-zA-Z_]\w*)
 128 |             \s*=\s*[^;]+;
 130 |             re.VERBOSE
 131 |         )
 133 |         self.patterns = {
 134 |             "class":      self.class_pattern,
 135 |             "forward_decl": self.forward_decl_pattern,
 136 |             "enum":       self.enum_pattern,
 137 |             "function":   self.function_pattern,
 138 |             "namespace":  self.namespace_pattern,
 139 |             "typedef":    self.typedef_pattern,
 140 |             "using":      self.using_pattern,
 141 |         }
 144 |         self.block_start = "{"
 145 |         self.block_end = "}"
 146 |         self.line_comment = "//"
 147 |         self.block_comment_start = "/*"
 148 |         self.block_comment_end = "*/"
 150 |     def parse(self, content: str) -> List[Declaration]:
 152 |         Main parse method:
 153 |         1) Remove block comments.
 154 |         2) Split by lines.
 155 |         3) For each line, strip preprocessor lines (#...), line comments, etc.
 156 |         4) Match patterns in a loop and accumulate symbols.
 157 |         5) For anything with a block, find the end of the block with _find_block_end.
 158 |         6) Convert collected CodeSymbol objects -> Declaration objects.
 161 |         content_no_block = self._remove_block_comments(content)
 162 |         lines = content_no_block.split("\n")
 164 |         symbols: List[CodeSymbol] = []
 165 |         i = 0
 166 |         line_count = len(lines)
 168 |         while i < line_count:
 169 |             raw_line = lines[i]
 170 |             line_stripped = raw_line.strip()
 173 |             if (not line_stripped
 174 |                 or line_stripped.startswith("//")
 175 |                 or line_stripped.startswith("#")):
 176 |                 i += 1
 177 |                 continue
 180 |             comment_pos = raw_line.find("//")
 181 |             if comment_pos >= 0:
 182 |                 raw_line = raw_line[:comment_pos]
 184 |             raw_line_stripped = raw_line.strip()
 185 |             if not raw_line_stripped:
 186 |                 i += 1
 187 |                 continue
 189 |             matched_something = False
 192 |             for kind, pattern in self.patterns.items():
 193 |                 match = pattern.match(raw_line_stripped)
 194 |                 if match:
 195 |                     name = match.group("name")
 196 |                     block_end = i
 198 |                     if kind in ["class", "enum", "namespace", "function"]:
 200 |                         if "{" in raw_line_stripped:
 201 |                             block_end = self._find_block_end(lines, i)
 202 |                         else:
 204 |                             block_end = i
 207 |                     symbol = CodeSymbol(
 208 |                         kind=kind,
 209 |                         name=name,
 210 |                         start_line=i,
 211 |                         end_line=block_end,
 212 |                         modifiers=set(),
 213 |                     )
 214 |                     symbols.append(symbol)
 215 |                     i = block_end + 1
 216 |                     matched_something = True
 217 |                     break
 219 |             if not matched_something:
 220 |                 i += 1
 223 |         declarations: List[Declaration] = []
 224 |         for sym in symbols:
 225 |             decl = Declaration(
 226 |                 kind=sym.kind,
 227 |                 name=sym.name,
 228 |                 start_line=sym.start_line + 1,
 229 |                 end_line=sym.end_line + 1,
 230 |                 modifiers=sym.modifiers,
 231 |             )
 232 |             declarations.append(decl)
 234 |         return declarations
 236 |     def _remove_block_comments(self, text: str) -> str:
 238 |         Remove all /* ... */ comments (including multi-line).
 239 |         Simple approach: repeatedly find the first /* and the next */, remove them,
 240 |         and continue until none remain.
 242 |         pattern = re.compile(r"/\*.*?\*/", re.DOTALL)
 243 |         return re.sub(pattern, "", text)
 245 |     def _find_block_end(self, lines: List[str], start: int) -> int:
 247 |         Find the end of a block that starts at 'start' if there's an unmatched '{'.
 248 |         We'll count braces until balanced or until we run out of lines.
 249 |         We'll skip lines that start with '#' as they are preprocessor directives (not code).
 252 |         line = lines[start]
 253 |         brace_count = 0
 256 |         comment_pos = line.find("//")
 257 |         if comment_pos >= 0:
 258 |             line = line[:comment_pos]
 260 |         brace_count += line.count("{") - line.count("}")
 263 |         if brace_count <= 0:
 264 |             return start
 266 |         n = len(lines)
 267 |         for i in range(start + 1, n):
 268 |             l = lines[i]
 271 |             if l.strip().startswith("#"):
 272 |                 continue
 275 |             comment_pos = l.find("//")
 276 |             if comment_pos >= 0:
 277 |                 l = l[:comment_pos]
 279 |             brace_count += l.count("{") - l.count("}")
 280 |             if brace_count <= 0:
 281 |                 return i
 283 |         return n - 1
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/cpp_parser.py
### Functions
### Classes

---
### File: ./codeconcat/parser/language_parsers/r_parser.py
#### Summary
```
File: r_parser.py
Language: python
```

```python
   5 | import re
   6 | from typing import List, Optional, Set, Dict
   7 | from codeconcat.base_types import Declaration, ParsedFileData
   8 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
  10 | def parse_r(file_path: str, content: str) -> Optional[ParsedFileData]:
  11 |     parser = RParser()
  12 |     declarations = parser.parse(content)
  13 |     return ParsedFileData(
  14 |         file_path=file_path,
  15 |         language="r",
  16 |         content=content,
  17 |         declarations=declarations
  18 |     )
  20 | class RParser(BaseParser):
  22 |     A regex-based R parser that attempts to capture:
  23 |       - Functions (including various assignment operators and nested definitions)
  24 |       - Classes (S3, S4, R6, Reference)
  25 |       - Methods (S3, S4, R6, $-notation, dot-notation)
  26 |       - Package imports (library/require)
  27 |       - Roxygen2 modifiers
  28 |     Then it scans block contents recursively for nested definitions.
  31 |     def __init__(self):
  32 |         super().__init__()
  33 |         self._setup_patterns()
  35 |     def _setup_patterns(self):
  37 |         Compile all regex patterns needed.
  38 |         We'll allow for all assignment operators: <-, <<-, =, ->, ->>, :=
  39 |         We'll handle S3, S4, R6, reference classes, plus roxygen modifiers.
  44 |         qualified_name = r"[a-zA-Z_]\w*(?:[.$][a-zA-Z_]\w*)*"
  48 |         self.method_pattern = re.compile(
  49 |             rf"""
  50 |             ^\s*
  51 |             (?:
  53 |                 (?P<dot_name>{qualified_name}\.[a-zA-Z_]\w*)
  54 |                 \s*(?:<<?-|=|->|->>|:=)
  55 |                 \s*function\s*\(
  56 |                 |
  58 |                 (?P<dollar_obj>{qualified_name})\$(?P<dollar_method>[a-zA-Z_]\w*)
  59 |                 \s*(?:<<?-|=|->|->>|:=)
  60 |                 \s*function\s*\(
  61 |                 |
  63 |                 setMethod\(\s*["'](?P<s4_name>[^"']+)["']
  64 |             )
  66 |             re.VERBOSE,
  67 |         )
  70 |         self.function_pattern = re.compile(
  71 |             rf"""
  72 |             ^\s*
  73 |             (?:
  78 |                (?P<fname1>{qualified_name})\s*(?:<<?-|=|:=)\s*function\s*\(
  79 |                |
  82 |                function\s*\([^)]*\)\s*(?:->|->>)\s*(?P<fname2>{qualified_name})
  83 |             )
  85 |             re.VERBOSE,
  86 |         )
  90 |         self.class_pattern = re.compile(
  91 |             rf"""
  92 |             ^\s*
  93 |             (?:
  97 |                 (?:setClass|setRefClass|R6Class)\(\s*["'](?P<cname1>[a-zA-Z_]\w*)["']
  98 |                 |
 100 |                 (?P<cname2>{qualified_name})\s*(?:<<?-|=|:=)\s*(?:setRefClass|R6Class)\(\s*["'](?P<cname3>[a-zA-Z_]\w*)["']
 101 |             )
 103 |             re.VERBOSE,
 104 |         )
 107 |         self.package_pattern = re.compile(
 108 |             rf"""
 109 |             ^\s*
 110 |             (?:library|require)\s*\(\s*
 111 |             (?:
 112 |                 ["'](?P<pkg1>[^"']+)["']
 113 |                 |
 114 |                 (?P<pkg2>[a-zA-Z_]\w*(?:\.[a-zA-Z_]\w*)*)
 115 |             )
 117 |             re.VERBOSE,
 118 |         )
 121 |         self.block_start = "{"
 122 |         self.block_end = "}"
 123 |         self.line_comment = "#"
 124 |         self.block_comment_start = "#["
 125 |         self.block_comment_end = "]#"
 127 |     def parse(self, content: str) -> List[Declaration]:
 129 |         Main parse entry:
 130 |           1) Merge multiline function/class assignments
 131 |           2) Parse top-level lines
 133 |         raw_lines = content.split("\n")
 135 |         merged_lines = self._merge_multiline_assignments(raw_lines, also_for_classes=True)
 137 |         symbols = self._parse_block(merged_lines, 0, len(merged_lines))
 140 |         declarations = []
 141 |         seen = set()
 142 |         for sym in symbols:
 143 |             key = (sym.kind, sym.name, sym.start_line, sym.end_line)
 144 |             if key not in seen:
 145 |                 seen.add(key)
 147 |                 declarations.append(
 148 |                     Declaration(
 149 |                         kind=sym.kind,
 150 |                         name=sym.name,
 151 |                         start_line=sym.start_line + 1,
 152 |                         end_line=sym.end_line + 1,
 153 |                         modifiers=sym.modifiers,
 154 |                     )
 155 |                 )
 156 |         return declarations
 158 |     def _parse_block(self, lines: List[str], start_idx: int, end_idx: int) -> List[CodeSymbol]:
 160 |         Parse lines from start_idx to end_idx (exclusive),
 161 |         capturing functions/methods/classes/packages, plus nested definitions.
 162 |         Return a list of CodeSymbol objects (with 0-based line indices).
 163 |         Recursively parse the contents of each function/class block to find nested items.
 165 |         symbols: List[CodeSymbol] = []
 166 |         i = start_idx
 169 |         current_modifiers = set()
 170 |         in_roxygen = False
 172 |         while i < end_idx:
 173 |             line = lines[i]
 174 |             stripped = line.strip()
 177 |             if stripped.startswith("#'"):
 178 |                 if not in_roxygen:
 179 |                     current_modifiers.clear()
 180 |                 in_roxygen = True
 181 |                 if "@" in stripped:
 182 |                     after_at = stripped.split("@", 1)[1].strip()
 183 |                     first_token = after_at.split()[0] if after_at else ""
 184 |                     if first_token:
 185 |                         current_modifiers.add(first_token)
 186 |                 i += 1
 187 |                 continue
 188 |             else:
 189 |                 in_roxygen = False
 192 |             if not stripped or stripped.startswith("#"):
 193 |                 i += 1
 194 |                 continue
 197 |             mm = self.method_pattern.match(line)
 198 |             if mm:
 199 |                 method_name = None
 200 |                 if mm.group("dot_name"):
 201 |                     method_name = mm.group("dot_name")
 202 |                 elif mm.group("dollar_obj") and mm.group("dollar_method"):
 203 |                     method_name = f"{mm.group('dollar_obj')}${mm.group('dollar_method')}"
 204 |                 else:
 206 |                     method_name = mm.group("s4_name")
 208 |                 start_blk, end_blk = self._find_function_block(lines, i)
 210 |                 sym = CodeSymbol(
 211 |                     name=method_name,
 212 |                     kind="method",
 213 |                     start_line=start_blk,
 214 |                     end_line=end_blk,
 215 |                     modifiers=current_modifiers.copy(),
 216 |                 )
 217 |                 symbols.append(sym)
 220 |                 nested_lines = lines[start_blk+1 : end_blk+1]
 221 |                 if end_blk >= start_blk:
 222 |                     nested_syms = self._parse_block(nested_lines, 0, len(nested_lines))
 223 |                     symbols.extend(nested_syms)
 225 |                 current_modifiers.clear()
 226 |                 i = end_blk + 1
 227 |                 continue
 230 |             fm = self.function_pattern.match(line)
 231 |             if fm:
 232 |                 fname = fm.group("fname1") or fm.group("fname2")
 233 |                 start_blk, end_blk = self._find_function_block(lines, i)
 235 |                 sym = CodeSymbol(
 236 |                     name=fname,
 237 |                     kind="function",
 238 |                     start_line=start_blk,
 239 |                     end_line=end_blk,
 240 |                     modifiers=current_modifiers.copy(),
 241 |                 )
 242 |                 symbols.append(sym)
 245 |                 if self._function_defines_s3(lines, start_blk, end_blk, fname):
 246 |                     sym.kind = "class"
 249 |                 nested_lines = lines[start_blk+1 : end_blk+1]
 250 |                 if end_blk >= start_blk:
 251 |                     nested_syms = self._parse_block(nested_lines, 0, len(nested_lines))
 252 |                     symbols.extend(nested_syms)
 254 |                 current_modifiers.clear()
 255 |                 i = end_blk + 1
 256 |                 continue
 259 |             cm = self.class_pattern.match(line)
 260 |             if cm:
 261 |                 cname = cm.group("cname1") or cm.group("cname2") or cm.group("cname3") or ""
 262 |                 cls_start, cls_end = self._find_matching_parenthesis_block(lines, i)
 264 |                 csym = CodeSymbol(
 265 |                     name=cname,
 266 |                     kind="class",
 267 |                     start_line=i,
 268 |                     end_line=cls_end,
 269 |                     modifiers=current_modifiers.copy(),
 270 |                 )
 271 |                 symbols.append(csym)
 274 |                 lowered_line = line.lower()
 275 |                 if "r6class" in lowered_line:
 276 |                     methods = self._parse_r6_methods(lines, i, cls_end, class_name=cname)
 277 |                     symbols.extend(methods)
 278 |                 elif "setrefclass" in lowered_line:
 279 |                     methods = self._parse_refclass_methods(lines, i, cls_end, class_name=cname)
 280 |                     symbols.extend(methods)
 283 |                 nested_lines = lines[i+1 : cls_end+1]
 284 |                 nested_syms = self._parse_block(nested_lines, 0, len(nested_lines))
 285 |                 symbols.extend(nested_syms)
 287 |                 current_modifiers.clear()
 288 |                 i = cls_end + 1
 289 |                 continue
 292 |             pm = self.package_pattern.match(line)
 293 |             if pm:
 294 |                 pkg_name = pm.group("pkg1") or pm.group("pkg2")
 295 |                 psym = CodeSymbol(
 296 |                     name=pkg_name,
 297 |                     kind="package",
 298 |                     start_line=i,
 299 |                     end_line=i,
 300 |                     modifiers=current_modifiers.copy(),
 301 |                 )
 302 |                 symbols.append(psym)
 303 |                 current_modifiers.clear()
 304 |                 i += 1
 305 |                 continue
 308 |             current_modifiers.clear()
 309 |             i += 1
 311 |         return symbols
 313 |     def _merge_multiline_assignments(self, raw_lines: List[str], also_for_classes: bool=False) -> List[str]:
 315 |         Fix for cases like:
 316 |           complex_func <- # comment
 317 |              function(x) { ... }
 318 |         We'll merge such lines so the regex sees them on a single line.
 320 |         If also_for_classes=True, we also merge if the line ends with an assignment operator
 321 |         and the next line starts with R6Class(, setRefClass(, or setClass(.
 323 |         merged = []
 324 |         i = 0
 325 |         n = len(raw_lines)
 327 |         while i < n:
 328 |             line = raw_lines[i]
 329 |             strip_line = line.strip()
 331 |             if re.search(r"(?:<<?-|=|->|->>|:=)\s*(?:#.*)?$", strip_line):
 332 |                 j = i + 1
 333 |                 comment_lines = []
 335 |                 while j < n and (not raw_lines[j].strip() or raw_lines[j].strip().startswith("#")):
 336 |                     comment_lines.append(raw_lines[j])
 337 |                     j += 1
 338 |                 if j < n:
 339 |                     next_strip = raw_lines[j].lstrip()
 341 |                     if next_strip.startswith("function"):
 343 |                         base_line = re.sub(r"#.*$", "", line).rstrip()
 344 |                         new_line = base_line + " " + " ".join(l.strip() for l in comment_lines) + " " + raw_lines[j].lstrip()
 345 |                         merged.append(new_line)
 346 |                         i = j + 1
 347 |                         continue
 349 |                     if also_for_classes:
 350 |                         if any(x in next_strip for x in ["R6Class(", "setRefClass(", "setClass("]):
 352 |                             base_line = re.sub(r"#.*$", "", line).rstrip()
 353 |                             new_line = base_line + " " + " ".join(l.strip() for l in comment_lines) + " " + raw_lines[j].lstrip()
 354 |                             merged.append(new_line)
 355 |                             i = j + 1
 356 |                             continue
 357 |             merged.append(line)
 358 |             i += 1
 359 |         return merged
 361 |     def _find_function_block(self, lines: List[str], start_idx: int) -> (int, int):
 363 |         Return (start_line, end_line) for a function (or method) definition starting at start_idx.
 364 |         We'll count braces to find the end of the function body. If no brace on that line,
 365 |         treat it as a single-line function definition (like "func <- function(x) x").
 367 |         line = lines[start_idx]
 369 |         if '{' not in line:
 370 |             return start_idx, start_idx
 372 |         brace_count = line.count("{") - line.count("}")
 373 |         end_idx = start_idx
 374 |         j = start_idx
 375 |         while j < len(lines):
 376 |             if j > start_idx:
 377 |                 brace_count += lines[j].count("{") - lines[j].count("}")
 378 |             if brace_count <= 0 and j > start_idx:
 379 |                 end_idx = j
 380 |                 break
 381 |             j += 1
 382 |         if j == len(lines):
 383 |             end_idx = len(lines) - 1
 384 |         return start_idx, end_idx
 386 |     def _function_defines_s3(self, lines: List[str], start_idx: int, end_idx: int, fname: str) -> bool:
 388 |         Check if between start_idx and end_idx there's 'class(...) <- "fname"'
 389 |         or something that sets 'class(...)' to the same name, indicating an S3 constructor.
 391 |         pattern = re.compile(
 392 |             rf'class\s*\(\s*[^\)]*\)\s*(?:<<?-|=)\s*["\']{re.escape(fname)}["\']'
 393 |         )
 394 |         for idx in range(start_idx, min(end_idx+1, len(lines))):
 395 |             if pattern.search(lines[idx]):
 396 |                 return True
 397 |         return False
 399 |     def _find_matching_parenthesis_block(self, lines: List[str], start_idx: int) -> (int, int):
 401 |         For code like MyClass <- R6Class("MyClass", public=list(...)),
 402 |         we only track parentheses '(' and ')' -- not braces -- so we don't get confused by
 403 |         function bodies inside the class definition. Return (start_line, end_line).
 405 |         line = lines[start_idx]
 406 |         open_parens = line.count("(")
 407 |         close_parens = line.count(")")
 409 |         paren_diff = open_parens - close_parens
 412 |         if paren_diff <= 0:
 413 |             return start_idx, start_idx
 415 |         j = start_idx
 416 |         while j < len(lines) and paren_diff > 0:
 417 |             j += 1
 418 |             if j < len(lines):
 419 |                 open_parens = lines[j].count("(")
 420 |                 close_parens = lines[j].count(")")
 421 |                 paren_diff += open_parens - close_parens
 423 |         return (start_idx, min(j, len(lines) - 1))
 425 |     def _parse_r6_methods(self, lines: List[str], start_idx: int, end_idx: int, class_name: str) -> List[CodeSymbol]:
 427 |         Inside R6Class("class_name", public=list(...), private=list(...)), parse:
 428 |            methodName = function(...) { ... }
 429 |         We'll produce code symbols with name: "class_name.methodName".
 430 |         Ignore fields like 'value = 0'.
 432 |         methods = []
 433 |         block = lines[start_idx:end_idx+1]
 434 |         combined = "\n".join(block)
 437 |         method_pattern = re.compile(
 438 |             r'([a-zA-Z_]\w*)\s*=\s*function\s*\([^{]*\)\s*{',
 439 |             re.MULTILINE
 440 |         )
 443 |         for match in method_pattern.finditer(combined):
 444 |             method_name = match.group(1)
 445 |             if method_name not in ["fields", "methods"]:  # Exclude these special names
 446 |                 full_name = f"{class_name}.{method_name}"
 447 |                 start_line = start_idx + combined[:match.start()].count("\n")
 448 |                 end_line = start_idx + combined[:match.end()].count("\n")
 449 |                 methods.append(
 450 |                     CodeSymbol(
 451 |                         name=full_name,
 452 |                         kind="method",
 453 |                         start_line=start_line,
 454 |                         end_line=end_line,
 455 |                         modifiers=set(),
 456 |                     )
 457 |                 )
 458 |         return methods
 460 |     def _parse_refclass_methods(self, lines: List[str], start_idx: int, end_idx: int, class_name: str) -> List[CodeSymbol]:
 462 |         For setRefClass("Employee", fields=list(...), methods=list(...)), parse methodName = function(...).
 463 |         We'll produce "Employee.methodName".
 465 |         methods = []
 466 |         block = lines[start_idx:end_idx+1]
 467 |         combined = "\n".join(block)
 470 |         method_pattern = re.compile(
 471 |             r'([a-zA-Z_]\w*)\s*=\s*function\s*\([^{]*\)\s*{',
 472 |             re.MULTILINE
 473 |         )
 476 |         for match in method_pattern.finditer(combined):
 477 |             method_name = match.group(1)
 478 |             if method_name not in ["fields", "methods"]:  # Exclude these special names
 479 |                 full_name = f"{class_name}.{method_name}"
 480 |                 start_line = start_idx + combined[:match.start()].count("\n")
 481 |                 end_line = start_idx + combined[:match.end()].count("\n")
 482 |                 methods.append(
 483 |                     CodeSymbol(
 484 |                         name=full_name,
 485 |                         kind="method",
 486 |                         start_line=start_line,
 487 |                         end_line=end_line,
 488 |                         modifiers=set(),
 489 |                     )
 490 |                 )
 491 |         return methods
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/r_parser.py
### Functions
### Classes

---
### File: ./codeconcat/parser/language_parsers/go_parser.py
#### Summary
```
File: go_parser.py
Language: python
```

```python
   3 | import re
   4 | from typing import List, Optional
   5 | from codeconcat.base_types import Declaration, ParsedFileData
   6 | from codeconcat.parser.language_parsers.base_parser import BaseParser, CodeSymbol
   8 | def parse_go(file_path: str, content: str) -> Optional[ParsedFileData]:
   9 |     parser = GoParser()
  10 |     declarations = parser.parse_file(content)
  11 |     return ParsedFileData(
  12 |         file_path=file_path,
  13 |         language="go",
  14 |         content=content,
  15 |         declarations=declarations
  16 |     )
  18 | class GoParser(BaseParser):
  19 |     def __init__(self):
  20 |         super().__init__()
  21 |         self._setup_patterns()
  23 |     def _setup_patterns(self):
  25 |         self.patterns = {}
  28 |         self.block_start = "{"
  29 |         self.block_end = "}"
  30 |         self.line_comment = "//"
  31 |         self.block_comment_start = "/*"
  32 |         self.block_comment_end = "*/"
  35 |         func_pattern = r"^\s*func\s+(?:\([^)]+\)\s+)?(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)\s*\("
  36 |         self.patterns["function"] = re.compile(func_pattern)
  39 |         interface_pattern = r"^\s*type\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)\s+interface\s*"
  40 |         self.patterns["interface"] = re.compile(interface_pattern)
  43 |         struct_pattern = r"^\s*type\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)\s+struct\s*"
  44 |         self.patterns["struct"] = re.compile(struct_pattern)
  47 |         const_pattern = r"^\s*(?:const\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)|const\s+\(\s*(?P<n2>[a-zA-Z_][a-zA-Z0-9_]*))"
  48 |         self.patterns["const"] = re.compile(const_pattern)
  51 |         var_pattern = r"^\s*(?:var\s+(?P<n>[a-zA-Z_][a-zA-Z0-9_]*)|var\s+\(\s*(?P<n2>[a-zA-Z_][a-zA-Z0-9_]*))"
  52 |         self.patterns["var"] = re.compile(var_pattern)
  54 |     def parse_file(self, content: str) -> List[Declaration]:
  56 |         return self.parse(content)
  58 |     def parse(self, content: str) -> List[Declaration]:
  60 |         declarations = []
  61 |         lines = content.split('\n')
  62 |         in_comment = False
  63 |         comment_buffer = []
  64 |         in_const_block = False
  65 |         in_var_block = False
  67 |         i = 0
  68 |         while i < len(lines):
  69 |             line = lines[i].strip()
  72 |             if not line or line.startswith('//'):
  73 |                 i += 1
  74 |                 continue
  77 |             if "/*" in line and not in_comment:
  78 |                 in_comment = True
  79 |                 i += 1
  80 |                 continue
  81 |             elif in_comment:
  82 |                 if "*/" in line:
  83 |                     in_comment = False
  84 |                 i += 1
  85 |                 continue
  88 |             if line.startswith("const ("):
  89 |                 in_const_block = True
  90 |                 i += 1
  91 |                 continue
  92 |             elif in_const_block:
  93 |                 if line == ")":
  94 |                     in_const_block = False
  95 |                     i += 1
  96 |                     continue
  97 |                 else:
  99 |                     name = line.split("=")[0].strip()
 100 |                     if name and name.isidentifier():
 101 |                         declarations.append(Declaration(
 102 |                             kind="const",
 103 |                             name=name,
 104 |                             start_line=i + 1,
 105 |                             end_line=i + 1,
 106 |                             modifiers=set(),
 107 |                             docstring=""
 108 |                         ))
 109 |                     i += 1
 110 |                     continue
 113 |             if line.startswith("var ("):
 114 |                 in_var_block = True
 115 |                 i += 1
 116 |                 continue
 117 |             elif in_var_block:
 118 |                 if line == ")":
 119 |                     in_var_block = False
 120 |                     i += 1
 121 |                     continue
 122 |                 else:
 124 |                     name = line.split("=")[0].strip().split()[0]
 125 |                     if name and name.isidentifier():
 126 |                         declarations.append(Declaration(
 127 |                             kind="var",
 128 |                             name=name,
 129 |                             start_line=i + 1,
 130 |                             end_line=i + 1,
 131 |                             modifiers=set(),
 132 |                             docstring=""
 133 |                         ))
 134 |                     i += 1
 135 |                     continue
 138 |             for kind, pattern in self.patterns.items():
 139 |                 match = pattern.match(line)
 140 |                 if match:
 141 |                     name = match.group("n")
 142 |                     if not name:
 143 |                         continue
 146 |                     end_line = i
 147 |                     if kind in ("function", "interface", "struct"):
 148 |                         brace_count = 0
 149 |                         found_opening = False
 152 |                         j = i
 153 |                         while j < len(lines):
 154 |                             curr_line = lines[j].strip()
 156 |                             if "{" in curr_line:
 157 |                                 found_opening = True
 158 |                                 brace_count += curr_line.count("{")
 159 |                             if "}" in curr_line:
 160 |                                 brace_count -= curr_line.count("}")
 162 |                             if found_opening and brace_count == 0:
 163 |                                 end_line = j
 164 |                                 break
 165 |                             j += 1
 168 |                     docstring = None
 169 |                     if end_line > i:
 170 |                         docstring = self.extract_docstring(lines, i, end_line)
 172 |                     declarations.append(Declaration(
 173 |                         kind=kind,
 174 |                         name=name,
 175 |                         start_line=i + 1,
 176 |                         end_line=end_line + 1,
 177 |                         modifiers=set(),
 178 |                         docstring=docstring or ""
 179 |                     ))
 180 |                     i = end_line + 1
 181 |                     break
 182 |             else:
 183 |                 i += 1
 185 |         return declarations
 187 |     def _find_block_end(self, lines: List[str], start: int) -> int:
 189 |         brace_count = 0
 190 |         i = start
 193 |         while i < len(lines):
 194 |             line = lines[i]
 195 |             if '{' in line:
 196 |                 brace_count += 1
 197 |                 break
 198 |             i += 1
 201 |         while i < len(lines):
 202 |             line = lines[i]
 203 |             brace_count += line.count('{')
 204 |             brace_count -= line.count('}')
 206 |             if brace_count == 0:
 207 |                 return i + 1
 209 |             i += 1
 211 |         return len(lines)
```

#### Analysis Notes
## File: ./codeconcat/parser/language_parsers/go_parser.py
### Functions
### Classes

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
   3 | import os
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
  70 | def is_test_or_config_file(file_path: str) -> bool:
  72 |     file_name = os.path.basename(file_path).lower()
  73 |     return (
  74 |         file_name.startswith("test_") 
  75 |         or file_name == "setup.py"
  76 |         or file_name == "conftest.py"
  77 |         or file_name.endswith("config.py")
  78 |         or "tests/" in file_path
  79 |     )
  82 | def write_markdown(
  83 |     annotated_files: List[AnnotatedFileData],
  84 |     docs: List[ParsedDocData],
  85 |     config: CodeConCatConfig,
  86 |     folder_tree_str: str = "",
  87 | ) -> str:
  89 |     spinner = Halo(text="Generating CodeConcat output", spinner="dots")
  90 |     spinner.start()
  92 |     output_chunks = []
  93 |     output_chunks.append("# CodeConCat Output\n\n")
  96 |     if not config.disable_ai_context:
  97 |         spinner.text = "Generating AI preamble"
  98 |         parsed_files = [
  99 |             ParsedFileData(
 100 |                 file_path=ann.file_path, language=ann.language, content=ann.content, declarations=[]
 101 |             )
 102 |             for ann in annotated_files
 103 |         ]
 104 |         output_chunks.append(generate_ai_preamble(parsed_files, docs, {}))
 107 |     if config.include_directory_structure:
 108 |         spinner.text = "Generating directory structure"
 109 |         output_chunks.append("## Directory Structure\n")
 110 |         output_chunks.append("```\n")
 111 |         all_files = [f.file_path for f in annotated_files] + [d.file_path for d in docs]
 112 |         dir_structure = generate_directory_structure(all_files)
 113 |         output_chunks.append(dir_structure)
 114 |         output_chunks.append("\n```\n\n")
 115 |     elif folder_tree_str:  # Fallback to provided folder tree
 116 |         output_chunks.append("## Folder Tree\n")
 117 |         output_chunks.append("```\n")
 118 |         output_chunks.append(folder_tree_str)
 119 |         output_chunks.append("\n```\n\n")
 122 |     doc_map = {}
 123 |     merged_docs = set()  # Track which docs have been merged
 124 |     if config.merge_docs:
 125 |         for doc in docs:
 126 |             base_name = os.path.splitext(os.path.basename(doc.file_path))[0].lower()
 127 |             doc_map[base_name] = doc
 130 |     if annotated_files:
 131 |         spinner.text = "Processing code files"
 132 |         output_chunks.append("## Code Files\n\n")
 133 |         for i, ann in enumerate(annotated_files, 1):
 134 |             spinner.text = f"Processing code file {i}/{len(annotated_files)}: {ann.file_path}"
 135 |             output_chunks.append(f"### File: {ann.file_path}\n")
 137 |             is_test_config = is_test_or_config_file(ann.file_path)
 140 |             if config.include_file_summary or is_test_config:
 141 |                 spinner.text = "Generating file summary"
 142 |                 summary = generate_file_summary(
 143 |                     ParsedFileData(
 144 |                         file_path=ann.file_path,
 145 |                         language=ann.language,
 146 |                         content=ann.content,
 147 |                         declarations=[],
 148 |                     )
 149 |                 )
 150 |                 output_chunks.append(f"#### Summary\n```\n{summary}\n```\n\n")
 154 |             if not is_test_config and ann.content:
 155 |                 spinner.text = "Processing file content"
 156 |                 processed_content = process_file_content(ann.content, config)
 157 |                 output_chunks.append(f"```{ann.language}\n{processed_content}\n```\n")
 160 |                 if ann.annotated_content:
 162 |                     analysis_lines = []
 163 |                     for line in ann.annotated_content.split('\n'):
 165 |                         if not line.strip() or line.strip() in ann.content:
 166 |                             continue
 168 |                         if line.startswith('#') or 'TODO' in line or 'NOTE' in line or 'FIXME' in line:
 169 |                             analysis_lines.append(line)
 171 |                     if analysis_lines:
 172 |                         output_chunks.append("\n#### Analysis Notes\n")
 173 |                         output_chunks.append('\n'.join(analysis_lines))
 174 |                         output_chunks.append("\n")
 177 |             if config.merge_docs:
 178 |                 base_name = os.path.splitext(os.path.basename(ann.file_path))[0].lower()
 179 |                 if base_name in doc_map:
 180 |                     doc = doc_map[base_name]
 181 |                     output_chunks.append("\n### Associated Documentation\n")
 182 |                     output_chunks.append(doc.content)
 183 |                     output_chunks.append("\n")
 184 |                     merged_docs.add(doc.file_path)
 186 |             output_chunks.append("\n---\n")
 189 |     remaining_docs = [doc for doc in docs if doc.file_path not in merged_docs]
 190 |     if remaining_docs:
 191 |         spinner.text = "Processing documentation files"
 192 |         output_chunks.append("## Documentation\n\n")
 193 |         for i, doc in enumerate(remaining_docs, 1):
 194 |             spinner.text = f"Processing doc file {i}/{len(remaining_docs)}: {doc.file_path}"
 195 |             output_chunks.append(f"### File: {doc.file_path}\n")
 196 |             if config.include_file_summary:
 197 |                 spinner.text = "Generating file summary"
 198 |                 summary = generate_file_summary(
 199 |                     ParsedFileData(
 200 |                         file_path=doc.file_path,
 201 |                         language="markdown",
 202 |                         content=doc.content,
 203 |                         declarations=[],
 204 |                     )
 205 |                 )
 206 |                 output_chunks.append(f"#### Summary\n```\n{summary}\n```\n\n")
 207 |             output_chunks.append(doc.content)
 208 |             output_chunks.append("\n---\n")
 210 |     spinner.text = "Finalizing output"
 211 |     final_str = "".join(output_chunks)
 214 |     spinner.text = "Counting tokens"
 215 |     output_tokens = count_tokens(final_str)
 217 |     with open(config.output, "w", encoding="utf-8") as f:
 218 |         f.write(final_str)
 220 |         f.write("\n\n## Token Statistics\n")
 221 |         f.write(f"Total CodeConcat output tokens (GPT-4): {output_tokens:,}\n")
 223 |     spinner.succeed("CodeConcat output generated successfully")
 224 |     print(f"[CodeConCat] Markdown output written to: {config.output}")
 227 |     print_quote_with_ascii(output_tokens)
 229 |     return final_str
```

#### Analysis Notes
## File: ./codeconcat/writer/markdown_writer.py
### Functions

---
### File: ./codeconcat/writer/__init__.py
#### Summary
```
File: __init__.py
Language: python
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

#### Analysis Notes
## File: ./codeconcat/writer/xml_writer.py
### Functions

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
  23 |         "# AI-Friendly Code Summary",
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

#### Analysis Notes
## File: ./codeconcat/writer/ai_context.py
### Functions

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

#### Analysis Notes
## File: ./codeconcat/writer/json_writer.py
### Functions

---


## Token Statistics
Total CodeConcat output tokens (GPT-4): 54,439
