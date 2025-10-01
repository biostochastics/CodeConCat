#!/usr/bin/env python3
"""
Proof of concept script to test tree-sitter-sql grammar capabilities.
Tests parsing of PostgreSQL, MySQL, and SQLite SQL samples.
"""

import tree_sitter_sql as tssql
from tree_sitter import Parser, Node, Language
from typing import List, Dict, Any


def print_tree(node: Node, indent: int = 0, max_depth: int = 5) -> None:
    """Recursively print the syntax tree."""
    if indent > max_depth:
        return

    node_type = node.type
    if node.is_named:
        text = node.text.decode('utf-8')[:50] if node.text else ""
        print("  " * indent + f"{node_type}: {repr(text)}")

    for child in node.children:
        print_tree(child, indent + 1, max_depth)


def collect_node_types(node: Node, types: set) -> None:
    """Collect all unique node types in the tree."""
    types.add(node.type)
    for child in node.children:
        collect_node_types(child, types)


def test_sql_sample(parser: Parser, sql: str, dialect: str) -> Dict[str, Any]:
    """Test parsing a SQL sample and return analysis."""
    print(f"\n{'='*80}")
    print(f"Testing {dialect}")
    print(f"{'='*80}")
    print(f"SQL:\n{sql}\n")

    tree = parser.parse(bytes(sql, "utf8"))

    # Check for errors
    errors = []
    def find_errors(node: Node):
        if node.type == "ERROR" or node.has_error:
            errors.append({
                'node': node.type,
                'text': node.text.decode('utf-8') if node.text else "",
                'position': (node.start_point, node.end_point)
            })
        for child in node.children:
            find_errors(child)

    find_errors(tree.root_node)

    # Collect node types
    node_types: set[str] = set()
    collect_node_types(tree.root_node, node_types)

    print(f"Parse Status: {'✗ ERRORS' if errors else '✓ SUCCESS'}")
    if errors:
        print(f"Errors found: {len(errors)}")
        for err in errors[:3]:  # Show first 3 errors
            print(f"  - {err['node']}: {err['text'][:50]}")

    print(f"\nNode types found ({len(node_types)}):")
    print(f"  {', '.join(sorted(node_types)[:10])}...")

    print(f"\nSyntax Tree (depth limited to 3):")
    print_tree(tree.root_node, max_depth=3)

    return {
        'dialect': dialect,
        'success': len(errors) == 0,
        'errors': errors,
        'node_types': node_types,
        'tree': tree
    }


def main():
    """Test tree-sitter-sql grammar with samples from each dialect."""

    # Initialize parser - tree-sitter-sql provides language() function that returns a PyCapsule
    # We need to wrap it in a Language object for tree-sitter 0.24.0+
    SQL_LANGUAGE = Language(tssql.language())
    parser = Parser()
    parser.language = SQL_LANGUAGE

    # Test samples for each dialect

    # PostgreSQL sample
    postgresql_sample = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE VIEW active_users AS
SELECT id, username, email
FROM users
WHERE created_at > NOW() - INTERVAL '30 days';

WITH monthly_stats AS (
    SELECT
        DATE_TRUNC('month', created_at) as month,
        COUNT(*) as user_count,
        ROW_NUMBER() OVER (ORDER BY COUNT(*) DESC) as rank
    FROM users
    GROUP BY month
)
SELECT * FROM monthly_stats WHERE rank <= 5;

CREATE FUNCTION get_user_count() RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM users);
END;
$$ LANGUAGE plpgsql;
"""

    # MySQL sample
    mysql_sample = """
CREATE TABLE `products` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100) NOT NULL,
    `price` DECIMAL(10, 2),
    `stock` INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

SELECT p.name, p.price, p.stock
FROM products p
WHERE p.stock > 0;

INSERT INTO products (name, price, stock) VALUES ('Widget', 19.99, 100);
UPDATE products SET stock = stock - 1 WHERE id = 1;
DELETE FROM products WHERE stock = 0;
"""

    # SQLite sample
    sqlite_sample = """
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    value REAL,
    quantity INTEGER DEFAULT 0
);

SELECT * FROM items WHERE quantity > 0;

CREATE VIEW expensive_items AS
SELECT id, name, value FROM items WHERE value > 100.0;
"""

    # Run tests
    results = []
    results.append(test_sql_sample(parser, postgresql_sample, "PostgreSQL"))
    results.append(test_sql_sample(parser, mysql_sample, "MySQL"))
    results.append(test_sql_sample(parser, sqlite_sample, "SQLite"))

    # Summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    for result in results:
        status = "✓ PASS" if result['success'] else "✗ FAIL"
        print(f"{result['dialect']:20} {status:10} {len(result['node_types'])} unique node types")

    # Analyze common node types
    all_types = set()
    for result in results:
        all_types.update(result['node_types'])

    print(f"\nTotal unique node types across all dialects: {len(all_types)}")
    print("\nKey node types for our parser:")
    key_types = [t for t in all_types if any(keyword in t.lower() for keyword in
                 ['create', 'select', 'insert', 'update', 'delete', 'with', 'cte',
                  'window', 'over', 'table', 'view', 'function', 'procedure'])]
    for t in sorted(key_types):
        print(f"  - {t}")


if __name__ == "__main__":
    main()
