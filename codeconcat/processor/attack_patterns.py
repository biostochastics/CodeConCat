"""
Comprehensive Attack Pattern Detection for CodeConCat.

This module implements attack patterns for detecting vulnerabilities and malicious code
across the languages supported by CodeConCat: C/C++, Python, R, Julia, Go, PHP, Rust, 
and JavaScript/TypeScript.
"""

import re
from typing import Dict, List, Pattern, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class Severity(Enum):
    """Severity levels for security findings."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"
    INFO = "INFO"


@dataclass
class SecurityPattern:
    """Represents a security pattern to detect."""
    name: str
    pattern: Pattern[str]
    severity: Severity
    message: str
    languages: List[str]
    cwe_id: Optional[str] = None


# C/C++ Attack Patterns
C_PATTERNS = [
    SecurityPattern(
        name="buffer_overflow_strcpy",
        pattern=re.compile(r'\b(strcpy|strcat|sprintf|gets)\s*\(', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Dangerous function that can cause buffer overflow",
        languages=["c", "cpp"],
        cwe_id="CWE-120"
    ),
    SecurityPattern(
        name="format_string_vulnerability",
        pattern=re.compile(r'(printf|fprintf|sprintf|syslog)\s*\(\s*[^"]\w+\s*\)', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Potential format string vulnerability",
        languages=["c", "cpp"],
        cwe_id="CWE-134"
    ),
    SecurityPattern(
        name="command_injection_c",
        pattern=re.compile(r'\b(system|popen|execl|execle|execlp|execv|execvp)\s*\([^"]+\)', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Potential OS command injection",
        languages=["c", "cpp"],
        cwe_id="CWE-78"
    ),
    SecurityPattern(
        name="use_after_free",
        pattern=re.compile(r'free\s*\([^)]+\).*?\n.*?(?:->|\*)', re.MULTILINE | re.DOTALL),
        severity=Severity.HIGH,
        message="Potential use after free vulnerability",
        languages=["c", "cpp"],
        cwe_id="CWE-416"
    ),
    SecurityPattern(
        name="integer_overflow",
        pattern=re.compile(r'(malloc|calloc|realloc)\s*\([^)]*[+*][^)]*\)', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Potential integer overflow in memory allocation",
        languages=["c", "cpp"],
        cwe_id="CWE-190"
    ),
]

# Python Attack Patterns
PYTHON_PATTERNS = [
    SecurityPattern(
        name="python_eval_injection",
        pattern=re.compile(r'\beval\s*\([^"\']*(?:user_input|request\.|input\(|argv|f["\']|%|\+)[^)]*\)', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Dangerous use of eval() with potential code injection",
        languages=["python"],
        cwe_id="CWE-95"
    ),
    SecurityPattern(
        name="python_exec_injection",
        pattern=re.compile(r'\bexec\s*\([^"\']*(?:user_|input|another_|request\.|argv|f["\']|%|\+)[^)]*\)', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Dangerous use of exec() with potential code injection",
        languages=["python"],
        cwe_id="CWE-95"
    ),
    SecurityPattern(
        name="python_pickle_deserialization",
        pattern=re.compile(r'pickle\.(loads?|Unpickler)\s*\(', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Insecure deserialization using pickle",
        languages=["python"],
        cwe_id="CWE-502"
    ),
    SecurityPattern(
        name="python_yaml_load",
        pattern=re.compile(r'yaml\.load\s*\([^,)]+\)', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Unsafe yaml.load() - use yaml.safe_load() instead",
        languages=["python"],
        cwe_id="CWE-502"
    ),
    SecurityPattern(
        name="python_sql_injection",
        pattern=re.compile(r'(execute|executemany|query)\s*\([^)]*["\'].*?["\'].*?[+%].*?(user_|request\.|input\(|argv|\$|f["\'])', re.IGNORECASE | re.DOTALL),
        severity=Severity.CRITICAL,
        message="Potential SQL injection via string concatenation",
        languages=["python"],
        cwe_id="CWE-89"
    ),
    SecurityPattern(
        name="python_command_injection",
        pattern=re.compile(r'(os\.system|subprocess\.(call|Popen|run))\s*\([^)]*(?:user_|cmd|command|input|request\.|argv|[+%]|f["\'])', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Potential command injection",
        languages=["python"],
        cwe_id="CWE-78"
    ),
    SecurityPattern(
        name="python_weak_crypto",
        pattern=re.compile(r'hashlib\.(md5|sha1)\s*\(', re.IGNORECASE),
        severity=Severity.MEDIUM,
        message="Use of weak cryptographic hash function",
        languages=["python"],
        cwe_id="CWE-327"
    ),
]

# R Language Attack Patterns
R_PATTERNS = [
    SecurityPattern(
        name="r_eval_parse_injection",
        pattern=re.compile(r'eval\s*\(\s*parse\s*\(\s*text\s*=\s*[^")]+\)\s*\)', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Dangerous use of eval(parse()) with potential code injection",
        languages=["r"],
        cwe_id="CWE-95"
    ),
    SecurityPattern(
        name="r_system_command_injection",
        pattern=re.compile(r'system\s*\(\s*paste0?\s*\(', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Potential command injection via system() with paste()",
        languages=["r"],
        cwe_id="CWE-78"
    ),
    SecurityPattern(
        name="r_sql_injection",
        pattern=re.compile(r'dbGetQuery\s*\([^,)]+,\s*[^,)]+(?:paste|sprintf|paste0)\s*\(', re.IGNORECASE | re.DOTALL),
        severity=Severity.CRITICAL,
        message="Potential SQL injection via string concatenation",
        languages=["r"],
        cwe_id="CWE-89"
    ),
    SecurityPattern(
        name="r_unsafe_rds_load",
        pattern=re.compile(r'readRDS\s*\(\s*[^")]+\)', re.IGNORECASE),
        severity=Severity.MEDIUM,
        message="Loading RDS from potentially untrusted source",
        languages=["r"],
        cwe_id="CWE-502"
    ),
    SecurityPattern(
        name="r_source_injection",
        pattern=re.compile(r'source\s*\(\s*[^")]+\)', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Loading R code from potentially untrusted source",
        languages=["r"],
        cwe_id="CWE-829"
    ),
]

# Julia Language Attack Patterns
JULIA_PATTERNS = [
    SecurityPattern(
        name="julia_eval_injection",
        pattern=re.compile(r'eval\s*\(\s*Meta\.parse\s*\([^")]+\)\s*\)', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Dangerous use of eval(Meta.parse()) with potential code injection",
        languages=["julia"],
        cwe_id="CWE-95"
    ),
    SecurityPattern(
        name="julia_unsafe_ccall",
        pattern=re.compile(r'ccall\s*\(\s*\([^,]+,\s*[^")]+\)', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Unsafe ccall with dynamic library name",
        languages=["julia"],
        cwe_id="CWE-426"
    ),
    SecurityPattern(
        name="julia_command_injection",
        pattern=re.compile(r'run\s*\(\s*`[^`]*\$', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Potential command injection via run() with interpolation",
        languages=["julia"],
        cwe_id="CWE-78"
    ),
    SecurityPattern(
        name="julia_include_injection",
        pattern=re.compile(r'include\s*\(\s*[^")]+\)', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Including code from potentially untrusted source",
        languages=["julia"],
        cwe_id="CWE-829"
    ),
]

# Go Language Attack Patterns
GO_PATTERNS = [
    SecurityPattern(
        name="go_sql_injection",
        pattern=re.compile(r'(Query|Exec|QueryRow)\s*\([^)]*[+].*?\)', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Potential SQL injection via string concatenation",
        languages=["go"],
        cwe_id="CWE-89"
    ),
    SecurityPattern(
        name="go_command_injection",
        pattern=re.compile(r'exec\.Command\s*\([^)]+\)', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Potential command injection via exec.Command",
        languages=["go"],
        cwe_id="CWE-78"
    ),
    SecurityPattern(
        name="go_path_traversal",
        pattern=re.compile(r'(ioutil\.ReadFile|os\.Open)\s*\([^")]+\)', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Potential path traversal vulnerability",
        languages=["go"],
        cwe_id="CWE-22"
    ),
    SecurityPattern(
        name="go_weak_random",
        pattern=re.compile(r'math/rand\.', re.IGNORECASE),
        severity=Severity.MEDIUM,
        message="Use of weak random number generator - use crypto/rand for security",
        languages=["go"],
        cwe_id="CWE-338"
    ),
    SecurityPattern(
        name="go_template_injection",
        pattern=re.compile(r'template\.(HTML|JS|URL)\s*\([^")]+\)', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Potential template injection vulnerability",
        languages=["go"],
        cwe_id="CWE-94"
    ),
]

# PHP Attack Patterns
PHP_PATTERNS = [
    SecurityPattern(
        name="php_sql_injection",
        pattern=re.compile(r'(mysql_query|mysqli_query|pg_query|PDO::query)\s*\([^)]*["\'].*\s*\.\s*\$\w+', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="SQL injection via direct user input concatenation",
        languages=["php"],
        cwe_id="CWE-89"
    ),
    SecurityPattern(
        name="php_command_injection",
        pattern=re.compile(r'(system|exec|shell_exec|passthru|eval)\s*\([^)]*\$_(GET|POST|REQUEST)', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Command injection via user input",
        languages=["php"],
        cwe_id="CWE-78"
    ),
    SecurityPattern(
        name="php_file_inclusion",
        pattern=re.compile(r'(include|require|include_once|require_once)\s*\([^)]*\$_(GET|POST|REQUEST)', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Remote/Local file inclusion vulnerability",
        languages=["php"],
        cwe_id="CWE-98"
    ),
    SecurityPattern(
        name="php_unserialize",
        pattern=re.compile(r'unserialize\s*\(\s*\$_(GET|POST|REQUEST|COOKIE)', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Unsafe deserialization of user input",
        languages=["php"],
        cwe_id="CWE-502"
    ),
    SecurityPattern(
        name="php_xss",
        pattern=re.compile(r'echo\s+[^;]*\$_(GET|POST|REQUEST)', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Potential XSS via direct echo of user input",
        languages=["php"],
        cwe_id="CWE-79"
    ),
]

# Rust Attack Patterns
RUST_PATTERNS = [
    SecurityPattern(
        name="rust_unsafe_unwrap",
        pattern=re.compile(r'\.unwrap\(\)|\.expect\(', re.IGNORECASE),
        severity=Severity.MEDIUM,
        message="Use of unwrap/expect can cause panic - consider proper error handling",
        languages=["rust"],
        cwe_id="CWE-248"
    ),
    SecurityPattern(
        name="rust_unsafe_transmute",
        pattern=re.compile(r'mem::transmute', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Use of unsafe transmute can violate memory safety",
        languages=["rust"],
        cwe_id="CWE-704"
    ),
    SecurityPattern(
        name="rust_unsafe_raw_pointer",
        pattern=re.compile(r'\*\s*(mut|const)\s+\w+', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Use of raw pointers requires careful validation",
        languages=["rust"],
        cwe_id="CWE-787"
    ),
    SecurityPattern(
        name="rust_static_mut",
        pattern=re.compile(r'static\s+mut\s+\w+', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Mutable static variables can cause race conditions",
        languages=["rust"],
        cwe_id="CWE-362"
    ),
]

# JavaScript/TypeScript Attack Patterns
JS_TS_PATTERNS = [
    SecurityPattern(
        name="js_dom_xss",
        pattern=re.compile(r'\.(innerHTML|outerHTML)\s*=\s*[^"\'`]', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Potential DOM XSS via innerHTML/outerHTML",
        languages=["javascript", "typescript"],
        cwe_id="CWE-79"
    ),
    SecurityPattern(
        name="js_eval_injection",
        pattern=re.compile(r'\beval\s*\([^")]+\)', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Use of eval() with potential code injection",
        languages=["javascript", "typescript"],
        cwe_id="CWE-95"
    ),
    SecurityPattern(
        name="js_prototype_pollution",
        pattern=re.compile(r'(\[["\'`]?(__proto__|prototype|constructor)["\'`]?\]|\.__proto__|\.(prototype|constructor))\s*=', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Potential prototype pollution vulnerability",
        languages=["javascript", "typescript"],
        cwe_id="CWE-1321"
    ),
    SecurityPattern(
        name="js_command_injection",
        pattern=re.compile(r'child_process\.(exec|spawn)\s*\([^")]+[+`]', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Potential command injection in child_process",
        languages=["javascript", "typescript"],
        cwe_id="CWE-78"
    ),
    SecurityPattern(
        name="js_sql_injection",
        pattern=re.compile(r'(query|execute)\s*\([^)]*[+`][^)]*\$\{', re.IGNORECASE),
        severity=Severity.CRITICAL,
        message="Potential SQL injection via template literals",
        languages=["javascript", "typescript"],
        cwe_id="CWE-89"
    ),
    SecurityPattern(
        name="js_react_dangerously_set_html_xss",
        pattern=re.compile(r'dangerouslySetInnerHTML\s*=\s*\{\s*\{', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Use of dangerouslySetInnerHTML can lead to XSS",
        languages=["javascript", "typescript"],
        cwe_id="CWE-79"
    ),
]

# Cross-Language Patterns
CROSS_LANGUAGE_PATTERNS = [
    SecurityPattern(
        name="hardcoded_secret_key",
        pattern=re.compile(r'(secret[_-]?key|api[_-]?key|private[_-]?key)\s*[:=]\s*["\'][^"\']{10,}["\']', re.IGNORECASE),
        severity=Severity.HIGH,
        message="Hardcoded secret key detected",
        languages=["all"],
        cwe_id="CWE-798"
    ),
    SecurityPattern(
        name="base64_obfuscation",
        pattern=re.compile(r'[A-Za-z0-9+/]{50,}={0,2}'),
        severity=Severity.INFO,
        message="Large base64 encoded string detected - possible obfuscation",
        languages=["all"],
        cwe_id="CWE-506"
    ),
    SecurityPattern(
        name="cryptocurrency_wallet",
        pattern=re.compile(r'(bc1|[13])[a-zA-HJ-NP-Z0-9]{25,62}|0x[a-fA-F0-9]{40}|4[0-9AB][1-9A-HJ-NP-Za-km-z]{93}'),
        severity=Severity.MEDIUM,
        message="Cryptocurrency wallet address detected",
        languages=["all"],
        cwe_id=None
    ),
    SecurityPattern(
        name="suspicious_ip_address",
        pattern=re.compile(r'\b(?:192\.168|10\.|172\.(?:1[6-9]|2[0-9]|3[01]))\.\d{1,3}\.\d{1,3}\b'),
        severity=Severity.INFO,
        message="Private IP address detected - verify if intentional",
        languages=["all"],
        cwe_id=None
    ),
]

# Combine all patterns
ALL_PATTERNS: List[SecurityPattern] = (
    C_PATTERNS + 
    PYTHON_PATTERNS + 
    R_PATTERNS + 
    JULIA_PATTERNS + 
    GO_PATTERNS + 
    PHP_PATTERNS + 
    RUST_PATTERNS + 
    JS_TS_PATTERNS + 
    CROSS_LANGUAGE_PATTERNS
)

# Language mapping for pattern selection
LANGUAGE_PATTERN_MAP: Dict[str, List[SecurityPattern]] = {
    "c": C_PATTERNS + CROSS_LANGUAGE_PATTERNS,
    "cpp": C_PATTERNS + CROSS_LANGUAGE_PATTERNS,
    "python": PYTHON_PATTERNS + CROSS_LANGUAGE_PATTERNS,
    "r": R_PATTERNS + CROSS_LANGUAGE_PATTERNS,
    "julia": JULIA_PATTERNS + CROSS_LANGUAGE_PATTERNS,
    "go": GO_PATTERNS + CROSS_LANGUAGE_PATTERNS,
    "php": PHP_PATTERNS + CROSS_LANGUAGE_PATTERNS,
    "rust": RUST_PATTERNS + CROSS_LANGUAGE_PATTERNS,
    "javascript": JS_TS_PATTERNS + CROSS_LANGUAGE_PATTERNS,
    "typescript": JS_TS_PATTERNS + CROSS_LANGUAGE_PATTERNS,
}


def get_patterns_for_language(language: str) -> List[SecurityPattern]:
    """Get security patterns applicable to a specific language."""
    language_lower = language.lower()
    return LANGUAGE_PATTERN_MAP.get(language_lower, CROSS_LANGUAGE_PATTERNS)


def scan_content(content: str, language: str) -> List[Dict[str, any]]:
    """
    Scan content for security patterns based on language.
    
    Args:
        content: The source code content to scan
        language: The programming language of the content
        
    Returns:
        List of findings with pattern details and locations
    """
    findings = []
    patterns = get_patterns_for_language(language)
    
    for pattern in patterns:
        if pattern.languages == ["all"] or language.lower() in pattern.languages:
            matches = pattern.pattern.finditer(content)
            for match in matches:
                # Calculate line number
                line_num = content[:match.start()].count('\n') + 1
                
                findings.append({
                    "type": "pattern",
                    "name": pattern.name,
                    "severity": pattern.severity.value,
                    "message": pattern.message,
                    "line": line_num,
                    "column": match.start() - content.rfind('\n', 0, match.start()),
                    "snippet": match.group(0)[:100],  # First 100 chars of match
                    "cwe_id": pattern.cwe_id,
                    "language": language
                })
    
    return findings