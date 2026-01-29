"""Modern syntax pattern registry for version-specific language features.

This module provides regex patterns for modern language features that may not
be supported by older parsers, enabling proper parsing of:
- TypeScript 5.0+ (satisfies, const assertions, type predicates)
- Python 3.11+ (pattern matching, walrus operator, union types, PEP 695)
- Go 1.18+ (generics)
- And other modern language constructs

Usage:
    from codeconcat.parser.shared.modern_patterns import MODERN_PATTERNS

    ts_patterns = MODERN_PATTERNS.get("typescript", {})
    if "satisfies" in ts_patterns:
        pattern = ts_patterns["satisfies"]
        matches = pattern.finditer(code)
"""

import re
from re import Pattern

# TypeScript 5.0+ Modern Features
TYPESCRIPT_MODERN_PATTERNS: dict[str, Pattern] = {
    # TypeScript 5.0: satisfies operator for type checking without widening
    # Example: const config = { ... } satisfies Config;
    "satisfies": re.compile(
        r"(?P<expr>[^=]+)\s+satisfies\s+(?P<type>[\w<>[\]|&,\s]+)", re.MULTILINE
    ),
    # const assertions (as const) - prevent type widening
    # Example: const colors = ['red', 'blue'] as const;
    "const_assertion": re.compile(r"(?P<expr>[^=]+)\s+as\s+const\s*[;\n]", re.MULTILINE),
    # Type predicates for user-defined type guards
    # Example: function isFish(pet: Fish | Bird): pet is Fish
    "type_predicate": re.compile(r":\s*(?P<param>\w+)\s+is\s+(?P<type>[\w<>[\]]+)", re.MULTILINE),
    # Const type parameters (TypeScript 5.0)
    # Example: function foo<const T>(...): T
    "const_type_param": re.compile(
        r"<\s*const\s+(?P<param>\w+)(?:\s+extends\s+[^>]+)?>\s*\(", re.MULTILINE
    ),
    # Template literal types
    # Example: type Color = `#${string}`;
    "template_literal_type": re.compile(r"type\s+\w+\s*=\s*`[^`]+`", re.MULTILINE),
    # Infer keyword in conditional types
    # Example: type ReturnType<T> = T extends (...args: any[]) => infer R ? R : any
    "infer_keyword": re.compile(r"infer\s+(?P<type_var>\w+)", re.MULTILINE),
}

# Python 3.11+ Modern Features
PYTHON_MODERN_PATTERNS: dict[str, Pattern] = {
    # Pattern matching (match/case) - PEP 634 (Python 3.10+)
    # Example: match value:
    #              case 1:
    #                  ...
    "pattern_matching": re.compile(r"^\s*match\s+(?P<expr>.+):\s*$", re.MULTILINE),
    # Case patterns for pattern matching
    "case_pattern": re.compile(r"^\s*case\s+(?P<pattern>[^:]+):\s*$", re.MULTILINE),
    # Walrus operator (assignment expressions) - PEP 572 (Python 3.8+)
    # Example: if (n := len(data)) > 10:
    "walrus_operator": re.compile(r"\(?\s*(?P<var>\w+)\s*:=\s*(?P<expr>[^)]+)\)?", re.MULTILINE),
    # Union type syntax with | - PEP 604 (Python 3.10+)
    # Example: def foo(x: int | str) -> bool | None:
    "type_union": re.compile(r":\s*(?P<types>[\w\s]+(?:\s*\|\s*[\w\s]+)+)", re.MULTILINE),
    # Type parameters (PEP 695) - Python 3.12+
    # Example: def foo[T](x: T) -> T:
    "type_params": re.compile(r"(?:def|class)\s+\w+\[(?P<params>[^\]]+)\]", re.MULTILINE),
    # Type alias statement - PEP 613 (Python 3.10+)
    # Example: type Point = tuple[float, float]
    "type_alias": re.compile(r"^\s*type\s+(?P<name>\w+)\s*=\s*(?P<type>.+)$", re.MULTILINE),
    # Structural pattern matching with guards
    # Example: case Point(x, y) if x == y:
    "case_with_guard": re.compile(
        r"^\s*case\s+(?P<pattern>[^:]+)\s+if\s+(?P<guard>[^:]+):\s*$", re.MULTILINE
    ),
    # Exception groups - PEP 654 (Python 3.11+)
    # Example: except* ValueError as e:
    "exception_group": re.compile(
        r"except\*\s+(?P<exc_types>[\w\s,|]+)(?:\s+as\s+(?P<var>\w+))?:", re.MULTILINE
    ),
}

# Go 1.18+ Modern Features (Generics)
GO_MODERN_PATTERNS: dict[str, Pattern] = {
    # Generic function declarations
    # Example: func Foo[T any](x T) T { ... }
    "generic_function": re.compile(
        r"func\s+(?P<name>\w+)\[(?P<type_params>[^\]]+)\]\s*\(", re.MULTILINE
    ),
    # Generic type declarations
    # Example: type List[T any] struct { ... }
    "generic_type": re.compile(
        r"type\s+(?P<name>\w+)\[(?P<type_params>[^\]]+)\]\s+(?:struct|interface)", re.MULTILINE
    ),
    # Type constraints
    # Example: type Number interface { int | float64 }
    "type_constraint": re.compile(
        r"type\s+\w+\s+interface\s*\{\s*(?P<types>[\w\s|]+)\s*\}", re.MULTILINE
    ),
    # Instantiated generic types
    # Example: var list List[int]
    "generic_instantiation": re.compile(r"(?P<type>\w+)\[(?P<type_args>[\w\s,]+)\]", re.MULTILINE),
}

