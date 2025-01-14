DROP TRIGGER IF EXISTS insert_default_prefix_trigger ON guilds;
CREATE TRIGGER insert_default_prefix_trigger
AFTER INSERT ON guilds
FOR EACH ROW EXECUTE PROCEDURE insert_default_prefix();
