PRAGMA foreign_keys = ON;

SELECT COUNT(*) AS total_listings FROM listings;
SELECT COUNT(*) AS total_hosts FROM host;
SELECT COUNT(*) AS total_amenities FROM amenities;
SELECT COUNT(*) AS total_relacion_listings_amenities FROM listings_amenities;
SELECT COUNT(*) AS total_reviews FROM review;

SELECT
  l.id,
  l.nombre,
  h.nombre AS host,
  pt.nombre AS tipo_propiedad,
  rt.nombre AS tipo_habitacion,
  l.price
FROM listings l
LEFT JOIN host h ON l.host_id = h.id
LEFT JOIN property_type pt ON l.property_type_id = pt.id
LEFT JOIN room_type rt ON l.room_type_id = rt.id
LIMIT 10;

SELECT n.nombre AS barrio, COUNT(*) AS cantidad_listings
FROM listings l
JOIN neighbourhoods n ON l.neighbourhood_id = n.id
GROUP BY n.nombre
ORDER BY cantidad_listings DESC
LIMIT 10;
