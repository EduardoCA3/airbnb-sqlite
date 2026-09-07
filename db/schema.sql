BEGIN TRANSACTION;
CREATE TABLE amenities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);
CREATE TABLE bathroom_text (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);
CREATE TABLE ciudad (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  departamento_id INTEGER NOT NULL,
  FOREIGN KEY (departamento_id) REFERENCES departamento(id)
);
CREATE TABLE departamento (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  pais_id INTEGER NOT NULL,
  FOREIGN KEY (pais_id) REFERENCES pais(id)
);
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
CREATE TABLE host_verifications (
  verification_id INTEGER NOT NULL,
  host_id INTEGER NOT NULL,
  PRIMARY KEY (verification_id, host_id),
  FOREIGN KEY (verification_id) REFERENCES verifications(id),
  FOREIGN KEY (host_id) REFERENCES host(id)
);
CREATE TABLE imagen (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL,
  listing_id INTEGER NOT NULL,
  FOREIGN KEY (listing_id) REFERENCES listings(id)
);
CREATE TABLE inquilinos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  persona_id INTEGER NOT NULL,
  FOREIGN KEY (persona_id) REFERENCES persona(id)
);
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
CREATE TABLE listings_amenities (
  amenity_id INTEGER NOT NULL,
  listing_id INTEGER NOT NULL,
  PRIMARY KEY (amenity_id, listing_id),
  FOREIGN KEY (amenity_id) REFERENCES amenities(id),
  FOREIGN KEY (listing_id) REFERENCES listings(id)
);
CREATE TABLE listings_payments (
  payment_id INTEGER NOT NULL,
  listing_id INTEGER NOT NULL,
  PRIMARY KEY (payment_id, listing_id),
  FOREIGN KEY (payment_id) REFERENCES payments(id),
  FOREIGN KEY (listing_id) REFERENCES listings(id)
);
CREATE TABLE neighbourhoods (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  longitud REAL,
  latitud REAL,
  neighbourhood_overview TEXT,
  ciudad_id INTEGER NOT NULL,
  FOREIGN KEY (ciudad_id) REFERENCES ciudad(id)
);
CREATE TABLE pais (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);
CREATE TABLE payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);
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
CREATE TABLE property_type (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);
CREATE TABLE response_time (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);
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
CREATE TABLE room_type (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);
CREATE TABLE schema_migrations (version varchar(255) PRIMARY KEY);
CREATE TABLE verifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);
CREATE INDEX idx_listings_host ON listings(host_id);
CREATE INDEX idx_listings_neighbourhood ON listings(neighbourhood_id);
CREATE INDEX idx_listings_property_type ON listings(property_type_id);
CREATE INDEX idx_review_listing ON review(listing_id);
CREATE INDEX idx_la_listing ON listings_amenities(listing_id);
CREATE INDEX idx_hv_host ON host_verifications(host_id);
DELETE FROM "sqlite_sequence";
COMMIT;
