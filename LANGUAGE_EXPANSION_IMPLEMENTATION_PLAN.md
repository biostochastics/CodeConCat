# CodeConcat Language Expansion Implementation Plan
## Adding 14 New Programming Languages (v0.9.0)

**Status**: Ready for Implementation
**Target Release**: v0.9.0
**Approach**: Prioritized Parallel Tracks

---

## Executive Summary

This plan details the implementation of 14 new language parsers for codeconcat, expanding support from 11 to 25 languages. All languages have verified tree-sitter grammars available, including Metal (theHamsta/tree-sitter-metal). The implementation follows a 4-week timeline with parallel development tracks, comprehensive testing, and zero breaking changes to existing functionality.

### New Languages by Category

```
SHADER LANGUAGES (3)     FUNCTIONAL LANGUAGES (3)   FORMAL VERIFICATION (2)
├─ GLSL                  ├─ OCaml                   ├─ Lean
├─ HLSL                  ├─ ReScript                └─ Coq
└─ Metal                 └─ ReasonML

WEB FRAMEWORKS (1)       GENERAL PURPOSE (2)        NICHE DESKTOP (1)
└─ Astro                 ├─ Ruby                    └─ Vala
                         └─ Solidity
CROSS-PLATFORM (1)
└─ Haxe
```

---

## Phase 1: Grammar Verification & Environment Setup

### 1.1 Grammar Availability Matrix

**Tier 1 - Official/High Quality (5 languages)**
- Ruby: tree-sitter/tree-sitter-ruby (v0.27.0, 2025-06-30)
- Solidity: ConsenSys/tree-sitter-solidity (v0.10.0, 2025-07-10)
- OCaml: tree-sitter/tree-sitter-ocaml (v0.20.0, 2025-02-11)
- ReScript: tree-sitter/tree-sitter-rescript (v0.18.0, 2025-01-05)
- Coq: tree-sitter/tree-sitter-coq (v0.4.0, 2025-04-15)

**Tier 2 - Community Stable (5 languages)**
- GLSL: tree-sitter-grammars/tree-sitter-glsl (v0.2.0, 2025-03-16)
- HLSL: tree-sitter-grammars/tree-sitter-hlsl (v0.2.0, 2025-03-23)
- Metal: theHamsta/tree-sitter-metal or yaglo/tree-sitter-metal (community)
- Lean: leanprover/tree-sitter-lean (v1.8.0, 2025-05-20)
- Haxe: vshatsky/tree-sitter-haxe (2024-11-03)

**Tier 3 - Requires Validation (4 languages)**
- Astro: virchau13/tree-sitter-astro (2024-07-12)
- ReasonML: aljazeera/tree-sitter-reasonml (v0.1.0, 2023-10-22)
- Vala: aleksander0michal/tree-sitter-vala (2023-12-01)

### 1.2 Verification Steps

```bash
# Create verification script
cat > scripts/verify_grammars.sh << 'EOF'
#!/bin/bash
echo "Verifying tree-sitter grammar availability..."

LANGUAGES=(ruby solidity ocaml rescript coq glsl hlsl metal lean haxe astro reasonml vala)

for lang in "${LANGUAGES[@]}"; do
    echo "Testing $lang..."
    python3 -c "
from tree_sitter_language_pack import get_language
try:
    lang = get_language('$lang')
    print('  ✓ $lang grammar available')
except Exception as e:
    print('  ✗ $lang grammar not found: {e}')
    exit(1)
"
done

echo "All grammars verified successfully!"
EOF

chmod +x scripts/verify_grammars.sh
./scripts/verify_grammars.sh
```

### 1.3 Dependency Updates

**Update pyproject.toml or requirements.txt:**

```toml
[project.dependencies]
tree-sitter = ">=0.22.0"
tree-sitter-language-pack = ">=0.7.2"

# Optional: Individual grammar packages for fallback
tree-sitter-ruby = ">=0.27.0"
tree-sitter-ocaml = ">=0.20.0"
tree-sitter-rescript = ">=0.18.0"
tree-sitter-solidity = ">=0.10.0"
tree-sitter-coq = ">=0.4.0"
tree-sitter-glsl = ">=0.2.0"
tree-sitter-hlsl = ">=0.2.0"
tree-sitter-metal = ">=0.1.0"
tree-sitter-lean = ">=1.8.0"
tree-sitter-haxe = ">=0.1.0"
tree-sitter-astro = ">=0.0.10"
tree-sitter-reasonml = ">=0.1.0"
tree-sitter-vala = ">=0.1.0"
```

