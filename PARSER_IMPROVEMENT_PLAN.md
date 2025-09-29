# CodeConcat Parser Improvement Implementation Plan

## Executive Summary
Comprehensive plan addressing 14 critical parser improvements across Enhanced Parsers, Tree-Sitter Parsers, and Pipeline & Tooling. Timeline: 4 weeks with 2 developers.

**Key Outcomes:**
- 30% performance improvement via query caching
- 500+ lines of duplicate code eliminated
- Modern syntax support (TypeScript 5.0, Python 3.11+)
- Graceful degradation with quality metrics
- Configurable per-language parser preferences

---

## Current State Analysis

### Architecture Overview
- **10 Enhanced Parsers**: Python, C#, R, PHP, JS/TS, Rust, C-family, Julia, Go
- **11 Tree-Sitter Parsers**: Above + Java, Swift, C++
- **Pipeline**: `unified_pipeline.py` (currently picks single winner)

### Critical Issues Identified
1. ❌ Tree-sitter parsers bypass `_get_compiled_query` caching
2. ❌ 500+ lines of duplicated comment extraction logic
3. ❌ No shared infrastructure components
4. ❌ Pipeline picks single winner instead of merging results
5. ❌ Missing modern syntax support (TS generics, Python 3.11)
6. ❌ No quality metrics for fallback decisions
7. ❌ Inadequate error recovery on parse failures

### Good News
✅ ParseResult already has most required fields:
- `missed_features: list[str]`
- `parser_quality: str` ("full", "partial", "basic")
- `degraded: bool`
- `error: str | None`
- `engine_used: str`

Only need to add:
- `confidence_score: Optional[float]`
- `parser_type: Optional[str]`

---

## Implementation Roadmap

## 🚀 PHASE 0: Quick Wins (Day 1-2)

### Day 1: Tree-Sitter Caching Fix
**Priority: CRITICAL** - 30% performance gain, isolated change

```python
# In base_tree_sitter_parser.py
class BaseTreeSitterParser:
    def __init__(self):
        self._query_cache = {}

    def parse(self, content: str, file_path: str) -> ParseResult:
        # ALWAYS use cached queries
        query = self._get_compiled_query()  # Never self.ts_language.query()
        # ...existing parse logic...
```

### Day 2: Performance Monitoring Baseline
```python
@dataclass
class ParserMetrics:
    parse_time_ms: float
    memory_usage_mb: float
    cache_hit_rate: float
    confidence_score: float
    features_detected: int
```

**Deploy both with feature flag for immediate validation**

---

## 📦 PHASE 1: Foundation (Week 1)

### 1.1 Extend ParseResult (Day 3)
```python
# codeconcat/base_types.py
@dataclass
class ParseResult:
    # Existing fields remain
    declarations: List[Declaration]
    imports: List[Import]
    missed_features: List[str]
    parser_quality: str
    degraded: bool
    error: Optional[str]
    engine_used: str

    # NEW: Add backward-compatible fields
    confidence_score: Optional[float] = None  # 0.0-1.0 for merger decisions
    parser_type: Optional[str] = None  # "tree-sitter", "enhanced", "simple"
```

### 1.2 Shared Infrastructure (Day 4-5)
Create `codeconcat/parser/shared/` directory:

#### comment_extractor.py
```python
class CommentExtractor:
    """Unified comment/docstring extraction for all languages"""

    def extract_pre_declaration_comments(
        self,
        lines: List[str],
        declaration_line: int,
        language: str
    ) -> Optional[str]:
        """Extract comments immediately before a declaration"""
        comment_patterns = {
            "python": r'^\s*#|^\s*"""',
            "javascript": r'^\s*//|^\s*/\*',
            "go": r'^\s*//',
            # ...more patterns
        }
        # Unified extraction logic here
```

