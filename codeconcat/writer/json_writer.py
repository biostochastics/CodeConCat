import json
from typing import List
from codeconcat.types import AnnotatedFileData, ParsedDocData, CodeConCatConfig

def write_json(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig,
    folder_tree_str: str = ""
) -> str:
    data = {
        "code": [],
        "docs": []
    }

    if folder_tree_str:
        data["folder_tree"] = folder_tree_str

    for ann in annotated_files:
        data["code"].append({
            "file_path": ann.file_path,
            "language": ann.language,
            "annotated_content": ann.annotated_content
        })

    if config.docs:
        for doc in docs:
            data["docs"].append({
                "file_path": doc.file_path,
                "doc_type": doc.doc_type,
                "content": doc.content
            })

    final_json = json.dumps(data, indent=2)

    with open(config.output, "w", encoding="utf-8") as f:
        f.write(final_json)

    print(f"[CodeConCat] JSON output written to: {config.output}")
    return final_json
