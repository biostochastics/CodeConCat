# Input Validation Module

This module provides comprehensive input validation for the CodeConCat application. It includes validation for file paths, file contents, URLs, and configuration data to ensure the security and reliability of the application.

## Features

- **File Path Validation**: Validate file paths, check existence, and detect path traversal attempts.
- **File Content Validation**: Detect binary files, check file sizes, and validate file extensions.
- **URL Validation**: Validate URLs and restrict to allowed domains.
- **Configuration Validation**: Validate configuration dictionaries against required fields.
- **Security Checks**: Detect potentially malicious file types and content.
- **Semgrep Integration**: Advanced code security scanning using the Apiiro malicious code ruleset.

## Recent Updates

- **Fixed Tree-sitter Dependencies**: Resolved missing tree-sitter module imports that were preventing proper parser initialization.
- **Fixed File Collection**: Corrected issue where `include_paths` was expecting directory paths instead of glob patterns.
- **YAML File Processing**: Removed YAML/YML files from default exclusion patterns, allowing them to be processed when explicitly included.
- **Comprehensive Attack Patterns**: Added extensive language-specific security patterns covering:
  - Memory corruption vulnerabilities (buffer overflows, use-after-free)
  - Injection attacks (SQL, command, code, XSS, template injection)
  - Insecure deserialization and file operations
  - Cryptographic weaknesses and hardcoded secrets
  - Language-specific anti-patterns and unsafe operations
- **Enhanced Semgrep Rules**: Created custom security rules for advanced vulnerability detection

## Usage

Import the validator instance:

```python
from codeconcat.validation import validator

# Validate a file path
try:
    file_path = validator.validate_file_path("path/to/file.txt")
    print(f"Valid file path: {file_path}")
except ValidationError as e:
    print(f"Validation error: {e}")

# Validate a file extension
try:
    is_valid = validator.validate_file_extension("script.py", allowed_extensions={".py", ".txt"})
    print("File extension is valid")
except ValidationError as e:
    print(f"Invalid file extension: {e}")

# Validate a URL
try:
    url = validator.validate_url("https://github.com/user/repo", allowed_domains={"github.com"})
    print(f"Valid URL: {url}")
except ValidationError as e:
    print(f"Invalid URL: {e}")

# Validate configuration
try:
    config = {"api_key": "12345", "enabled": True}
    validator.validate_config(config, required_fields=["api_key"])
    print("Configuration is valid")
except ValidationError as e:
    print(f"Invalid configuration: {e}")
```

## ValidationError

The `ValidationError` exception is raised when validation fails. It includes:

- `message`: Explanation of the error
- `field`: The name of the field that failed validation (if applicable)
- `value`: The invalid value (if applicable)
- `original_exception`: The original exception that caused the error (if any)

## Security Considerations

The validation module includes several security features:

- Path traversal detection
- Binary file detection
- Malicious file extension blocking
- URL domain whitelisting
- File size limits
- Semgrep-based code scanning for security vulnerabilities

## Semgrep Integration

CodeConCat now integrates with [Semgrep](https://semgrep.dev/) for advanced security scanning of code files using the [Apiiro malicious code ruleset](https://github.com/apiiro/malicious-code-ruleset).

### Usage

Enable Semgrep scanning in your configuration:

```python
from codeconcat.validation.integration import setup_semgrep
from codeconcat.base_types import CodeConCatConfig

# Configure with Semgrep enabled
config = CodeConCatConfig(
    enable_semgrep=True,
    install_semgrep=True  # Set to True to auto-install if not present
)

# Set up Semgrep
semgrep_available = setup_semgrep(config)
```

Or via the command line:

```bash
codeconcant --enable-semgrep --install-semgrep
```

### Options

- `--enable-semgrep`: Enable Semgrep security scanning
- `--install-semgrep`: Install Semgrep if not already installed
- `--semgrep-ruleset PATH`: Use a custom ruleset instead of the Apiiro ruleset
- `--semgrep-languages LANG [LANG ...]`: Specify languages to scan with Semgrep
- `--strict-security`: Fail validation when suspicious content is detected

## Testing

Run the validation tests with:

```bash
pytest tests/unit/validation/
```

## Best Practices

1. **Always validate early**: Validate inputs as soon as they enter your application.
2. **Use specific validators**: Choose the most specific validator for your use case.
3. **Provide clear error messages**: Catch `ValidationError` and present user-friendly messages.
4. **Keep validators up to date**: Update the validation rules as new threats emerge.
5. **Use allowlists**: Prefer allowlisting known good values over blacklisting bad ones.