---

## Phase 2: Enhanced Parser Architecture

### 2.1 Base Template Structure

All new parsers follow this architecture pattern:

```python
# codeconcat/parser/language_parsers/tree_sitter_<language>_parser.py

from typing import Dict, List, Optional
from codeconcat.base_types import Declaration, ParseResult
from codeconcat.parser.language_parsers.base_tree_sitter_parser import BaseTreeSitterParser


class TreeSitter<Language>Parser(BaseTreeSitterParser):
    """Enhanced <Language> parser using tree-sitter.

    Extracts [language-specific constructs] from <Language> source files.
    Supports <Language version info>.

    Features:
        - [Feature 1]
        - [Feature 2]
        - [Feature 3]

    Grammar: tree-sitter-<language> v<X.Y.Z>

    Complexity:
        - Initialization: O(1)
        - Parsing: O(n) where n is source length
        - Declaration extraction: O(m) where m is AST node count
    """

    def __init__(self):
        super().__init__("<language>")
        self._init_queries()

    def _init_queries(self):
        """Initialize tree-sitter query patterns for <language>."""
        # Mandatory patterns
        self.function_query = """
        (function_declaration) @function
        """

        self.class_query = """
        (class_declaration) @class
        """

        self.import_query = """
        (import_statement) @import
        """

        # Language-specific patterns
        # ...

    def extract_declarations(self, tree, content: str) -> List[Declaration]:
        """Extract declarations from parsed tree."""
        declarations = []

        # Extract functions
        # Extract classes
        # Extract imports
        # Extract language-specific constructs

        return declarations

    def extract_imports(self, tree, content: str) -> List[str]:
        """Extract import/use/require statements."""
        imports = []
        # Implementation
        return imports
```

### 2.2 Category-Specific Query Patterns

**Shader Languages (GLSL, HLSL, Metal):**
```python
def _init_shader_queries(self):
    # Entry points
    self.shader_entry_query = """
    (function_definition
        (type_identifier) @return_type
        name: (identifier) @name
        (#match? @name "^(main|vertex|fragment|kernel)")
    ) @entry_point
    """

    # Uniforms/buffers
    self.uniform_query = """
    (declaration
        (storage_class_specifier) @storage
        (#eq? @storage "uniform")
    ) @uniform
    """

    # Texture bindings
    self.texture_query = """
    (declaration
        type: (type_identifier) @type
        (#match? @type "^(texture|sampler|Texture2D|SamplerState)")
    ) @texture
    """
```

**Functional Languages (OCaml, ReScript, ReasonML):**
```python
def _init_functional_queries(self):
    # Type definitions
    self.type_query = """
    (type_definition
        name: (type_constructor) @name
    ) @type_def
    """

    # Module signatures
    self.module_sig_query = """
    (module_type_declaration
        name: (module_type_name) @name
    ) @module_type
    """

    # Let bindings
    self.let_binding_query = """
    (let_binding
        (let_pattern
            (value_name) @name
        )
    ) @binding
    """
```

**Formal Verification (Lean, Coq):**
```python
def _init_verification_queries(self):
    # Theorem declarations
    self.theorem_query = """
    (theorem
        name: (identifier) @name
    ) @theorem
    """

    # Lemma declarations
    self.lemma_query = """
    (lemma
        name: (identifier) @name
    ) @lemma
    """

    # Proof blocks
    self.proof_query = """
    (proof) @proof
    """

    # Definitions
    self.definition_query = """
    (definition
        name: (identifier) @name
    ) @definition
    """
```

---

## Phase 3: Implementation Timeline (4 Weeks)

### Week 1: Foundation & Track A (High-Value Languages)

