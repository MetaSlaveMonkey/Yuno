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

CREATE TABLE IF NOT EXISTS action (
    user_id BIGINT NOT NULL,
    target_id BIGINT NOT NULL,
    action_type VARCHAR(255) NOT NULL,
    action_count BIGINT NOT NULL,
    PRIMARY KEY (user_id, target_id, action_type),
    FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE,
    FOREIGN KEY (target_id) REFERENCES users (user_id) ON DELETE CASCADE
);

CREATE OR REPLACE FUNCTION insert_action_item(
    p_user_id BIGINT,
    p_target_id BIGINT,
    p_action_type VARCHAR(255)
) RETURNS VOID AS $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM action
        WHERE user_id = p_user_id
          AND target_id = p_target_id
          AND action_type = p_action_type
    ) THEN
        UPDATE action
        SET action_count = action_count + 1
        WHERE user_id = p_user_id
          AND target_id = p_target_id
          AND action_type = p_action_type;
    ELSE
        INSERT INTO action (user_id, target_id, action_type, action_count)
        VALUES (p_user_id, p_target_id, p_action_type, 1);
    END IF;
END;
$$ LANGUAGE plpgsql;

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
