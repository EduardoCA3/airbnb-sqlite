-- migrate:up
CREATE TABLE inquilinos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  persona_id INTEGER NOT NULL,
  FOREIGN KEY (persona_id) REFERENCES persona(id)
);

-- migrate:down
DROP TABLE IF EXISTS inquilinos;