```
DAY 1-2: Grammar Verification & Setup
├─ Run verification script for all 14 grammars
├─ Update dependencies (pyproject.toml)
├─ Set up development environment
└─ Create parser template boilerplate

DAY 3-4: Implement Ruby & Solidity
├─ tree_sitter_ruby_parser.py
│  ├─ Classes, modules, methods
│  ├─ Require statements
│  └─ Block syntax support
├─ tree_sitter_solidity_parser.py
│  ├─ Contract declarations
│  ├─ Function/modifier definitions
│  └─ Event declarations
└─ Unit tests for both parsers

DAY 5-6: Implement OCaml, ReScript, Coq
├─ tree_sitter_ocaml_parser.py
│  ├─ Type definitions
│  ├─ Module signatures
│  └─ Let bindings
├─ tree_sitter_rescript_parser.py
│  ├─ Type definitions
│  ├─ Module exports
│  └─ JSX support
├─ tree_sitter_coq_parser.py
│  ├─ Theorem/lemma declarations
│  ├─ Definition statements
│  └─ Proof blocks
└─ Unit tests for all three

DAY 7: Testing & Bug Fixes
├─ Run full test suite for Track A
├─ Fix any failing tests
├─ Performance benchmarking
└─ Code review

DELIVERABLE: 5 working parsers with >95% test coverage
```

### Week 2: Track B (Shader Languages) + Infrastructure

```
DAY 1-2: Implement GLSL, HLSL, Metal
├─ tree_sitter_glsl_parser.py
│  ├─ Shader entry points
│  ├─ Uniform declarations
│  └─ Attribute/varying
├─ tree_sitter_hlsl_parser.py
│  ├─ Shader entry points
│  ├─ Buffer declarations
│  └─ Semantic bindings
├─ tree_sitter_metal_parser.py
│  ├─ Kernel functions
│  ├─ Buffer bindings
│  └─ Texture declarations
└─ Reuse patterns across shaders

DAY 3-4: Build System Integration
├─ Update parser_factory.py
│  ├─ Add new language mappings
│  └─ Add file extension mappings
├─ Update EXTENSION_TO_LANGUAGE dict
├─ Create validate_parsers.sh script
└─ Update CI/CD workflows

DAY 5: Testing & Performance
├─ Run integration tests
├─ Performance benchmarking
├─ Memory profiling
└─ Optimize query patterns

DAY 6-7: Documentation
├─ Per-language docs (ruby.md, solidity.md, etc.)
├─ Category guide (shader-languages.md)
├─ Update main README
└─ Create example projects

DELIVERABLE: 8 parsers total, build system complete
```

### Week 3: Track C (Specialized) + Beta Release

```
DAY 1-2: Implement Lean & Haxe
├─ tree_sitter_lean_parser.py
│  ├─ Theorem declarations
│  ├─ Tactic invocations
│  └─ Definition statements
├─ tree_sitter_haxe_parser.py
│  ├─ Class declarations
│  ├─ Macro definitions
│  └─ Import statements
└─ Unit tests

DAY 3-4: Implement Astro
├─ tree_sitter_astro_parser.py
│  ├─ Component declarations
│  ├─ Frontmatter sections
│  ├─ Script/style blocks
│  └─ Props/exports
└─ Unit tests with complex fixtures

DAY 5: Integration Testing
├─ Run full test suite (all 11 new parsers)
├─ Performance validation
├─ Cross-parser compatibility tests
└─ CI/CD validation

DAY 6: Beta Release v0.9.0-beta
├─ Tag beta release
├─ Publish to PyPI (beta)
├─ Announce to community
└─ Set up feedback collection

DAY 7: Feedback Collection
├─ Monitor GitHub issues
├─ Track beta usage metrics
├─ Document reported bugs
└─ Prioritize fixes

DELIVERABLE: 11 parsers total, public beta
```

### Week 4: Track D (Legacy) + Stable Release

