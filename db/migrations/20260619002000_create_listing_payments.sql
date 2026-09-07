-- migrate:up
CREATE TABLE listings_payments (
  payment_id INTEGER NOT NULL,
  listing_id INTEGER NOT NULL,
  PRIMARY KEY (payment_id, listing_id),
  FOREIGN KEY (payment_id) REFERENCES payments(id),
  FOREIGN KEY (listing_id) REFERENCES listings(id)
);

-- migrate:down
DROP TABLE IF EXISTS listings_payments;
