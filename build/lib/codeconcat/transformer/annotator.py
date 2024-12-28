"""
annotator.py

Takes ParsedFileData and produces AnnotatedFileData with headings for each file
and subheadings for declarations, plus a code fence block.
"""

from codeconcat.types import ParsedFileData, AnnotatedFileData, CodeConCatConfig

def annotate(parsed_data: ParsedFileData, config: CodeConCatConfig) -> AnnotatedFileData:
    pieces = []
    pieces.append(f"## File: {parsed_data.file_path}\n")

    for decl in parsed_data.declarations:
        if decl.kind == "function":
            pieces.append(f"### Function: {decl.name}\n")
        elif decl.kind == "class":
            pieces.append(f"### Class: {decl.name}\n")
        elif decl.kind == "struct":
            pieces.append(f"### Struct: {decl.name}\n")

    pieces.append(f"```{parsed_data.language}\n{parsed_data.content}\n```\n")

    return AnnotatedFileData(
        file_path=parsed_data.file_path,
        language=parsed_data.language,
        annotated_content="".join(pieces)
    )
