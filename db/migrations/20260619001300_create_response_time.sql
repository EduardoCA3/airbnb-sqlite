-- migrate:up
CREATE TABLE response_time (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS response_time;
