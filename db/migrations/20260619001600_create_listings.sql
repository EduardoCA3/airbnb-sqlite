-- migrate:up
CREATE TABLE listings (
  id INTEGER PRIMARY KEY,
  nombre TEXT,
  description TEXT,
  listing_url TEXT,
  price REAL,
  accommodates INTEGER,
  instant_bookable INTEGER,
  calendar_last_scraped TEXT,
  beds INTEGER,
  last_review TEXT,
  first_review TEXT,
  number_of_reviews INTEGER,
  has_availability INTEGER,
  bedrooms INTEGER,
  minimum_nights INTEGER,
  maximum_nights INTEGER,
  room_type_id INTEGER,
  bathroom_text_id INTEGER,
  neighbourhood_id INTEGER,
  property_type_id INTEGER,
  host_id INTEGER,
  FOREIGN KEY (room_type_id) REFERENCES room_type(id),
  FOREIGN KEY (bathroom_text_id) REFERENCES bathroom_text(id),
  FOREIGN KEY (neighbourhood_id) REFERENCES neighbourhoods(id),
  FOREIGN KEY (property_type_id) REFERENCES property_type(id),
  FOREIGN KEY (host_id) REFERENCES host(id)
);

-- migrate:down
DROP TABLE IF EXISTS listings;
