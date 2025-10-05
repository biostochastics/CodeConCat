import abc
import logging
from collections import OrderedDict, deque
from typing import Dict, List, Optional, Tuple

from codeconcat.base_types import Declaration, ParseResult, ParserInterface

from ...errors import LanguageParserError
from ...utils.path_security import PathTraversalError, validate_safe_path
from ..error_handling import (
    ErrorHandler,
    ParserInitializationError,
    handle_security_error,
)
from ..type_mapping import standardize_declaration_kind

# Import tree-sitter dependencies with proper error handling
TREE_SITTER_AVAILABLE = False
TREE_SITTER_LANGUAGE_PACK_AVAILABLE = (
    False  # Specifically indicates tree_sitter_language_pack presence
)
TREE_SITTER_LANGUAGES_AVAILABLE = (
    False  # Specifically indicates legacy tree_sitter_languages presence
)
TREE_SITTER_BACKEND: Optional[str] = None  # "tree_sitter_language_pack" or "tree_sitter_languages"

try:
    # Try to import both packages in a single block to reduce filesystem operations
    from tree_sitter import Language, Node, Parser, Query, Tree

    # QueryCursor was removed in tree-sitter 0.24.0 - import it if available for backward compatibility
    try:
        from tree_sitter import QueryCursor
    except ImportError:
        QueryCursor = None  # type: ignore[assignment,misc]

    # Prefer the modern tree_sitter_language_pack backend; fall back to legacy tree_sitter_languages
    try:
        from tree_sitter_language_pack import get_language, get_parser

        TREE_SITTER_BACKEND = "tree_sitter_language_pack"
    except ImportError:
        # Fallback to alternative name if first import fails
        from tree_sitter_languages import (  # type: ignore[no-redef, assignment]
            get_language,
            get_parser,
        )

        TREE_SITTER_BACKEND = "tree_sitter_languages"

    # Set availability flags if imports succeeded
    TREE_SITTER_AVAILABLE = True
    if TREE_SITTER_BACKEND == "tree_sitter_language_pack":
        TREE_SITTER_LANGUAGE_PACK_AVAILABLE = True
    elif TREE_SITTER_BACKEND == "tree_sitter_languages":
        TREE_SITTER_LANGUAGES_AVAILABLE = True
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

    class QueryCursor:  # type: ignore[no-redef]
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

    def __init__(self, language_name: str, max_cache_size: int = 128):
        """Initializes the parser and loads the language grammar.

        Args:
            language_name: The name of the language (e.g., 'python', 'javascript').
            max_cache_size: Maximum number of queries to cache (default: 128).

        Raises:
            LanguageParserError: If the Tree-sitter grammar cannot be loaded or parser creation fails.
        """
        self.language_name = language_name
        self.max_cache_size = max_cache_size
        # Initialize error handler
        self.error_handler = ErrorHandler(self.language_name)

        try:
            # Load the language object first
            self.ts_language: Language = self._load_language()
            # Create the parser instance and set its language
            self.parser: Parser = self._create_parser()
            # Instance-level cache for compiled queries with LRU eviction
            self._query_cache: Dict[Tuple[str, str, str], Optional[Query]] = {}
            # Use OrderedDict for O(1) LRU operations (move_to_end, popitem)
            self._cache_access_order: OrderedDict[Tuple[str, str, str], None] = OrderedDict()
        except Exception as e:
            # Use standardized error handling for initialization failures
            raise ParserInitializationError(
                f"Failed to initialize {self.language_name} parser: {e}",
                parser_name=self.language_name,
                details={"original_error": str(e)},
            ) from e

    def check_language_availability(self) -> bool:
        """Checks if the Tree-sitter language was successfully loaded."""
        # The grammar is loaded in __init__. If it failed, an exception would
        # have been raised. This method confirms the instance is usable.
        return self.parser is not None

    def _compile_query_cached(self, cache_key: Tuple[str, str, str]) -> Optional[Query]:
        """Compile a Tree-sitter query with instance-level LRU caching.

        Args:
            cache_key: Tuple of (language_name, query_name, query_str) for cache key

        Returns:
            Compiled Query object or None if compilation fails
        """
        # Check instance cache first
        if cache_key in self._query_cache:
            # Update access order for LRU
            self._update_cache_access_order(cache_key)
            return self._query_cache[cache_key]

        language_name, query_name, query_str = cache_key

        if not TREE_SITTER_AVAILABLE:
            raise ParserInitializationError(
                "Tree-sitter is not available. Please install it with: pip install tree-sitter-language-pack>=0.7.2",
                parser_name=self.language_name,
            )

        try:
            # Use modern Query() constructor instead of deprecated query() method
            compiled_query = Query(self.ts_language, query_str)
            logger.debug(f"Compiled Tree-sitter query '{query_name}' for {language_name}")

            # Implement LRU cache eviction if needed
            self._evict_cache_if_needed()

            # Cache the result
            self._query_cache[cache_key] = compiled_query
            self._cache_access_order[cache_key] = None
            return compiled_query
        except Exception as e:
            error_msg = (
                f"Failed to compile Tree-sitter query '{query_name}' for {language_name}: {e}"
            )
            logger.error(error_msg, exc_info=True)
            # Cache None to avoid repeated compilation attempts
            self._evict_cache_if_needed()
            self._query_cache[cache_key] = None
            self._cache_access_order[cache_key] = None
            return None

    def _update_cache_access_order(self, cache_key: Tuple[str, str, str]) -> None:
        """Update the access order for LRU cache with O(1) move_to_end."""
        # OrderedDict.move_to_end() is O(1), much better than deque.remove() which is O(n)
        self._cache_access_order.move_to_end(cache_key)

    def _evict_cache_if_needed(self) -> None:
        """Evict oldest entries from cache if it exceeds max size with O(1) popitem."""
        while len(self._query_cache) >= self.max_cache_size:
            if not self._cache_access_order:
                break  # Safety check to avoid infinite loop

            # Use popitem(last=False) for O(1) FIFO eviction
            oldest_key, _ = self._cache_access_order.popitem(last=False)
            if oldest_key in self._query_cache:
                del self._query_cache[oldest_key]
                logger.debug(f"Evicted query from cache: {oldest_key[1]}")

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

    def _execute_query_with_cursor(self, query: Query, root_node: Node):  # type: ignore[no-any-return]
        """Execute a tree-sitter query with version compatibility.

        Handles both tree-sitter 0.23.x (with QueryCursor) and 0.24.0+ (without QueryCursor).
        This method provides a consistent interface for executing queries across different
        tree-sitter versions.

        Args:
            query: Compiled tree-sitter Query object
            root_node: Root node to query against

        Returns:
            Captures from the query execution, or empty dict on failure. Format depends on tree-sitter version:
            - 0.23.x: Returns list of (node, capture_name) tuples
            - 0.24.0+: Returns dict of {capture_name: [nodes]}

        Complexity: O(n) where n is the number of nodes in the tree
        """
        try:
            if QueryCursor is None:
                # tree-sitter 0.24.0+ - use query.captures() directly
                result = query.captures(root_node)
                # 0.24.0+ already returns dict format
                return result if isinstance(result, dict) else {}
            else:
                # tree-sitter 0.23.x - use QueryCursor
                cursor = QueryCursor(query)
                captures = cursor.captures(root_node)
                # Check if already in dict format or needs conversion
                if isinstance(captures, dict):
                    return captures
                # Convert tuple format to dict for consistency
                if captures:
                    result_dict: Dict[str, List[Node]] = {}
                    for item in captures:
                        # Handle both (node, name) tuples and dict entries
                        if isinstance(item, tuple) and len(item) == 2:
                            node, capture_name = item
                            if capture_name not in result_dict:
                                result_dict[capture_name] = []
                            result_dict[capture_name].append(node)
                    return result_dict
                return {}
        except Exception as e:
            logger.warning(
                f"Error executing captures for query on {getattr(root_node, 'type', 'root')}: {e}",
                exc_info=True,
            )
            return {}

    def _execute_query_matches(self, query: Query, root_node: Node):  # type: ignore[no-any-return]
        """Execute a tree-sitter query using matches with version compatibility.

        Similar to _execute_query_with_cursor but uses matches() instead of captures().
        Matches provide structured pattern matching with multiple captures per match.

        Args:
            query: Compiled tree-sitter Query object
            root_node: Root node to query against

        Returns:
            List of matches from the query execution, or empty list on failure. Format depends on tree-sitter version:
            - 0.23.x: Returns list of (match_id, {capture_name: [nodes]}) tuples
            - 0.24.0+: Returns list of (match_id, {capture_name: [nodes]}) tuples

        Complexity: O(n) where n is the number of nodes in the tree
        """
        try:
            if QueryCursor is None:
                # tree-sitter 0.24.0+ - use query.matches() directly
                result = query.matches(root_node)
                # Ensure we return a list, not a generator
                return list(result) if result is not None else []
            else:
                # tree-sitter 0.23.x - use QueryCursor
                cursor = QueryCursor(query)
                result = cursor.matches(root_node)
                # Ensure we return a list, not a generator
                return list(result) if result is not None else []
        except Exception as e:
            logger.warning(
                f"Error executing matches for query on {getattr(root_node, 'type', 'root')}: {e}",
                exc_info=True,
            )
            return []

    def _load_language(self) -> Language:
        """Loads the Tree-sitter language object.

        Uses tree-sitter-language-pack if available, which provides a simple and reliable
        way to load language grammars across different Python versions and platforms.
        Falls back to standalone tree-sitter-<language> packages if not found in the pack.

        Returns:
            Language: The loaded Tree-sitter language object

        Raises:
            LanguageParserError: If the language cannot be loaded
        """
        # Try primary backend first (language_pack or languages)
        if TREE_SITTER_LANGUAGE_PACK_AVAILABLE or TREE_SITTER_LANGUAGES_AVAILABLE:
            try:
                # get_language returns a tree_sitter.Language object directly
                language = get_language(self.language_name)  # type: ignore[arg-type]
                logger.debug(
                    f"Successfully loaded Tree-sitter language for '{self.language_name}' via {TREE_SITTER_BACKEND or 'tree-sitter backend'}"
                )
                return language  # type: ignore
            except (ImportError, KeyError, ValueError) as e:
                # Language not found in pack - try standalone package
                logger.debug(
                    f"'{self.language_name}' not found in {TREE_SITTER_BACKEND}, trying standalone package"
                )

                # Try standalone tree-sitter-<language> package
                try:
                    import importlib

                    # Import tree_sitter_<language>.language() function
                    module_name = f"tree_sitter_{self.language_name}"
                    module = importlib.import_module(module_name)
                    language_fn = getattr(module, "language", None)

                    if language_fn and callable(language_fn):
                        language = language_fn()
                        logger.debug(
                            f"Successfully loaded Tree-sitter language for '{self.language_name}' via standalone package {module_name}"
                        )
                        return language  # type: ignore
                    else:
                        raise AttributeError(
                            f"Module {module_name} has no callable 'language' function"
                        )
                except (ImportError, AttributeError) as standalone_error:
                    logger.error(
                        f"Failed to load '{self.language_name}' from both {TREE_SITTER_BACKEND} and standalone package: {standalone_error}"
                    )
                    raise LanguageParserError(
                        f"Could not load Tree-sitter language for {self.language_name}. "
                        f"Tried {TREE_SITTER_BACKEND} (not found) and standalone package tree-sitter-{self.language_name} (failed). "
                        f"Install with: pip install tree-sitter-{self.language_name}"
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
            # No backend is available
            # Provide a helpful error message directing the user to install the preferred backend
            logger.error(
                f"Cannot load Tree-sitter language for '{self.language_name}'. "
                f"No Tree-sitter backend is available. Install with: pip install tree-sitter-language-pack>=0.7.2"
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
            if TREE_SITTER_LANGUAGE_PACK_AVAILABLE or TREE_SITTER_LANGUAGES_AVAILABLE:
                parser = get_parser(self.language_name)  # type: ignore[arg-type]
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
            error_msg = f"Failed to create parser for {self.language_name}: {e}"
            logger.error(error_msg)
            raise ParserInitializationError(
                error_msg, parser_name=self.language_name, details={"original_error": str(e)}
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

        # Security: Validate file path to prevent path traversal
        try:
            # Validate the file path is safe
            validated_path = validate_safe_path(file_path)
            logger.debug(f"Validated file path: {validated_path}")
        except PathTraversalError as e:
            return handle_security_error(
                f"Path traversal attempt detected for {file_path}: {e}",
                self.language_name,
                file_path,
                {"validation_error": str(e)},
            )
        except Exception as e:
            return self.error_handler.handle_error(
                f"Path validation failed for {file_path}: {e}",
                file_path,
                context={"validation_error": str(e)},
            )

        # Security: Check content size to prevent memory exhaustion
        max_content_size = 10 * 1024 * 1024  # 10MB limit
        # First check string length (faster, approximate for non-ASCII)
        if len(content) > max_content_size:
            return handle_security_error(
                f"File too large for parsing: {len(content)} characters (max: {max_content_size})",
                self.language_name,
                file_path,
                {"content_size": len(content), "max_size": max_content_size},
            )
        # Encode content once for both size check and parsing (optimization: avoid double encoding)
        content_bytes = content.encode("utf-8")

        # For more accurate byte count, check encoded size only if close to limit
        if len(content) > max_content_size * 0.8:  # Check if within 80% of limit
            content_size_bytes = len(content_bytes)
            if content_size_bytes > max_content_size:
                return handle_security_error(
                    f"File too large for parsing: {content_size_bytes} bytes (max: {max_content_size})",
                    self.language_name,
                    file_path,
                    {"content_size": content_size_bytes, "max_size": max_content_size},
                )

        # --- Add diagnostic logging --- #
        parser_state = f"Parser: {type(self.parser).__name__ if self.parser else 'None'}"
        lang_state = f"Language: {type(self.ts_language).__name__ if self.ts_language else 'None'}"
        logger.debug(f"[Parse Check] State before parse call: {parser_state}, {lang_state}")
        # ----------------------------- #

        if not self.parser or not self.ts_language:
            return self.error_handler.handle_error(
                f"Parser or language not loaded for {self.language_name}. Cannot parse {file_path}.",
                file_path,
                context={"parser_state": "uninitialized"},
            )

        tree: Optional[Tree] = None
        try:
            logger.debug(f"Attempting self.parser.parse() for {file_path}")
            tree = self.parser.parse(content_bytes)
            logger.debug(f"Finished self.parser.parse() for {file_path}")
        except Exception as e:
            return self.error_handler.handle_error(
                f"Exception occurred during self.parser.parse() for {file_path}: {e}",
                file_path,
                context={"exception_type": type(e).__name__},
            )

        # Check if parsing was successful even if no exception was raised
        if tree is None:
            return self.error_handler.handle_error(
                f"Tree-sitter parsing returned None for {file_path}",
                file_path,
                context={"tree_result": "null"},
            )

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
            try:
                declarations, imports = self._run_queries(root_node, content_bytes)
                return self.error_handler.handle_partial_parse(
                    declarations,
                    imports,
                    f"Tree-sitter parsing error near line {line}, column {col}",
                    file_path,
                    line_number=line,
                    context={"error_node_type": error_node.type if error_node else "unknown"},
                    missed_features=["error_recovery"],
                    ast_root=root_node,
                )
            except Exception as e:
                # If even partial extraction fails, return error
                return self.error_handler.handle_error(
                    f"Failed to extract declarations after parsing error: {e}",
                    file_path,
                    line_number=line,
                    context={
                        "original_error": f"Tree-sitter parsing error near line {line}, column {col}"
                    },
                )
        else:
            try:
                declarations, imports = self._run_queries(root_node, content_bytes)
                return self.error_handler.create_success_result(
                    declarations,
                    imports,
                    file_path,
                    context={"root_node_type": root_node.type},
                    ast_root=root_node,
                )
            except Exception as e:
                # If extraction fails after successful parsing
                return self.error_handler.handle_partial_parse(
                    [],
                    [],
                    f"Failed to extract declarations after successful parsing: {e}",
                    file_path,
                    context={"root_node_type": root_node.type, "extraction_error": str(e)},
                    missed_features=["declaration_extraction"],
                    ast_root=root_node,
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
                # Query API changed in tree-sitter 0.24.0
                # Old API: QueryCursor(query).captures(node)
                # New API: query.captures(node)
                if QueryCursor is not None:
                    # Use legacy QueryCursor API for older tree-sitter versions
                    cursor = QueryCursor(query)
                    captures = cursor.captures(root_node)
                else:
                    # Use modern API (tree-sitter 0.24.0+)
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
                    # Use matches for better structure
                    if QueryCursor is not None:
                        matches = cursor.matches(root_node)  # type: ignore[possibly-undefined]
                    else:
                        matches = query.matches(root_node)
                    logger.debug(f"Processing {len(matches)} matches for declarations.")
                    for match_id, captures_in_match in matches:
                        declaration_node = None
                        name_node = None
                        kind = None

                        # Determine the kind and main node based on the @capture name
                        # The capture names (@function, @class, @object, @property, etc.) must match the query
                        # Each capture value is a list of nodes, even if there's only one

                        # Try all common declaration types
                        declaration_types = [
                            "function",
                            "class",
                            "object",
                            "property",
                            "interface",
                            "enum",
                            "struct",
                            "trait",
                            "protocol",
                            "module",
                            "macro",
                        ]

                        for decl_type in declaration_types:
                            if decl_type in captures_in_match:
                                decl_nodes = captures_in_match[decl_type]
                                if decl_nodes and len(decl_nodes) > 0:
                                    declaration_node = decl_nodes[0]
                                    kind = decl_type
                                name_nodes = captures_in_match.get("name", [])
                                if name_nodes and len(name_nodes) > 0:
                                    name_node = name_nodes[0]
                                break

                        if declaration_node and name_node and kind:
                            decl_name = byte_content[
                                name_node.start_byte : name_node.end_byte
                            ].decode("utf8", errors="replace")
                            start_line = declaration_node.start_point[0] + 1  # TS is 0-indexed
                            end_line = declaration_node.end_point[0] + 1

                            # Standardize the kind using the type mapping
                            standardized_kind = standardize_declaration_kind(
                                self.language_name, kind
                            )

                            # TODO: Extract signature and docstring if queries support them
                            declarations.append(
                                Declaration(
                                    name=decl_name,
                                    kind=standardized_kind,
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
        # Use deque for O(1) popleft and extend operations instead of O(n) list.pop(0)
        nodes_to_check = deque([(node, current_depth)])

        while nodes_to_check:
            # Use popleft() for O(1) operation instead of pop(0) which is O(n)
            check_node, depth = nodes_to_check.popleft()

            if depth >= max_depth:
                logger.warning(
                    f"Maximum recursion depth ({max_depth}) reached while searching for error nodes"
                )
                continue

            if check_node.is_error or check_node.is_missing:
                return check_node

            # Use extend() to efficiently add children to the queue (breadth-first search)
            if check_node.children:
                nodes_to_check.extend((child, depth + 1) for child in check_node.children)

        return None
