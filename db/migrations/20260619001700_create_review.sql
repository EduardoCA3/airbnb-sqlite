-- migrate:up
CREATE TABLE review (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  comentario TEXT,
  score INTEGER,
  fecha TEXT,
  listing_id INTEGER NOT NULL,
  inquilino_id INTEGER NOT NULL,
  FOREIGN KEY (listing_id) REFERENCES listings(id),
  FOREIGN KEY (inquilino_id) REFERENCES inquilinos(id)
);

-- migrate:down
DROP TABLE IF EXISTS review;
