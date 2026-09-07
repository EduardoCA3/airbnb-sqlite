-- migrate:up
CREATE TABLE ciudad (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  departamento_id INTEGER NOT NULL,
  FOREIGN KEY (departamento_id) REFERENCES departamento(id)
);

-- migrate:down
DROP TABLE IF EXISTS ciudad;
