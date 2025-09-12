import abc
import logging
from typing import Dict, List, Optional

from codeconcat.base_types import Declaration, ParseResult, ParserInterface

from ...errors import LanguageParserError

# Import tree-sitter dependencies with proper error handling
TREE_SITTER_AVAILABLE = False
TREE_SITTER_LANGUAGE_PACK_AVAILABLE = False
TREE_SITTER_BACKEND: Optional[str] = None  # "tree_sitter_language_pack" or "tree_sitter_languages"

try:
    # Try to import both packages in a single block to reduce filesystem operations
    from tree_sitter import Language, Node, Parser, Query, Tree

    # Prefer the modern tree_sitter_language_pack backend; fall back to legacy tree_sitter_languages
    try:
        from tree_sitter_language_pack import get_language, get_parser

        TREE_SITTER_BACKEND = "tree_sitter_language_pack"
    except ImportError:
        # Fallback to alternative name if first import fails
        from tree_sitter_languages import get_language, get_parser

        TREE_SITTER_BACKEND = "tree_sitter_languages"

    # Set availability flags if imports succeeded
    TREE_SITTER_AVAILABLE = True
    TREE_SITTER_LANGUAGE_PACK_AVAILABLE = True
except ImportError:
    # Create dummy classes to avoid type errors
    class Language:  # type: ignore[no-redef]
        pass

    class Node:  # type: ignore[no-redef]
        pass

    class Parser:  # type: ignore[no-redef]
        pass

    class Tree:  # type: ignore[no-redef]
        pass

    class Query:  # type: ignore[no-redef]
        pass

    # Try to determine which package is missing for more helpful error messages
    try:
        from tree_sitter import Language

        # If we get here, tree-sitter is available but tree-sitter-language-pack isn't
        TREE_SITTER_AVAILABLE = True
        logger = logging.getLogger(__name__)
        logger.warning(
            "tree-sitter-language-pack not found, language loading may fail on Python 3.12+"
        )
    except ImportError:
        # Both packages are missing
        logger = logging.getLogger(__name__)
        logger.warning(
            "tree-sitter not available. Install with: pip install tree-sitter tree-sitter-language-pack>=0.7.2"
        )

logger = logging.getLogger(__name__)


