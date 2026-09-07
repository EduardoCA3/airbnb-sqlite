-- migrate:up
CREATE TABLE listings_amenities (
  amenity_id INTEGER NOT NULL,
  listing_id INTEGER NOT NULL,
  PRIMARY KEY (amenity_id, listing_id),
  FOREIGN KEY (amenity_id) REFERENCES amenities(id),
  FOREIGN KEY (listing_id) REFERENCES listings(id)
);

-- migrate:down
DROP TABLE IF EXISTS listings_amenities;
