-- Create a trigger function to notify on new URL insertion
CREATE FUNCTION notify_new_url() RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify('new_url', row_to_json(NEW)::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger that calls the notify function after an insert
CREATE TRIGGER new_url_trigger
AFTER INSERT ON urls
FOR EACH ROW EXECUTE FUNCTION notify_new_url();

-- OR

-- Create a trigger function to notify on URL insert or update
CREATE FUNCTION notify_url_change() RETURNS trigger AS $$
BEGIN
    PERFORM pg_notify('url_change', row_to_json(NEW)::text);
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger for inserts
CREATE TRIGGER url_insert_trigger
AFTER INSERT ON urls
FOR EACH ROW EXECUTE FUNCTION notify_url_change();

-- Create the trigger for updates
CREATE TRIGGER url_update_trigger
AFTER UPDATE ON urls
FOR EACH ROW EXECUTE FUNCTION notify_url_change();
