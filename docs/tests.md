# CodeConCat Tests

This directory contains tests for CodeConCat, including unit tests, integration tests, and test resources.

## Test Structure

```
tests/
├── integration/             # Integration tests
│   ├── test_end_to_end_validation.py    # End-to-end tests for validation
│   └── test_repository_validation.py    # Tests using real repositories
├── unit/                    # Unit tests
│   ├── api/                 # API tests
│   ├── base_types/          # Base types tests
│   ├── config/              # Configuration tests
│   ├── integration/         # Integration unit tests
│   ├── parser/              # Parser tests
│   ├── processor/           # Processor tests
│   ├── transformer/         # Transformer tests
│   ├── validation/          # Validation tests
│   │   ├── test_input_validation.py     # Input validation tests
│   │   ├── test_integration.py          # Validation integration tests
│   │   ├── test_schema_validation.py    # Schema validation tests
│   │   ├── test_security.py             # Security validation tests
│   │   ├── test_semgrep_validator.py    # Semgrep validator tests
│   │   ├── test_setup_semgrep.py        # Semgrep setup tests
│   │   └── test_validation_integration.py # Validation integration tests
│   └── writer/              # Writer tests
└── parser_test_corpus/      # Test files for parsers
    ├── c/                   # C test files
    ├── cpp/                 # C++ test files
    ├── csharp/              # C# test files
    ├── go/                  # Go test files
    ├── java/                # Java test files
    ├── javascript/          # JavaScript test files
    ├── julia/               # Julia test files
    ├── php/                 # PHP test files
    ├── python/              # Python test files
    ├── r/                   # R test files
    ├── rust/                # Rust test files
    └── typescript/          # TypeScript test files
```

## Running Tests

### Prerequisites

To run all tests, you'll need:

1. Python 3.8+ with pytest installed
2. Git (for repository tests)
3. Semgrep (optional, for full semgrep tests)

For Semgrep tests, you can either:
- Install Semgrep globally: `pip install semgrep`
- Let the tests install it automatically when needed

To enable GitHub repository tests, set the `GITHUB_TOKEN` environment variable:

```bash
export GITHUB_TOKEN=your_github_token
```

### Running the Tests

Run all tests:

```bash
python -m pytest
```

Run only unit tests:

```bash
python -m pytest tests/unit/
```

Run only validation tests:

```bash
python -m pytest tests/unit/validation/
```

Run integration tests:

```bash
python -m pytest tests/integration/
```

### Test with Verbose Output and Logging

For more detailed output:

```bash
python -m pytest -v --log-cli-level=DEBUG
```

### Run Specific Test Files

```bash
python -m pytest tests/unit/validation/test_semgrep_validator.py
```

### Run Tests with Coverage Report

```bash
python -m pytest --cov=codeconcat
```

## Test Categories

### Unit Tests

- **Input Validation**: Tests for file path, content, and URL validation
- **Schema Validation**: Tests for JSON Schema validation
- **Security Validation**: Tests for security checks and content sanitization
- **Semgrep Integration**: Tests for Semgrep validator and setup

### Integration Tests

- **End-to-End Validation**: Tests the entire validation pipeline with different security configurations
- **Repository Validation**: Tests CodeConCat on real GitHub repositories

## Semgrep Testing Notes

The Semgrep tests are designed to work in multiple modes:

1. **Mock Mode**: Tests use mocked Semgrep results (default)
2. **Real Mode**: Tests use actual Semgrep installation if available
3. **Apiiro Ruleset Mode**: Tests with the Apiiro malicious code ruleset

For full Semgrep testing with the actual binary:

```bash
# Install Semgrep
pip install semgrep

# Run tests with real Semgrep
python -m pytest tests/integration/test_end_to_end_validation.py::TestEndToEndValidation::test_validation_with_real_semgrep
```
