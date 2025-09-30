from codeconcat.base_types import AnnotatedFileData, CodeConCatConfig, ParsedFileData


def annotate(parsed_data: ParsedFileData, config: CodeConCatConfig) -> AnnotatedFileData:
    """Annotate parsed file data according to the specified configuration.
    Parameters:
        - parsed_data (ParsedFileData): Contains the various components extracted from the parsed file, such as file path, language, content, declarations, imports, token statistics, and potential security issues.
        - config (CodeConCatConfig): Holds configuration options that control features like whether to include symbols in the annotations.
    Returns:
        - AnnotatedFileData: Includes the original file path, language, content, annotated content with declarations listed by kind, detailed summary, and a set of tags describing the content.
    """
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

    # Explicitly list all found functions, classes, structs, and symbols
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

    # Generate basic summary
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

    # Handle potential None values
    language = parsed_data.language or "unknown"
    content = parsed_data.content or ""

    tags.append(language)

    return AnnotatedFileData(
        file_path=parsed_data.file_path,
        language=language,
        content=content,
        annotated_content="".join(pieces),
        declarations=parsed_data.declarations,
        imports=parsed_data.imports,
        token_stats=parsed_data.token_stats,
        security_issues=parsed_data.security_issues,
        summary=summary,
        ai_summary=parsed_data.ai_summary,  # Transfer AI summary separately
        ai_metadata=getattr(parsed_data, "ai_metadata", None),  # Preserve AI metadata
        tags=tags,
        # Preserve diff data if present
        diff_content=getattr(parsed_data, "diff_content", None),
        diff_metadata=getattr(parsed_data, "diff_metadata", None),
    )
