-- PostgreSQL Stored Procedures Test Fixture
-- Tests: CREATE FUNCTION, CREATE PROCEDURE, PL/pgSQL

-- Simple function
CREATE FUNCTION get_user_count() RETURNS INTEGER AS $$
BEGIN
    RETURN (SELECT COUNT(*) FROM users);
END;
$$ LANGUAGE plpgsql;

-- Function with parameters
CREATE FUNCTION get_user_posts(user_id_param INTEGER)
RETURNS TABLE(post_id INTEGER, title VARCHAR, created_at TIMESTAMP) AS $$
BEGIN
    RETURN QUERY
    SELECT id, title, created_at
    FROM posts
    WHERE user_id = user_id_param
    ORDER BY created_at DESC;
END;
$$ LANGUAGE plpgsql;

-- Function with OUT parameters
CREATE FUNCTION get_user_stats(user_id_param INTEGER,
    OUT post_count INTEGER,
    OUT first_post_date TIMESTAMP,
    OUT last_post_date TIMESTAMP
) AS $$
BEGIN
    SELECT COUNT(*), MIN(created_at), MAX(created_at)
    INTO post_count, first_post_date, last_post_date
    FROM posts
    WHERE user_id = user_id_param;
END;
$$ LANGUAGE plpgsql;

-- Procedure (PostgreSQL 11+)
CREATE PROCEDURE update_user_email(user_id_param INTEGER, new_email VARCHAR) AS $$
BEGIN
    UPDATE users SET email = new_email WHERE id = user_id_param;
    COMMIT;
END;
$$ LANGUAGE plpgsql;
