-- migrate:up
CREATE TABLE listing_inquilinos (
  cantidad_dias INTEGER,
  llegada TEXT,
  retiro TEXT,
  inquilino_id INTEGER NOT NULL,
  listing_id INTEGER NOT NULL,
  PRIMARY KEY (inquilino_id, listing_id, llegada),
  FOREIGN KEY (inquilino_id) REFERENCES inquilinos(id),
  FOREIGN KEY (listing_id) REFERENCES listings(id)
);

-- migrate:down
DROP TABLE IF EXISTS listing_inquilinos;
