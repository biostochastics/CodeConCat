"""Constants and shared configuration values for CodeConcat."""

# Default file patterns to exclude from processing
DEFAULT_EXCLUDE_PATTERNS: list[str] = [
    # Version Control
    ".git/",  # Match the .git directory itself
    ".git/**",  # Match contents of .git directory
    "**/.git/",  # Match .git directory anywhere in tree
    "**/.git/**",  # Match contents of .git directory anywhere in tree
    ".gitignore",
    "**/.gitignore",
    ".svn/",
    "**/.svn/",
    "**/.svn/**",
    ".hg/",
    "**/.hg/",
    "**/.hg/**",
    ".bzr/",
    "**/.bzr/",
    "**/.bzr/**",
    ".gitattributes",
    ".hgignore",
    ".svnignore",
    # CodeConcat configuration
    ".codeconcat.yml",
    # Dependencies and build artifacts
    "node_modules/",
    "**/node_modules/",
    "**/node_modules/**",
    "vendor/",
    "**/vendor/",
    "**/vendor/**",
    "bower_components/",
    "**/bower_components/",
    "**/bower_components/**",
    "__pycache__/",
    "**/__pycache__/",
    "**/__pycache__/**",
    "*.pyc",
    "**/*.pyc",
    "*.pyo",
    "**/*.pyo",
    "*.pyd",
    "**/*.pyd",
    ".Python",
    "build/",
    "**/build/",
    "**/build/**",
    "dist/",
    "**/dist/",
    "**/dist/**",
    "*.egg-info/",
    "**/*.egg-info/",
    "**/*.egg-info/**",
    "*.egg",
    "**/*.egg",
    # IDE and editor files
    ".vscode/",
    ".idea/",
    "*.swp",
    "*.swo",
    "*~",
    ".project",
    ".classpath",
    ".settings/",
    "*.sublime-project",
    "*.sublime-workspace",
    ".vim/",
    ".vimrc",
    # OS generated files
    ".DS_Store",
    "**/.DS_Store",
    "._*",
    "**/._*",
    ".Spotlight-V100",
    ".Trashes",
    "ehthumbs.db",
    "Thumbs.db",
    "**/Thumbs.db",
    "desktop.ini",
    # Testing and coverage
    ".coverage",
    ".pytest_cache/",
    "**/.pytest_cache/**",
    ".tox/",
    "nosetests.xml",
    "coverage.xml",
    "*.cover",
    ".hypothesis/",
    "htmlcov/",
    "coverage/",
    "**/coverage/",
    "**/coverage/**",
    ".phpunit.result.cache",
    # R specific
    ".Rcheck/",
    "**/.Rcheck/",
    "**/.Rcheck/**",
    ".Rhistory",
    "**/.Rhistory",
    ".RData",
    "**/.RData",
    # Next.js specific
    ".next/",
    "**/.next/",
    "**/.next/**",
    "**/static/chunks/**",
    "**/server/chunks/**",
    "**/BUILD_ID",
    "**/trace",
    "**/*.map",
    "**/webpack-*.js",
    "**/manifest*.js",
    "**/server-reference-manifest.js",
    "**/middleware-manifest.js",
    "**/client-reference-manifest.js",
    "**/webpack-runtime.js",
    "**/middleware-build-manifest.js",
    "**/middleware-react-loadable-manifest.js",
    "**/interception-route-rewrite-manifest.js",
    "**/next-font-manifest.js",
    "**/polyfills-*.js",
    "**/main-*.js",
    "**/framework-*.js",
    # Documentation
    "docs/_build/",
    "site/",
    # Environment files
    ".env",
    "**/.env",
    ".env.*",
    "**/.env.*",
    "venv/",
    "venv/**",
    "**/venv/",
    "**/venv/**",
    "*venv/",
    "*venv/**",
    "ENV/",
    "**/ENV/",
    "**/ENV/**",
    "env/",
    "**/env/",
    "**/env/**",
    # Logs
    "*.log",
    "logs/",
    "npm-debug.log*",
    "yarn-debug.log*",
    "yarn-error.log*",
    # Package lock files
    "package-lock.json",
    "**/package-lock.json",
    "yarn.lock",
    "**/yarn.lock",
    "pnpm-lock.yaml",
    "**/pnpm-lock.yaml",
    "Gemfile.lock",
    "composer.lock",
    "poetry.lock",
    "Pipfile.lock",
    # Database files
    "*.sql",
    "*.sqlite",
    "*.db",
    # Temporary files
    "tmp/",
    "temp/",
    "*.tmp",
    "*.temp",
    "*.bak",
    "*.backup",
    "*.old",
    # Binary and media files
    "*.exe",
    "*.dll",
    "*.so",
    "*.dylib",
    "*.bin",
    "*.jpg",
    "*.jpeg",
    "*.png",
    "*.gif",
    "*.ico",
    "*.svg",
    "*.mp3",
    "*.mp4",
    "*.avi",
    "*.mov",
    "*.mkv",
    "*.pdf",
    "*.doc",
    "*.docx",
    "*.xls",
    "*.xlsx",
    "*.ppt",
    "*.pptx",
    # Archive files
    "*.jar",
    "**/*.jar",
    "*.war",
    "**/*.war",
    "*.ear",
    "**/*.ear",
    "*.zip",
    "**/*.zip",
    "*.tar.gz",
    "**/*.tar.gz",
    "*.rar",
    "**/*.rar",
    # Cache directories
    ".cache/",
    "**/.cache/",
    "**/.cache/**",
    ".sass-cache/",
    ".parcel-cache/",
    "out/",
    # Test directories (can be uncommented if you want to exclude tests)
    # "tests/",
    # "**/tests/",
    # "**/tests/**",
    # "**/test/",
    # "**/test/**",
    # Common large directories
    "**/libs/**",
    "**/third_party/**",
    # Hidden directories (specific exclusions - NOT all hidden files)
    # Version control directories are already excluded above
    ".secrets/",
    "**/.secrets/",
    "**/.secrets/**",
    # Security and secrets
    "*.pem",
    "*.key",
    "*.cert",
    "*.crt",
    "secrets.yml",
    "secrets.json",
]

