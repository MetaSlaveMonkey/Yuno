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
