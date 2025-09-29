"""Tests for the Tree-sitter Bash parser."""

from codeconcat.parser.language_parsers.tree_sitter_bash_parser import TreeSitterBashParser


class TestTreeSitterBashParser:
    """Test suite for TreeSitterBashParser."""

    def test_parser_initialization(self):
        """Test that the parser initializes correctly."""
        parser = TreeSitterBashParser()
        assert parser is not None
        assert parser.language_name == "bash"
        assert parser.ts_language is not None
        assert parser.parser is not None

    def test_parse_simple_function(self):
        """Test parsing a simple bash function."""
        parser = TreeSitterBashParser()
        content = """
#!/bin/bash

function hello() {
    echo "Hello, World!"
}

hello
"""
        result = parser.parse(content, "test.sh")
        assert result is not None
        assert len(result.declarations) == 1
        assert result.declarations[0].kind == "function"
        assert result.declarations[0].name == "hello"
        assert result.declarations[0].start_line == 4
        assert result.declarations[0].end_line == 6

    def test_parse_function_without_keyword(self):
        """Test parsing a bash function without the 'function' keyword."""
        parser = TreeSitterBashParser()
        content = """
#!/bin/bash

validate_input() {
    local input="$1"
    [[ -n "$input" ]] && return 0 || return 1
}
"""
        result = parser.parse(content, "test.sh")
        assert result is not None
        # Note: parser might find duplicates for local variable (assignment and reference)
        assert len(result.declarations) >= 2  # function + local variable(s)
        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert functions[0].name == "validate_input"

    def test_parse_variables(self):
        """Test parsing variable declarations."""
        parser = TreeSitterBashParser()
        content = """
#!/bin/bash

export PATH="/usr/local/bin:$PATH"
SCRIPT_DIR="$(pwd)"
readonly VERSION="1.0.0"
local config_file="$HOME/.config"
"""
        result = parser.parse(content, "test.sh")
        assert result is not None

        variables = [d for d in result.declarations if d.kind == "variable"]
        var_names = {v.name for v in variables}

        assert "PATH" in var_names
        assert "SCRIPT_DIR" in var_names
        assert "VERSION" in var_names
        assert "config_file" in var_names

    def test_parse_aliases(self):
        """Test parsing alias declarations."""
        parser = TreeSitterBashParser()
        content = """
#!/bin/bash

alias ll='ls -la'
alias grep='grep --color=auto'
alias ..='cd ..'
"""
        result = parser.parse(content, "test.sh")
        assert result is not None

        aliases = [d for d in result.declarations if d.kind == "alias"]
        assert len(aliases) == 3

        alias_names = {a.name for a in aliases}
        assert "ll" in alias_names
        assert "grep" in alias_names
        assert ".." in alias_names

    def test_parse_source_imports(self):
        """Test parsing source and dot imports."""
        parser = TreeSitterBashParser()
        content = """
#!/bin/bash

source ~/.bashrc
. /etc/profile
source "$HOME/.config/myapp.conf"

if [[ -f "$config_file" ]]; then
    source "$config_file"
fi
"""
        result = parser.parse(content, "test.sh")
        assert result is not None
        assert len(result.imports) >= 3

        # Check for expected imports
        import_paths = set(result.imports)
        assert "~/.bashrc" in import_paths or "~/.bashrc" in str(import_paths)
        assert "/etc/profile" in import_paths or "/etc/profile" in str(import_paths)

    def test_parse_complex_script(self):
        """Test parsing a complex bash script with multiple elements."""
        parser = TreeSitterBashParser()
        content = """#!/bin/bash

# Configuration
export PATH="/usr/local/bin:$PATH"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="1.0.0"

# Function definitions
function setup_environment() {
    echo "Setting up environment..."
    local config_file="$1"

    if [[ -f "$config_file" ]]; then
        source "$config_file"
    fi
}

validate_input() {
    local input="$1"
    [[ -n "$input" ]] && return 0 || return 1
}

# Alias definitions
alias ll='ls -la'
alias grep='grep --color=auto'

# Source external scripts
source ~/.bashrc
. /etc/profile

# Main execution
main() {
    setup_environment "$HOME/.config/myapp.conf"

    if validate_input "$1"; then
        echo "Processing: $1"
    else
        echo "Invalid input" >&2
        exit 1
    fi
}

# Run main if not sourced
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
"""
        result = parser.parse(content, "test.sh")
        assert result is not None

        # Check functions
        functions = [d for d in result.declarations if d.kind == "function"]
        func_names = {f.name for f in functions}
        assert "setup_environment" in func_names
        assert "validate_input" in func_names
        assert "main" in func_names

        # Check variables
        variables = [d for d in result.declarations if d.kind == "variable"]
        var_names = {v.name for v in variables}
        assert "PATH" in var_names
        assert "SCRIPT_DIR" in var_names
        assert "VERSION" in var_names

        # Check aliases
        aliases = [d for d in result.declarations if d.kind == "alias"]
        assert len(aliases) == 2

        # Check imports
        assert len(result.imports) >= 2

    def test_parse_empty_script(self):
        """Test parsing an empty script."""
        parser = TreeSitterBashParser()
        content = ""
        result = parser.parse(content, "empty.sh")
        assert result is not None
        assert len(result.declarations) == 0
        assert len(result.imports) == 0

    def test_parse_comments_only(self):
        """Test parsing a script with only comments."""
        parser = TreeSitterBashParser()
        content = """#!/bin/bash
# This is a comment
# Another comment
# Yet another comment
"""
        result = parser.parse(content, "comments.sh")
        assert result is not None
        assert len(result.declarations) == 0
        assert len(result.imports) == 0

    def test_parse_nested_functions(self):
        """Test parsing nested function calls and definitions."""
        parser = TreeSitterBashParser()
        content = """
#!/bin/bash

outer_function() {
    inner_function() {
        echo "Inner function"
    }

    inner_function
}
"""
        result = parser.parse(content, "nested.sh")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        func_names = {f.name for f in functions}
        assert "outer_function" in func_names
        # Note: inner_function might be detected depending on parser implementation

    def test_parse_arrays(self):
        """Test parsing array declarations."""
        parser = TreeSitterBashParser()
        content = """
#!/bin/bash

declare -a fruits=("apple" "banana" "orange")
colors[0]="red"
colors[1]="green"
"""
        result = parser.parse(content, "arrays.sh")
        assert result is not None

        # Arrays might be detected as variables
        variables = [d for d in result.declarations if d.kind == "variable"]
        assert len(variables) > 0

    def test_parse_case_statements(self):
        """Test parsing with case statements."""
        parser = TreeSitterBashParser()
        content = """
#!/bin/bash

process_option() {
    local option="$1"

    case "$option" in
        start)
            echo "Starting..."
            ;;
        stop)
            echo "Stopping..."
            ;;
        *)
            echo "Unknown option"
            ;;
    esac
}
"""
        result = parser.parse(content, "case.sh")
        assert result is not None

        functions = [d for d in result.declarations if d.kind == "function"]
        assert len(functions) == 1
        assert functions[0].name == "process_option"

    def test_get_queries(self):
        """Test that get_queries returns expected query types."""
        parser = TreeSitterBashParser()
        queries = parser.get_queries()

        assert isinstance(queries, dict)
        assert "functions" in queries
        assert "variables" in queries
        assert "aliases" in queries
        assert "imports" in queries
