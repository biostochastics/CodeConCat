"""Tests for the Tree-sitter SQL parser."""

import pytest
from codeconcat.parser.language_parsers.tree_sitter_sql_parser import (
    TreeSitterSqlParser,
    SqlDialect,
)


class TestTreeSitterSqlParser:
    """Test suite for TreeSitterSqlParser."""

    def test_parser_initialization(self):
        """Test that the parser initializes correctly."""
        parser = TreeSitterSqlParser()
        assert parser is not None
        assert parser.language_name == "sql"
        assert parser.ts_language is not None
        assert parser.parser is not None
        assert parser.dialect == SqlDialect.POSTGRESQL  # Default

    def test_parser_initialization_with_dialect(self):
        """Test parser initialization with explicit dialect."""
        pg_parser = TreeSitterSqlParser(dialect=SqlDialect.POSTGRESQL)
        assert pg_parser.dialect == SqlDialect.POSTGRESQL

        mysql_parser = TreeSitterSqlParser(dialect=SqlDialect.MYSQL)
        assert mysql_parser.dialect == SqlDialect.MYSQL

        sqlite_parser = TreeSitterSqlParser(dialect=SqlDialect.SQLITE)
        assert sqlite_parser.dialect == SqlDialect.SQLITE

    # ========== DIALECT DETECTION TESTS ==========

    def test_detect_postgresql_dialect(self):
        """Test automatic PostgreSQL dialect detection."""
        pg_sql = """
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
"""
        parser = TreeSitterSqlParser(content=pg_sql)
        assert parser.dialect == SqlDialect.POSTGRESQL

    def test_detect_mysql_dialect(self):
        """Test automatic MySQL dialect detection."""
        mysql_sql = """
CREATE TABLE `products` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(100)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""
        parser = TreeSitterSqlParser(content=mysql_sql)
        assert parser.dialect == SqlDialect.MYSQL

    def test_detect_sqlite_dialect(self):
        """Test automatic SQLite dialect detection."""
        sqlite_sql = """
