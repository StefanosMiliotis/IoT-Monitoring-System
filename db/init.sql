CREATE TABLE IF NOT EXISTS sensors_data (
    timestamp TIMESTAMPTZ NOT NULL, 
    device_name TEXT NOT NULL, 
    payload JSONB
); 

-- #δημιουργια πινακα sensors_data με δεδομενα απο τους αισθητηρες ,στηλες timestamp , device_name για το ονομα της συσκευης που εστειλε τα δεδομενα και payload για τα δεδομενα json

SELECT create_hypertable('sensors_data', 'timestamp', if_not_exists => TRUE);

-- #μετατροπη του sensors_data σε hypertable για να μπορει να χειριστει μεγαλο ογκο δεδομενων 