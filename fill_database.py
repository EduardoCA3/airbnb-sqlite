"""
fill_database.py
----------------
Script de llenado de datos para el proyecto Airbnb en SQLite.

Requisitos:
    pip install pandas

Uso:
    1. Coloca el archivo "listings (1).csv" en la raíz del proyecto.
    2. Asegúrate de tener la base db/database.db creada con las migraciones.
    3. Ejecuta:
       python fill_database.py

Qué hace pandas aquí:
    - Lee el CSV con pandas.read_csv().
    - Selecciona solo las columnas necesarias.
    - Elimina duplicados.
    - Limpia datos nulos, precios, fechas y booleanos.
    - Agrupa datos para crear tablas maestras como neighbourhoods y host.

Nota:
    El CSV no trae pagos, inquilinos ni reservas reales. Por eso esas tablas se llenan con datos simulados.
"""

import ast
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

CSV_PATH = Path("listings (1).csv")
DB_PATH = Path("db/database.db")

# -------------------------
# Funciones de limpieza
# -------------------------
def clean_text(x):
    if pd.isna(x):
        return None
    s = str(x).strip()
    if s == "" or s.lower() == "nan":
        return None
    return re.sub(r"\s+", " ", s)


def clean_int(x):
    if pd.isna(x):
        return None
    try:
        return int(float(str(x).replace(",", "").strip()))
    except Exception:
        return None


def clean_real(x):
    if pd.isna(x):
        return None
    try:
        s = str(x).replace("$", "").replace(",", "").strip()
        return float(s) if s else None
    except Exception:
        return None


def clean_bool(x):
    if pd.isna(x):
        return None
    s = str(x).strip().lower()
    if s in ("t", "true", "1", "yes", "y", "si", "sí"):
        return 1
    if s in ("f", "false", "0", "no", "n"):
        return 0
    return None


def clean_date(x):
    s = clean_text(x)
    return s[:19] if s else None


def parse_list_cell(x):
    """Convierte textos tipo ['Wifi', 'Kitchen'] en listas reales."""
    s = clean_text(x)
    if not s:
        return []
    try:
        value = ast.literal_eval(s)
        if isinstance(value, list):
            return [clean_text(v) for v in value if clean_text(v)]
    except Exception:
        pass
    parts = [p.strip().strip("\"'") for p in s.strip("[]").split(",")]
    return [p for p in parts if p]


def split_name(full_name):
    s = clean_text(full_name) or "Sin nombre"
    parts = s.split(" ", 1)
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]


def insert_lookup(cursor, conn, table, column, values):
    """Inserta valores únicos en una tabla maestra y devuelve un diccionario nombre->id."""
    clean_values = sorted({clean_text(v) for v in values if clean_text(v)})
    if clean_values:
        cursor.executemany(
            f"INSERT INTO {table} ({column}) VALUES (?)",
            [(v,) for v in clean_values]
        )
        conn.commit()
    cursor.execute(f"SELECT id, {column} FROM {table}")
    return {name: id_ for id_, name in cursor.fetchall()}


# -------------------------
# Inicio del proceso
# -------------------------
if not CSV_PATH.exists():
    raise FileNotFoundError(f"No se encontró el archivo {CSV_PATH}. Colócalo en la raíz del proyecto.")

if not DB_PATH.exists():
    raise FileNotFoundError(f"No se encontró la base {DB_PATH}. Primero crea la base con las migraciones.")

print("Leyendo CSV con pandas...")
usecols = [
    "id", "listing_url", "name", "description", "neighborhood_overview", "picture_url",
    "host_id", "host_url", "host_name", "host_since", "host_about", "host_response_time",
    "host_response_rate", "host_acceptance_rate", "host_is_superhost", "host_thumbnail_url",
    "host_picture_url", "host_listings_count", "host_total_listings_count", "host_verifications",
    "host_has_profile_pic", "host_identity_verified", "host_neighbourhood",
    "neighbourhood_cleansed", "latitude", "longitude", "property_type", "room_type",
    "accommodates", "bathrooms_text", "bedrooms", "beds", "amenities", "price",
    "minimum_nights", "maximum_nights", "has_availability", "calendar_last_scraped",
    "number_of_reviews", "first_review", "last_review", "review_scores_rating", "instant_bookable"
]

df = pd.read_csv(CSV_PATH, usecols=usecols, low_memory=False)
df = df.dropna(subset=["id", "host_id"]).copy()
df["id"] = df["id"].apply(clean_int)
df["host_id"] = df["host_id"].apply(clean_int)
df = df.dropna(subset=["id", "host_id"]).drop_duplicates(subset=["id"], keep="first")
df["id"] = df["id"].astype(int)
df["host_id"] = df["host_id"].astype(int)

