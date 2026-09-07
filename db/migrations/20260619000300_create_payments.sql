-- migrate:up
CREATE TABLE payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS payments;
