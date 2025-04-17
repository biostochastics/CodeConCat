import os

# Suppress HuggingFace tokenizers parallelism warning
os.environ["TOKENIZERS_PARALLELISM"] = "false"

#!/usr/bin/env python3
# SPDX‑License‑Identifier: MIT
"""
CodeConCat – entry point
"""

import sys
import argparse
import logging
import importlib.resources
from typing import List

from tqdm import tqdm

from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig
from codeconcat.collector.github_collector import collect_github_files
from codeconcat.collector.local_collector import collect_local_files
from codeconcat.config.config_loader import load_config
from codeconcat.parser.doc_extractor import extract_docs
from codeconcat.parser.file_parser import parse_code_files
from codeconcat.transformer.annotator import annotate
from codeconcat.writer.json_writer import write_json
from codeconcat.writer.markdown_writer import write_markdown
from codeconcat.writer.xml_writer import write_xml
from codeconcat.quotes import get_random_quote
from .version import __version__

# ------------------------------------------------------------------------------

logger = logging.getLogger("codeconcat")


# ──────────────────────────────────────────────────────────────────────────────
# Exception hierarchy
# ──────────────────────────────────────────────────────────────────────────────
class CodeConcatError(Exception):
    """Base exception for CodeConCat."""


class ConfigurationError(CodeConcatError):
    pass


class FileProcessingError(CodeConcatError):
    pass


class OutputError(CodeConcatError):
    pass


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def _write_output_files(output_text: str, config: CodeConCatConfig) -> None:
    """Write the final (or split) output files to disk."""
    output_path = config.output or f"code_concat_output.{config.format}"
    parts = max(1, getattr(config, "split_output", 1))

    if parts > 1 and config.format == "markdown":
        lines = output_text.splitlines(keepends=True)
        chunk_size = (len(lines) + parts - 1) // parts
        base, ext = os.path.splitext(output_path)

        for idx in range(parts):
            chunk = "".join(lines[idx * chunk_size : (idx + 1) * chunk_size])
            chunk_file = f"{base}.part{idx + 1}{ext}"
            with open(chunk_file, "w", encoding="utf-8") as fh:
                fh.write(chunk)
            logger.info("Output chunk %d/%d → %s", idx + 1, parts, chunk_file)
        print("✔ Output split into", parts, "chunks.")
    else:
        with open(output_path, "w", encoding="utf-8") as fh:
            fh.write(output_text)
        logger.info("Output written → %s", output_path)
        print("✔ Output written to:", output_path)

    # Handle clipboard copy if enabled
    if not getattr(config, "disable_copy", True) and parts <= 1:
        try:
            import pyperclip

            pyperclip.copy(output_text)
            logger.info("Output copied to clipboard.")
        except ImportError:
            logger.warning("pyperclip not installed, skipping clipboard copy.")
        except Exception as e:
            logger.warning(f"Failed to copy to clipboard: {e}")


def create_default_config() -> None:
    """Write `.codeconcat.yml` from the embedded template."""
    target_path = ".codeconcat.yml"
    if os.path.exists(target_path):
        logger.warning("%s already exists; aborting.", target_path)
        return

    try:
        template_content = importlib.resources.read_text(
            "codeconcat.config", "default_config.template.yml"
        )

        with open(target_path, "w") as f:
            f.write(template_content)

        logger.info(f"Created default configuration file: {target_path}")
    except FileNotFoundError:
        logger.error("Default configuration template not found within the package.")
    except Exception as e:
        logger.error(f"Failed to create default configuration file: {e}")