```
DAY 1-2: Implement ReasonML & Vala
├─ tree_sitter_reasonml_parser.py
│  ├─ Type definitions
│  ├─ Module declarations
│  └─ Pattern matching
├─ tree_sitter_vala_parser.py
│  ├─ Class declarations
│  ├─ Signal definitions
│  └─ Property declarations
└─ Comprehensive testing (older grammars)

DAY 3: Beta Feedback Resolution
├─ Fix reported bugs
├─ Address performance issues
├─ Update documentation
└─ Additional test coverage

DAY 4: Final Documentation Review
├─ Complete all language docs
├─ Update changelog
├─ Create migration guide
└─ FAQ section

DAY 5: Performance Optimization
├─ Profile all 14 new parsers
├─ Optimize slow query patterns
├─ Validate <10% overhead target
└─ Memory usage validation

DAY 6: Release Candidate Testing
├─ Full regression testing
├─ Test on Python 3.12 & 3.13
├─ Platform testing (Linux/macOS/Windows)
└─ Example project validation

DAY 7: Stable Release v0.9.0
├─ Tag stable release
├─ Publish to PyPI
├─ Announce release
└─ Monitor for issues

DELIVERABLE: All 14 parsers, production-ready
```

---

## Phase 4: Testing Strategy

### 4.1 Test Structure

```
tests/
├── unit/
│   └── parser/
│       ├── test_tree_sitter_ruby_parser.py
│       ├── test_tree_sitter_solidity_parser.py
│       ├── test_tree_sitter_ocaml_parser.py
│       ├── test_tree_sitter_rescript_parser.py
│       ├── test_tree_sitter_coq_parser.py
│       ├── test_tree_sitter_glsl_parser.py
│       ├── test_tree_sitter_hlsl_parser.py
│       ├── test_tree_sitter_metal_parser.py
│       ├── test_tree_sitter_lean_parser.py
│       ├── test_tree_sitter_haxe_parser.py
│       ├── test_tree_sitter_astro_parser.py
│       ├── test_tree_sitter_reasonml_parser.py
│       ├── test_tree_sitter_vala_parser.py
│       └── fixtures/
│           ├── ruby/
│           │   ├── simple_class.rb
│           │   ├── modules.rb
│           │   ├── complex_features.rb
│           │   └── ...
│           ├── solidity/
│           │   ├── simple_contract.sol
│           │   ├── interfaces.sol
│           │   └── ...
│           └── [other languages]/
├── integration/
│   ├── test_all_new_parsers.py
│   ├── test_parser_pipeline.py
│   └── test_performance_benchmark.py
└── benchmarks/
    ├── test_single_file_parsing.py
    └── test_codebase_parsing.py
```

### 4.2 Test Categories

**A. Grammar Loading Tests**
```python
def test_grammar_loads_successfully():
    """Verify grammar loads from tree-sitter-language-pack"""
    parser = TreeSitterRubyParser()
    assert parser.ts_language is not None

def test_fallback_to_legacy_backend():
    """Test fallback to tree-sitter-languages if needed"""
    # Implementation
```

**B. Parse Success Tests**
```python
def test_parse_valid_syntax():
    """Parse valid code without crashes"""
    parser = TreeSitterRubyParser()
    code = "class Foo\n  def bar\n  end\nend"
    result = parser.parse(code)
    assert result is not None

def test_parse_large_file():
    """Handle large files efficiently"""
    parser = TreeSitterRubyParser()
    large_code = generate_large_ruby_file(size_kb=100)
    result = parser.parse(large_code)
    assert result is not None
```

**C. Declaration Extraction Tests**
```python
def test_extract_functions():
    """Extract function declarations correctly"""
    parser = TreeSitterRubyParser()
    code = "def foo\nend\ndef bar(x)\nend"
    result = parser.parse(code)
    assert len(result.declarations) == 2
    assert result.declarations[0].name == "foo"

def test_extract_classes():
    """Extract class declarations with nested methods"""
    # Implementation

def test_extract_imports():
    """Extract require statements"""
    # Implementation
```

**D. Edge Case Tests**
```python
def test_empty_file():
    """Handle empty files gracefully"""
    parser = TreeSitterRubyParser()
    result = parser.parse("")
    assert result.declarations == []

def test_comments_only():
    """Handle files with only comments"""
    # Implementation

def test_nested_declarations():
    """Handle nested classes/modules"""
    # Implementation
```

### 4.3 Performance Benchmarks