print(f"Listings válidos encontrados: {len(df)}")

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("PRAGMA foreign_keys = OFF")
cur.execute("PRAGMA synchronous = OFF")
cur.execute("PRAGMA journal_mode = MEMORY")
cur.execute("PRAGMA temp_store = MEMORY")
conn.commit()

# -------------------------
# Limpiar tablas antes de rellenar
# -------------------------
print("Limpiando tablas...")
tables_reverse_order = [
    "review", "listing_inquilinos", "listings_payments", "listings_amenities", "imagen",
    "host_verifications", "listings", "host", "inquilinos", "persona", "neighbourhoods",
    "ciudad", "departamento", "pais", "payments", "amenities", "verifications",
    "response_time", "bathroom_text", "room_type", "property_type"
]
for table in tables_reverse_order:
    cur.execute(f"DELETE FROM {table}")
cur.execute("DELETE FROM sqlite_sequence")
conn.commit()

# -------------------------
# Tablas maestras
# -------------------------
print("Insertando tablas maestras...")
property_map = insert_lookup(cur, conn, "property_type", "nombre", df["property_type"])
room_map = insert_lookup(cur, conn, "room_type", "nombre", df["room_type"])
bath_map = insert_lookup(cur, conn, "bathroom_text", "nombre", df["bathrooms_text"])
response_map = insert_lookup(cur, conn, "response_time", "nombre", df["host_response_time"])

verification_values = set()
for x in df["host_verifications"].dropna():
    verification_values.update(parse_list_cell(x))
verification_map = insert_lookup(cur, conn, "verifications", "nombre", verification_values)

amenity_values = set()
for x in df["amenities"].dropna():
    amenity_values.update(parse_list_cell(x))
amenity_map = insert_lookup(cur, conn, "amenities", "nombre", amenity_values)

payment_map = insert_lookup(
    cur, conn, "payments", "nombre",
    ["Tarjeta de crédito", "Tarjeta de débito", "PayPal", "Transferencia bancaria", "Efectivo"]
)

# -------------------------
# Ubicación
# -------------------------
print("Insertando ubicación...")
cur.execute("INSERT INTO pais (nombre) VALUES (?)", ("Brazil",))
pais_id = cur.lastrowid
cur.execute("INSERT INTO departamento (nombre, pais_id) VALUES (?, ?)", ("Rio de Janeiro", pais_id))
departamento_id = cur.lastrowid
cur.execute("INSERT INTO ciudad (nombre, departamento_id) VALUES (?, ?)", ("Rio de Janeiro", departamento_id))
ciudad_id = cur.lastrowid
conn.commit()

neighbourhood_map = {}
for neighbourhood, group in df.groupby("neighbourhood_cleansed", dropna=True):
    nombre = clean_text(neighbourhood)
    if not nombre:
        continue
    lat = pd.to_numeric(group["latitude"], errors="coerce").mean()
    lon = pd.to_numeric(group["longitude"], errors="coerce").mean()
    overview = None
    for value in group["neighborhood_overview"].dropna():
        overview = clean_text(value)
        if overview:
            break
    cur.execute(
        """
        INSERT INTO neighbourhoods (nombre, longitud, latitud, neighbourhood_overview, ciudad_id)
        VALUES (?, ?, ?, ?, ?)
        """,
        (nombre, None if pd.isna(lon) else float(lon), None if pd.isna(lat) else float(lat), overview, ciudad_id)
    )
    neighbourhood_map[nombre] = cur.lastrowid

if "Sin barrio" not in neighbourhood_map:
    cur.execute(
        "INSERT INTO neighbourhoods (nombre, longitud, latitud, neighbourhood_overview, ciudad_id) VALUES (?, ?, ?, ?, ?)",
        ("Sin barrio", None, None, None, ciudad_id)
    )
    neighbourhood_map["Sin barrio"] = cur.lastrowid
conn.commit()