# ──────────────────────────────────────────────────────────────────────────────
# CLI
# ──────────────────────────────────────────────────────────────────────────────
def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="codeconcat",
        description="CodeConCat – LLM‑friendly code aggregator & doc extractor",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    # positional
    p.add_argument("target_path", nargs="?", default=".", help="Directory to process.")

    # version + misc
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument("--show-skip", action="store_true", help="Show skipped files list.")
    p.add_argument("--debug", action="store_true", help="Enable debug logging.")
    p.add_argument(
        "--log-level",
        default="WARNING",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Base logging level when --debug is absent.",
    )
    p.add_argument("--init", action="store_true", help="Create default config and exit.")
    p.add_argument("--show-config", action="store_true", help="Print merged config and exit.")

    # input
    g_in = p.add_argument_group("Input Source")
    g_in.add_argument("--github", help="GitHub URL or owner/repo shorthand.")
    g_in.add_argument("--github-token", help="PAT for private repos.")
    g_in.add_argument("--ref", help="Branch, tag or commit hash.")

    # output
    g_out = p.add_argument_group("Output")
    g_out.add_argument("-o", "--output", help="Output file path.")
    g_out.add_argument("--format", default="markdown", choices=["markdown", "json", "xml"])
    g_out.add_argument("--split-output", type=int, metavar="N", default=1, help="Split Markdown.")
    g_out.add_argument("--sort-files", action="store_true", help="Sort files alphabetically.")

    # feature toggles
    g_feat = p.add_argument_group("Feature Toggles")
    g_feat.add_argument("--docs", action="store_true", help="Extract standalone docs.")
    g_feat.add_argument("--merge-docs", action="store_true", help="Merge docs into main output.")
    g_feat.add_argument("--no-tree", action="store_true", help="Omit folder tree in output.")
    g_feat.add_argument("--no-ai-context", action="store_true", help="Skip AI preamble.")
    g_feat.add_argument("--no-annotations", action="store_true", help="Skip code annotation.")
    g_feat.add_argument("--no-symbols", action="store_true", help="Skip symbol index.")
    g_feat.add_argument("--remove-docstrings", action="store_true", help="Strip docstrings.")
    g_feat.add_argument(
        "--cross-link-symbols", action="store_true", help="Cross‑link symbol list ↔ definitions."
    )
    g_feat.add_argument(
        "--no-progress-bar", action="store_true", help="Disable tqdm progress bars."
    )

    # processing
    p.add_argument("--max-workers", type=int, default=4, help="Thread‑pool size.")

    return p


# ──────────────────────────────────────────────────────────────────────────────
def cli_entry_point() -> None:
    print("\n🐾  " + get_random_quote() + "\n")

    parser = build_parser()
    args = parser.parse_args()

    # logging setup
    level = logging.DEBUG if args.debug else getattr(logging, args.log_level, logging.WARNING)
    logging.basicConfig(level=level, format="%(levelname)s %(name)s: %(message)s")
    logger.setLevel(level)

    # early exits
    if args.init:
        create_default_config()
        sys.exit(0)

    if args.show_config:
        merged = load_config({k: v for k, v in vars(args).items() if v is not None})
        print("--- Final merged configuration ---\n", merged)
        sys.exit(0)

    # merge CLI → pydantic config
    config = load_config(vars(args))
    # Add show_skip to config for downstream functions
    config.show_skip = args.show_skip  # type: ignore[attr-defined]

    try:
        output_text = run_codeconcat(config)
        _write_output_files(output_text, config)
    except CodeConcatError as exc:
        logger.error("Operation failed: %s", exc)
        sys.exit(1)
    except Exception as exc:
        logger.critical("Unexpected error occurred: %s", exc, exc_info=True)
        sys.exit(1)


def generate_folder_tree(root_path: str, config: CodeConCatConfig) -> str:
    """
    Walk the directory tree starting at root_path and return a string that represents the folder structure.
    Respects exclusion patterns from the config.
    """
    from codeconcat.collector.local_collector import should_include_file, should_skip_dir

    lines = []
    for root, dirs, files in os.walk(root_path):
        # Check if we should skip this directory
        if should_skip_dir(root, config.exclude_paths):
            dirs[:] = []  # Clear dirs to prevent descending into this directory
            continue

        level = root.replace(root_path, "").count(os.sep)
        indent = "    " * level
        folder_name = os.path.basename(root) or root_path
        lines.append(f"{indent}{folder_name}/")

        # Filter files based on exclusion patterns
        included_files = [f for f in files if should_include_file(os.path.join(root, f), config)]

        sub_indent = "    " * (level + 1)
        for f in sorted(included_files):
            lines.append(f"{sub_indent}{f}")

        # Filter directories for the next iteration
        dirs[:] = [
            d for d in dirs if not should_skip_dir(os.path.join(root, d), config.exclude_paths)
        ]
        dirs.sort()  # Sort directories for consistent output

    return "\n".join(lines)


