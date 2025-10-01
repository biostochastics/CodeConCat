-- SQLite Queries Test Fixture
-- Tests: SELECT, JOIN, aggregates, date functions

-- Simple SELECT
SELECT * FROM users WHERE username LIKE 'john%';

-- JOIN query
SELECT
    u.username,
    n.title,
    n.created_at
FROM notes n
INNER JOIN users u ON n.user_id = u.id
ORDER BY n.created_at DESC
LIMIT 10;

-- Aggregation
SELECT
    u.username,
    COUNT(n.id) as note_count,
    MAX(n.created_at) as last_note_date
FROM users u
LEFT JOIN notes n ON u.id = n.user_id
GROUP BY u.id, u.username
HAVING note_count > 0;

-- Subquery
SELECT title, content
FROM notes
WHERE user_id IN (
    SELECT id FROM users WHERE email LIKE '%@example.com'
);

-- CASE expression
SELECT
    title,
    CASE
        WHEN LENGTH(content) < 100 THEN 'Short'
        WHEN LENGTH(content) < 500 THEN 'Medium'
        ELSE 'Long'
    END as content_length_category
FROM notes;

-- Date functions (SQLite-specific)
SELECT
    title,
    created_at,
    date(created_at) as date_only,
    time(created_at) as time_only,
    strftime('%Y-%m', created_at) as year_month
FROM notes;