# Hidden config files that should be INCLUDED (whitelist)
# These are valuable configuration files that are often hidden
HIDDEN_CONFIG_WHITELIST = frozenset(
    {
        # JavaScript/TypeScript tooling
        ".eslintrc",
        ".eslintrc.js",
        ".eslintrc.cjs",
        ".eslintrc.json",
        ".eslintrc.yml",
        ".eslintrc.yaml",
        ".prettierrc",
        ".prettierrc.js",
        ".prettierrc.cjs",
        ".prettierrc.json",
        ".prettierrc.yml",
        ".prettierrc.yaml",
        ".babelrc",
        ".babelrc.js",
        ".babelrc.json",
        ".swcrc",
        ".npmrc",
        ".nvmrc",
        ".yarnrc",
        ".yarnrc.yml",
        # Editor configuration
        ".editorconfig",
        # Python tooling
        ".flake8",
        ".pylintrc",
        ".python-version",
        ".pre-commit-config.yaml",
        ".isort.cfg",
        ".style.yapf",
        ".coveragerc",
        # Docker
        ".dockerignore",
        # Templates and examples (not actual secrets)
        ".env.example",
        ".env.template",
        ".env.sample",
        # Ruby
        ".rubocop.yml",
        ".ruby-version",
        # Other tools
        ".browserslistrc",
        ".commitlintrc",
        ".commitlintrc.js",
        ".commitlintrc.json",
        ".lintstagedrc",
        ".lintstagedrc.js",
        ".lintstagedrc.json",
        ".huskyrc",
        ".huskyrc.js",
        ".huskyrc.json",
        ".markdownlint.json",
        ".markdownlintrc",
        ".prettierignore",
        ".eslintignore",
        ".stylelintrc",
        ".stylelintrc.json",
        ".stylelintrc.js",
    }
)

# File extensions considered as source code
SOURCE_CODE_EXTENSIONS = {
    # Programming languages
    ".py",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".java",
    ".cpp",
    ".cc",
    ".cxx",
    ".c",
    ".h",
    ".hpp",
    ".cs",
    ".php",
    ".rb",
    ".go",
    ".rs",
    ".swift",
    ".kt",
    ".scala",
    ".r",
    ".jl",
    ".lua",
    ".pl",
    ".sh",
    ".bash",
    # Markup and config
    ".html",
    ".htm",
    ".xml",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".conf",
    # Web technologies
    ".css",
    ".scss",
    ".sass",
    ".less",
    ".vue",
    ".svelte",
    # Documentation
    ".md",
    ".rst",
    ".txt",
}

