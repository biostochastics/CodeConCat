#!/usr/bin/env python3
"""
Basic test for TreeSitterSqlParser implementation.
Verifies parser initialization, dialect detection, and basic extraction.
"""

from codeconcat.parser.language_parsers.tree_sitter_sql_parser import TreeSitterSqlParser, SqlDialect


def test_dialect_detection():
    """Test automatic dialect detection."""
    print("Testing dialect detection...")

    # PostgreSQL
    pg_sql = "CREATE TABLE users (id SERIAL PRIMARY KEY);"
    pg_parser = TreeSitterSqlParser(content=pg_sql)
    assert pg_parser.dialect == SqlDialect.POSTGRESQL, f"Expected POSTGRESQL, got {pg_parser.dialect}"
    print(f"  ✓ PostgreSQL detected correctly")

    # MySQL
    mysql_sql = "CREATE TABLE `products` (`id` INT AUTO_INCREMENT PRIMARY KEY) ENGINE=InnoDB;"
    mysql_parser = TreeSitterSqlParser(content=mysql_sql)
    assert mysql_parser.dialect == SqlDialect.MYSQL, f"Expected MYSQL, got {mysql_parser.dialect}"
    print(f"  ✓ MySQL detected correctly")

    # SQLite
    sqlite_sql = "CREATE TABLE items (id INTEGER PRIMARY KEY AUTOINCREMENT);"
    sqlite_parser = TreeSitterSqlParser(content=sqlite_sql)
    assert sqlite_parser.dialect == SqlDialect.SQLITE, f"Expected SQLITE, got {sqlite_parser.dialect}"
    print(f"  ✓ SQLite detected correctly")


def test_statement_classification():
    """Test DDL/DML classification."""
    print("\nTesting statement classification...")

    parser = TreeSitterSqlParser()

    # DDL
    assert parser.classify_statement("CREATE TABLE users (id INT)") == "DDL"
    assert parser.classify_statement("ALTER TABLE users ADD COLUMN name VARCHAR(100)") == "DDL"
    assert parser.classify_statement("DROP TABLE old_table") == "DDL"
    print("  ✓ DDL statements classified correctly")

    # DML
    assert parser.classify_statement("SELECT * FROM users") == "DML"
    assert parser.classify_statement("INSERT INTO users VALUES (1, 'Alice')") == "DML"
    assert parser.classify_statement("UPDATE users SET name='Bob' WHERE id=1") == "DML"
    assert parser.classify_statement("DELETE FROM users WHERE id=1") == "DML"
    print("  ✓ DML statements classified correctly")


def test_table_extraction():
    """Test table definition extraction."""
    print("\nTesting table extraction...")

    sql = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE
);

CREATE TABLE products (
    id INT PRIMARY KEY,
    name TEXT NOT NULL
);
"""

    parser = TreeSitterSqlParser(dialect=SqlDialect.POSTGRESQL)
    byte_content = sql.encode('utf-8')
    tables = parser.extract_tables(byte_content)

    assert len(tables) == 2, f"Expected 2 tables, got {len(tables)}"
    assert tables[0]['name'] == 'users'
    assert tables[1]['name'] == 'products'
    print(f"  ✓ Extracted {len(tables)} tables correctly")
    for table in tables:
        print(f"    - {table['name']} (line {table['line_number']})")


def test_view_extraction():
    """Test view definition extraction."""
    print("\nTesting view extraction...")

    sql = """
CREATE VIEW active_users AS
SELECT id, username FROM users WHERE active = true;
"""

    parser = TreeSitterSqlParser()
    byte_content = sql.encode('utf-8')
    views = parser.extract_views(byte_content)

    assert len(views) >= 1, f"Expected at least 1 view, got {len(views)}"
    assert 'active_users' in views[0]['name']
    print(f"  ✓ Extracted {len(views)} views correctly")


def main():
    """Run all tests."""
    print("="*60)
    print("TreeSitterSqlParser Basic Tests")
    print("="*60)

    try:
        test_dialect_detection()
        test_statement_classification()
        test_table_extraction()
        test_view_extraction()

        print("\n" + "="*60)
        print("✓ All tests passed!")
        print("="*60)

    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