class BaseTreeSitterParser(ParserInterface, abc.ABC):
    """Abstract Base Class for Tree-sitter based parsers.

    This class provides a robust foundation for language-specific parsers using
    the Tree-sitter parsing library. It handles grammar loading, query compilation,
    and provides a consistent interface for extracting declarations and imports
    from source code across different programming languages.

    The parser implements a caching mechanism for compiled queries to improve
    performance and includes comprehensive error handling with fallback support.

    Attributes:
        language_name: Name of the programming language (e.g., 'python', 'javascript')
        ts_language: The loaded Tree-sitter language grammar object
        parser: The Tree-sitter parser instance configured for the language
        _compiled_queries: Cache of compiled Tree-sitter queries for performance

    Complexity:
        - Initialization: O(1) + grammar loading time
        - Parsing: O(n) where n is the length of the source code
        - Query execution: O(m) where m is the number of AST nodes
        - Cached query retrieval: O(1)
    """

    def __init__(self, language_name: str):
        """Initializes the parser and loads the language grammar.

        Args:
            language_name: The name of the language (e.g., 'python', 'javascript').

        Raises:
            LanguageParserError: If the Tree-sitter grammar cannot be loaded or parser creation fails.
        """
        self.language_name = language_name
        # Load the language object first
        self.ts_language: Language = self._load_language()
        # Create the parser instance and set its language
        self.parser: Parser = self._create_parser()
        # Instance-level cache for compiled queries to avoid memory leaks
        self._query_cache: Dict[tuple, Optional[Query]] = {}

    def check_language_availability(self) -> bool:
        """Checks if the Tree-sitter language was successfully loaded."""
        # The grammar is loaded in __init__. If it failed, an exception would
        # have been raised. This method confirms the instance is usable.
        return self.parser is not None

    def _compile_query_cached(self, cache_key: tuple) -> Optional[Query]:
        """Compile a Tree-sitter query with instance-level caching.

        Args:
            cache_key: Tuple of (language_name, query_name, query_str) for cache key

        Returns:
            Compiled Query object or None if compilation fails
        """
        # Check instance cache first
        if cache_key in self._query_cache:
            return self._query_cache[cache_key]

        language_name, query_name, query_str = cache_key

        if not TREE_SITTER_AVAILABLE:
            raise LanguageParserError(
                "Tree-sitter is not available. Please install it with: pip install tree-sitter-language-pack>=0.7.2"
            )

        try:
            compiled_query = self.ts_language.query(query_str)
            logger.debug(f"Compiled Tree-sitter query '{query_name}' for {language_name}")
            # Cache the result
            self._query_cache[cache_key] = compiled_query
            return compiled_query
        except Exception as e:
            logger.error(
                f"Failed to compile Tree-sitter query '{query_name}' for {language_name}: {e}",
                exc_info=True,
            )
            # Cache None to avoid repeated compilation attempts
            self._query_cache[cache_key] = None
            return None

    def _get_compiled_query(self, query_name: str) -> Query | None:
        """Gets a compiled Tree-sitter query using instance cache.

        Args:
            query_name: The name of the query to compile.

        Returns:
            The compiled Tree-sitter Query object.
        """
        query_str = self.get_queries().get(query_name, "")
        if not query_str:
            logger.warning(
                f"No query string found for '{query_name}' in {self.language_name} parser"
            )
            return None

        # Create a hashable cache key
        cache_key = (self.language_name, query_name, query_str)
        result = self._compile_query_cached(cache_key)
        return result if result is not None else None

    def _load_language(self) -> Language:
        """Loads the Tree-sitter language object.

        Uses tree-sitter-language-pack if available, which provides a simple and reliable
        way to load language grammars across different Python versions and platforms.

        Returns:
            Language: The loaded Tree-sitter language object

        Raises:
            LanguageParserError: If the language cannot be loaded
        """
        # Use tree-sitter-language-pack if available (preferred method)
        if TREE_SITTER_LANGUAGE_PACK_AVAILABLE:
            try:
                # get_language returns a tree_sitter.Language object directly
                language = get_language(self.language_name)
                logger.debug(
                    f"Successfully loaded Tree-sitter language for '{self.language_name}' via {TREE_SITTER_BACKEND or 'tree-sitter backend'}"
                )
                return language  # type: ignore
            except (ImportError, KeyError, ValueError) as e:
                # ImportError: Package not installed
                # KeyError: Language not found in pack
                # ValueError: Invalid language name
                logger.error(
                    f"Failed to load '{self.language_name}' with {TREE_SITTER_BACKEND or 'tree-sitter backend'}: {e}"
                )
                raise LanguageParserError(
                    f"Could not load Tree-sitter language for {self.language_name} using {TREE_SITTER_BACKEND or 'tree-sitter backend'}. "
                    f"Error: {e}. Ensure the backend is installed and the language name is correct."
                ) from e
            except Exception as e:
                # Any other unexpected error
                logger.error(
                    f"Unexpected error loading '{self.language_name}' with {TREE_SITTER_BACKEND or 'tree-sitter backend'}: {e}",
                    exc_info=True,
                )
                raise LanguageParserError(
                    f"Unexpected error loading Tree-sitter language for {self.language_name} using {TREE_SITTER_BACKEND or 'tree-sitter backend'}: {e}"
                ) from e
        else:
            # tree-sitter-language-pack is not available
            # This is a helpful error message directing the user to install it
            logger.error(
                f"Cannot load Tree-sitter language for '{self.language_name}'. "
                f"The tree-sitter-language-pack package is required for reliable language loading."
            )
            raise LanguageParserError(
                f"Could not load Tree-sitter language for {self.language_name}. "
                f"Please install tree-sitter-language-pack: 'pip install tree-sitter-language-pack'"
            )

    def _create_parser(self) -> Parser:
        """Creates the Parser instance and sets its language.

        Uses tree-sitter-language-pack's get_parser if available, which returns a pre-configured
        parser instance. Falls back to manual parser creation if not available.

        Returns:
            Parser: A configured Tree-sitter parser for this language

        Raises:
            LanguageParserError: If parser creation fails
        """
        try:
            # Use the backend's pre-configured parser if available
            if TREE_SITTER_LANGUAGE_PACK_AVAILABLE:
                parser = get_parser(self.language_name)
                logger.debug(
                    f"Created parser for {self.language_name} via {TREE_SITTER_BACKEND or 'tree-sitter backend'}"
                )
                return parser  # type: ignore[no-any-return]

            # Fall back to manual parser creation if tree-sitter-language-pack is not available
            # This is a backup option and should generally not be needed
            parser = Parser()
            parser.language = self.ts_language  # type: ignore[attr-defined]
            logger.debug(f"Created parser for {self.language_name} manually")
            return parser
        except Exception as e:
            logger.error(f"Failed to create parser for {self.language_name}: {e}")
            raise LanguageParserError(
                f"Failed to create parser for {self.language_name}: {e}"
            ) from e

    @abc.abstractmethod
    def get_queries(self) -> Dict[str, str]:
        """Returns a dictionary of Tree-sitter queries for the language.

        Keys should describe the query (e.g., 'declarations', 'imports'),
        and values should be the S-expression query strings.

        Returns:
            Dict mapping query names to Tree-sitter S-expression query strings.
            Expected keys include:
            - 'declarations': Query to extract functions, classes, methods
            - 'imports': Query to extract import statements
            - 'doc_comments': (Optional) Query to extract documentation

        Example:
            {
                'declarations': '(function_definition name: (identifier) @name) @function',
                'imports': '(import_statement) @import_statement'
            }

        Complexity: O(1) - Returns a static dictionary
        """
        pass

    def extract_signature(self, node: Node, byte_content: bytes) -> str:
        """Extract function/method signature from a declaration node.

        Args:
            node: The declaration node
            byte_content: The source code as bytes

        Returns:
            The extracted signature string
        """
        try:
            # Find parameter list node
            params_node = None
            for child in node.children:
                if child.type in ["parameters", "formal_parameters", "parameter_list"]:
                    params_node = child
                    break

            if params_node:
                params_text = byte_content[params_node.start_byte : params_node.end_byte].decode(
                    "utf-8", errors="replace"
                )
                return params_text.strip()
        except Exception as e:
            logger.debug(f"Failed to extract signature: {e}")
        return ""

    def extract_modifiers(self, node: Node, byte_content: bytes) -> set:
        """Extract modifiers from a declaration node.

        Args:
            node: The declaration node
            byte_content: The source code as bytes

        Returns:
            Set of modifier strings
        """
        modifiers = set()
        try:
            # Look for common modifier keywords in the node's text
            node_text = byte_content[node.start_byte : node.end_byte].decode(
                "utf-8", errors="replace"
            )

            # Common modifiers across languages
            modifier_keywords = {
                "public",
                "private",
                "protected",
                "static",
                "async",
                "const",
                "final",
                "abstract",
                "virtual",
                "override",
                "inline",
                "extern",
                "export",
            }

            for keyword in modifier_keywords:
                if f" {keyword} " in f" {node_text} " or node_text.startswith(f"{keyword} "):
                    modifiers.add(keyword)

        except Exception as e:
            logger.debug(f"Failed to extract modifiers: {e}")
        return modifiers

    def parse(self, content: str, file_path: str) -> ParseResult:
        """Parses the code content using Tree-sitter and extracts information.

        Args:
            content: The code content as a string.
            file_path: The path to the file being parsed.

        Returns:
            A ParseResult object.
        """
        logger.debug(f"Starting Tree-sitter parsing for: {file_path} ({self.language_name})")

        # --- Add diagnostic logging --- #
        parser_state = f"Parser: {type(self.parser).__name__ if self.parser else 'None'}"
        lang_state = f"Language: {type(self.ts_language).__name__ if self.ts_language else 'None'}"
        logger.debug(f"[Parse Check] State before parse call: {parser_state}, {lang_state}")
        # ----------------------------- #

        if not self.parser or not self.ts_language:
            logger.error(
                f"Parser or language not loaded for {self.language_name}. Cannot parse {file_path}."
            )
            # Return empty result or raise an error, depending on desired handling
            return ParseResult(declarations=[], imports=[])

        tree: Optional[Tree] = None
        try:
            content_bytes = content.encode("utf-8")
            logger.debug(f"Attempting self.parser.parse() for {file_path}")
            tree = self.parser.parse(content_bytes)
            logger.debug(f"Finished self.parser.parse() for {file_path}")
        except Exception as e:
            logger.error(
                f"Exception occurred during self.parser.parse() for {file_path}: {e}",
                exc_info=True,  # Log the full traceback
            )
            # Decide how to handle: return empty, raise, etc.
            return ParseResult(declarations=[], imports=[])

        # Check if parsing was successful even if no exception was raised
        if tree is None:
            logger.error(f"Tree-sitter parsing returned None for {file_path}")
            return ParseResult(declarations=[], imports=[])

        root_node: Node = tree.root_node

        logger.debug(f"Root node type: {root_node.type}, Has Error: {root_node.has_error}")
        # Log node structure for debugging (modern tree-sitter API doesn't have sexp() method)
        logger.debug(
            f"Root node structure - Type: {root_node.type}, Start: {root_node.start_point}, End: {root_node.end_point}"
        )
        try:
            # Try to get string representation of the node structure instead of sexp
            # This is more compatible with different tree-sitter versions
            node_str = f"Node({root_node.type}, children: {len(root_node.children)})"
            logger.debug(f"Root node representation: {node_str}")

            # Log some children information if available
            if hasattr(root_node, "children") and root_node.children:
                child_types = [child.type for child in root_node.children[:5]]
                logger.debug(f"First few child types: {child_types}")
        except Exception as node_err:
            logger.debug(f"Could not get detailed node information: {node_err}")

        if root_node.has_error:
            # Basic error reporting - find first error node
            error_node = self._find_first_error_node(root_node)
            line = error_node.start_point[0] + 1 if error_node else 1
            col = error_node.start_point[1] if error_node else 0
            logger.warning(
                f"Tree-sitter parsing error detected near line {line}, column {col} in file {file_path}"
            )
            # Still attempt extraction, but report error
            declarations, imports = self._run_queries(root_node, content_bytes)
            return ParseResult(
                declarations=declarations,
                imports=imports,
                ast_root=root_node,  # Include AST root even if errors exist
                error=f"Tree-sitter parsing error near line {line}, column {col}",
                engine_used="tree_sitter",
                parser_quality="partial",
                missed_features=["error_recovery"],
            )
        else:
            declarations, imports = self._run_queries(root_node, content_bytes)
            return ParseResult(
                declarations=declarations,
                imports=imports,
                ast_root=root_node,
                error=None,
                engine_used="tree_sitter",
                parser_quality="full",
                missed_features=[],
            )

    def _run_queries(
        self, root_node: Node, byte_content: bytes
    ) -> tuple[List[Declaration], List[str]]:
        """Runs the language-specific queries against the parsed tree."""
        queries = self.get_queries()
        declarations = []
        imports = []

        for query_name in queries:
            # Get the compiled query from cache or compile it if not cached yet
            query = self._get_compiled_query(query_name)
            if not query:  # Skip if no valid query was found or compiled
                continue

            try:
                captures = query.captures(root_node)
                logger.debug(f"Running query '{query_name}', found {len(captures)} captures.")

                if query_name == "imports":
                    # captures is a dict of {capture_name: [list of nodes]}
                    for capture_name, nodes in captures.items():
                        # Check capture name matches query (@import_statement or @import_from_statement)
                        if capture_name in ["import_statement", "import_from_statement"]:
                            for node in nodes:
                                import_text = byte_content[node.start_byte : node.end_byte].decode(
                                    "utf8", errors="replace"
                                )
                                # Basic cleanup: remove extra whitespace/newlines
                                imports.append(" ".join(import_text.split()))

                elif query_name == "declarations":
                    # Use query.matches for better structure
                    matches = query.matches(root_node)
                    logger.debug(f"Processing {len(matches)} matches for declarations.")
                    for match_id, captures_in_match in matches:
                        declaration_node = None
                        name_node = None
                        kind = None

                        # Determine the kind and main node based on the @capture name
                        # The capture names (@function, @class) must match the query
                        # Each capture value is a list of nodes, even if there's only one
                        if "function" in captures_in_match:
                            func_nodes = captures_in_match["function"]
                            if func_nodes and len(func_nodes) > 0:
                                declaration_node = func_nodes[0]
                                kind = "function"
                            name_nodes = captures_in_match.get("name", [])
                            if name_nodes and len(name_nodes) > 0:
                                name_node = name_nodes[0]
                        elif "class" in captures_in_match:
                            class_nodes = captures_in_match["class"]
                            if class_nodes and len(class_nodes) > 0:
                                declaration_node = class_nodes[0]
                                kind = "class"
                            name_nodes = captures_in_match.get("name", [])
                            if name_nodes and len(name_nodes) > 0:
                                name_node = name_nodes[0]
                        # Add elif for async_function, lambda_function etc. if defined in query

                        if declaration_node and name_node and kind:
                            decl_name = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")
                            start_line = declaration_node.start_point[0] + 1  # TS is 0-indexed
                            end_line = declaration_node.end_point[0] + 1

                            # TODO: Extract signature and docstring if queries support them
                            declarations.append(
                                Declaration(
                                    name=decl_name,
                                    kind=kind,
                                    start_line=start_line,
                                    end_line=end_line,
                                    # signature="", # Placeholder
                                    # docstring=""  # Placeholder
                                )
                            )
                        else:
                            # Log if a match didn't yield the expected captures
                            capture_keys = list(captures_in_match.keys())
                            logger.debug(
                                f"Declaration match {match_id} did not yield expected nodes. Captures: {capture_keys}"
                            )

                # Add handling for other query types (e.g., comments, docstrings)
                # elif query_name == "doc_comments": ...

            except Exception as e:
                logger.warning(
                    f"Failed to execute or process Tree-sitter query '{query_name}' for {self.language_name}: {e}",
                    exc_info=True,  # Log traceback for debugging
                )

        # Deduplicate imports
        imports = sorted(set(imports))
        logger.debug(
            f"Tree-sitter extracted {len(declarations)} declarations and {len(imports)} imports."
        )
        return declarations, imports

    def _find_first_error_node(
        self, node: Node, max_depth: int = 100, current_depth: int = 0
    ) -> Optional[Node]:
        """Helper to find the first node marked as an error in the tree.

        Args:
            node: The AST node to search from
            max_depth: Maximum recursion depth to prevent stack overflow (default: 100)
            current_depth: Current recursion depth (used internally)

        Returns:
            The first error node found, or None if no errors or max depth reached
        """
        # Prevent stack overflow on deeply nested ASTs
        if current_depth >= max_depth:
            logger.warning(
                f"Maximum recursion depth ({max_depth}) reached while searching for error nodes"
            )
            return None

        if node.is_error or node.is_missing:
            return node
        for child in node.children:
            error_node = self._find_first_error_node(child, max_depth, current_depth + 1)
            if error_node:
                return error_node
        return None
