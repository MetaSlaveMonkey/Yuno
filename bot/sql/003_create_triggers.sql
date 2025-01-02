DROP TRIGGER IF EXISTS insert_default_prefix_trigger ON guild;
CREATE TRIGGER insert_default_prefix_trigger
AFTER INSERT ON guild
FOR EACH ROW EXECUTE PROCEDURE insert_default_prefix();
