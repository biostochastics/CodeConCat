import json
from typing import List
from codeconcat.types import AnnotatedFileData, ParsedDocData, CodeConCatConfig

def write_json(
    annotated_files: List[AnnotatedFileData],
    docs: List[ParsedDocData],
    config: CodeConCatConfig
) -> None:
    data = {
        "code": [],
        "docs": []
    }

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

    with open(config.output, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

    print(f"[CodeConCat] JSON output written to: {config.output}")