#### block_walker.py
```python
class BlockWalker:
    """Reusable AST/block traversal with scope tracking"""

    def walk_blocks(
        self,
        content: str,
        language_hooks: LanguageHooks,
        callback: Callable
    ) -> List[Declaration]:
        """Walk code blocks with language-specific hooks"""

    def track_scope(self, line: str) -> ScopeChange:
        """Track indentation/bracket-based scope changes"""
```

#### modern_patterns.py
```python
MODERN_PATTERNS = {
    "typescript": {
        "generic_function": r"function\s+(\w+)\s*<([^>]+)>\s*\([^)]*\)",
        "type_predicate": r":\s*\w+\s+is\s+\w+",
        "const_assertion": r"as\s+const\s*[;\n]",
        "satisfies": r"\s+satisfies\s+\w+",
    },
    "python": {
        "pattern_matching": r"match\s+(.+):\s*\n",
        "walrus_operator": r"(\w+)\s*:=\s*(.+)",
        "type_union": r":\s*(\w+)\s*\|\s*(\w+)",
        "type_params": r"def\s+\w+\[([^\]]+)\]",  # PEP 695
    }
}
```

### 1.3 Shadow Mode Infrastructure (Day 5)
```python
class ShadowModeRunner:
    """Run new pipeline alongside old for comparison"""

    def compare_pipelines(self, content: str, file_path: str):
        old_result = self.old_pipeline.parse(content, file_path)
        new_result = self.new_pipeline.parse(content, file_path)

        metrics = {
            "quality_delta": new_result.confidence_score - old_result.confidence_score,
            "declarations_matched": len(set(new_result.declarations) & set(old_result.declarations)),
            "new_features_found": len(new_result.declarations) - len(old_result.declarations),
        }

        if metrics["quality_delta"] < -0.05:  # 5% quality drop
            self.trigger_rollback_alert()
```

---

## 🔧 PHASE 2: Parser Modernization (Week 2-3)

### 2.1 Tree-Sitter Updates (Week 2)

#### Captures Handling Update
```python
# Support both old and new Tree-sitter Python API
def parse_captures(self, query, root_node):
    captures = query.captures(root_node)

    for capture in captures:
        if isinstance(capture, tuple):
            node, capture_name = capture  # New API
        else:
            # Legacy fallback
            node = capture.node
            capture_name = capture.name

        yield node, capture_name
```

#### Structured Error Recovery
```python
def _handle_parse_errors(self, root_node, content):
    if root_node.has_error:
        # Log error details for monitoring
        self.metrics.parse_errors += 1

        # Try SimpleTreeSitterParser as fallback
        simple_parser = SimpleTreeSitterParser()
        fallback_result = simple_parser.parse(content)
        fallback_result.parser_quality = "fallback"
        fallback_result.confidence_score = 0.3

        # Try to salvage partial results
        partial_nodes = self._extract_valid_subtrees(root_node)
        if partial_nodes:
            fallback_result.declarations.extend(partial_nodes)
            fallback_result.confidence_score = 0.5

        return fallback_result
```

#### Extended Queries for Zero-Declaration Languages
```scheme
; TypeScript ambient declarations
(ambient_declaration
  (function_signature
    name: (identifier) @function.name))

; PHP traits
(trait_declaration
  name: (name) @class.name)

; C# partial classes
(partial_class_declaration
  name: (identifier) @class.name)

; R S4 classes
(call_expression
  function: (identifier) @_setClass
  (#eq? @_setClass "setClass")
  arguments: (argument_list
    (string) @class.name))
```

### 2.2 Enhanced Parser Integration (Week 3)

#### AST-Assisted Fallback for Python
```python
class EnhancedPythonParser:
    def parse_with_ast_fallback(self, content: str):
        try:
            # Try AST parsing for accurate structure
            tree = ast.parse(content)
            declarations = self._extract_from_ast(tree)
            return ParseResult(
                declarations=declarations,
                parser_quality="full",
                confidence_score=0.9,
                parser_type="ast"
            )
        except SyntaxError:
            # Fall back to regex patterns
            return self.parse_with_patterns(content)
```

