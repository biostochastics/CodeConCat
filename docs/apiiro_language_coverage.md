# Apiiro Ruleset Language Coverage

This document shows which CodeConCat-supported languages are covered by the Apiiro malicious code ruleset.

## CodeConCat Supported Languages (10 Primary Languages)

CodeConCat currently has full parser support for these languages:

1. **C#** ✅ Apiiro ruleset supported
2. **Go** ✅ Apiiro ruleset supported  
3. **JavaScript/TypeScript** ✅ Apiiro ruleset supported
4. **Python** ✅ Apiiro ruleset supported
5. **Rust** ✅ Apiiro ruleset supported
6. **Java** ✅ Apiiro ruleset supported
7. **PHP** ✅ Apiiro ruleset supported
8. **R** ❌ No Apiiro ruleset (basic security only)
9. **Julia** ❌ No Apiiro ruleset (basic security only)
10. **C/C++** ❌ No Apiiro ruleset (basic security only)

## Security Scanning Coverage

### Languages with Full Apiiro Security Scanning (7 languages)

When Semgrep is enabled, these languages get comprehensive malicious code detection:

- **C#** - Detects C#-specific malicious patterns
- **Go** - Detects Go-specific malicious patterns
- **JavaScript/TypeScript** - Detects JS/TS-specific malicious patterns
- **Python** - Detects Python-specific malicious patterns
- **Rust** - Detects Rust-specific malicious patterns
- **Java** - Detects Java-specific malicious patterns
- **PHP** - Detects PHP-specific malicious patterns

### Languages with Basic Security Scanning Only (3 languages)

These languages still get security scanning but without language-specific Apiiro rules:

- **R** - Basic pattern matching for credentials, SQL injection, etc.
- **Julia** - Basic pattern matching for credentials, SQL injection, etc.
- **C/C++** - Basic pattern matching for credentials, SQL injection, etc.

## Implementation Notes

When Semgrep scanning is enabled in CodeConCat:

1. **Covered Languages**: Files in languages supported by the Apiiro ruleset will be scanned for malicious patterns specific to that language.

2. **Uncovered Languages**: Files in languages not covered by the Apiiro ruleset will still undergo:
   - Basic security pattern matching (hardcoded credentials, etc.)
   - Generic security checks
   - But won't have language-specific malicious code detection

3. **Language Filtering**: You can specify which languages to scan using the `--semgrep-languages` option:
   ```bash
   codeconcat --enable-semgrep --semgrep-languages python,javascript,go
   ```

4. **Custom Rules**: For languages not covered by Apiiro, you can add custom Semgrep rules using the `--semgrep-ruleset` option.

## Recommendations

1. For maximum security coverage, focus Semgrep scanning on the supported languages listed above.
2. For unsupported languages, rely on CodeConCat's built-in security pattern matching.
3. Consider adding custom Semgrep rules for critical unsupported languages in your codebase.