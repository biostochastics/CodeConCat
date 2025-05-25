# codeconcat/language_map.py
import logging
from typing import Optional

logger = logging.getLogger(__name__)

GUESSLANG_AVAILABLE = False
guesslang_instance = None

try:
    from guesslang import Guess

    guesslang_instance = Guess()
    GUESSLANG_AVAILABLE = True
    logger.info("Successfully imported guesslang. Advanced language detection is enabled.")
except ImportError:
    logger.info(
        "guesslang library not found. Falling back to basic extension-based language detection. "
        "For more accurate language detection, install with 'pip install codeconcat[guesslang]'."
    )


def get_language_guesslang(content: str) -> Optional[str]:
    """Detect language using guesslang if available."""
    if not GUESSLANG_AVAILABLE or guesslang_instance is None:
        return None
    try:
        language = guesslang_instance.language_name(content)
        # guesslang might return 'Unknown' or similar for unrecognizable content
        if language and language.lower() != "unknown":
            # Normalize to lowercase as our ext_map keys are lowercase
            return language.lower()
    except Exception as e:
        logger.debug(f"guesslang failed to detect language: {e}")
    return None


# Basic extension map (fallback and used by should_include_file)
# Keys should be lowercase
ext_map = {
    ".py": "python",
    ".js": "javascript",
    ".jsx": "javascript",
    ".ts": "typescript",
    ".tsx": "typescript",
    ".java": "java",
    ".c": "c",
    ".cpp": "cpp",
    ".h": "c_header",
    ".hpp": "cpp_header",
    ".cs": "csharp",
    ".go": "go",
    ".rb": "ruby",
    ".php": "php",
    ".swift": "swift",
    ".kt": "kotlin",
    ".rs": "rust",
    ".scala": "scala",
    ".m": "objective-c",
    ".mm": "objective-cpp",
    ".pl": "perl",
    ".pm": "perl",
    ".lua": "lua",
    ".r": "r",
    ".R": "r",
    ".sh": "shell",
    ".bash": "bash",
    ".zsh": "zsh",
    ".fish": "fish",
    ".ps1": "powershell",
    ".bat": "batch",
    ".cmd": "batch",
    ".sql": "sql",
    ".html": "html",
    ".htm": "html",
    ".css": "css",
    ".sass": "sass",
    ".less": "less",
    ".xml": "xml",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".conf": "ini",
    ".md": "markdown",
    ".rst": "restructuredtext",
    ".tex": "latex",
    ".dockerfile": "dockerfile",
    "dockerfile": "dockerfile",  # Allow Dockerfile with no extension
    ".makefile": "makefile",
    "makefile": "makefile",  # Allow Makefile with no extension
    ".env": "dotenv",
    ".gitignore": "gitignore",
    ".gitattributes": "gitattributes",
    ".csv": "csv",
    ".tsv": "tsv",
    ".http": "http",
    ".graphql": "graphql",
    ".gql": "graphql",
    ".vue": "vue",
    ".svelte": "svelte",
    ".dart": "dart",
    ".ex": "elixir",
    ".exs": "elixir",
    ".erl": "erlang",
    ".hrl": "erlang",
    ".fs": "fsharp",
    ".fsi": "fsharp",
    ".fsx": "fsharp",
    ".fsscript": "fsharp",
    ".hs": "haskell",
    ".lhs": "haskell",
    ".purescript": "purescript",
    ".purs": "purescript",
    ".clj": "clojure",
    ".cljs": "clojurescript",
    ".cljc": "clojure",
    ".edn": "edn",
    ".tf": "terraform",
    ".hcl": "hcl",
    ".groovy": "groovy",
    ".gvy": "groovy",
    ".gradle": "gradle",
    ".sol": "solidity",
    ".cshtml": "razor",
    ".vb": "vbnet",
    ".vbs": "vbscript",
    ".pas": "pascal",
    ".dfm": "delphi_form",
    ".lpr": "delphi_project",
    ".dpr": "delphi_project",
    ".asm": "assembly",
    ".s": "assembly",
    ".cbl": "cobol",
    ".cob": "cobol",
    ".f": "fortran",
    ".for": "fortran",
    ".f90": "fortran",
    ".f95": "fortran",
    ".f03": "fortran",
    ".f08": "fortran",
    ".jl": "julia",
    ".nim": "nim",
    ".cr": "crystal",
    ".zig": "zig",
    ".applescript": "applescript",
    ".scpt": "applescript",
    ".gd": "gdscript",
    ".tcl": "tcl",
    ".cmake": "cmake",
    "cmakelists.txt": "cmake",
    ".abap": "abap",
    ".ada": "ada",
    ".ads": "ada",
    ".adb": "ada",
    ".elm": "elm",
    ".nix": "nix",
    ".rkt": "racket",
    ".scheme": "scheme",
    ".v": "verilog",
    ".sv": "systemverilog",
    ".vhdl": "vhdl",
    ".txt": "text",
    ".liquid": "liquid",
    ".ejs": "ejs",
    ".mustache": "mustache",
    ".handlebars": "handlebars",
    ".hbs": "handlebars",
    ".pug": "pug",
    ".jade": "jade",
    ".haml": "haml",
    ".slim": "slim",
    ".jsx.babel": "javascript",
    ".ipynb": "jupyter_notebook",
}
