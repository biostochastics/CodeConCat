from codeconcat.types import ParsedFileData, AnnotatedFileData, CodeConCatConfig

def annotate(parsed_data: ParsedFileData, config: CodeConCatConfig) -> AnnotatedFileData:
    pieces = []
    pieces.append(f"## File: {parsed_data.file_path}\n")

    # Group declarations by kind
    functions = []
    classes = []
    structs = []
    symbols = []

    for decl in parsed_data.declarations:
        if decl.kind == "function":
            functions.append(decl.name)
        elif decl.kind == "class":
            classes.append(decl.name)
        elif decl.kind == "struct":
            structs.append(decl.name)
        elif decl.kind == "symbol":
            symbols.append(decl.name)

    # Add headers for each kind if they exist
    if functions:
        pieces.append("### Functions\n")
        for name in functions:
            pieces.append(f"- {name}\n")

    if classes:
        pieces.append("### Classes\n")
        for name in classes:
            pieces.append(f"- {name}\n")

    if structs:
        pieces.append("### Structs\n")
        for name in structs:
            pieces.append(f"- {name}\n")

    if symbols:
        pieces.append("### Symbols\n")
        for name in symbols:
            pieces.append(f"- {name}\n")

    pieces.append(f"```{parsed_data.language}\n{parsed_data.content}\n```\n")

    return AnnotatedFileData(
        file_path=parsed_data.file_path,
        language=parsed_data.language,
        annotated_content="".join(pieces)
    )
