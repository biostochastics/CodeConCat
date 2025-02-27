# Security Processor in CodeConCat

The Security Processor is a built-in feature that helps identify potential security issues in your code, such as hardcoded secrets, API keys, and other sensitive information.

## Integration Status

The Security Processor is currently optional and not enabled by default. It's integrated into the codebase but requires explicit configuration to use.

## Detected Issues

The processor can detect various types of sensitive information:

1. **AWS Keys**
   - AWS Access Key IDs
   - AWS Secret Access Keys

2. **GitHub Tokens**
   - Personal Access Tokens
   - OAuth Tokens

3. **Generic API Keys**
   - Any API key patterns
   - Bearer tokens
   - Basic authentication

4. **Private Keys**
   - RSA Private Keys
   - SSH Private Keys

5. **Generic Secrets**
   - Passwords
   - Generic tokens
   - Other sensitive strings

## Using the Security Processor

### 1. Direct API Usage

```python
from codeconcat.processor.security_processor import SecurityProcessor

# Scan a single file or string
issues = SecurityProcessor.scan_content(
    content="your code here",
    file_path="path/to/file.py"
)

# Format issues for display
formatted = SecurityProcessor.format_issues(issues)
print(formatted)
```

### 2. Integration with CodeConCat Pipeline

The Security Processor is integrated into the main CodeConCat pipeline. Security issues are stored in the `security_issues` field of `ParsedFileData` objects:

```python
from codeconcat import run_codeconcat_in_memory, CodeConCatConfig

config = CodeConCatConfig(
    target_path="path/to/code",
    format="json"
)

output = run_codeconcat_in_memory(config)
# Security issues will be included in the output
```

## Best Practices

1. **Regular Scanning**
   - Run security scans regularly as part of your development workflow
   - Include security scanning in your CI/CD pipeline

2. **False Positives**
   - The processor includes patterns to ignore common test/sample values
   - You can extend these patterns for your specific needs

3. **Sensitive Data Handling**
   - Never commit sensitive data to version control
   - Use environment variables or secure secret management
   - Remove any discovered secrets immediately

4. **Configuration**
   - Consider enabling security scanning for all production code
   - Adjust sensitivity levels based on your needs
   - Document any custom patterns or rules

## Future Enhancements

1. **Configuration Options**
   - Enable/disable specific security checks
   - Custom pattern definitions
   - Severity level adjustments

2. **Integration Points**
   - CI/CD pipeline integration
   - Pre-commit hook support
   - Real-time scanning in IDEs

3. **Reporting**
   - Detailed security reports
   - Issue tracking and history
   - Integration with security tools

## Example Configuration

Here's how you might configure security scanning in your `.codeconcat.yml`:

```yaml
# Future enhancement - not yet implemented
security:
  enabled: true
  checks:
    aws_keys: true
    github_tokens: true
    api_keys: true
    private_keys: true
    generic_secrets: true
  ignore_patterns:
    - "example_key"
    - "test_token"
  severity_levels:
    private_keys: critical
    aws_keys: high
    github_tokens: high
    api_keys: medium
    generic_secrets: medium
```

## Contributing

We welcome contributions to improve the Security Processor:

1. **New Patterns**
   - Additional secret patterns
   - Better false positive handling
   - Language-specific patterns

2. **Performance**
   - Pattern matching optimization
   - Parallel processing
   - Resource usage improvements

3. **Integration**
   - Additional tool integrations
   - Reporting formats
   - CI/CD plugins
