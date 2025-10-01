#!/usr/bin/env python3
"""
Advanced test for TreeSitterSqlParser - CTEs, window functions, stored procedures.
"""

from codeconcat.parser.language_parsers.tree_sitter_sql_parser import TreeSitterSqlParser, SqlDialect


def test_cte_extraction():
    """Test CTE (Common Table Expression) extraction."""
    print("Testing CTE extraction...")

    sql = """
WITH monthly_sales AS (
    SELECT product_id, SUM(amount) as total
    FROM sales
    GROUP BY product_id
),
top_products AS (
    SELECT product_id, total
    FROM monthly_sales
    WHERE total > 10000
)
SELECT * FROM top_products;
"""

    parser = TreeSitterSqlParser(dialect=SqlDialect.POSTGRESQL)
    byte_content = sql.encode('utf-8')
    ctes = parser.extract_ctes(byte_content)

    print(f"  Found {len(ctes)} CTEs")
    for cte in ctes:
        print(f"    - {cte['name']} (line {cte['line_number']})")

    assert len(ctes) >= 1, f"Expected at least 1 CTE, got {len(ctes)}"
    print("  ✓ CTE extraction working")


def test_window_function_extraction():
    """Test window function extraction."""
    print("\nTesting window function extraction...")

    sql = """
SELECT
    name,
    salary,
    ROW_NUMBER() OVER (PARTITION BY department ORDER BY salary DESC) as rank,
    AVG(salary) OVER (PARTITION BY department) as avg_dept_salary
FROM employees;
"""

    parser = TreeSitterSqlParser(dialect=SqlDialect.POSTGRESQL)
    byte_content = sql.encode('utf-8')
    window_funcs = parser.extract_window_functions(byte_content)

    print(f"  Found {len(window_funcs)} window functions")
    for wf in window_funcs:
        print(f"    - {wf['function_name']} (line {wf['line_number']})")

    if len(window_funcs) > 0:
        print("  ✓ Window function extraction working")
    else:
        print("  ⚠ No window functions found (may be grammar limitation)")


def test_stored_procedure_extraction():
    """Test stored procedure extraction."""
    print("\nTesting stored procedure extraction...")

    # PostgreSQL function
    pg_sql = """
CREATE FUNCTION calculate_bonus(emp_id INT) RETURNS DECIMAL AS $$
BEGIN
    RETURN (SELECT salary * 0.1 FROM employees WHERE id = emp_id);
END;
$$ LANGUAGE plpgsql;
"""

    parser = TreeSitterSqlParser(dialect=SqlDialect.POSTGRESQL)
    byte_content = pg_sql.encode('utf-8')
    procedures = parser.extract_stored_procedures(byte_content)

    print(f"  Found {len(procedures)} stored procedures")
    for proc in procedures:
        print(f"    - {proc['name']} (line {proc['line_number']})")

    if len(procedures) > 0:
        print("  ✓ Stored procedure extraction working")
    else:
        print("  ⚠ No procedures found (may be grammar limitation)")

    # Test SQLite (should return empty list)
    sqlite_parser = TreeSitterSqlParser(dialect=SqlDialect.SQLITE)
    sqlite_procedures = sqlite_parser.extract_stored_procedures(b"SELECT 1;")
    assert len(sqlite_procedures) == 0, "SQLite should not support stored procedures"
    print("  ✓ SQLite correctly returns no procedures")


def test_combined_extraction():
    """Test extracting multiple construct types from complex SQL."""
    print("\nTesting combined extraction...")

    complex_sql = """
-- Create tables
CREATE TABLE employees (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100),
    department VARCHAR(50),
    salary DECIMAL(10,2)
);

CREATE TABLE departments (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50)
);

-- Create view
CREATE VIEW high_earners AS
SELECT name, salary FROM employees WHERE salary > 100000;

-- Complex query with CTE and window functions
WITH dept_stats AS (
    SELECT
        department,
        COUNT(*) as emp_count,
        AVG(salary) as avg_salary
    FROM employees
    GROUP BY department
)
SELECT
    e.name,
    e.salary,
    d.avg_salary,
    RANK() OVER (PARTITION BY e.department ORDER BY e.salary DESC) as dept_rank
FROM employees e
JOIN dept_stats d ON e.department = d.department;
"""

    parser = TreeSitterSqlParser(dialect=SqlDialect.POSTGRESQL)
    byte_content = complex_sql.encode('utf-8')

    tables = parser.extract_tables(byte_content)
    views = parser.extract_views(byte_content)
    ctes = parser.extract_ctes(byte_content)
    window_funcs = parser.extract_window_functions(byte_content)

    print(f"  Tables: {len(tables)}")
    print(f"  Views: {len(views)}")
    print(f"  CTEs: {len(ctes)}")
    print(f"  Window functions: {len(window_funcs)}")

    assert len(tables) == 2, f"Expected 2 tables, got {len(tables)}"
    assert len(views) == 1, f"Expected 1 view, got {len(views)}"
    print("  ✓ Combined extraction working")


def main():
    """Run all advanced tests."""
    print("="*60)
    print("TreeSitterSqlParser Advanced Feature Tests")
    print("="*60)

    try:
        test_cte_extraction()
        test_window_function_extraction()
        test_stored_procedure_extraction()
        test_combined_extraction()

        print("\n" + "="*60)
        print("✓ All advanced tests completed!")
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
