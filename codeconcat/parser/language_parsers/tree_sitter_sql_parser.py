# file: codeconcat/parser/language_parsers/tree_sitter_sql_parser.py

"""
Multi-dialect SQL parser using tree-sitter.

Extracts DDL and DML constructs from SQL code supporting PostgreSQL, MySQL,
and SQLite dialects using the DerekStride/tree-sitter-sql grammar.

Supports:
- Table and view definitions
- Common Table Expressions (CTEs)
- Window functions
- Stored procedures (PostgreSQL/MySQL)
- DDL/DML classification
"""

import logging
import re
from enum import Enum, auto
from typing import Any

from .base_tree_sitter_parser import BaseTreeSitterParser

try:
    from tree_sitter import QueryCursor  # type: ignore[attr-defined]
except ImportError:
    QueryCursor = None  # type: ignore

logger = logging.getLogger(__name__)


class SqlDialect(Enum):
    """SQL dialect enumeration."""

    POSTGRESQL = auto()
    MYSQL = auto()
    SQLITE = auto()
    UNKNOWN = auto()


# SQL parser queries for construct extraction
SQL_QUERIES = {
    "ddl_statements": """
        ; DDL statements - Data Definition Language
        (statement
          (create_table) @ddl_statement
        )
        (statement
          (create_view) @ddl_statement
        )
        (statement
          (create_function) @ddl_statement
        )
    """,
    "dml_statements": """
        ; DML statements - Data Manipulation Language
        (statement
          (select) @dml_statement
        )
        (statement
          (insert) @dml_statement
        )
        (statement
          (update) @dml_statement
        )
        (statement
          (delete) @dml_statement
        )
    """,
    "table_definitions": """
        ; Extract table definitions
        (create_table
          (object_reference) @table_name
          (column_definitions) @columns
        ) @table_def
    """,
    "view_definitions": """
        ; Extract view definitions
        (create_view
          (object_reference) @view_name
          (create_query) @view_query
        ) @view_def
    """,
    "cte_definitions": """
        ; Extract Common Table Expressions
        (cte
          (identifier) @cte_name
          (statement) @cte_query
        ) @cte_def
    """,
    "window_functions": """
        ; Extract window function usage
        (window_function) @window_func
    """,
    "stored_procedures": """
        ; Extract stored procedure/function definitions
        (create_function
          (object_reference) @proc_name
          (function_body) @proc_body
        ) @proc_def
    """,
}


