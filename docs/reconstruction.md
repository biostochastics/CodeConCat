# CodeConCat Reconstruction Tool

The CodeConCat reconstruction tool allows you to reconstruct your original source files from CodeConCat output files. This is useful in scenarios where you need to restore code from a previously generated output, or when sharing code with collaborators who want to extract and use the original files.

## Features

- Reconstructs source files from any CodeConCat output format (markdown, XML, JSON)
- Automatically detects input format if not specified
- Preserves the original directory structure
- Handles compressed content placeholders
- Provides detailed statistics about the reconstruction process

## Usage

### Command Line

You can reconstruct files using the `--reconstruct` flag with the CodeConCat CLI:

```bash
# Basic usage (auto-detects format)
codeconcat --reconstruct codeconcat_ccc.markdown --output-dir ./restored_code

# Specify format explicitly
codeconcat --reconstruct output.xml --input-format xml --output-dir ./from_xml

# With verbose output
codeconcat --reconstruct output.json --input-format json -v
```

### Options

- `--reconstruct FILE`: Path to the CodeConCat output file to reconstruct from
- `--output-dir DIR`: Directory to output reconstructed files (default: `./reconstructed`)
- `--input-format FORMAT`: Format of input file (`markdown`, `xml`, `json`, or `auto` for auto-detection)
- `-v` or `--verbose`: Show detailed progress information

## Supported Input Formats

### Markdown

The tool can parse markdown files produced by CodeConCat, extracting file content from code blocks. It supports both the standard format with file headers as `## File: \`path/to/file.ext\`` and code blocks marked with triple backticks.

### XML

XML output format includes explicit `<file>` elements with `path` attributes and `<content>` child elements, making it straightforward to extract file information.

### JSON

JSON output contains a `files` array with objects that have `path` and `content` properties, which are parsed to reconstruct the original files.

## Handling Compressed Content

When reconstructing files from CodeConCat output with compression enabled, the reconstruction tool will preserve compression placeholders in the reconstructed files. These placeholders indicate where code has been omitted in the original output.

## Programmatic Usage

You can also use the reconstruction functionality directly in your Python code:

```python
from codeconcat.reconstruction import reconstruct_from_file

# Reconstruct files from a markdown file
stats = reconstruct_from_file(
    "codeconcat_output.md",
    "./reconstructed_code",
    format_type=None,  # Auto-detect format
    verbose=True
)

print(f"Files processed: {stats['files_processed']}")
print(f"Files created: {stats['files_created']}")
print(f"Errors: {stats['errors']}")
```

## Limitations

- Reconstructed files will exactly match what was in the CodeConCat output, which might not include all original files if they were filtered out
- If compression was used, compressed segments will remain as placeholders in the reconstructed files
- Binary files that were encoded or processed may not be reconstructed correctly
