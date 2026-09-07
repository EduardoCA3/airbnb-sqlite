-- migrate:up
CREATE TABLE neighbourhoods (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  longitud REAL,
  latitud REAL,
  neighbourhood_overview TEXT,
  ciudad_id INTEGER NOT NULL,
  FOREIGN KEY (ciudad_id) REFERENCES ciudad(id)
);

-- migrate:down
DROP TABLE IF EXISTS neighbourhoods;