class TreeSitterSqlParser(BaseTreeSitterParser):
    """
    Multi-dialect SQL parser using tree-sitter.

    Supports PostgreSQL, MySQL, and SQLite with automatic dialect detection.
    Extracts DDL/DML constructs, table/view definitions, CTEs, window functions,
    and stored procedures.

    Attributes:
        dialect: The SQL dialect being parsed
        language_name: Always 'sql' for this parser

    Complexity:
        - Parsing: O(n) where n is the length of SQL code
        - Query execution: O(m) where m is the number of AST nodes
        - Dialect detection: O(n) single pass through content
    """

    def __init__(self, dialect: SqlDialect | None = None, content: str | None = None):
        """Initialize the SQL parser.

        Args:
            dialect: Explicit SQL dialect to use. If None, will attempt auto-detection.
            content: SQL content for dialect detection. If None, defaults to POSTGRESQL.

        Raises:
            LanguageParserError: If tree-sitter-sql grammar cannot be loaded.
        """
        # Initialize base tree-sitter parser with 'sql' language
        super().__init__("sql")

        # Determine dialect
        if dialect is not None:
            self.dialect = dialect
        elif content is not None:
            self.dialect = self._detect_dialect(content)
        else:
            # Default to PostgreSQL (most feature-rich)
            self.dialect = SqlDialect.POSTGRESQL

        logger.info(f"Initialized SQL parser with dialect: {self.dialect.name}")

    def get_queries(self) -> dict[str, str]:
        """Returns the SQL-specific tree-sitter queries.

        Returns:
            Dictionary mapping query names to query strings
        """
        return SQL_QUERIES

    def _detect_dialect(self, content: str) -> SqlDialect:
        """Detect SQL dialect from content.

        Detection strategy:
        1. Check for dialect-specific keywords
        2. Check for syntax patterns (backticks, specific functions)
        3. Default to PostgreSQL if ambiguous

        Args:
            content: SQL content to analyze

        Returns:
            Detected SqlDialect enum value

        Complexity: O(n) where n is length of content
        """
        content_lower = content.lower()

        # MySQL indicators
        mysql_indicators = [
            r"`[a-zA-Z_]",  # Backtick identifiers
            r"\bauto_increment\b",
            r"\bengine\s*=",
            r"\bcharset\s*=",
            r"\bcollate\s*=",
        ]

        # PostgreSQL indicators
        postgresql_indicators = [
            r"\bserial\b",
            r"\bbigserial\b",
            r"\bplpgsql\b",
            r"\b\$\$",  # Dollar-quoted strings
            r"\breturning\b",
            r"\:\:",  # Type casts
        ]

        # SQLite indicators
        sqlite_indicators = [
            r"\bautoincrement\b",  # Single word (vs MySQL AUTO_INCREMENT)
            r"\bwithout\s+rowid\b",
        ]

        # Count matches for each dialect
        mysql_score = sum(
            1 for pattern in mysql_indicators if re.search(pattern, content_lower, re.IGNORECASE)
        )
        postgresql_score = sum(
            1
            for pattern in postgresql_indicators
            if re.search(pattern, content_lower, re.IGNORECASE)
        )
        sqlite_score = sum(
            1 for pattern in sqlite_indicators if re.search(pattern, content_lower, re.IGNORECASE)
        )

        logger.debug(
            f"Dialect detection scores - MySQL: {mysql_score}, PostgreSQL: {postgresql_score}, SQLite: {sqlite_score}"
        )

        # Return dialect with highest score
        if mysql_score > postgresql_score and mysql_score > sqlite_score:
            return SqlDialect.MYSQL
        elif sqlite_score > postgresql_score and sqlite_score > mysql_score:
            return SqlDialect.SQLITE
        elif postgresql_score > 0:
            return SqlDialect.POSTGRESQL

        # Default to PostgreSQL (most feature-rich and permissive)
        logger.debug("No strong dialect indicators found, defaulting to PostgreSQL")
        return SqlDialect.POSTGRESQL

    def classify_statement(self, statement_text: str) -> str:
        """Classify a SQL statement as DDL or DML.

        Args:
            statement_text: SQL statement to classify

        Returns:
            'DDL', 'DML', or 'UNKNOWN'

        Complexity: O(1) - simple pattern matching
        """
        statement_lower = statement_text.strip().lower()

        # DDL keywords
        ddl_keywords = ["create", "alter", "drop", "truncate", "rename"]
        # DML keywords
        dml_keywords = ["select", "insert", "update", "delete", "merge", "with"]

        first_word = statement_lower.split()[0] if statement_lower else ""

        if first_word in ddl_keywords:
            return "DDL"
        elif first_word in dml_keywords:
            return "DML"
        else:
            return "UNKNOWN"

    def extract_tables(self, byte_content: bytes) -> list[dict]:
        """Extract table definitions from parsed SQL.

        Args:
            byte_content: SQL source code as bytes

        Returns:
            List of dictionaries containing table metadata:
            {
                'name': str,
                'line_number': int,
                'definition': str
            }

        Complexity: O(m) where m is number of CREATE TABLE statements
        """
        tables: list[dict[str, Any]] = []

        # Parse SQL content (thread-safe - uses local variable)
        tree = self.parser.parse(byte_content)

        # Get compiled query for table definitions
        query = self._get_compiled_query("table_definitions")
        if not query:
            logger.warning("No query available for table_definitions")
            return tables

        try:
            # tree-sitter 0.25.x API: Use QueryCursor to execute queries
            root_node = tree.root_node
            if QueryCursor is not None:
                # tree-sitter 0.25.x with QueryCursor
                captures = self._execute_query_with_cursor(query, root_node)
            else:
                # Fallback (shouldn't reach here with 0.25.x)
                raise RuntimeError("QueryCursor not available - incompatible tree-sitter version")

            # Extract table information from captures
            table_defs = captures.get("table_def", [])
            table_names = captures.get("table_name", [])

            for i, table_node in enumerate(table_defs):
                name_node = table_names[i] if i < len(table_names) else None
                name = (
                    byte_content[name_node.start_byte : name_node.end_byte].decode("utf-8")
                    if name_node
                    else "unknown"
                )

                tables.append(
                    {
                        "name": name.strip('`"'),  # Remove quotes/backticks
                        "line_number": table_node.start_point[0] + 1,
                        "definition": byte_content[
                            table_node.start_byte : table_node.end_byte
                        ].decode("utf-8"),
                    }
                )

        except Exception as e:
            logger.error(f"Error extracting tables: {e}", exc_info=True)

        return tables

    def extract_views(self, byte_content: bytes) -> list[dict]:
        """Extract view definitions from parsed SQL.

        Args:
            byte_content: SQL source code as bytes

        Returns:
            List of dictionaries containing view metadata

        Complexity: O(m) where m is number of CREATE VIEW statements
        """
        views: list[dict[str, Any]] = []

        # Parse SQL content (thread-safe - uses local variable)
        tree = self.parser.parse(byte_content)

        query = self._get_compiled_query("view_definitions")
        if not query:
            return views

        try:
            # tree-sitter 0.25.x API: Use QueryCursor
            if QueryCursor is not None:
                captures = self._execute_query_with_cursor(query, tree.root_node)
            else:
                raise RuntimeError("QueryCursor not available")
            view_defs = captures.get("view_def", [])
            view_names = captures.get("view_name", [])

            for i, view_node in enumerate(view_defs):
                name_node = view_names[i] if i < len(view_names) else None
                name = (
                    byte_content[name_node.start_byte : name_node.end_byte].decode("utf-8")
                    if name_node
                    else "unknown"
                )

                views.append(
                    {
                        "name": name.strip('`"'),
                        "line_number": view_node.start_point[0] + 1,
                        "definition": byte_content[
                            view_node.start_byte : view_node.end_byte
                        ].decode("utf-8"),
                    }
                )
        except Exception as e:
            logger.error(f"Error extracting views: {e}", exc_info=True)

        return views

    def extract_ctes(self, byte_content: bytes) -> list[dict]:
        """Extract Common Table Expressions (CTEs) from parsed SQL.

        Args:
            byte_content: SQL source code as bytes

        Returns:
            List of dictionaries containing CTE metadata:
            {
                'name': str,
                'line_number': int,
                'definition': str
            }

        Complexity: O(m) where m is number of WITH clauses
        """
        ctes: list[dict[str, Any]] = []

        # Parse SQL content (thread-safe - uses local variable)
        tree = self.parser.parse(byte_content)

        query = self._get_compiled_query("cte_definitions")
        if not query:
            return ctes

        try:
            if QueryCursor is not None:
                captures = self._execute_query_with_cursor(query, tree.root_node)
            else:
                raise RuntimeError("QueryCursor not available")

            cte_defs = captures.get("cte_def", [])
            cte_names = captures.get("cte_name", [])

            for i, cte_node in enumerate(cte_defs):
                name_node = cte_names[i] if i < len(cte_names) else None
                name = (
                    byte_content[name_node.start_byte : name_node.end_byte].decode("utf-8")
                    if name_node
                    else "unknown"
                )

                ctes.append(
                    {
                        "name": name.strip(),
                        "line_number": cte_node.start_point[0] + 1,
                        "definition": byte_content[cte_node.start_byte : cte_node.end_byte].decode(
                            "utf-8"
                        ),
                    }
                )
        except Exception as e:
            logger.error(f"Error extracting CTEs: {e}", exc_info=True)

        return ctes

    def extract_window_functions(self, byte_content: bytes) -> list[dict]:
        """Extract window function usage from parsed SQL.

        Args:
            byte_content: SQL source code as bytes

        Returns:
            List of dictionaries containing window function metadata:
            {
                'function_name': str,
                'line_number': int,
                'context': str (surrounding code snippet)
            }

        Complexity: O(m) where m is number of window functions
        """
        window_funcs: list[dict[str, Any]] = []

        # Parse SQL content (thread-safe - uses local variable)
        tree = self.parser.parse(byte_content)

        query = self._get_compiled_query("window_functions")
        if not query:
            return window_funcs

        try:
            if QueryCursor is not None:
                captures = self._execute_query_with_cursor(query, tree.root_node)
            else:
                raise RuntimeError("QueryCursor not available")

            window_func_nodes = captures.get("window_func", [])

            for func_node in window_func_nodes:
                # Extract function name from the invocation child node
                func_name = "window_function"
                for child in func_node.children:
                    if child.type == "invocation":
                        # The invocation contains the function call
                        # Extract just the invocation text (function name + parens)
                        invocation_text = byte_content[child.start_byte : child.end_byte].decode(
                            "utf-8"
                        )
                        # Get function name (text before first parenthesis)
                        func_name = (
                            invocation_text.split("(")[0].strip()
                            if "(" in invocation_text
                            else invocation_text
                        )
                        break

                # Get surrounding context (line containing the window function)
                context_start = max(0, func_node.start_byte - 50)
                context_end = min(len(byte_content), func_node.end_byte + 50)
                context = byte_content[context_start:context_end].decode("utf-8", errors="replace")

                window_funcs.append(
                    {
                        "function_name": func_name.strip(),
                        "line_number": func_node.start_point[0] + 1,
                        "context": context.strip(),
                    }
                )
        except Exception as e:
            logger.error(f"Error extracting window functions: {e}", exc_info=True)

        return window_funcs

    def extract_stored_procedures(self, byte_content: bytes) -> list[dict]:
        """Extract stored procedure/function definitions from parsed SQL.

        Note: SQLite does not support stored procedures, so this will return
        an empty list for SQLite dialect.

        Args:
            byte_content: SQL source code as bytes

        Returns:
            List of dictionaries containing procedure metadata:
            {
                'name': str,
                'line_number': int,
                'definition': str
            }

        Complexity: O(m) where m is number of CREATE FUNCTION/PROCEDURE statements
        """
        procedures: list[dict[str, Any]] = []

        # SQLite doesn't support stored procedures
        if self.dialect == SqlDialect.SQLITE:
            logger.debug("SQLite does not support stored procedures, returning empty list")
            return procedures

        # Parse SQL content (thread-safe - uses local variable)
        tree = self.parser.parse(byte_content)

        query = self._get_compiled_query("stored_procedures")
        if not query:
            return procedures

        try:
            if QueryCursor is not None:
                captures = self._execute_query_with_cursor(query, tree.root_node)
            else:
                raise RuntimeError("QueryCursor not available")

            proc_defs = captures.get("proc_def", [])
            proc_names = captures.get("proc_name", [])

            for i, proc_node in enumerate(proc_defs):
                name_node = proc_names[i] if i < len(proc_names) else None
                name = (
                    byte_content[name_node.start_byte : name_node.end_byte].decode("utf-8")
                    if name_node
                    else "unknown"
                )

                procedures.append(
                    {
                        "name": name.strip('`"'),
                        "line_number": proc_node.start_point[0] + 1,
                        "definition": byte_content[
                            proc_node.start_byte : proc_node.end_byte
                        ].decode("utf-8"),
                    }
                )
        except Exception as e:
            logger.error(f"Error extracting stored procedures: {e}", exc_info=True)

        return procedures
