CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    time_zone VARCHAR(255) NOT NULL DEFAULT 'UTC',
    locale VARCHAR(255) NOT NULL DEFAULT 'en_US',
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS guilds (
    guild_id BIGINT PRIMARY KEY,
    locale VARCHAR(255) NOT NULL DEFAULT 'en_US',
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
)

CREATE TABLE IF NOT EXISTS prefix (
    prefix_id SERIAL PRIMARY KEY,
    guild_id BIGINT NOT NULL REFERENCES guilds (guild_id) ON DELETE CASCADE,
    prefix VARCHAR(255) NOT NULL,
    added_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS actions (
    user_id BIGINT NOT NULL,
    target_id BIGINT NOT NULL,
    action_type VARCHAR(255) NOT NULL,
    action_count BIGINT NOT NULL,
    PRIMARY KEY (user_id, target_id, action_type),
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE OR REPLACE FUNCTION insert_action(one BIGINT, two TEXT, three BIGINT)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    IF EXISTS (
        SELECT * FROM actions
        WHERE user_id = one
        AND action_type = two
        AND target_id = three
    ) THEN
        UPDATE actions
        SET action_count = action_count + 1
        WHERE user_id = one
        AND action_type = two
        AND target_id = three;
    ELSE
        INSERT INTO actions (
            user_id,
            action_type,
            target_id,
            action_count
        ) VALUES (one, two, three, 1);
    END IF;
END $$;

CREATE OR REPLACE FUNCTION get_total_action_count(one BIGINT, two TEXT)
RETURNS INTEGER
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN (
        SELECT SUM(action_count) FROM actions
        WHERE user_id = one
        AND action_type = two
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

DROP TRIGGER IF EXISTS insert_default_prefix_trigger ON guild;
CREATE TRIGGER insert_default_prefix_trigger
AFTER INSERT ON guild
FOR EACH ROW EXECUTE PROCEDURE insert_default_prefix();
