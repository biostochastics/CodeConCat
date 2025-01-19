import json
from typing import List

from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedDocData


def write_json(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = "",
) -> str:
    data = {"files": []}  # Single list of all files with clear type indicators

    # Add folder tree if present
    if folder_tree_str:
        data["folder_tree"] = folder_tree_str

    # Add code files if any
    for ann in annotated_files:
        data["files"].append(
            {
                "type": "code",
                "file_path": ann.file_path,
                "language": ann.language,
                "content": ann.annotated_content,
            }
        )

    # Add docs if any
    for doc in docs:
        data["files"].append(
            {
                "type": "documentation",
                "file_path": doc.file_path,
                "doc_type": doc.doc_type,
                "content": doc.content,
            }
        )

    final_json = json.dumps(data, indent=2)

    with open(config.output, "w", encoding="utf-8") as f:
        f.write(final_json)

    print(f"[CodeConCat] JSON output written to: {config.output}")
    return final_json
