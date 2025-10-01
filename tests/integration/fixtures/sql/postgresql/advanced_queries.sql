-- PostgreSQL Advanced Queries Test Fixture
-- Tests: CTEs, Window Functions, Complex Joins

-- CTE with multiple definitions
WITH monthly_stats AS (
    SELECT
        DATE_TRUNC('month', created_at) as month,
        COUNT(*) as user_count,
        AVG(EXTRACT(EPOCH FROM (NOW() - created_at))) as avg_age_seconds
    FROM users
    GROUP BY DATE_TRUNC('month', created_at)
),
top_months AS (
    SELECT month, user_count
    FROM monthly_stats
    WHERE user_count > 10
    ORDER BY user_count DESC
    LIMIT 5
)
SELECT * FROM top_months;

-- Window functions: ROW_NUMBER, RANK, DENSE_RANK, LEAD, LAG
SELECT
    username,
    created_at,
    ROW_NUMBER() OVER (ORDER BY created_at) as row_num,
    RANK() OVER (ORDER BY created_at) as rank,
    DENSE_RANK() OVER (ORDER BY created_at) as dense_rank,
    LEAD(username) OVER (ORDER BY created_at) as next_user,
    LAG(username) OVER (ORDER BY created_at) as prev_user
FROM users;

-- Window functions with PARTITION BY
SELECT
    p.title,
    p.created_at,
    u.username,
    COUNT(*) OVER (PARTITION BY p.user_id) as user_post_count,
    AVG(LENGTH(p.content)) OVER (PARTITION BY p.user_id) as avg_content_length,
    FIRST_VALUE(p.title) OVER (PARTITION BY p.user_id ORDER BY p.created_at) as first_post
FROM posts p
JOIN users u ON p.user_id = u.id;

-- Recursive CTE
WITH RECURSIVE number_series AS (
    SELECT 1 as n
    UNION ALL
    SELECT n + 1 FROM number_series WHERE n < 100
)
SELECT n FROM number_series;
