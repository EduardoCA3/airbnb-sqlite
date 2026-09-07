-- migrate:up
CREATE TABLE persona (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  apellido TEXT,
  dni INTEGER,
  telefono TEXT,
  correo TEXT,
  fecha_nacimiento TEXT,
  neighbourhood_id INTEGER,
  FOREIGN KEY (neighbourhood_id) REFERENCES neighbourhoods(id)
);

-- migrate:down
DROP TABLE IF EXISTS persona;