def run_codeconcat(config: CodeConCatConfig) -> str:
    """Main execution function for CodeConCat. Returns the generated output string."""
    try:
        # Validate configuration
        if not config.target_path:
            raise ConfigurationError("Target path is required")
        if config.format not in ["markdown", "json", "xml"]:
            raise ConfigurationError(f"Invalid format: {config.format}")

        # Collect files
        try:
            if config.github_url:
                code_files = collect_github_files(config)
            else:
                code_files = collect_local_files(config.target_path, config, show_progress=True)

            if not code_files:
                raise FileProcessingError("No files found to process")
        except Exception as e:
            raise FileProcessingError(f"Error collecting files: {str(e)}")

        # Generate folder tree if enabled
        logger.info("[CodeConCat] Generating folder tree...")
        folder_tree_str = ""
        if not config.disable_tree:
            try:
                folder_tree_str = generate_folder_tree(config.target_path, config)
                logger.info("[CodeConCat] Folder tree generated.")
            except Exception as e:
                logger.warning(f"Warning: Failed to generate folder tree: {str(e)}")

        # Parse code files
        try:
            logger.info(f"[CodeConCat] Found {len(code_files)} code files. Starting parsing...")
            file_paths = [f.file_path for f in code_files]
            parsed_files, errors = parse_code_files(file_paths, config)
            logger.info(f"[CodeConCat] Parsing complete. Parsed {len(parsed_files)} files.")
            if config.show_skip and errors:
                print("\n[Skipped Files]")
                for err in errors:
                    file_path = getattr(err, "file_path", None)
                    msg = str(err)
                    if file_path:
                        print(f"  {file_path}: {msg}")
                    else:
                        print(f"  [Unknown file]: {msg}")
                print("")
            # Defensive flattening: flatten any nested lists in parsed_files
            flattened = []
            for pf in parsed_files:
                if isinstance(pf, list):
                    flattened.extend(pf)
                else:
                    flattened.append(pf)
            parsed_files = flattened
            # Token stats will be calculated at the end of the run

            if not parsed_files:
                raise FileProcessingError("No files were successfully parsed")
        except Exception as e:
            raise FileProcessingError(f"Error parsing files: {str(e)}")

        # Extract docs if requested
        docs = []
        if config.extract_docs:
            try:
                doc_paths = [f.file_path for f in code_files]
                docs = extract_docs(doc_paths, config)
            except Exception as e:
                logger.warning(f"Warning: Failed to extract documentation: {str(e)}")

        logger.info("[CodeConCat] Starting annotation of parsed files...")
        # Annotate files if enabled
        try:
            annotated_files = []
            if not config.disable_annotations:
                for file in parsed_files:
                    try:
                        annotated = annotate(file, config)
                        annotated_files.append(annotated)
                    except Exception as e:
                        # DEBUG: Log type and value of 'file' before using file.file_path
                        logger.error(
                            f"DEBUG: Annotation exception for file object. Type: {type(file)}, Value: {repr(file)}"
                        )
                        try:
                            file_path_debug = file.file_path
                        except Exception as path_exc:
                            file_path_debug = f"<unavailable: {path_exc}>"
                        logger.warning(f"Warning: Failed to annotate {file_path_debug}: {str(e)}")
                        # Fall back to basic annotation
                        try:
                            annotated_files.append(
                                AnnotatedFileData(
                                    file_path=file.file_path,
                                    language=file.language,
                                    content=file.content,
                                    annotated_content=file.content,
                                    summary="",
                                    tags=[],
                                )
                            )
                        except Exception as fallback_exc:
                            logger.error(
                                f"DEBUG: Fallback AnnotatedFileData creation failed: {fallback_exc}"
                            )
                            # Optionally, skip appending if fallback also fails

            else:
                # Create basic annotations without AI analysis
                for file in parsed_files:
                    annotated_files.append(
                        AnnotatedFileData(
                            file_path=file.file_path,
                            language=file.language,
                            content=file.content,
                            annotated_content=file.content,
                            summary="",
                            tags=[],
                        )
                    )
        except Exception as e:
            raise FileProcessingError(f"Error during annotation: {str(e)}")

        # Sort files alphabetically if requested (#31)
        if config.sort_files:
            logger.info("Sorting files alphabetically by path...")
            # Debug: Check types before sorting
            for idx, item in enumerate(annotated_files):
                if not isinstance(item, AnnotatedFileData):
                    logger.error(
                        f"Type Error: Element at index {idx} in annotated_files is {type(item)}, not AnnotatedFileData. Value: {repr(item)}"
                    )
            # End Debug
            try:
                annotated_files.sort(key=lambda f: f.file_path)
            except AttributeError as e:
                logger.error(f"Error sorting files: {e}")
                raise
            logger.debug("Files sorted.")

        logger.info(f"[CodeConCat] Writing output in {config.format} format...")
        # Write output in requested format
        try:
            output = None
            if config.format == "markdown":
                output = write_markdown(
                    annotated_files, parsed_files, docs, config, folder_tree_str
                )
            elif config.format == "json":
                output = write_json(annotated_files, docs, config, folder_tree_str)
            elif config.format == "xml":
                output = write_xml(
                    parsed_files,
                    docs,
                    {f.file_path: f for f in annotated_files},
                    folder_tree_str,
                )
        except Exception as e:
            raise OutputError(f"Error generating {config.format} output: {str(e)}")

        # --- Token stats summary (all files) ---
        try:
            from codeconcat.processor.token_counter import get_token_stats

            total_gpt4 = total_davinci = total_claude = 0
            for pf in parsed_files:
                stats = get_token_stats(pf.content)
                total_gpt4 += stats.gpt4_tokens
                total_davinci += stats.davinci_tokens
                total_claude += stats.claude_tokens
            print(f"\n[Token Summary] Total tokens for all parsed files:")
            print(f"  Claude:   {total_claude}")
            print(f"  GPT-4:    {total_gpt4}")
            print(f"  Davinci:  {total_davinci}")
        except Exception as e:
            logger.warning(f"[Tokens] Failed to calculate token stats: {e}")
        # Return the generated output string
        return output

    except CodeConcatError as e:
        logger.error(f"[CodeConCat] Error: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"[CodeConCat] Unexpected error: {str(e)}")
        raise


def run_codeconcat_in_memory(config: CodeConCatConfig) -> str:
    """Run CodeConCat and return the output as a string."""
    try:
        if config.disable_copy is None:
            config.disable_copy = True  # Always disable clipboard in memory mode

        # Process code
        if config.github_url:
            code_files = collect_github_files(config)
        else:
            code_files = collect_local_files(config.target_path, config)

        if not code_files:
            raise FileProcessingError("No files found to process")

        # Generate folder tree
        folder_tree_str = ""
        if not config.disable_tree:
            folder_tree_str = generate_folder_tree(config.target_path, config)

        # Parse and process files
        parsed_files, errors = parse_code_files([f.file_path for f in code_files], config)
        if not parsed_files:
            raise FileProcessingError("No files were successfully parsed")

        # Extract docs if requested
        docs = []
        if config.extract_docs:
            docs = extract_docs([f.file_path for f in code_files], config)

        # Annotate files
        annotated_files = []
        if not config.disable_annotations:
            for file in parsed_files:
                try:
                    annotated = annotate(file, config)
                    annotated_files.append(annotated)
                except Exception as e:
                    logger.warning(f"Warning: Failed to annotate {file.file_path}: {str(e)}")
                    # Fall back to basic annotation
                    annotated_files.append(
                        AnnotatedFileData(
                            file_path=file.file_path,
                            language=file.language,
                            content=file.content,
                            annotated_content=file.content,
                            summary="",
                            tags=[],
                        )
                    )
        else:
            for file in parsed_files:
                annotated_files.append(
                    AnnotatedFileData(
                        file_path=file.file_path,
                        language=file.language,
                        content=file.content,
                        annotated_content=file.content,
                        summary="",
                        tags=[],
                    )
                )

        # Generate output in requested format
        if config.format == "markdown":
            from codeconcat.writer.ai_context import generate_ai_preamble
            from codeconcat.writer.markdown_writer import write_markdown

            output_chunks = []

            # Only generate AI preamble if not disabled
            if not config.disable_ai_context:
                ai_preamble = generate_ai_preamble(code_files, docs, annotated_files)
                if ai_preamble:
                    output_chunks.append(ai_preamble)

            output = write_markdown(
                annotated_files,
                parsed_files,
                docs,
                config,
                folder_tree_str,
            )
            if output:
                output_chunks.append(output)

            return "\n".join(output_chunks)
        elif config.format == "json":
            return write_json(annotated_files, docs, config, folder_tree_str)
        elif config.format == "xml":
            return write_xml(
                parsed_files,
                docs,
                {f.file_path: f for f in annotated_files},
                folder_tree_str,
            )
        else:
            raise ConfigurationError(f"Invalid format: {config.format}")

    except Exception as e:
        error_msg = f"Error processing code: {str(e)}"
        logger.error(f"[CodeConCat] {error_msg}")
        raise CodeConcatError(error_msg) from e


def main():
    cli_entry_point()


if __name__ == "__main__":
    main()