# -------------------------
# Persona y host
# -------------------------
print("Insertando personas y hosts...")
host_rows = []
for host_id, group in df.groupby("host_id", sort=False):
    row = group.iloc[0]
    nombre, apellido = split_name(row.get("host_name"))
    neighbourhood_name = clean_text(row.get("host_neighbourhood")) or clean_text(row.get("neighbourhood_cleansed")) or "Sin barrio"
    neighbourhood_id = neighbourhood_map.get(neighbourhood_name, neighbourhood_map["Sin barrio"])

    cur.execute(
        """
        INSERT INTO persona (nombre, apellido, dni, telefono, correo, fecha_nacimiento, neighbourhood_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (nombre, apellido, None, None, None, None, neighbourhood_id)
    )
    persona_id = cur.lastrowid

    host_rows.append((
        int(host_id), clean_bool(row.get("host_is_superhost")), clean_text(row.get("host_picture_url")),
        clean_text(row.get("host_name")), clean_text(row.get("host_about")),
        clean_text(row.get("host_acceptance_rate")), clean_text(row.get("host_response_rate")),
        clean_date(row.get("host_since")), clean_text(row.get("host_thumbnail_url")),
        clean_bool(row.get("host_has_profile_pic")), clean_text(row.get("host_url")),
        clean_bool(row.get("host_identity_verified")), clean_int(row.get("host_listings_count")),
        clean_int(row.get("host_total_listings_count")), response_map.get(clean_text(row.get("host_response_time"))),
        persona_id
    ))

cur.executemany(
    """
    INSERT INTO host (
        id, is_superhost, picture_url, nombre, about, acceptance_rate, response_rate, since,
        thumbnail_url, has_profile_pic, url, identity_verified, listing_count,
        total_listing_count, response_time_id, persona_id
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    host_rows
)
conn.commit()

# Host-verifications
host_verification_pairs = set()
for host_id, group in df.groupby("host_id", sort=False):
    cell = group.iloc[0].get("host_verifications")
    for verification in parse_list_cell(cell):
        verification_id = verification_map.get(verification)
        if verification_id:
            host_verification_pairs.add((verification_id, int(host_id)))
cur.executemany(
    "INSERT OR IGNORE INTO host_verifications (verification_id, host_id) VALUES (?, ?)",
    list(host_verification_pairs)
)
conn.commit()

# -------------------------
# Listings
# -------------------------
print("Insertando listings...")
listing_rows = []
for _, row in df.iterrows():
    neighbourhood_name = clean_text(row.get("neighbourhood_cleansed")) or "Sin barrio"
    listing_rows.append((
        int(row["id"]), clean_text(row.get("name")), clean_text(row.get("description")),
        clean_text(row.get("listing_url")), clean_real(row.get("price")),
        clean_int(row.get("accommodates")), clean_bool(row.get("instant_bookable")),
        clean_date(row.get("calendar_last_scraped")), clean_int(row.get("beds")),
        clean_date(row.get("last_review")), clean_date(row.get("first_review")),
        clean_int(row.get("number_of_reviews")), clean_bool(row.get("has_availability")),
        clean_int(row.get("bedrooms")), clean_int(row.get("minimum_nights")),
        clean_int(row.get("maximum_nights")), room_map.get(clean_text(row.get("room_type"))),
        bath_map.get(clean_text(row.get("bathrooms_text"))),
        neighbourhood_map.get(neighbourhood_name, neighbourhood_map["Sin barrio"]),
        property_map.get(clean_text(row.get("property_type"))), int(row["host_id"])
    ))

cur.executemany(
    """
    INSERT INTO listings (
        id, nombre, description, listing_url, price, accommodates, instant_bookable,
        calendar_last_scraped, beds, last_review, first_review, number_of_reviews,
        has_availability, bedrooms, minimum_nights, maximum_nights, room_type_id,
        bathroom_text_id, neighbourhood_id, property_type_id, host_id
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
    listing_rows
)
conn.commit()

# Imagen
imagen_rows = []
for _, row in df.iterrows():
    url = clean_text(row.get("picture_url"))
    if url:
        imagen_rows.append((url, int(row["id"])))
cur.executemany("INSERT INTO imagen (url, listing_id) VALUES (?, ?)", imagen_rows)
conn.commit()

# Listings-amenities
print("Insertando relación listings_amenities...")
listings_amenities_pairs = set()
for listing_id, amenities in df[["id", "amenities"]].itertuples(index=False, name=None):
    for amenity in parse_list_cell(amenities):
        amenity_id = amenity_map.get(amenity)
        if amenity_id:
            listings_amenities_pairs.add((amenity_id, int(listing_id)))
cur.executemany(
    "INSERT OR IGNORE INTO listings_amenities (amenity_id, listing_id) VALUES (?, ?)",
    list(listings_amenities_pairs)
)
conn.commit()

# Listings-payments: simulado porque el CSV no trae métodos de pago
payment_ids = sorted(payment_map.values())
listing_payment_rows = [(payment_ids[int(listing_id) % len(payment_ids)], int(listing_id)) for listing_id in df["id"].tolist()]
cur.executemany(
    "INSERT OR IGNORE INTO listings_payments (payment_id, listing_id) VALUES (?, ?)",
    listing_payment_rows
)
conn.commit()

# -------------------------
# Inquilinos simulados
# -------------------------
print("Insertando inquilinos simulados...")
cur.execute("SELECT id FROM neighbourhoods ORDER BY id")
neighbourhood_ids = [row[0] for row in cur.fetchall()]
sample_names = [
    ("Ana", "Silva"), ("Bruno", "Souza"), ("Carla", "Oliveira"), ("Daniel", "Santos"),
    ("Eduardo", "Lima"), ("Fernanda", "Costa"), ("Gabriel", "Pereira"), ("Helena", "Ribeiro"),
    ("Igor", "Mendes"), ("Juliana", "Alves"), ("Lucas", "Ferreira"), ("Mariana", "Gomes"),
    ("Nicolas", "Rocha"), ("Patricia", "Martins"), ("Rafael", "Barbosa"), ("Sofia", "Dias"),
    ("Thiago", "Nunes"), ("Valeria", "Cardoso"), ("William", "Teixeira"), ("Yasmin", "Moreira")
]

inquilino_ids = []
for i in range(200):
    nombre, apellido = sample_names[i % len(sample_names)]
    dni = 10000000 + i
    telefono = f"+55 21 9{1000+i:04d}-{2000+i:04d}"
    correo = f"inquilino{i+1}@example.com"
    fecha_nacimiento = f"{1980 + (i % 25):04d}-{1 + (i % 12):02d}-{1 + (i % 27):02d}"
    neighbourhood_id = neighbourhood_ids[i % len(neighbourhood_ids)]

    cur.execute(
        """
        INSERT INTO persona (nombre, apellido, dni, telefono, correo, fecha_nacimiento, neighbourhood_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (nombre, apellido, dni, telefono, correo, fecha_nacimiento, neighbourhood_id)
    )
    persona_id = cur.lastrowid
    cur.execute("INSERT INTO inquilinos (persona_id) VALUES (?)", (persona_id,))
    inquilino_ids.append(cur.lastrowid)
conn.commit()

# Reviews: puntaje real del CSV + inquilino simulado
review_rows = []
for _, row in df.iterrows():
    rating = clean_real(row.get("review_scores_rating"))
    number_reviews = clean_int(row.get("number_of_reviews")) or 0
    if rating is None or number_reviews <= 0:
        continue
    score = max(1, min(5, int(round(rating))))
    fecha = clean_date(row.get("last_review")) or clean_date(row.get("first_review")) or clean_date(row.get("calendar_last_scraped"))
    inquilino_id = inquilino_ids[int(row["id"]) % len(inquilino_ids)]
    review_rows.append(("Calificación promedio importada del dataset.", score, fecha, int(row["id"]), inquilino_id))

cur.executemany(
    "INSERT INTO review (comentario, score, fecha, listing_id, inquilino_id) VALUES (?, ?, ?, ?, ?)",
    review_rows
)
conn.commit()

# Reservas simuladas para listing_inquilinos
base_date = datetime(2026, 1, 1)
booking_rows = []
for i, (_, row) in enumerate(df.head(1000).iterrows()):
    days = max(1, min(clean_int(row.get("minimum_nights")) or 1, 30))
    llegada = base_date + timedelta(days=i % 180)
    retiro = llegada + timedelta(days=days)
    inquilino_id = inquilino_ids[i % len(inquilino_ids)]
    booking_rows.append((days, llegada.date().isoformat(), retiro.date().isoformat(), inquilino_id, int(row["id"])))

cur.executemany(
    """
    INSERT OR IGNORE INTO listing_inquilinos (cantidad_dias, llegada, retiro, inquilino_id, listing_id)
    VALUES (?, ?, ?, ?, ?)
    """,
    booking_rows
)
conn.commit()

# Índices para consultas más rápidas
indexes = [
    "CREATE INDEX IF NOT EXISTS idx_listings_host ON listings(host_id)",
    "CREATE INDEX IF NOT EXISTS idx_listings_neighbourhood ON listings(neighbourhood_id)",
    "CREATE INDEX IF NOT EXISTS idx_listings_property_type ON listings(property_type_id)",
    "CREATE INDEX IF NOT EXISTS idx_review_listing ON review(listing_id)",
    "CREATE INDEX IF NOT EXISTS idx_la_listing ON listings_amenities(listing_id)",
    "CREATE INDEX IF NOT EXISTS idx_hv_host ON host_verifications(host_id)"
]
for index_sql in indexes:
    cur.execute(index_sql)
conn.commit()

# Validar claves foráneas
cur.execute("PRAGMA foreign_keys = ON")
fk_errors = cur.execute("PRAGMA foreign_key_check").fetchall()
if fk_errors:
    print("Errores de foreign key encontrados:")
    print(fk_errors[:10])
else:
    print("Foreign keys correctas: 0 errores.")

# Mostrar conteos finales
print("\nConteos finales:")
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('sqlite_sequence', 'schema_migrations') ORDER BY name")
for (table,) in cur.fetchall():
    cur.execute(f"SELECT COUNT(*) FROM {table}")
    print(f"{table}: {cur.fetchone()[0]}")

conn.close()
print("\nCarga finalizada correctamente.")