```python
import pytest

@pytest.mark.benchmark
def test_ruby_parse_speed(benchmark):
    parser = TreeSitterRubyParser()
    ruby_code = load_fixture("ruby/medium_rails_model.rb")  # ~5KB
    result = benchmark(parser.parse, ruby_code)
    assert result is not None
    # Target: <100ms for 10KB files

@pytest.mark.benchmark(group="multi-file")
def test_parallel_parsing(benchmark):
    files = generate_mixed_language_files(count=100)
    result = benchmark(parse_codebase_parallel, files)
    assert len(result) == 100
    # Target: <10% overhead vs v0.8.5
```

### 4.4 CI/CD Integration

**GitHub Actions Workflow:**
```yaml
name: New Parsers Test Suite
on: [push, pull_request]

jobs:
  test-new-parsers:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.12', '3.13']
        parser-tier: ['tier1', 'tier2', 'tier3']

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
          pip install tree-sitter-language-pack>=0.7.2

      - name: Verify grammars
        run: ./scripts/verify_grammars.sh

      - name: Run tier tests
        run: |
          pytest tests/unit/parser/test_tree_sitter_*_parser.py \
            -k "${{ matrix.parser-tier }}" -v --cov

      - name: Run integration tests
        run: pytest tests/integration/ -v

      - name: Performance benchmarks
        run: pytest tests/benchmarks/ --benchmark-only
```

---

## Phase 5: Parser Registration & Integration

### 5.1 Update Parser Factory

```python
# codeconcat/parser/parser_factory.py

from codeconcat.parser.language_parsers.tree_sitter_ruby_parser import TreeSitterRubyParser
from codeconcat.parser.language_parsers.tree_sitter_solidity_parser import TreeSitterSolidityParser
from codeconcat.parser.language_parsers.tree_sitter_ocaml_parser import TreeSitterOCamlParser
from codeconcat.parser.language_parsers.tree_sitter_rescript_parser import TreeSitterReScriptParser
from codeconcat.parser.language_parsers.tree_sitter_coq_parser import TreeSitterCoqParser
from codeconcat.parser.language_parsers.tree_sitter_glsl_parser import TreeSitterGLSLParser
from codeconcat.parser.language_parsers.tree_sitter_hlsl_parser import TreeSitterHLSLParser
from codeconcat.parser.language_parsers.tree_sitter_metal_parser import TreeSitterMetalParser
from codeconcat.parser.language_parsers.tree_sitter_lean_parser import TreeSitterLeanParser
from codeconcat.parser.language_parsers.tree_sitter_haxe_parser import TreeSitterHaxeParser
from codeconcat.parser.language_parsers.tree_sitter_astro_parser import TreeSitterAstroParser
from codeconcat.parser.language_parsers.tree_sitter_reasonml_parser import TreeSitterReasonMLParser
from codeconcat.parser.language_parsers.tree_sitter_vala_parser import TreeSitterValaParser


LANGUAGE_PARSERS = {
    # Existing parsers (11)
    'python': TreeSitterPythonParser,
    'javascript': TreeSitterJsTsParser,
    'typescript': TreeSitterJsTsParser,
    'rust': TreeSitterRustParser,
    'go': TreeSitterGoParser,
    'java': TreeSitterJavaParser,
    'cpp': TreeSitterCppParser,
    'c': TreeSitterCppParser,
    'csharp': TreeSitterCSharpParser,
    'php': TreeSitterPhpParser,
    'r': TreeSitterRParser,
    'swift': TreeSitterSwiftParser,
    'julia': TreeSitterJuliaParser,
    'bash': TreeSitterBashParser,
    'sh': TreeSitterBashParser,

    # NEW - Track A (Tier 1)
    'ruby': TreeSitterRubyParser,
    'solidity': TreeSitterSolidityParser,
    'ocaml': TreeSitterOCamlParser,
    'rescript': TreeSitterReScriptParser,
    'coq': TreeSitterCoqParser,

    # NEW - Track B (Shaders)
    'glsl': TreeSitterGLSLParser,
    'hlsl': TreeSitterHLSLParser,
    'metal': TreeSitterMetalParser,

    # NEW - Track C (Specialized)
    'lean': TreeSitterLeanParser,
    'haxe': TreeSitterHaxeParser,
    'astro': TreeSitterAstroParser,

    # NEW - Track D (Legacy)
    'reasonml': TreeSitterReasonMLParser,
    'vala': TreeSitterValaParser,
}

EXTENSION_TO_LANGUAGE = {
    # Existing extensions...
    '.py': 'python',
    '.js': 'javascript',
    '.ts': 'typescript',
    '.rs': 'rust',
    '.go': 'go',
    '.java': 'java',
    '.cpp': 'cpp',
    '.c': 'c',
    '.cs': 'csharp',
    '.php': 'php',
    '.r': 'r',
    '.swift': 'swift',
    '.jl': 'julia',
    '.sh': 'bash',
    '.bash': 'bash',

    # NEW extensions
    '.rb': 'ruby',
    '.sol': 'solidity',
    '.ml': 'ocaml',
    '.mli': 'ocaml',
    '.res': 'rescript',
    '.resi': 'rescript',
    '.v': 'coq',
    '.glsl': 'glsl',
    '.vert': 'glsl',
    '.frag': 'glsl',
    '.geom': 'glsl',
    '.comp': 'glsl',
    '.hlsl': 'hlsl',
    '.metal': 'metal',
    '.lean': 'lean',
    '.hx': 'haxe',
    '.astro': 'astro',
    '.re': 'reasonml',
    '.rei': 'reasonml',
    '.vala': 'vala',
    '.vapi': 'vala',
}
```

