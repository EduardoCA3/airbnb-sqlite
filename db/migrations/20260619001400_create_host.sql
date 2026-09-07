-- migrate:up
CREATE TABLE host (
  id INTEGER PRIMARY KEY,
  is_superhost INTEGER,
  picture_url TEXT,
  nombre TEXT,
  about TEXT,
  acceptance_rate TEXT,
  response_rate TEXT,
  since TEXT,
  thumbnail_url TEXT,
  has_profile_pic INTEGER,
  url TEXT,
  identity_verified INTEGER,
  listing_count INTEGER,
  total_listing_count INTEGER,
  response_time_id INTEGER,
  persona_id INTEGER NOT NULL,
  FOREIGN KEY (response_time_id) REFERENCES response_time(id),
  FOREIGN KEY (persona_id) REFERENCES persona(id)
);

-- migrate:down
DROP TABLE IF EXISTS host;
