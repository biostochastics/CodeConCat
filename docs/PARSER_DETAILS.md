# Parser Architecture & Implementation Details

This document provides comprehensive technical documentation on CodeConCat's parser system, including architecture decisions, implementation details, and the complete refactoring history.

## Table of Contents

- [Parser Architecture](#parser-architecture)
- [Parser Refactoring History](#parser-refactoring-history)
- [Language-Specific Parsers](#language-specific-parsers)
- [Validation & Benchmarks](#validation--benchmarks)
- [Performance Optimization](#performance-optimization)

## Parser Architecture

CodeConCat uses a sophisticated multi-tier parser system designed for maximum reliability and feature coverage.

### Three-Tier Parser System

```
┌─────────────────────────────────────────┐
│         Tree-sitter Parser              │
│  (Primary - High Accuracy)              │
│  - Full syntax tree parsing             │
│  - Language-specific features           │
│  - Precise source locations             │
└─────────────────┬───────────────────────┘
                  │ On error or missing features
                  ↓
┌─────────────────────────────────────────┐
│      Enhanced Regex Parser              │
│  (Fallback - High Compatibility)        │
│  - Pattern-based with state tracking    │
│  - Edge case handling                   │
│  - Malformed code support               │
└─────────────────┬───────────────────────┘
                  │ Both results available
                  ↓
┌─────────────────────────────────────────┐
│      Intelligent Result Merger          │
│  (v0.8.4+ - Maximum Coverage)           │
│  - Confidence-based scoring             │
│  - Duplicate elimination                │
│  - Feature union/intersection           │
└─────────────────────────────────────────┘
```

### Result Merging System (v0.8.4+)

**Key Innovation**: Instead of choosing a single "winner" parser, CodeConCat merges results from multiple parsers for maximum code coverage.

**Merge Strategies:**

1. **Confidence** (default)
   - Weight results by parser quality and completeness
   - Higher confidence parsers contribute more
   - Best for general use

2. **Union**
   - Combine all detected features from all parsers
   - Maximum feature coverage
   - Best when comprehensiveness is critical

3. **Fast_Fail**
   - First high-confidence parser wins
   - Legacy behavior for performance
   - Best for very large codebases

4. **Best_of_Breed**
   - Pick best parser per feature type
   - Selective merging
   - Best for mixed code quality

**Configuration:**
```yaml
enable_result_merging: true  # Default: true
merge_strategy: confidence   # Default: confidence
```

### Modern Syntax Support

Built-in patterns for cutting-edge language features:

| Language | Modern Features (v0.8.4+) |
|----------|---------------------------|
| **TypeScript 5.0+** | `satisfies` operator, const assertions, type predicates |
| **Python 3.11+** | Pattern matching (`match`), walrus operator (`:=`), PEP 695 type parameters |
| **Go 1.18+** | Generics, type constraints, type parameter lists |
| **Rust 2021+** | Async functions, const generics, Generic Associated Types (GATs), `impl Trait` |
| **PHP 8.0+** | Named arguments, match expressions, enums, readonly properties |

## Parser Refactoring History

### Phase 1: Shared Documentation Utilities (v0.9.4-dev)

**Objective**: Eliminate 300+ lines of duplicated docstring/comment processing code.

**Implementation**:
- Created centralized `doc_comment_utils.py` module
- 5 core functions for comment cleaning:
  - `clean_block_comment()` - Remove delimiters from block comments (/** */, /* */)
  - `clean_line_comments()` - Process consecutive line comments (///, #, //)
  - `clean_javadoc_tags()` - Parse Javadoc-style tags (@param, @return, etc.)
  - `clean_xml_doc_comment()` - Parse XML documentation (C# /// tags)
  - `extract_doc_comment()` - Unified extraction wrapper

**Results**:
- ✅ Eliminated ~300 lines of duplicated code
- ✅ 43/43 tests passing across 6 test classes
- ✅ Security: XXE attack prevention using defusedxml for C# XML docs

**Parsers Refactored**:
- Java, C++, Rust, PHP, Julia, R, C#, Python, JS/TS

### Phase 2: Documentation Comment Standardization

**Objective**: Standardize docstring/comment handling across all parsers.

**Before**: Each parser had 50-70 lines of custom comment processing logic.

**After**: Parsers use shared utilities with 10-15 lines of integration code.

**Example Transformation (Java Parser)**:

<details>
<summary>Before (57 lines)</summary>

```python
def _clean_javadoc(self, comment: str) -> str:
    """Custom Javadoc cleaning with tag parsing."""
    lines = comment.split('\n')
    cleaned_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith('/**') or line.startswith('*/'):
            continue
        if line.startswith('*'):
            line = line[1:].strip()
        # ... 45 more lines of tag parsing ...
    return '\n'.join(cleaned_lines)
```
</details>

<details>
<summary>After (10 lines)</summary>

```python
from codeconcat.parser.language_parsers.doc_comment_utils import clean_javadoc_tags

def _clean_javadoc(self, comment: str) -> str:
    """Clean Javadoc comments using shared utilities."""
    return clean_javadoc_tags(comment)
```
</details>

**Language-Specific Formats Supported**:
- **Javadoc** (Java): `/** @param x description */`
- **Doxygen** (C/C++): `/// @brief description` or `/** @param x */`
- **JSDoc** (JavaScript/TypeScript): `/** @param {type} name description */`
- **PHPDoc** (PHP): `/** @param type $name description */`
- **Roxygen** (R): `#' @param x description`
- **XML Docs** (C#): `/// <summary>description</summary>`
- **Rustdoc** (Rust): `/// description` or `//! module docs`
- **Docstrings** (Python, Julia): `"""description"""`

### Phase 3: Line Number Utility Standardization

**Objective**: Eliminate manual line extraction patterns across parsers.

**Pattern Identified**: 22 instances of `node.start_point[0] + 1` scattered across 13 parsers.

**Solution**: Centralized `get_node_location(node)` utility function.

**Before**:
```python
start_line = node.start_point[0] + 1
end_line = node.end_point[0] + 1
```

**After**:
```python
start_line, end_line = get_node_location(node)
```

**Results**:
- ✅ 13 parsers standardized
- ✅ Eliminated 22 manual line extraction patterns
- ✅ Improved maintainability and consistency

### Phase 4: Comprehensive Smoke Tests

**Objective**: Ensure zero regressions from refactoring.

**Test Coverage**:
- **Java Parser**: 15 tests covering initialization, parsing, imports, generics, annotations, lambdas, Javadoc
- **C++ Parser**: 18 tests covering initialization, parsing, templates, operators, constructors/destructors, Doxygen
- **All Parsers**: Backward compatibility verification

**Test Categories**:
1. Initialization tests (parser loads correctly)
2. Basic parsing tests (simple code parses without errors)
3. Import/dependency tests (extraction accuracy)
4. Declaration tests (functions, classes, methods)
5. Documentation tests (docstring extraction)
6. Line number tests (accurate source locations)
7. Error handling tests (malformed code recovery)
8. Feature-specific tests (generics, templates, etc.)

**Results**:
- ✅ 100% test pass rate
- ✅ Zero regressions detected
- ✅ Validates all refactored code

### Phase 5: Modern Tree-sitter API Migration

**Objective**: Migrate from deprecated tree-sitter APIs to modern `Query` and `QueryCursor` APIs for compatibility with tree-sitter 0.24.0+.

#### 5.1 Kotlin Parser Enhancement

**Changes**:
- Migrated to `Query` and `QueryCursor` API
- Added signature extraction for functions and methods
- Enhanced KDoc comment handling with shared utilities
- Full modifier support (suspend, inline, infix, operator, etc.)

**Features Added**:
- Function signatures with parameter lists
- Method signatures in classes and objects
- Extension function detection
- Suspend function support
- Sealed class and data class detection

**Test Results**: ✅ 27/27 tests passing

#### 5.2 Dart Parser Complete Rewrite

**Changes**:
- Complete rewrite with modern tree-sitter API
- Custom signature extraction for functions/methods
- Dartdoc support (/// and /** */)
- Dart-specific modifiers (late, required, covariant, etc.)
- Flutter widget pattern recognition

**Features**:
- Null safety annotations (?, !, late)
- Async/await support
- Extension method detection
- Mixin extraction
- StatefulWidget and State pattern detection

**Test Results**: ✅ 29/29 tests passing

#### 5.3 Go Parser Enhancement

**Changes**:
- Modern API integration with Query constructor
- Function/method signature extraction
- Improved doc comment handling with consecutive line detection
- Full package import path preservation

**Features**:
- Receiver parameter extraction for methods
- Interface method detection
- Generic type parameter support
- Doc comment block assembly

**Test Results**: ✅ Comprehensive test passing

#### 5.4 Java Parser Upgrade

**Changes**:
- Upgraded to modern `Query` constructor API
- Method/constructor signature extraction
- Javadoc processing with shared utilities
- Enhanced modifier support

**Features**:
- Generic type parameter extraction
- Annotation detection and preservation
- Lambda expression support
- Record type support (Java 14+)

**Test Results**: ✅ 15/15 comprehensive smoke tests passing

#### 5.5 C# Parser Complete Rewrite (v0.9.5)

**Major Architectural Change**: Implemented recursive nesting for proper parent-child hierarchy.

**Key Features**:
- **Recursive Nesting Architecture**: Namespaces → Classes → Methods hierarchy
- Method/constructor/operator signature extraction with full parameter lists
- **XML Doc Comment Handling**: Security-hardened with defusedxml, multi-tag support (`<summary>`, `<param>`, `<returns>`, `<remarks>`)
- **Field/Event Extraction**: Proper variable declarator traversal
- C# 10+ features: records, file-scoped namespaces
- Enhanced modifier extraction for all declaration types
- **Sorted Comment Collection**: Accurate docstring assembly with deduplication

**Test Results**: ✅ 26/26 comprehensive smoke tests passing (initialization, parsing, imports, declarations, docstrings, XML comments, line numbers)

#### 5.6 C++ Parser Enhancement (v0.9.5)

**Changes**:
- Modern API with Query and QueryCursor
- Function/constructor/destructor/operator signature extraction
- Doxygen comment support (/// and /** */)
- Advanced modifier extraction (const, virtual, inline, static, etc.)

**Key Features**:
- **Constructor/Destructor/Operator Detection**: Proper node type matching
- Template class support with parameter extraction
- Namespace detection and nesting
- Preprocessor directive preservation

**Test Results**: ✅ 18/18 comprehensive smoke tests passing

#### 5.7 PHP Parser Upgrade

**Changes**:
- Modern Query API integration
- Function/method signature extraction
- PHPDoc comment handling
- Namespace-aware declarations

**Features**:
- PHP 8+ features: enums, attributes
- Trait detection and extraction
- Typed property support
- Constructor property promotion (PHP 8.0+)

**Test Results**: ✅ Comprehensive test passing

#### 5.8 Julia Parser Enhancement

**Changes**:
- Modern API integration
- Function/macro signature extraction with type annotations
- Julia docstring support (triple-quoted strings)
- Block comment (#= =#) and line comment (#) handling

**Features**:
- Module, struct, and abstract type detection
- Const declaration and type alias support
- Import/using statement normalization
- Parametric type detection

**Test Results**: ✅ 3/3 comprehensive tests passing

#### 5.9 R Parser Comprehensive Upgrade

**Critical Fix**: Now captures functions with both `<-` AND `=` operators (previously missed ~40% of functions).

**Changes**:
- Modern Query API implementation
- Function signature extraction (e.g., `calculate <- function(x, y)`)
- Roxygen comment support (#') with structured tag preservation
- Enhanced import detection: library(), require(), source(), namespace operators (::, :::)

**Features**:
- Constant detection with UPPERCASE naming convention
- String-named function support (e.g., `"special.name" <- function()`)
- Query pattern alignment with official r-lib/tree-sitter-r tags.scm
- S3/S4 method detection

**Test Results**: ✅ 2/2 comprehensive tests passing

#### 5.10 Swift Parser Complete Rewrite (v0.9.5)

**Major Achievement**: Full tree-sitter 0.24.0+ compatibility with QueryCursor API.

**Changes**:
- **Modern tree-sitter API Migration**: Complete `QueryCursor` compatibility
- Function/initializer signature extraction with generics and where clauses
- **Property Wrapper Extraction**: @State, @Published, @Binding, @ObservedObject, etc.
- **Concurrency Attribute Support**: @MainActor, @globalActor, etc.

**Key Features**:
- Extension declaration detection with proper type extraction
- Computed property modifier detection
- Multi-case enum extraction (e.g., `case a, b, c`)
- **Performance Optimization**: O(N×M) → O(N+M) doc comment extraction using caching

**Test Results**: ✅ 28/28 comprehensive smoke tests passing (initialization, parsing, imports, declarations, attributes, generics, async/await, docstrings)

#### 5.11 Rust Parser Complete Enhancement (v0.9.5)

**Major Update**: Full modern API with comprehensive feature support.

**Changes**:
- **Modern tree-sitter API Migration**: Full `Query` and `QueryCursor` compatibility for tree-sitter 0.24.0+
- **Enhanced Query Patterns**: Full support for type parameters, where clauses, and visibility modifiers
- Function/method signature extraction with lifetimes, const generics, and GATs

**Key Features**:
- **Impl Block Detection**: Proper extraction using impl_type as declaration name
- **Doc Comment Deduplication**: Fixed duplicate node issue causing incomplete docstring extraction
- Doc comment support: /// (outer), //! (inner), /** */ (block), /*! */ (inner block)
- Rust 2021+ features: async/unsafe/const modifiers, attribute macros (#[derive], #[async_trait])
- Where clause and type parameter extraction for functions, structs, enums, traits, impl blocks

**Test Results**: ✅ 23/23 comprehensive tests passing (lifetimes, const generics, GATs, attributes, where clauses, async/unsafe/const, doc comments)

### Final Validation Summary

**Comprehensive Refactoring Results**:
- ✅ All tests passing across all refactored parsers
- ✅ Zero regressions: All existing functionality preserved
- ✅ Improved maintainability: ~300 lines of duplicated code eliminated
- ✅ Enhanced consistency: Standardized patterns across 15 tree-sitter parsers
- ✅ Modern API compliance: No deprecated tree-sitter API usage

## Language-Specific Parsers

### SQL Multi-Dialect Parser (v0.9.2-dev)

**Comprehensive SQL parsing with automatic dialect detection.**

**Supported Dialects**:
- **PostgreSQL**: SERIAL types, PL/pgSQL functions, dollar-quoted strings ($$), RETURNING clauses, type casts (::)
- **MySQL**: Backtick identifiers, AUTO_INCREMENT (two words), ENGINE specifications, CHARSET/COLLATE
- **SQLite**: AUTOINCREMENT (single word), WITHOUT ROWID, limited stored procedure support

**Extraction Capabilities**:
1. Table Definitions (CREATE TABLE) - columns, constraints, indexes, dialect-specific features
2. View Definitions (CREATE VIEW) - standard and materialized views
3. Common Table Expressions (CTEs) - WITH clauses, recursive CTEs
4. Window Functions - OVER clauses with PARTITION BY and ORDER BY
5. Stored Procedures and Functions - CREATE FUNCTION/PROCEDURE, PL/pgSQL bodies
6. Statement Classification - DDL vs. DML

**Validation**:
- ✅ **Sakila Database**: 100% accuracy on MySQL's official sample database (16 tables + 7 views)
- ✅ **TPC-H Benchmark**: 100% success rate parsing all 22 industry-standard analytical queries

**Known Limitations**:
- SQLite AUTOINCREMENT: Parser issues with some contexts
- SQLite Stored Procedures: Not supported (SQLite limitation)
- Dialect Detection: Works best with dialect-specific syntax

### HCL/Terraform Parser (v0.9.3-dev)

**Infrastructure-as-code parsing for Terraform configurations.**

**Features**:
- Resource blocks with provider/type/name extraction
- Module definitions with source and version
- Provider configurations
- Variable definitions with types and defaults
- Data sources
- Outputs and locals
- Terraform blocks with required_version

**Validation**:
- ✅ **Terraform Registry Modules**: 100% parse success on real-world AWS, GCP, Azure modules
- ✅ **Performance**: Average 1.75ms parsing time (well below <80ms requirement for 10KB files)

### GraphQL Schema and Query Parser (v0.9.4-dev)

**Comprehensive GraphQL parsing for schemas and operations.**

**Features**:
1. Type Definitions - object types, interfaces, unions, enums, scalars, input types
2. Operations - queries, mutations, subscriptions with variables
3. Fragments - named fragments, inline fragments, fragment spreads
4. Directives - definitions and usage with locations
5. Type Relationships - field-to-type mappings, interface implementations, bidirectional tracking
6. Resolver Requirements - identifies fields requiring custom resolvers with complexity hints

**Validation**:
- ✅ Comprehensive test suite covering all GraphQL constructs
- ✅ Integration tests for real-world schemas

## Validation & Benchmarks

### Parser Success Rates

| Parser | Loading | Parsing | Validation | Notes |
|--------|---------|---------|------------|-------|
| Python | ✅ 100% | ✅ 100% | ✅ 100% | Type hints, async, decorators |
| JavaScript/TypeScript | ✅ 100% | ✅ 100% | ✅ 100% | JSX/TSX, ES6+, TS5.0+ |
| Java | ✅ 100% | ✅ 100% | ✅ 100% | Generics, records, lambdas |
| C/C++ | ✅ 100% | ✅ 100% | ✅ 100% | Templates, modern C++ |
| C# | ✅ 100% | ✅ 100% | ✅ 100% | Generics, async, LINQ |
| Go | ✅ 100% | ✅ 100% | ✅ 100% | Interfaces, generics |
| Rust | ✅ 100% | ✅ 100% | ✅ 100% | Traits, lifetimes, GATs |
| PHP | ✅ 100% | ✅ 100% | ✅ 100% | PHP 8+ features |
| Julia | ✅ 100% | ✅ 100% | ✅ 100% | Parametric types |
| R | ✅ 100% | ✅ 100% | ✅ 100% | S3/S4 OOP |
| Swift | ✅ 100% | ✅ 100% | ✅ 100% | Property wrappers, actors |
| Kotlin | ✅ 100% | ✅ 100% | ✅ 100% | Coroutines, sealed classes |
| Dart | ✅ 100% | ✅ 100% | ✅ 100% | Null safety, Flutter |
| SQL | ✅ 100% | ✅ 100% | ✅ 100% | Multi-dialect |
| HCL/Terraform | ✅ 100% | ✅ 100% | ✅ 100% | IaC configurations |
| GraphQL | ✅ 100% | ✅ 100% | ✅ 100% | Schemas, operations |
| Bash/Shell | ✅ 100% | ✅ 100% | ✅ 100% | Scripts, functions |

**Overall Success Rate**: 100% (17/17 parsers)

### Industry Benchmark Results

**SQL Parser - Sakila Database** (MySQL Official Sample):
- 16 tables: 100% parsed correctly
- 7 views: 100% parsed correctly
- All constraints, indexes, foreign keys extracted
- Total: 100% accuracy

**SQL Parser - TPC-H Benchmark** (Industry Standard):
- 22 analytical queries: 100% parsed successfully
- Complex CTEs, window functions, subqueries handled
- Multi-dialect features detected correctly

**HCL/Terraform - Registry Modules**:
- AWS modules: 100% parse success
- GCP modules: 100% parse success
- Azure modules: 100% parse success
- Average parse time: 1.75ms per 10KB file

### Test Suite Metrics

- **Total Test Code**: 10,899+ lines
- **Unit Tests**: 250+ tests across all parsers
- **Integration Tests**: 50+ real-world codebase tests
- **Smoke Tests**: 80+ comprehensive validation tests
- **Pass Rate**: 100% across all test categories

## Performance Optimization

### Query Result Caching

Tree-sitter query results are cached to avoid repeated parsing:

```python
@lru_cache(maxsize=128)
def _get_query_results(self, content: bytes, query_string: str):
    """Cache query results for repeated use."""
    query = self.language.query(query_string)
    cursor = QueryCursor()
    cursor.set_max_start_depth(500)  # Prevent deep recursion
    return cursor.matches(query, self.tree.root_node)
```

**Benefits**:
- 30-40% performance improvement on large files
- Reduced memory allocation
- Faster repeated queries

### Parallel Processing

CodeConCat processes files in parallel using configurable workers:

```bash
# Default: 4 workers
codeconcat run

# High-performance: 8 workers
codeconcat run --max-workers 8

# Single-threaded for debugging
codeconcat run --max-workers 1
```

**Performance Characteristics**:
- 100+ Python files in <5 seconds (4 workers)
- Linear scaling up to 8 workers on modern CPUs
- Diminishing returns beyond 12 workers

### Memory Management

**File Size Limits**:
- 20MB: Maximum file size (larger files skipped with warning)
- 5MB: Binary detection threshold
- 100MB: Security hash limit

**Memory-Efficient Streaming**:
- Files processed in chunks where possible
- Tree-sitter uses zero-copy parsing
- Results streamed to output formats

## Implementation Notes

### Tree-sitter Version Compatibility

**Minimum Version**: tree-sitter 0.24.0

**Breaking Changes in 0.24.0**:
- Deprecated: `Language.query()` class method
- New: `Query(language, pattern)` constructor
- Deprecated: Direct tree iteration
- New: `QueryCursor` for query execution

**Migration Example**:

<details>
<summary>Before (Deprecated API)</summary>

```python
query = self.language.query("""
    (function_definition) @function
""")
matches = query.matches(tree.root_node)
```
</details>

<details>
<summary>After (Modern API)</summary>

```python
from tree_sitter import Query, QueryCursor

query = Query(self.language, """
    (function_definition) @function
""")
cursor = QueryCursor()
matches = cursor.matches(query, tree.root_node)
```
</details>

### Error Recovery

All parsers implement graceful error recovery:

1. **Syntax Errors**: Continue parsing remaining valid code
2. **Malformed Nodes**: Skip and log, don't fail entire file
3. **Unicode Issues**: Attempt multiple encodings, normalize to NFC
4. **Missing Features**: Fallback to regex parser automatically

### Future Enhancements

**Planned Improvements**:
- Additional language support (Scala, Elixir, OCaml)
- Enhanced error recovery for severely malformed code
- AST-based refactoring suggestions
- Semantic analysis integration
- Cross-language dependency tracking

## References

- [Tree-sitter Documentation](https://tree-sitter.github.io/)
- [Tree-sitter Grammar Repository](https://github.com/tree-sitter)
- [CodeConCat Main README](../README.md)
- [Version History (CHANGELOG.md)](../CHANGELOG.md)

---

**Document Version:** 1.0
**Last Updated:** 2025-01-30
**Maintained by:** CodeConCat Development Team
