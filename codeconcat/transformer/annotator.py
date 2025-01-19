from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedFileData


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
        elif decl.kind == "symbol" and not config.disable_symbols:
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

    # Generate summary
    summary_parts = []
    if functions:
        summary_parts.append(f"{len(functions)} functions")
    if classes:
        summary_parts.append(f"{len(classes)} classes")
    if structs:
        summary_parts.append(f"{len(structs)} structs")
    if symbols:
        summary_parts.append(f"{len(symbols)} symbols")

    summary = f"Contains {', '.join(summary_parts)}" if summary_parts else "No declarations found"

    # Generate tags
    tags = []
    if functions:
        tags.append("has_functions")
    if classes:
        tags.append("has_classes")
    if structs:
        tags.append("has_structs")
    if symbols:
        tags.append("has_symbols")
    tags.append(parsed_data.language)

    return AnnotatedFileData(
        file_path=parsed_data.file_path,
        language=parsed_data.language,
        content=parsed_data.content,
        annotated_content="".join(pieces),
        summary=summary,
        tags=tags,
    )
