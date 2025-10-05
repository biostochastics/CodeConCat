# Grammar Verification Script

## Overview

The `verify_grammars.sh` script ensures that all required tree-sitter grammars are available before parser development or builds proceed. This is a critical quality gate for the codeconcat language expansion project.

## Purpose

As codeconcat expands from 11 to 40 languages across multiple tiers (v0.9.0 - v0.12.0), this script:

- Verifies grammar availability for current and planned languages
- Prevents parser implementation without required grammars
- Provides early feedback in CI/CD pipelines
- Reduces debugging time for grammar-related issues

## Usage

### Basic Usage

Verify current languages only (v0.8.6):

```bash
./scripts/verify_grammars.sh
```

### Tier-Based Verification

Verify specific tiers:

```bash
# Verify Tier 1 languages (v0.9.0 target)
./scripts/verify_grammars.sh --tier tier1

# Verify Tier 2 languages (v0.10.0 target)
./scripts/verify_grammars.sh --tier tier2

# Verify all languages across all tiers
./scripts/verify_grammars.sh --all
```

### Verbose Output

Show detailed per-language status:

```bash
./scripts/verify_grammars.sh --verbose
# or
./scripts/verify_grammars.sh -v
```

### Report All Missing Grammars

By default, the script exits on the first missing grammar. To see all missing grammars:

```bash
./scripts/verify_grammars.sh --all --no-exit
```

### Help

Display usage information:

```bash
./scripts/verify_grammars.sh --help
```

## Command-Line Options

| Option | Description |
|--------|-------------|
| `--tier TIER` | Verify specific tier: `current`, `tier1`, `tier2`, `tier3`, `tier4`, `all` |
| `--all` | Verify all languages across all tiers (equivalent to `--tier all`) |
| `--verbose`, `-v` | Show detailed output for each language |
| `--no-exit` | Report all missing grammars instead of exiting on first error |
| `--help`, `-h` | Show help message |

## Exit Codes

- `0`: All grammars verified successfully
- `1`: One or more grammars missing or failed to load

## Language Tiers

### Current (v0.8.6)
14 languages: Python, C, C++, C#, Java, JavaScript, TypeScript, Go, Rust, PHP, Swift, Julia, Bash, R

### Tier 1 (v0.9.0 target)
7 languages: Kotlin, Dart, SQL, HCL (Terraform), GraphQL, Ruby, Solidity

### Tier 2 (v0.10.0 target)
8 languages: GLSL, HLSL, Metal, WASM, Zig, Elixir, Crystal

### Tier 3 (v0.11.0 target)
8 languages: OCaml, ReScript, Reason, Lean, Coq, Haxe, V, Scala

### Tier 4 (v0.12.0 target)
6 languages: Nim, Nix, Vala, Astro, Embedded C, Community Pick

## Maintenance

### Adding New Languages

To add a new language to the verification list:

1. Open `scripts/verify_grammars.sh`
2. Locate the appropriate tier array (e.g., `TIER1_LANGUAGES`)
3. Add the language name to the array
4. Ensure the name matches the tree-sitter-language-pack convention

Example:

```bash
TIER1_LANGUAGES=(
  kotlin dart sql hcl graphql ruby solidity
  newlang  # Add new language here
)
```

### Language Naming Conventions

The script uses tree-sitter-language-pack naming conventions:

- Most languages use lowercase: `python`, `kotlin`, `rust`
- C# uses `csharp` (not `c_sharp` or `c-sharp`)
- C++ uses `cpp` (not `c++`)
- TypeScript uses `typescript` (not `ts`)

To verify the correct name for a language:

```python
from tree_sitter_language_pack import get_language
lang = get_language('language_name')
```

### Updating the Language List

When new parsers are added:

1. Update the appropriate tier array in `verify_grammars.sh`
2. Test locally: `./scripts/verify_grammars.sh --tier tierX --verbose`
3. Commit the changes
4. CI will automatically verify on next run

## CI/CD Integration

The script is integrated into GitHub Actions CI pipeline (`.github/workflows/ci.yml`):

- Runs as a parallel job alongside `lint` and `test`
- Gates the `build` job - build only proceeds if verification passes
- Uses `--verbose` flag for detailed CI logs
- Fails the pipeline if any grammar is missing

### Local CI Testing

Test the script as it runs in CI:

```bash
# Simulate CI environment
poetry install --no-interaction
./scripts/verify_grammars.sh --verbose
```

## Troubleshooting

### Grammar Not Found

**Error:**
```
Testing kotlin... ✗ FAILED
Language 'kotlin' grammar not found
```

**Solutions:**

1. **Check tree-sitter-language-pack version:**
   ```bash
   pip show tree-sitter-language-pack
   # Should be >= 0.7.2
   ```

2. **Update tree-sitter-language-pack:**
   ```bash
   pip install --upgrade tree-sitter-language-pack
   ```

3. **Verify language name:**
   ```python
   from tree_sitter_language_pack import get_language
   # Try different naming conventions
   get_language('kotlin')  # lowercase
   get_language('Kotlin')  # capitalized
   ```

4. **Check if grammar is available:**
   ```bash
   python3 -c "from tree_sitter_language_pack import list_languages; print(list_languages())"
   ```

### Script Permission Denied

**Error:**
```
bash: ./scripts/verify_grammars.sh: Permission denied
```

**Solution:**
```bash
chmod +x scripts/verify_grammars.sh
```

### Python Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'tree_sitter_language_pack'
```

**Solution:**
```bash
pip install tree-sitter-language-pack>=0.7.2
# or with poetry
poetry add tree-sitter-language-pack
```

### Script Fails in CI but Works Locally

**Common Causes:**

1. **Different Python versions:** CI uses Python 3.12, ensure local testing uses same version
2. **Cache issues:** CI may have stale dependencies, clear cache
3. **Poetry lock file:** Ensure `poetry.lock` is up to date

**Debug in CI:**
- Check the "Verify tree-sitter grammars" step logs
- Look for specific language failures
- Verify dependencies were installed correctly

## Examples

### Development Workflow

```bash
# Before implementing a Tier 1 parser
./scripts/verify_grammars.sh --tier tier1 --verbose

# Check specific language
./scripts/verify_grammars.sh --tier tier1 --verbose | grep kotlin

# Report all issues
./scripts/verify_grammars.sh --all --no-exit --verbose > grammar_report.txt
```

### CI/CD Workflow

The script automatically runs in CI on:
- Push to `main` or `development` branches
- Pull requests to `main`

View results in GitHub Actions → CI workflow → "verify-grammars" job

## Dependencies

- **Bash:** POSIX-compliant shell
- **Python 3.10+:** Required for tree-sitter-language-pack
- **tree-sitter-language-pack >= 0.7.2:** Provides grammar bindings

## Related Files

- **Implementation:** `scripts/verify_grammars.sh`
- **CI Configuration:** `.github/workflows/ci.yml`
- **Dependencies:** `pyproject.toml` (tree-sitter-language-pack)
- **PRD:** `.taskmaster/docs/prd.txt` (language expansion details)

## Support

For issues or questions:
1. Check this documentation
2. Review PRD: `.taskmaster/docs/prd.txt`
3. File an issue: [GitHub Issues](https://github.com/biostochastics/codeconcat/issues)

## Version History

- **v1.0.0** (2025-09-30): Initial implementation
  - Support for 4 tiers (40 languages total)
  - Tier-based verification
  - CI/CD integration
  - Comprehensive error reporting