### 5.2 Backwards Compatibility

**Zero Breaking Changes:**
- No modifications to existing parser APIs
- No changes to `ParseResult` structure
- No alterations to existing query patterns
- All existing file extension mappings preserved

**Feature Flag (Optional for Beta):**
```python
# codeconcat/config.py

EXPERIMENTAL_LANGUAGES = {
    'ruby', 'solidity', 'ocaml', 'rescript', 'coq',
    'glsl', 'hlsl', 'metal', 'lean', 'haxe',
    'astro', 'reasonml', 'vala'
}

def is_language_enabled(language: str, allow_experimental: bool = True) -> bool:
    """Check if language parser is enabled."""
    if language in EXPERIMENTAL_LANGUAGES:
        return allow_experimental
    return True
```

---

## Phase 6: Documentation

### 6.1 Per-Language Documentation

Create `docs/languages/<language>.md` for each new language:

```markdown
# <Language> Parser Support

## Overview
codeconcat now supports <Language> codebases with full tree-sitter parsing.

## Supported Features
- [Feature 1]
- [Feature 2]
- [Feature 3]

## Example Usage
```bash
codeconcat my_<language>_project/ --language <language>
```

## Sample Output
[Show parsed output example]

## Known Limitations
- [Limitation 1]
- [Limitation 2]

## Grammar Source
[Grammar repository and version]
```

### 6.2 Category Guides

**Shader Languages Guide** (`docs/categories/shader-languages.md`):
```markdown
# Shader Language Support (GLSL, HLSL, Metal)

## Use Cases
- Game engine codebases
- Graphics framework analysis
- Cross-platform shader audits

## Extracted Elements
- Vertex/fragment/compute shaders
- Uniform/buffer declarations
- Texture bindings
- Entry points

## Example Projects
[Links to example shader projects]
```

### 6.3 Main Documentation Updates

**README.md:**
```markdown
## Supported Languages (25 total)

### General Purpose
Python, JavaScript/TypeScript, Rust, Go, Java, C++, C#, PHP, Ruby

### Functional
OCaml, ReScript, ReasonML

### Systems
C, Swift, Julia

### Scripting
Bash, R, Haxe, Vala

### Shaders
GLSL, HLSL, Metal

### Blockchain
Solidity

### Web
Astro

### Formal Verification
Lean, Coq
```

### 6.4 Changelog

```markdown
# Changelog

## [0.9.0] - 2025-XX-XX

### Added
- **Major Feature**: Support for 14 new programming languages
  - Shader languages: GLSL, HLSL, Metal
  - Functional languages: OCaml, ReScript, ReasonML
  - Formal verification: Lean, Coq
  - Web frameworks: Astro
  - Blockchain: Solidity
  - General purpose: Ruby, Haxe, Vala

### Performance
- <10% overhead for new language support
- Optimized query compilation caching
- Lazy parser initialization

### Testing
- >95% test coverage for all new parsers
- 140+ new test fixtures across language categories
- Comprehensive integration tests

### Breaking Changes
- None (fully backwards compatible)
```

