import os
from concurrent.futures import ThreadPoolExecutor

from codeconcat.base_types import CodeConCatConfig, ParsedDocData


def extract_docs(file_paths: list[str], config: CodeConCatConfig) -> list[ParsedDocData]:
    """Extract documentation from a list of file paths.

    Filters documentation files based on configured extensions and parses
    them in parallel using the configured number of workers.

    Args:
        file_paths: List of file paths to check for documentation.
        config: CodeConCatConfig containing doc_extensions and max_workers settings.

    Returns:
        list[ParsedDocData]: List of parsed documentation data objects.
    """
    doc_paths = [fp for fp in file_paths if is_doc_file(fp, config.doc_extensions)]

    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        results = list(executor.map(lambda fp: parse_doc_file(fp), doc_paths))
    return results


def is_doc_file(file_path: str, doc_exts: list[str]) -> bool:
    """Check if a file path has a documentation extension.

    Args:
        file_path: Path to the file to check.
        doc_exts: List of valid documentation extensions (e.g., ['.md', '.rst']).

    Returns:
        bool: True if the file has a documentation extension.
    """
    ext = os.path.splitext(file_path)[1].lower()
    return ext in doc_exts


def parse_doc_file(file_path: str) -> ParsedDocData:
    """Parse a documentation file into ParsedDocData.

    Args:
        file_path: Path to the documentation file to parse.

    Returns:
        ParsedDocData: Parsed documentation data with file path, type, and content.
    """
    ext = os.path.splitext(file_path)[1].lower()
    content = read_doc_content(file_path)
    doc_type = ext.lstrip(".")
    return ParsedDocData(file_path=file_path, doc_type=doc_type, content=content)


def read_doc_content(file_path: str) -> str:
    """Read the content of a documentation file.

    Args:
        file_path: Path to the documentation file.

    Returns:
        str: File content as a string, or empty string if reading fails.
    """
    try:
        with open(file_path, encoding="utf-8", errors="replace") as f:
            return f.read()
    except Exception:
        return ""