---

## 🔄 PHASE 3: Pipeline Integration (Week 4)

### 3.1 Intelligent Result Merger

```python
class ResultMerger:
    """Merge results from multiple parsers intelligently"""

    def merge_parse_results(
        self,
        tree_sitter_result: ParseResult,
        enhanced_result: ParseResult,
        strategy: MergeStrategy = MergeStrategy.CONFIDENCE_WEIGHTED
    ) -> ParseResult:

        if strategy == MergeStrategy.CONFIDENCE_WEIGHTED:
            if tree_sitter_result.confidence_score > 0.8:
                base = tree_sitter_result
                supplement = enhanced_result
            else:
                base = enhanced_result
                supplement = tree_sitter_result

        # Merge unique declarations
        seen_signatures = {self._get_signature(d) for d in base.declarations}
        for decl in supplement.declarations:
            if self._get_signature(decl) not in seen_signatures:
                base.declarations.append(decl)
                base.missed_features.remove(decl.kind) if decl.kind in base.missed_features else None

        # Update confidence
        base.confidence_score = max(base.confidence_score,
                                   supplement.confidence_score * 0.8)

        return base
```

### 3.2 Configuration System

```python
# In codeconcat_config.py
@dataclass
class ParserConfig:
    """Per-language parser configuration"""

    parser_preferences: Dict[str, str] = field(default_factory=lambda: {
        "python": "tree-sitter",      # Best for Python
        "typescript": "enhanced",      # Better generics support
        "javascript": "tree-sitter",   # Fast and accurate
        "go": "tree-sitter",          # Excellent Go support
        "rust": "tree-sitter",        # Complex syntax
        "php": "enhanced",            # Better for mixed HTML/PHP
    })

    merge_strategies: Dict[str, MergeStrategy] = field(default_factory=lambda: {
        "default": MergeStrategy.CONFIDENCE_WEIGHTED,
        "typescript": MergeStrategy.FEATURE_UNION,  # Get all features
        "python": MergeStrategy.FAST_FAIL,         # Tree-sitter usually wins
    })

    quality_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "min_confidence": 0.5,
        "rollback_threshold": 0.05,  # 5% quality drop triggers rollback
    })
```

### 3.3 Comprehensive Test Suite

```python
class ParserTestSuite:
    """Comprehensive parser testing framework"""

    def test_modern_syntax(self):
        """Test TypeScript 5.0, Python 3.11+ features"""

        # TypeScript generics
        ts_code = """
        function identity<T extends string>(arg: T): T {
            return arg;
        }
        const result = identity("hello") satisfies string;
        """

        # Python 3.11 pattern matching
        py_code = """
        def process[T](data: list[T]) -> T | None:
            match data:
                case []:
                    return None
                case [first, *rest]:
                    return first
        """

        self.assert_all_features_detected(ts_code, py_code)

    def differential_testing(self):
        """Compare old vs new pipeline outputs"""
        for test_file in self.test_corpus:
            old_result = self.old_pipeline.parse(test_file)
            new_result = self.new_pipeline.parse(test_file)

            # Allow improvements but flag regressions
            if len(new_result.declarations) < len(old_result.declarations):
                self.flag_regression(test_file)
```

---

## 🎯 Success Metrics

### Performance Targets
- ✅ 30% performance improvement via caching
- ✅ < 100ms parse time for average file (1000 lines)
- ✅ < 50MB memory usage per parser instance

### Quality Targets
- ✅ 95% declaration detection accuracy
- ✅ Zero code duplication in shared components
- ✅ 100% backward compatibility
- ✅ Support for all modern syntax features

### Operational Targets
- ✅ < 5% quality regression threshold
- ✅ 100% test coverage for new code
- ✅ Shadow mode validation for 1 week
- ✅ Rollback capability within 5 minutes

---

## ⚠️ Risk Mitigation

### High Risk: Tree-sitter API Breaking Changes
**Mitigation:**
- Adapter pattern with version detection
- Maintain compatibility layer for 2 versions
- Automated API compatibility tests