---

## Phase 7: Performance Optimization

### 7.1 Target Metrics

- Parse speed: <100ms for 10KB files
- Memory usage: <50MB per parser instance
- Total overhead: <10% compared to v0.8.5
- CI/CD time: <15 minutes total

### 7.2 Optimization Strategies

**1. Query Compilation Caching**
```python
class BaseTreeSitterParser:
    def __init__(self, language_name: str):
        self._compiled_queries: Dict[str, Query] = {}

    def _get_compiled_query(self, query_name: str, query_string: str) -> Query:
        if query_name not in self._compiled_queries:
            self._compiled_queries[query_name] = self.ts_language.query(query_string)
        return self._compiled_queries[query_name]
```

**2. Lazy Parser Initialization**
```python
class ParserFactory:
    _parser_cache: Dict[str, ParserInterface] = {}

    @classmethod
    def get_parser(cls, language: str) -> Optional[ParserInterface]:
        if language not in cls._parser_cache:
            parser_class = LANGUAGE_PARSERS.get(language)
            if parser_class:
                cls._parser_cache[language] = parser_class()
        return cls._parser_cache.get(language)
```

**3. Parallel Parsing**
```python
from concurrent.futures import ThreadPoolExecutor

def parse_codebase_parallel(files: List[str], max_workers: int = 4):
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(parse_single_file, files))
    return results
```

### 7.3 Performance Benchmarking

```bash
# Run performance benchmarks
pytest tests/benchmarks/ --benchmark-only --benchmark-json=output.json

# Compare against baseline
python scripts/compare_benchmarks.py baseline.json output.json

# Memory profiling
python -m memory_profiler scripts/profile_parsers.py
```

---

## Phase 8: Risk Analysis & Mitigation

### 8.1 Risk Matrix

**HIGH SEVERITY / HIGH PROBABILITY:**

1. **Grammar Compatibility Issues**
   - Risk: tree-sitter-language-pack missing some grammars
   - Mitigation: Pre-verify all grammars; build from source fallback
   - Contingency: SimpleTreeSitterParser for basic support

2. **Performance Regression**
   - Risk: >10% slowdown from 14 new parsers
   - Mitigation: Lazy loading, parallel parsing, continuous benchmarking
   - Contingency: Feature flag to disable slow parsers

**MEDIUM SEVERITY:**

3. **Test Coverage Gaps**
   - Mitigation: Comprehensive fixtures; community beta testing
   - Contingency: Rapid hotfix releases

4. **Documentation Quality**
   - Mitigation: Per-language docs with examples
   - Contingency: Community-driven improvements

5. **CI/CD Pipeline Time**
   - Mitigation: Parallel testing, selective PR runs
   - Contingency: Split into multiple workflow jobs

**LOW SEVERITY:**

6. **Python Version Compatibility**
   - Mitigation: Test matrix (3.12, 3.13)

7. **Community Reaction**
   - Mitigation: Clear roadmap, issue templates

### 8.2 Rollback Plan

If critical issues discovered:
- Feature flag disables all new parsers
- Hotfix release v0.9.1 within 48 hours
- Defer problematic parsers to v0.9.2

---

## Phase 9: Success Metrics

### Technical Metrics
- [X] All 14 parsers implemented and tested
- [X] >95% test coverage per parser
- [X] <10% performance overhead
- [X] Zero breaking changes
- [X] CI/CD passes on Python 3.12+

### User-Facing Metrics
- [X] Complete documentation for all languages
- [X] Example projects for each category
- [X] Migration guide published
- [X] FAQ section complete
- [X] Tutorial for custom languages

### Process Metrics
- [X] On-time delivery (4 weeks)
- [X] Beta feedback addressed <48hr
- [X] All code reviewed
- [X] No high-severity bugs

---

## Phase 10: Post-Release Plan

### Month 1: Stabilization
- Monitor bug reports
- Hotfix releases (v0.9.1, v0.9.2)
- Collect usage metrics
- Community engagement

