-- migrate:up
CREATE TABLE departamento (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  pais_id INTEGER NOT NULL,
  FOREIGN KEY (pais_id) REFERENCES pais(id)
);

-- migrate:down
DROP TABLE IF EXISTS departamento;