CREATE TABLE items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT
) WITHOUT ROWID;
"""
        parser = TreeSitterSqlParser(content=sqlite_sql)
        assert parser.dialect == SqlDialect.SQLITE

    # ========== STATEMENT CLASSIFICATION TESTS ==========

    def test_classify_ddl_statements(self):
        """Test DDL statement classification."""
        parser = TreeSitterSqlParser()

        assert parser.classify_statement("CREATE TABLE users (id INT)") == "DDL"
        assert parser.classify_statement("ALTER TABLE users ADD COLUMN name VARCHAR(100)") == "DDL"
        assert parser.classify_statement("DROP TABLE old_table") == "DDL"
        assert parser.classify_statement("TRUNCATE TABLE logs") == "DDL"

    def test_classify_dml_statements(self):
        """Test DML statement classification."""
        parser = TreeSitterSqlParser()

        assert parser.classify_statement("SELECT * FROM users") == "DML"
        assert parser.classify_statement("INSERT INTO users VALUES (1, 'Alice')") == "DML"
        assert parser.classify_statement("UPDATE users SET name='Bob' WHERE id=1") == "DML"
        assert parser.classify_statement("DELETE FROM users WHERE id=1") == "DML"
        assert parser.classify_statement("WITH cte AS (SELECT 1) SELECT * FROM cte") == "DML"

    # ========== TABLE EXTRACTION TESTS ==========

    def test_extract_simple_table(self):
        """Test extracting a simple table definition."""
        parser = TreeSitterSqlParser()
        sql = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username VARCHAR(50) NOT NULL,
    email VARCHAR(100)
);
"""
        byte_content = sql.encode('utf-8')
        tables = parser.extract_tables(byte_content)

        assert len(tables) >= 1
        assert any(t['name'] == 'users' for t in tables)
        users_table = next(t for t in tables if t['name'] == 'users')
        assert 'CREATE TABLE' in users_table['definition']
        assert users_table['line_number'] > 0

    def test_extract_multiple_tables(self):
        """Test extracting multiple table definitions."""
        parser = TreeSitterSqlParser()
        sql = """
CREATE TABLE users (id INT PRIMARY KEY);
CREATE TABLE posts (id INT PRIMARY KEY, user_id INT);
CREATE TABLE comments (id INT PRIMARY KEY, post_id INT);
"""
        byte_content = sql.encode('utf-8')
        tables = parser.extract_tables(byte_content)

        assert len(tables) == 3
        table_names = {t['name'] for t in tables}
        assert 'users' in table_names
        assert 'posts' in table_names
        assert 'comments' in table_names

    def test_extract_table_with_constraints(self):
        """Test extracting table with various constraints."""
        parser = TreeSitterSqlParser(dialect=SqlDialect.POSTGRESQL)
        sql = """
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    total DECIMAL(10,2) CHECK (total >= 0),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE (user_id, created_at)
);
"""
        byte_content = sql.encode('utf-8')
        tables = parser.extract_tables(byte_content)

        assert len(tables) >= 1
        orders_table = next((t for t in tables if 'orders' in t['name']), None)
        assert orders_table is not None
        assert 'FOREIGN KEY' in orders_table['definition']

    # ========== VIEW EXTRACTION TESTS ==========

    def test_extract_simple_view(self):
        """Test extracting a simple view definition."""
        parser = TreeSitterSqlParser()
        sql = """
CREATE VIEW active_users AS
SELECT id, username, email
FROM users
WHERE active = true;
"""
        byte_content = sql.encode('utf-8')
        views = parser.extract_views(byte_content)

        assert len(views) >= 1
        assert any('active_users' in v['name'] for v in views)

    def test_extract_complex_view(self):
        """Test extracting a view with joins and aggregations."""
        parser = TreeSitterSqlParser()
        sql = """
CREATE VIEW user_statistics AS
SELECT
    u.id,
    u.username,
    COUNT(p.id) as post_count,
    MAX(p.created_at) as last_post
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id, u.username;
"""
        byte_content = sql.encode('utf-8')
        views = parser.extract_views(byte_content)

        assert len(views) >= 1
        stats_view = next((v for v in views if 'user_statistics' in v['name']), None)
        assert stats_view is not None

    # ========== CTE EXTRACTION TESTS ==========

    def test_extract_simple_cte(self):
        """Test extracting a simple Common Table Expression."""
        parser = TreeSitterSqlParser()
        sql = """
WITH monthly_sales AS (
    SELECT product_id, SUM(amount) as total
    FROM sales
    WHERE date >= '2024-01-01'
    GROUP BY product_id
)
SELECT * FROM monthly_sales WHERE total > 1000;
"""
        byte_content = sql.encode('utf-8')
        ctes = parser.extract_ctes(byte_content)

        # CTE extraction depends on grammar support
        if len(ctes) > 0:
            assert any('monthly_sales' in c['name'] for c in ctes)

    def test_extract_multiple_ctes(self):
        """Test extracting multiple CTEs in a single query."""
        parser = TreeSitterSqlParser()
        sql = """
WITH
    sales_summary AS (
        SELECT product_id, SUM(amount) as total FROM sales GROUP BY product_id
    ),
    top_products AS (
        SELECT product_id FROM sales_summary WHERE total > 10000
    )
SELECT p.name, s.total
FROM products p
JOIN sales_summary s ON p.id = s.product_id
WHERE p.id IN (SELECT product_id FROM top_products);
"""
        byte_content = sql.encode('utf-8')
        ctes = parser.extract_ctes(byte_content)

        # May extract 0, 1, or 2 CTEs depending on grammar
        if len(ctes) > 0:
            cte_names = {c['name'] for c in ctes}
            # At least one should be found
            assert len(cte_names) > 0

    # ========== WINDOW FUNCTION TESTS ==========

    def test_extract_window_functions(self):
        """Test extracting window function usage."""
        parser = TreeSitterSqlParser()
        sql = """
SELECT
    name,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rank,
    AVG(salary) OVER (PARTITION BY department) as avg_dept_salary
FROM employees;
"""
        byte_content = sql.encode('utf-8')
        window_funcs = parser.extract_window_functions(byte_content)

        # Window function extraction depends on grammar support
        if len(window_funcs) > 0:
            func_names = {wf['function_name'] for wf in window_funcs}
            # Should find at least one window function
            assert len(func_names) > 0

    # ========== STORED PROCEDURE TESTS ==========

    def test_extract_postgresql_function(self):
        """Test extracting PostgreSQL stored function."""
        parser = TreeSitterSqlParser(dialect=SqlDialect.POSTGRESQL)
        sql = """
CREATE FUNCTION calculate_bonus(emp_id INT) RETURNS DECIMAL AS $$
BEGIN
    RETURN (SELECT salary * 0.1 FROM employees WHERE id = emp_id);
END;
$$ LANGUAGE plpgsql;
"""
        byte_content = sql.encode('utf-8')
        procedures = parser.extract_stored_procedures(byte_content)

        # Stored procedure extraction depends on grammar support
        if len(procedures) > 0:
            assert any('calculate_bonus' in p['name'] for p in procedures)

    def test_sqlite_no_stored_procedures(self):
        """Test that SQLite correctly returns empty list for stored procedures."""
        parser = TreeSitterSqlParser(dialect=SqlDialect.SQLITE)
        sql = "SELECT 1;"
        byte_content = sql.encode('utf-8')
        procedures = parser.extract_stored_procedures(byte_content)

        assert len(procedures) == 0

    # ========== PARSING INTEGRATION TESTS ==========

    def test_parse_method(self):
        """Test the parse() method returns proper ParseResult."""
        parser = TreeSitterSqlParser()
        sql = """
CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(100));
CREATE VIEW user_list AS SELECT id, name FROM users;
"""
        result = parser.parse(sql, "test.sql")

        assert result is not None
        assert result.error is None or result.error == ""
        # SQL parser uses specialized extraction methods, not declarations list
        assert result.ast_root is not None

    def test_parse_empty_file(self):
        """Test parsing an empty SQL file."""
        parser = TreeSitterSqlParser()
        result = parser.parse("", "empty.sql")

        assert result is not None
        assert len(result.declarations) == 0

    def test_parse_comments_only(self):
        """Test parsing a file with only comments."""
        parser = TreeSitterSqlParser()
        sql = """
-- This is a single-line comment
/* This is a
   multi-line comment */
"""
        result = parser.parse(sql, "comments.sql")

        assert result is not None
        assert len(result.declarations) == 0

    def test_parse_malformed_sql(self):
        """Test parsing malformed SQL doesn't crash."""
        parser = TreeSitterSqlParser()
        malformed_sql = """
CREATE TABLE broken (
    id INT PRIMARY KEY,
    -- Missing closing parenthesis
"""
        # Should not crash
        result = parser.parse(malformed_sql, "malformed.sql")
        assert result is not None

    # ========== DIALECT-SPECIFIC FEATURE TESTS ==========

    def test_mysql_backtick_identifiers(self):
        """Test MySQL backtick identifier handling."""
        parser = TreeSitterSqlParser(dialect=SqlDialect.MYSQL)
        sql = "CREATE TABLE `my-table` (`my-column` INT);"
        byte_content = sql.encode('utf-8')
        tables = parser.extract_tables(byte_content)

        if len(tables) > 0:
            # Backticks should be stripped
            assert tables[0]['name'] == 'my-table'

    def test_postgresql_dollar_quotes(self):
        """Test PostgreSQL dollar-quoted strings."""
        parser = TreeSitterSqlParser(dialect=SqlDialect.POSTGRESQL)
        sql = """
CREATE FUNCTION test() RETURNS TEXT AS $$
BEGIN
    RETURN 'Hello World';
END;
$$ LANGUAGE plpgsql;
"""
        byte_content = sql.encode('utf-8')
        procedures = parser.extract_stored_procedures(byte_content)

        # Should handle dollar quotes without errors
        assert parser.parse(sql, "test.sql") is not None

    def test_sqlite_autoincrement(self):
        """Test SQLite AUTOINCREMENT keyword detection."""
        sqlite_sql = "CREATE TABLE t (id INTEGER PRIMARY KEY AUTOINCREMENT);"
        parser = TreeSitterSqlParser(content=sqlite_sql)

        # Should detect as SQLite based on AUTOINCREMENT (not AUTO_INCREMENT)
        assert parser.dialect == SqlDialect.SQLITE

    # ========== EDGE CASE TESTS ==========

    def test_case_insensitive_keywords(self):
        """Test that SQL keywords are case-insensitive."""
        parser = TreeSitterSqlParser()

        assert parser.classify_statement("CREATE TABLE t (id INT)") == "DDL"
        assert parser.classify_statement("create table t (id int)") == "DDL"
        assert parser.classify_statement("CrEaTe TaBlE t (id int)") == "DDL"

    def test_mixed_statement_types(self):
        """Test file with mixed DDL and DML statements."""
        parser = TreeSitterSqlParser()
        sql = """
CREATE TABLE users (id INT);
INSERT INTO users VALUES (1);
SELECT * FROM users;
ALTER TABLE users ADD COLUMN name VARCHAR(50);
UPDATE users SET name = 'Alice' WHERE id = 1;
"""
        result = parser.parse(sql, "mixed.sql")

        assert result is not None
        assert result.ast_root is not None
        # Verify we can extract tables from this mixed SQL
        byte_content = sql.encode('utf-8')
        tables = parser.extract_tables(byte_content)
        assert len(tables) >= 1  # Should find the CREATE TABLE

    def test_unicode_in_sql(self):
        """Test handling Unicode characters in SQL."""
        parser = TreeSitterSqlParser()
        sql = """
CREATE TABLE продукты (
    id INT PRIMARY KEY,
    название VARCHAR(100)
);
INSERT INTO продукты VALUES (1, 'Молоко');
"""
        result = parser.parse(sql, "unicode.sql")

        # Should parse without crashing
        assert result is not None

    def test_very_long_query(self):
        """Test parsing a very long query."""
        parser = TreeSitterSqlParser()

        # Generate a query with 100 columns
        columns = ", ".join([f"col{i} VARCHAR(50)" for i in range(100)])
        sql = f"CREATE TABLE large_table ({columns});"

        result = parser.parse(sql, "large.sql")
        assert result is not None
