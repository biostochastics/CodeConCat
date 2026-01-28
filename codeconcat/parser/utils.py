"""Parser utility functions for tree-sitter node processing."""

from tree_sitter import Node


def get_node_location(node: Node) -> tuple[int, int]:
    """
    Extract 1-indexed start/end line numbers from tree-sitter Node.

    Args:
        node: Tree-sitter Node object

    Returns:
        Tuple of (start_line, end_line) using 1-based indexing

    Note:
        Tree-sitter uses 0-based indexing, but we convert to 1-based
        for consistency with editor line numbers and user expectations.
    """
    start_line = node.start_point[0] + 1
    end_line = node.end_point[0] + 1
    return start_line, end_line


def get_node_text(node: Node, source_code: bytes) -> str:
    """
    Extract text content from a tree-sitter node.

    Args:
        node: Tree-sitter Node object
        source_code: Original source code as bytes

    Returns:
        Text content of the node as string
    """
    return source_code[node.start_byte : node.end_byte].decode("utf-8")


def find_child_by_type(node: Node, *node_types: str) -> Node | None:
    """
    Find first child node matching any of the given types.

    Args:
        node: Parent node to search
        node_types: One or more node type strings to match

    Returns:
        First matching child node or None if not found
    """
    for child in node.children:
        if child.type in node_types:
            return child
    return None


def find_all_children_by_type(node: Node, *node_types: str) -> list[Node]:
    """
    Find all child nodes matching any of the given types.

    Args:
        node: Parent node to search
        node_types: One or more node type strings to match

    Returns:
        List of matching child nodes
    """
    matches = []
    for child in node.children:
        if child.type in node_types:
            matches.append(child)
    return matches
