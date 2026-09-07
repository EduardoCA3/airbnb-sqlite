-- migrate:up
CREATE TABLE room_type (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS room_type;
