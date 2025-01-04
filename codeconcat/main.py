import argparse
import sys
from typing import List
import os

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
    parser.add_argument("--github", help="GitHub URL", default=None)
    parser.add_argument("--github-token", help="GitHub personal access token", default=None)

    parser.add_argument("--docs", action="store_true", help="Enable doc extraction")
    parser.add_argument("--merge-docs", action="store_true", help="Merge doc content with code output")

    parser.add_argument("--output", default="code_concat_output.md", help="Output file name")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format")

    parser.add_argument("--include-languages", nargs="*", default=[], help="Only include these languages")
    parser.add_argument("--exclude-languages", nargs="*", default=[], help="Exclude these languages")
    parser.add_argument("--exclude", nargs="*", default=[], help="Paths/patterns to exclude")

    parser.add_argument("--max-workers", type=int, default=4, help="Number of worker threads")

    parser.add_argument("--no-tree", action="store_true", help="Disable folder tree generation (enabled by default)")
    parser.add_argument("--no-copy", action="store_true", help="Disable copying output to clipboard (enabled by default)")

    args = parser.parse_args()

    cli_args = {
        "target_path": args.target_path,
        "github_url": args.github,
        "github_token": args.github_token,
        "docs": args.docs,
        "merge_docs": args.merge_docs,
        "output": args.output,
        "format": args.format,
        "include_languages": args.include_languages,
        "exclude_languages": args.exclude_languages,
        "exclude_paths": args.exclude,
        "max_workers": args.max_workers,
        "include_tree": not args.no_tree,
        "copy_output": not args.no_copy
    }

    config = load_config(cli_args)
    run_codeconcat(config)


def generate_folder_tree(root_path: str) -> str:
    """
    Walk the directory tree starting at root_path and return a string that represents the folder structure.
    """
    lines = []
    for root, dirs, files in os.walk(root_path):
        level = root.replace(root_path, "").count(os.sep)
        indent = "    " * level
        folder_name = os.path.basename(root) or root_path
        lines.append(f"{indent}{folder_name}/")
        sub_indent = "    " * (level + 1)
        for f in files:
            lines.append(f"{sub_indent}{f}")
    return "\n".join(lines)


def run_codeconcat(config: CodeConCatConfig) -> None:
    if config.github_url:
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

    parsed_files = parse_code_files(file_paths, config)

    annotated_files: List[AnnotatedFileData] = []
    for pf in parsed_files:
        annotated_files.append(annotate(pf, config))

    folder_tree_str = ""
    if config.include_tree:
        folder_tree_str = generate_folder_tree(config.target_path)

    # Always write code and docs separately
    if config.format == "json":
        code_output = write_json(annotated_files, [], config, folder_tree_str)  # Empty docs list
        if docs:
            docs_output_path = os.path.splitext(config.output)[0] + "_docs.json"
            write_json([], docs, config._replace(output=docs_output_path), "")  # Empty code list
    else:
        code_output = write_markdown(annotated_files, [], config, folder_tree_str)  # Empty docs list
        if docs:
            docs_output_path = os.path.splitext(config.output)[0] + "_docs.md"
            write_markdown([], docs, config._replace(output=docs_output_path), "")  # Empty code list

    # Only copy code to clipboard
    if config.copy_output and code_output:
        try:
            import pyperclip
            pyperclip.copy(code_output)
            print("[CodeConCat] Code output copied to clipboard.")
        except ImportError:
            print("[CodeConCat] pyperclip not installed. Unable to copy to clipboard.")


def main():
    cli_entry_point()


if __name__ == "__main__":
    main()
