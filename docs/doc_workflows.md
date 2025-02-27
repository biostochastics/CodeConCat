# Documentation Workflows in CodeConCat

CodeConCat provides powerful features for handling documentation alongside your code. This guide explains how to use these features effectively.

## Configuration Options

### `extract_docs` (Default: False)
When enabled, CodeConCat will:
- Search for documentation files (`.md`, `.rst`, `.txt`, `.rmd`)
- Parse and include them in the final output
- Maintain their original formatting
- Include them as a separate section in the output

Example:
```bash
codeconcat --docs /path/to/codebase
```

### `merge_docs` (Default: False)
When enabled along with `extract_docs`, CodeConCat will:
- Merge documentation content with related code files
- Place documentation before the corresponding code sections
- Help maintain context between documentation and implementation

Example:
```bash
codeconcat --docs --merge-docs /path/to/codebase
```

### `doc_extensions` (Default: [".md", ".rst", ".txt", ".rmd"])
Customize which file extensions are treated as documentation:
```yaml
# .codeconcat.yml
doc_extensions:
  - .md
  - .rst
  - .txt
  - .rmd
  - .wiki
```

## Common Workflows

### 1. Code with Separate Documentation
```bash
codeconcat --docs /path/to/codebase
```
This will:
- Process all code files
- Include documentation files separately
- Output both in organized sections

### 2. Integrated Code and Documentation
```bash
codeconcat --docs --merge-docs /path/to/codebase
```
This will:
- Process all code files
- Find related documentation files
- Merge documentation with code
- Present an integrated view

### 3. Custom Documentation Types
```bash
codeconcat --docs --doc-extensions .md,.wiki,.custom /path/to/codebase
```
This will:
- Include files with custom extensions as documentation
- Process them alongside standard doc types

## Best Practices

1. **Documentation Organization**
   - Keep documentation close to related code
   - Use consistent file extensions
   - Follow a clear naming convention

2. **Documentation Content**
   - Write clear, concise documentation
   - Include examples where helpful
   - Keep documentation up-to-date with code changes

3. **Integration with Code**
   - When using `merge_docs`, ensure documentation references match code structure
   - Consider using relative links between documentation files
   - Maintain a consistent style across all documentation

## Output Formats

Documentation can be included in all supported output formats:

### Markdown
```bash
codeconcat --docs --format markdown /path/to/codebase
```
- Documentation maintains original Markdown formatting
- Clean, readable output
- Easy to view on GitHub or other Markdown viewers

### JSON
```bash
codeconcat --docs --format json /path/to/codebase
```
- Documentation included in structured JSON
- Useful for programmatic processing
- Maintains all metadata

### XML
```bash
codeconcat --docs --format xml /path/to/codebase
```
- Documentation wrapped in XML tags
- Maintains structure and metadata
- Suitable for XML-based tooling

## Example Configuration

Complete example of documentation-related settings in `.codeconcat.yml`:
```yaml
extract_docs: true
merge_docs: true
doc_extensions:
  - .md
  - .rst
  - .txt
  - .rmd
  - .wiki
output: "codebase_with_docs.md"
format: "markdown"
```
