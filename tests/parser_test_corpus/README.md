# Parser Test Corpus

This directory contains code samples for testing each language parser in CodeConcat.

## Purpose

The test corpus serves multiple purposes:

1. **Validation**: Ensure each parser correctly identifies declarations, imports, docstrings, etc.
2. **Regression Testing**: Prevent regressions when modifying parsers
3. **Documentation**: Provide examples of code that should be properly parsed
4. **Edge Cases**: Test boundary conditions and special syntax features

## Structure

Each language has its own subdirectory containing:

- `basic.{ext}`: Simple examples with standard declarations (functions, classes, etc.)
- `complex.{ext}`: More complex examples with nested structures, unusual syntax, etc.
- `edge_cases.{ext}`: Edge cases that might break parsers (unusual whitespace, multiple declarations per line, etc.)
- `docstrings.{ext}`: Different docstring formats and styles
- `expected_output.json`: The expected parsing results for validation

## Running Tests

To test a specific language parser:

```bash
python -m pytest tests/test_parsers.py -k "test_language_parser[python]"
```

To test all parsers:

```bash
python -m pytest tests/test_parsers.py
```

## Adding New Test Cases

When adding a new test case:

1. Add the code sample to the appropriate language directory
2. Update the expected_output.json file with the expected parsing results
3. Run the tests to ensure the parser handles the new test case correctly
