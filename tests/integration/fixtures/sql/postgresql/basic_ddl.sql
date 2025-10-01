-- PostgreSQL Basic DDL Test Fixture
-- Tests: CREATE TABLE, CREATE VIEW, PRIMARY KEY, FOREIGN KEY, SERIAL

-- Users table with SERIAL primary key (PostgreSQL-specific)
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    email VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Posts table with foreign key
CREATE TABLE posts (
    id BIGSERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT,
    published BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- View definition
CREATE VIEW active_users AS
SELECT id, username, email, created_at
FROM users
WHERE created_at > NOW() - INTERVAL '30 days';

-- Materialized view (PostgreSQL-specific)
CREATE MATERIALIZED VIEW user_post_counts AS
SELECT u.id, u.username, COUNT(p.id) as post_count
FROM users u
LEFT JOIN posts p ON u.id = p.user_id
GROUP BY u.id, u.username;
