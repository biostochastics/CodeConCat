"""
main.py

The CLI entry for CodeConCat. Uses argparse to parse flags, merges with .codeconcat.yml,
collects code and doc files, parses them concurrently, annotates them, and writes the final output.
"""

import argparse
import sys
from typing import List

from codeconcat.config.config_loader import load_config
from codeconcat.collector.local_collector import collect_local_files
from codeconcat.collector.github_collector import collect_github_files
from codeconcat.parser.file_parser import parse_code_files
from codeconcat.parser.doc_extractor import extract_docs
from codeconcat.transformer.annotator import annotate
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.json_writer import write_json

from codeconcat.types import CodeConCatConfig, AnnotatedFileData, ParsedDocData

def cli_entry_point():
    parser = argparse.ArgumentParser(
        prog="codeconcat",
        description="CodeConCat - An LLM-friendly code aggregator and doc extractor."
    )

    parser.add_argument("target_path", nargs="?", default=".")
    parser.add_argument("--github", help="GitHub URL (stubbed)", default=None)

    parser.add_argument("--docs", action="store_true", help="Enable doc extraction (md/rst/txt/rmd)")
    parser.add_argument("--merge-docs", action="store_true", help="Merge doc content with code output")

    parser.add_argument("--output", default="code_concat_output.md", help="Output file name")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")

    parser.add_argument("--include-languages", nargs="*", default=[], help="Only include these languages")
    parser.add_argument("--exclude-languages", nargs="*", default=[], help="Exclude these languages")
    parser.add_argument("--exclude", nargs="*", default=[], help="Paths or patterns to exclude (e.g. node_modules)")

    parser.add_argument("--max-workers", type=int, default=4, help="Number of worker threads for concurrency")

    args = parser.parse_args()

    # Convert CLI to dict for merging
    cli_args = {
        "target_path": args.target_path,
        "github_url": args.github,
        "docs": args.docs,
        "merge_docs": args.merge_docs,
        "output": args.output,
        "format": args.format,
        "include_languages": args.include_languages,
        "exclude_languages": args.exclude_languages,
        "exclude_paths": args.exclude,
        "max_workers": args.max_workers,
    }

    config = load_config(cli_args)
    run_codeconcat(config)

def run_codeconcat(config: CodeConCatConfig) -> None:
    if config.github_url:
        # Not implemented in detail
        try:
            file_paths = collect_github_files(config.github_url, config)
        except NotImplementedError as e:
            print(e)
            sys.exit(1)
    else:
        file_paths = collect_local_files(config.target_path, config)

    if not file_paths:
        print("[CodeConCat] No files found. Check your config or directory.")
        return

    docs: List[ParsedDocData] = []
    if config.docs:
        docs = extract_docs(file_paths, config)

    # Parse code
    parsed_files = parse_code_files(file_paths, config)

    # Annotate code
    annotated_files: List[AnnotatedFileData] = []
    for pf in parsed_files:
        annotated_files.append(annotate(pf, config))

    # Write final output
    if config.format == "json":
        write_json(annotated_files, docs, config)
    else:
        write_markdown(annotated_files, docs, config)

def main():
    cli_entry_point()

if __name__ == "__main__":
    main()