# Maximum file size for processing (in bytes)
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

# Maximum total project size (in bytes)
MAX_PROJECT_SIZE = 100 * 1024 * 1024  # 100 MB

# Token limits for different models (updated January 2026)
TOKEN_LIMITS = {
    # OpenAI GPT models (2026)
    "gpt-5": 500000,
    "gpt-5.1": 500000,
    "gpt-5.2": 1000000,
    "gpt-5-mini": 256000,
    "gpt-4.5": 256000,
    "gpt-4o": 128000,
    "gpt-4o-mini": 128000,
    "gpt-4-turbo": 128000,
    "gpt-4": 8192,
    "o1": 200000,
    "o1-mini": 128000,
    "o3": 500000,
    "o3-mini": 256000,
    # Anthropic Claude models (2026)
    "claude-opus-4.5": 500000,
    "claude-opus-4": 500000,
    "claude-sonnet-4": 400000,
    "claude-sonnet-4.5": 400000,
    "claude-haiku-4": 256000,
    "claude-3.5-sonnet": 200000,
    "claude-3.5-haiku": 200000,
    "claude-3-opus": 200000,
    "claude-3-sonnet": 200000,
    "claude-3-haiku": 200000,
    "claude-2.1": 200000,
    "claude": 100000,
    # Google Gemini models (2026)
    "gemini-3-preview": 2000000,
    "gemini-2.5-pro": 2000000,
    "gemini-2.5-flash": 1000000,
    "gemini-2.0-pro": 2000000,
    "gemini-2.0-flash": 1000000,
    "gemini-1.5-pro": 1000000,
    "gemini-1.5-flash": 1000000,
    # Default fallback
    "default": 200000,
}

# Compression levels and their settings
COMPRESSION_SETTINGS = {
    "low": {
        "importance_threshold": 0.25,
        "context_lines": 2,
        "min_segment_size": 5,
    },
    "medium": {
        "importance_threshold": 0.5,
        "context_lines": 1,
        "min_segment_size": 3,
    },
    "high": {
        "importance_threshold": 0.75,
        "context_lines": 0,
        "min_segment_size": 1,
    },
    "aggressive": {
        "importance_threshold": 0.9,
        "context_lines": 0,
        "min_segment_size": 1,
    },
}

# Security scan patterns
SECURITY_PATTERNS = {
    "high_risk_functions": [
        "exec",
        "eval",
        "system",
        "popen",
        "subprocess",
        "os.system",
        "child_process",
        "shellexec",
        "wscript.shell",
    ],
    "sql_keywords": [
        "SELECT",
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "CREATE",
        "ALTER",
        "TRUNCATE",
        "UNION",
    ],
    "crypto_functions": [
        "md5",
        "sha1",
        "des",
        "rc4",
        "ecb",
    ],
}

# --- Processing Constants ---

# Timeout settings (in seconds)
REDOS_TIMEOUT_SECONDS: float = 2.0  # Timeout for regex validation
FILE_PROCESSING_TIMEOUT_SECONDS: int = 30  # Timeout for processing single file

# Size limits
MAX_REGEX_LENGTH: int = 1000  # Maximum allowed regex pattern length
BINARY_CHECK_SAMPLE_BYTES: int = 4096  # Bytes to read for binary detection
GUESSLANG_SAMPLE_CHARS: int = 5000  # Characters to sample for language detection

# Cache sizes
LANGUAGE_CACHE_SIZE: int = 1024  # LRU cache size for language detection
PARSER_CACHE_SIZE: int = 64  # LRU cache size for parser instances

# Known ReDoS vulnerability patterns (static analysis)
REDOS_PATTERNS: list[str] = [
    r"\(\.\+\)\+",  # Nested quantifiers like (.+)+
    r"\(\[\.\*\]\+\)\+",  # Nested character class quantifiers
    r"\(\.\*\)\+",  # (.*)+
    r"\(\.\+\)\*",  # (.+)*
    r"\(\?:.*\)\+\(\?:",  # Multiple nested non-capturing groups
]