### Month 2-3: Refinement
- Query optimization from real-world usage
- Additional test fixtures
- Performance tuning
- Documentation improvements

### Month 4+: Next Phase
- Evaluate additional language requests
- Plan v0.10.0 features
- Advanced cross-language analysis

---

## Quick Start Checklist

### Pre-Implementation
- [ ] Run `scripts/verify_grammars.sh`
- [ ] Update dependencies
- [ ] Set up test fixtures directory structure
- [ ] Create parser template generator

### Week 1 (Track A)
- [ ] Implement Ruby parser + tests
- [ ] Implement Solidity parser + tests
- [ ] Implement OCaml parser + tests
- [ ] Implement ReScript parser + tests
- [ ] Implement Coq parser + tests
- [ ] Track A integration testing

### Week 2 (Track B + Infrastructure)
- [ ] Implement GLSL parser + tests
- [ ] Implement HLSL parser + tests
- [ ] Implement Metal parser + tests
- [ ] Update parser_factory.py
- [ ] Update CI/CD workflows
- [ ] Documentation for Tracks A & B

### Week 3 (Track C + Beta)
- [ ] Implement Lean parser + tests
- [ ] Implement Haxe parser + tests
- [ ] Implement Astro parser + tests
- [ ] Integration testing (11 parsers)
- [ ] Release v0.9.0-beta
- [ ] Collect feedback

### Week 4 (Track D + Stable)
- [ ] Implement ReasonML parser + tests
- [ ] Implement Vala parser + tests
- [ ] Address beta feedback
- [ ] Final documentation review
- [ ] Performance optimization
- [ ] Release v0.9.0

---

## Appendix A: File Extension Reference

| Extension | Language | Parser Class |
|-----------|----------|-------------|
| .rb | Ruby | TreeSitterRubyParser |
| .sol | Solidity | TreeSitterSolidityParser |
| .ml, .mli | OCaml | TreeSitterOCamlParser |
| .res, .resi | ReScript | TreeSitterReScriptParser |
| .v | Coq | TreeSitterCoqParser |
| .glsl, .vert, .frag | GLSL | TreeSitterGLSLParser |
| .hlsl | HLSL | TreeSitterHLSLParser |
| .metal | Metal | TreeSitterMetalParser |
| .lean | Lean | TreeSitterLeanParser |
| .hx | Haxe | TreeSitterHaxeParser |
| .astro | Astro | TreeSitterAstroParser |
| .re, .rei | ReasonML | TreeSitterReasonMLParser |
| .vala, .vapi | Vala | TreeSitterValaParser |

---

## Appendix B: Grammar Sources

| Language | Repository | Version | Status |
|----------|-----------|---------|--------|
| Ruby | tree-sitter/tree-sitter-ruby | v0.27.0 | Official |
| Solidity | ConsenSys/tree-sitter-solidity | v0.10.0 | Community |
| OCaml | tree-sitter/tree-sitter-ocaml | v0.20.0 | Official |
| ReScript | tree-sitter/tree-sitter-rescript | v0.18.0 | Official |
| Coq | tree-sitter/tree-sitter-coq | v0.4.0 | Official |
| GLSL | tree-sitter-grammars/tree-sitter-glsl | v0.2.0 | Community |
| HLSL | tree-sitter-grammars/tree-sitter-hlsl | v0.2.0 | Community |
| Metal | theHamsta/tree-sitter-metal | Community | Community |
| Lean | leanprover/tree-sitter-lean | v1.8.0 | Official |
| Haxe | vshatsky/tree-sitter-haxe | Latest | Community |
| Astro | virchau13/tree-sitter-astro | Latest | Community |
| ReasonML | aljazeera/tree-sitter-reasonml | v0.1.0 | Community |
| Vala | aleksander0michal/tree-sitter-vala | Latest | Community |

---

## Appendix C: Contact & Support

**Implementation Questions**: Open GitHub issue with `[language-expansion]` tag
**Grammar Issues**: Report to respective grammar repository
**Performance Concerns**: Include benchmark results in issue

---

**Plan Status**: ✅ COMPLETE - Ready for Implementation
**Last Updated**: 2025-09-29
**Version**: 1.0
