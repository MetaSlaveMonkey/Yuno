CREATE OR REPLACE FUNCTION insert_action(user_id BIGINT, action_type TEXT, target_id BIGINT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM actions
        WHERE user_id = user_id
          AND action_type = action_type
          AND target_id = target_id
    ) THEN
        UPDATE actions
        SET action_count = action_count + 1
        WHERE user_id = user_id
          AND action_type = action_type
          AND target_id = target_id;
    ELSE
        INSERT INTO actions (
            user_id,
            action_type,
            target_id,
            action_count
        ) VALUES (
            user_id,
            action_type,
            target_id,
            1
        );
    END IF;
END $$;

CREATE OR REPLACE FUNCTION get_total_action_count(user_id BIGINT, action_type TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN (
        SELECT SUM(action_count) FROM actions
        WHERE user_id = user_id
          AND action_type = action_type
    );
END $$;

CREATE OR REPLACE FUNCTION get_action_count(one BIGINT, two TEXT, three BIGINT)
RETURNS INTEGER  -- action_count
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN (
        SELECT action_count FROM actions
        WHERE user_id = one
        AND action_type = two
        AND target_id = three
    );
END $$;

CREATE OR REPLACE FUNCTION ensure_relationship(one BIGINT, two TEXT, three BIGINT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT EXISTS (
        SELECT * FROM users
        WHERE user_id = one
    ) THEN
        INSERT INTO users (user_id) VALUES (one);
    END IF;

    IF NOT EXISTS (
        SELECT * FROM users
        WHERE user_id = three
    ) THEN
        INSERT INTO users (user_id) VALUES (three);
    END IF;
END $$;

CREATE OR REPLACE FUNCTION insert_default_prefix()
RETURNS TRIGGER AS
$BODY$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM prefix WHERE guild_id = NEW.guild_id) THEN
        INSERT INTO prefix (guild_id, prefix) VALUES (NEW.guild_id, 'y');
    END IF;
    RETURN NEW;
END;
$BODY$
LANGUAGE plpgsql;
