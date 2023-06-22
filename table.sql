CREATE TABLE logs (
        id_logs SERIAL PRIMARY KEY,
        ip VARCHAR(15),
        dt DATE,
        request TEXT,
        status INTEGER,
        bytes_sent TEXT
    )