# Rust Modern Features
RUST_MODERN_PATTERNS: dict[str, Pattern] = {
    # Async functions
    "async_function": re.compile(r"^\s*(?:pub\s+)?async\s+fn\s+(?P<name>\w+)", re.MULTILINE),
    # Impl Trait syntax
    "impl_trait": re.compile(
        r"impl\s+(?P<trait>\w+)(?:<[^>]+>)?\s+for\s+(?P<type>\w+)", re.MULTILINE
    ),
    # Const generics (Rust 1.51+)
    # Example: struct Array<T, const N: usize> { ... }
    "const_generics": re.compile(
        r"<[^>]*const\s+(?P<name>\w+):\s*(?P<type>\w+)[^>]*>", re.MULTILINE
    ),
    # Async blocks
    "async_block": re.compile(r"async\s+(?:move\s+)?\{", re.MULTILINE),
}

# PHP Modern Features (PHP 8.0+)
PHP_MODERN_PATTERNS: dict[str, Pattern] = {
    # Named arguments (PHP 8.0+)
    # Example: foo(param: 'value')
    "named_arguments": re.compile(r"(?P<name>\w+):\s*(?P<value>[^,)]+)", re.MULTILINE),
    # Union types (PHP 8.0+)
    # Example: function foo(int|string $x): bool|null
    "union_types": re.compile(r":\s*(?P<types>[\w\\]+(?:\|[\w\\]+)+)", re.MULTILINE),
    # Match expression (PHP 8.0+)
    # Example: $result = match($x) { ... };
    "match_expression": re.compile(r"match\s*\(\s*(?P<expr>[^)]+)\s*\)\s*\{", re.MULTILINE),
    # Constructor property promotion (PHP 8.0+)
    # Example: public function __construct(private string $name)
    "constructor_promotion": re.compile(
        r"__construct\s*\([^)]*(?:public|private|protected)\s+(?:\w+\s+)?\$\w+", re.MULTILINE
    ),
    # Readonly properties (PHP 8.1+)
    "readonly_property": re.compile(
        r"readonly\s+(?:public|private|protected)\s+(?P<type>[\w\\|]+)\s+\$(?P<name>\w+)",
        re.MULTILINE,
    ),
    # Enums (PHP 8.1+)
    "enum": re.compile(r"^\s*enum\s+(?P<name>\w+)(?:\s*:\s*(?P<type>\w+))?\s*\{", re.MULTILINE),
}

# JavaScript/TypeScript Common Modern Features
JS_TS_MODERN_PATTERNS: dict[str, Pattern] = {
    # Optional chaining (?.)
    # Example: obj?.prop?.method?.()
    "optional_chaining": re.compile(r"(?P<object>\w+)\?\.", re.MULTILINE),
    # Nullish coalescing (??)
    # Example: value ?? defaultValue
    "nullish_coalescing": re.compile(r"(?P<expr>[^?]+)\?\?\s*(?P<default>[^;]+)", re.MULTILINE),
    # Dynamic import
    # Example: const module = await import('./module.js');
    "dynamic_import": re.compile(r"import\s*\(\s*(?P<path>['\"][^'\"]+['\"])\s*\)", re.MULTILINE),
    # Top-level await
    "top_level_await": re.compile(r"^\s*await\s+", re.MULTILINE),
    # Private class fields (#field)
    "private_field": re.compile(r"#(?P<name>\w+)", re.MULTILINE),
}

# Master pattern registry
MODERN_PATTERNS: dict[str, dict[str, Pattern]] = {
    "typescript": {**TYPESCRIPT_MODERN_PATTERNS, **JS_TS_MODERN_PATTERNS},
    "javascript": JS_TS_MODERN_PATTERNS,
    "python": PYTHON_MODERN_PATTERNS,
    "go": GO_MODERN_PATTERNS,
    "rust": RUST_MODERN_PATTERNS,
    "php": PHP_MODERN_PATTERNS,
}


def get_modern_patterns(language: str) -> dict[str, Pattern]:
    """Get modern syntax patterns for a specific language.

    Args:
        language: Programming language identifier (case-insensitive)

    Returns:
        Dictionary of pattern name to compiled regex pattern

    Example:
        >>> patterns = get_modern_patterns("python")
        >>> if "pattern_matching" in patterns:
        ...     matches = patterns["pattern_matching"].finditer(code)
    """
    return MODERN_PATTERNS.get(language.lower(), {})


def check_modern_syntax(code: str, language: str) -> dict[str, int]:
    """Check which modern syntax features are present in code.

    Args:
        code: Source code to analyze
        language: Programming language identifier

    Returns:
        Dictionary mapping feature name to occurrence count

    Example:
        >>> code = "def foo[T](x: T) -> T: ..."
        >>> features = check_modern_syntax(code, "python")
        >>> features["type_params"]  # 1
    """
    patterns = get_modern_patterns(language)
    features = {}

    for feature_name, pattern in patterns.items():
        matches = list(pattern.finditer(code))
        if matches:
            features[feature_name] = len(matches)

    return features
