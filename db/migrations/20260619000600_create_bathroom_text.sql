-- migrate:up
CREATE TABLE bathroom_text (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS bathroom_text;
