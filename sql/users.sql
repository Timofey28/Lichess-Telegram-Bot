CREATE OR REPLACE FUNCTION get_user(p_tg_id BIGINT)
RETURNS TABLE(
    id INT,
    tg_id BIGINT,
    tg_username VARCHAR(32),
    tg_first_name VARCHAR(64),
    tg_last_name VARCHAR(64),
    lichess_username TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.tg_id, u.tg_username, u.tg_first_name, u.tg_last_name, u.lichess_username
    FROM users u
    WHERE u.tg_id = p_tg_id;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION get_all_users()
RETURNS TABLE(
    id INT,
    tg_id BIGINT,
    tg_username VARCHAR(32),
    tg_first_name VARCHAR(64),
    tg_last_name VARCHAR(64),
    lichess_username TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT u.id, u.tg_id, u.tg_username, u.tg_first_name, u.tg_last_name, u.lichess_username
    FROM users u
    ORDER BY u.id;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION add_user(
    p_tg_id BIGINT,
    p_tg_username VARCHAR(32),
    p_tg_first_name VARCHAR(64),
    p_tg_last_name VARCHAR(64)
) RETURNS INT AS $$
DECLARE
    v_id INT;
BEGIN
    INSERT INTO users (tg_id, tg_username, tg_first_name, tg_last_name)
    VALUES (p_tg_id, p_tg_username, p_tg_first_name, p_tg_last_name)
    RETURNING id INTO v_id;
    RETURN v_id;
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION update_lichess_username(
    p_tg_id BIGINT,
    p_lichess_username TEXT
) RETURNS VOID AS $$
BEGIN
    UPDATE users
    SET lichess_username = p_lichess_username
    WHERE tg_id = p_tg_id;
END;
$$ LANGUAGE plpgsql;