**Fallback:**
```python
class TreeSitterAdapter:
    def __init__(self):
        self.api_version = self._detect_api_version()

    def get_captures(self, query, node):
        if self.api_version >= (0, 20, 0):
            return self._new_api_captures(query, node)
        else:
            return self._legacy_captures(query, node)
```

### Medium Risk: Performance Regression
**Mitigation:**
- Continuous performance monitoring
- A/B testing with subset of users
- Profile-guided optimization

**Rollback Criteria:**
- > 5% quality drop → automatic rollback
- > 20% performance degradation → investigate
- User complaints > threshold → review

### Low Risk: Test Maintenance
**Mitigation:**
- Automated fixture generation
- Property-based testing
- Golden test set from real projects

---

## 📋 Implementation Checklist

### Week 0 (Prep)
- [ ] Set up performance monitoring
- [ ] Create test corpus from real projects
- [ ] Configure feature flags
- [ ] Set up shadow mode infrastructure

### Week 1 (Foundation)
- [ ] Day 1: Tree-sitter caching fix
- [ ] Day 2: Performance baseline
- [ ] Day 3: ParseResult extension
- [ ] Day 4-5: Shared infrastructure

### Week 2 (Tree-Sitter)
- [ ] Update captures handling
- [ ] Implement error recovery
- [ ] Extend queries for all languages
- [ ] Add doc comment captures

### Week 3 (Enhanced Parsers)
- [ ] Integrate shared helpers
- [ ] Add AST fallbacks
- [ ] Expand pattern library
- [ ] Remove duplicate code

### Week 4 (Integration)
- [ ] Implement result merger
- [ ] Add configuration system
- [ ] Complete test suite
- [ ] Shadow mode validation

### Week 5 (Deployment)
- [ ] Gradual rollout (10% → 50% → 100%)
- [ ] Monitor metrics
- [ ] Gather feedback
- [ ] Document migration

---

## 📚 Appendix

### A. Merge Strategy Algorithms

```python
class MergeStrategy(Enum):
    CONFIDENCE_WEIGHTED = "confidence"  # Weight by parser confidence
    FEATURE_UNION = "union"            # Union all detected features
    MAJORITY_VOTE = "majority"         # Consensus on conflicts
    FAST_FAIL = "fast_fail"           # First high-confidence wins

    def merge(self, results: List[ParseResult]) -> ParseResult:
        if self == MergeStrategy.CONFIDENCE_WEIGHTED:
            return self._weighted_merge(results)
        elif self == MergeStrategy.FEATURE_UNION:
            return self._union_merge(results)
        # ...etc
```

### B. Performance Monitoring Dashboard

```python
@dataclass
class ParserDashboard:
    """Real-time parser performance metrics"""

    # Performance
    avg_parse_time_ms: float
    p95_parse_time_ms: float
    cache_hit_rate: float

    # Quality
    avg_confidence_score: float
    declaration_detection_rate: float
    error_recovery_rate: float

    # Health
    active_parsers: int
    failed_parses_per_hour: int
    rollback_triggered: bool
```

### C. Migration Guide

For existing users:
1. No breaking changes - all existing code continues to work
2. New quality metrics available but optional
3. Performance improvements automatic
4. Configure parser preferences if desired
5. Monitor shadow mode results for validation

---

## Team & Timeline

**Team Requirements:**
- 2 Senior Engineers (parser expertise)
- 1 QA Engineer (test suite)
- Part-time: DevOps (monitoring setup)

**Critical Path:**
1. Week 0: Tree-sitter caching (immediate win)
2. Week 1: Foundation (enables everything else)
3. Week 2-3: Parser updates (parallel work possible)
4. Week 4: Integration (requires previous phases)

**Total Duration:** 4 weeks active development + 1 week validation

---

*Document Version: 1.0*
*Last Updated: 2025-09-28*
*Status: Ready for Implementation*
