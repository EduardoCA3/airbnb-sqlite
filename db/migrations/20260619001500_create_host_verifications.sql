-- migrate:up
CREATE TABLE host_verifications (
  verification_id INTEGER NOT NULL,
  host_id INTEGER NOT NULL,
  PRIMARY KEY (verification_id, host_id),
  FOREIGN KEY (verification_id) REFERENCES verifications(id),
  FOREIGN KEY (host_id) REFERENCES host(id)
);

-- migrate:down
DROP TABLE IF EXISTS host_verifications;
