-- migrate:up
CREATE TABLE imagen (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL,
  listing_id INTEGER NOT NULL,
  FOREIGN KEY (listing_id) REFERENCES listings(id)
);

-- migrate:down
DROP TABLE IF EXISTS imagen;
