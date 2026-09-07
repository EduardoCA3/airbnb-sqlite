import os, re, ast, sqlite3, zipfile, shutil, json, math
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd

SRC_CSV = Path('/mnt/data/listings (1).csv')
OUT = Path('/mnt/data/airbnb_sqlite_limpio')
DB_PATH = OUT / 'db' / 'database.db'
MIG_DIR = OUT / 'db' / 'migrations'

if OUT.exists():
    shutil.rmtree(OUT)
MIG_DIR.mkdir(parents=True, exist_ok=True)

# ---------- Helpers ----------
def clean_text(x, max_len=None):
    if pd.isna(x):
        return None
    s = str(x).strip()
    if s == '' or s.lower() == 'nan':
        return None
    # normalize whitespace but preserve useful text
    s = re.sub(r'\s+', ' ', s)
    if max_len and len(s) > max_len:
        return s[:max_len]
    return s

def clean_date(x):
    s = clean_text(x)
    if not s:
        return None
    # keep ISO-ish text. SQLite dates are TEXT.
    return s[:19]

def clean_int(x):
    if pd.isna(x):
        return None
    try:
        return int(float(str(x).replace(',', '').strip()))
    except Exception:
        return None

def clean_real(x):
    if pd.isna(x):
        return None
    try:
        s = str(x).replace('$','').replace(',','').strip()
        if s == '': return None
        return float(s)
    except Exception:
        return None

def clean_bool(x):
    if pd.isna(x):
        return None
    s = str(x).strip().lower()
    if s in ('t','true','1','yes','y','si','sí'):
        return 1
    if s in ('f','false','0','no','n'):
        return 0
    return None

def parse_list_cell(x):
    s = clean_text(x)
    if not s:
        return []
    try:
        value = ast.literal_eval(s)
        if isinstance(value, list):
            return [clean_text(v) for v in value if clean_text(v)]
    except Exception:
        pass
    # fallback for strings like [a, b]
    s2 = s.strip('[]')
    parts = [p.strip().strip('"\'') for p in s2.split(',')]
    return [p for p in parts if p]

def split_name(full):
    s = clean_text(full) or 'Sin nombre'
    parts = s.split(' ', 1)
    if len(parts) == 1:
        return parts[0], None
    return parts[0], parts[1]

# ---------- Migrations ----------
migrations = {
'20260619000100_create_property_type.sql': '''-- migrate:up
CREATE TABLE property_type (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS property_type;
''',
'20260619000200_create_verifications.sql': '''-- migrate:up
CREATE TABLE verifications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS verifications;
''',
'20260619000300_create_payments.sql': '''-- migrate:up
CREATE TABLE payments (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS payments;
''',
'20260619000400_create_amenities.sql': '''-- migrate:up
CREATE TABLE amenities (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS amenities;
''',
'20260619000500_create_room_type.sql': '''-- migrate:up
CREATE TABLE room_type (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS room_type;
''',
'20260619000600_create_bathroom_text.sql': '''-- migrate:up
CREATE TABLE bathroom_text (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS bathroom_text;
''',
'20260619000700_create_pais.sql': '''-- migrate:up
CREATE TABLE pais (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS pais;
''',
'20260619000800_create_departamento.sql': '''-- migrate:up
CREATE TABLE departamento (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  pais_id INTEGER NOT NULL,
  FOREIGN KEY (pais_id) REFERENCES pais(id)
);

-- migrate:down
DROP TABLE IF EXISTS departamento;
''',
'20260619000900_create_ciudad.sql': '''-- migrate:up
CREATE TABLE ciudad (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  departamento_id INTEGER NOT NULL,
  FOREIGN KEY (departamento_id) REFERENCES departamento(id)
);

-- migrate:down
DROP TABLE IF EXISTS ciudad;
''',
'20260619001000_create_neighbourhoods.sql': '''-- migrate:up
CREATE TABLE neighbourhoods (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL,
  longitud REAL,
  latitud REAL,
  neighbourhood_overview TEXT,
  ciudad_id INTEGER NOT NULL,
  FOREIGN KEY (ciudad_id) REFERENCES ciudad(id)
);

-- migrate:down
DROP TABLE IF EXISTS neighbourhoods;
''',
'20260619001100_create_persona.sql': '''-- migrate:up
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

-- migrate:down
DROP TABLE IF EXISTS persona;
''',
'20260619001200_create_inquilinos.sql': '''-- migrate:up
CREATE TABLE inquilinos (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  persona_id INTEGER NOT NULL,
  FOREIGN KEY (persona_id) REFERENCES persona(id)
);

-- migrate:down
DROP TABLE IF EXISTS inquilinos;
''',
'20260619001300_create_response_time.sql': '''-- migrate:up
CREATE TABLE response_time (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL
);

-- migrate:down
DROP TABLE IF EXISTS response_time;
''',
'20260619001400_create_host.sql': '''-- migrate:up
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
''',
'20260619001500_create_host_verifications.sql': '''-- migrate:up
CREATE TABLE host_verifications (
  verification_id INTEGER NOT NULL,
  host_id INTEGER NOT NULL,
  PRIMARY KEY (verification_id, host_id),
  FOREIGN KEY (verification_id) REFERENCES verifications(id),
  FOREIGN KEY (host_id) REFERENCES host(id)
);

-- migrate:down
DROP TABLE IF EXISTS host_verifications;
''',
'20260619001600_create_listings.sql': '''-- migrate:up
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
''',
'20260619001700_create_review.sql': '''-- migrate:up
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

-- migrate:down
DROP TABLE IF EXISTS review;
''',
'20260619001800_create_listing_inquilinos.sql': '''-- migrate:up
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
''',
'20260619001900_create_imagen.sql': '''-- migrate:up
CREATE TABLE imagen (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  url TEXT NOT NULL,
  listing_id INTEGER NOT NULL,
  FOREIGN KEY (listing_id) REFERENCES listings(id)
);

-- migrate:down
DROP TABLE IF EXISTS imagen;
''',
'20260619002000_create_listing_payments.sql': '''-- migrate:up
CREATE TABLE listings_payments (
  payment_id INTEGER NOT NULL,
  listing_id INTEGER NOT NULL,
  PRIMARY KEY (payment_id, listing_id),
  FOREIGN KEY (payment_id) REFERENCES payments(id),
  FOREIGN KEY (listing_id) REFERENCES listings(id)
);

-- migrate:down
DROP TABLE IF EXISTS listings_payments;
''',
'20260619002100_create_listings_amenities.sql': '''-- migrate:up
CREATE TABLE listings_amenities (
  amenity_id INTEGER NOT NULL,
  listing_id INTEGER NOT NULL,
  PRIMARY KEY (amenity_id, listing_id),
  FOREIGN KEY (amenity_id) REFERENCES amenities(id),
  FOREIGN KEY (listing_id) REFERENCES listings(id)
);

-- migrate:down
DROP TABLE IF EXISTS listings_amenities;
'''
}

for fname, sql in migrations.items():
    (MIG_DIR / fname).write_text(sql, encoding='utf-8')

# ---------- Project metadata ----------
(OUT / '.env').write_text('DB=sqlite:db/database.db\n', encoding='utf-8')
(OUT / 'package.json').write_text(json.dumps({
    "name": "airbnb-sqlite-migraciones",
    "version": "1.0.0",
    "description": "Proyecto SQLite con migraciones dbmate y carga desde listings.csv",
    "main": "index.js",
    "scripts": {
        "dbmate:new": "npx dbmate -d db/migrations -e DB new",
        "dbmate:up": "npx dbmate -d db/migrations -e DB up",
        "dbmate:rollback": "npx dbmate -d db/migrations -e DB rollback",
        "dbmate:dump": "npx dbmate -d db/migrations -e DB dump",
        "load": "python cargar_datos.py"
    },
    "dependencies": {"dbmate": "^2.33.0"}
}, indent=2, ensure_ascii=False), encoding='utf-8')

# ---------- Create DB ----------
conn = sqlite3.connect(DB_PATH)
conn.execute('PRAGMA foreign_keys = ON;')
cur = conn.cursor()
# schema_migrations like dbmate
cur.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version varchar(255) PRIMARY KEY);')
for fname in sorted(migrations):
    sql = migrations[fname]
    up = sql.split('-- migrate:down')[0].replace('-- migrate:up', '')
    cur.executescript(up)
    cur.execute('INSERT INTO schema_migrations(version) VALUES (?)', (fname.split('_')[0],))
conn.commit()

# ---------- Load CSV ----------
usecols = [
'id','listing_url','name','description','neighborhood_overview','picture_url',
'host_id','host_url','host_name','host_since','host_about','host_response_time','host_response_rate','host_acceptance_rate','host_is_superhost','host_thumbnail_url','host_picture_url','host_listings_count','host_total_listings_count','host_verifications','host_has_profile_pic','host_identity_verified','host_neighbourhood',
'neighbourhood','neighbourhood_cleansed','latitude','longitude','property_type','room_type','accommodates','bathrooms_text','bedrooms','beds','amenities','price','minimum_nights','maximum_nights','has_availability','calendar_last_scraped','number_of_reviews','first_review','last_review','review_scores_rating','instant_bookable'
]
print('Leyendo CSV...')
df = pd.read_csv(SRC_CSV, usecols=usecols, low_memory=False)
# Drop bad rows with missing ids or host ids
df = df.dropna(subset=['id','host_id']).copy()
df['id'] = df['id'].apply(clean_int)
df['host_id'] = df['host_id'].apply(clean_int)
df = df.dropna(subset=['id','host_id']).copy()
df['id'] = df['id'].astype(int)
df['host_id'] = df['host_id'].astype(int)
# de-dupe listings
before = len(df)
df = df.drop_duplicates(subset=['id'], keep='first').copy()
print(f'Filas listings: {len(df)} de {before}')

# Insert dimension helper

def insert_lookup(table, col, values):
    values = sorted({clean_text(v) for v in values if clean_text(v)})
    if not values:
        return {}
    cur.executemany(f'INSERT INTO {table} ({col}) VALUES (?)', [(v,) for v in values])
    conn.commit()
    cur.execute(f'SELECT id, {col} FROM {table}')
    return {row[1]: row[0] for row in cur.fetchall()}

property_map = insert_lookup('property_type','nombre',df['property_type'])
room_map = insert_lookup('room_type','nombre',df['room_type'])
bath_map = insert_lookup('bathroom_text','nombre',df['bathrooms_text'])
response_map = insert_lookup('response_time','nombre',df['host_response_time'])

# verifications and amenities
verif_values = set()
for x in df['host_verifications'].dropna():
    verif_values.update(parse_list_cell(x))
verification_map = insert_lookup('verifications','nombre',verif_values)

amenity_values = set()
for x in df['amenities'].dropna():
    amenity_values.update(parse_list_cell(x))
amenity_map = insert_lookup('amenities','nombre',amenity_values)

# Manual/simulated useful lookup
payment_methods = ['Tarjeta de crédito', 'Tarjeta de débito', 'PayPal', 'Transferencia bancaria', 'Efectivo']
payment_map = insert_lookup('payments','nombre',payment_methods)

# Geography
cur.execute('INSERT INTO pais (nombre) VALUES (?)', ('Brazil',))
pais_id = cur.lastrowid
cur.execute('INSERT INTO departamento (nombre, pais_id) VALUES (?,?)', ('Rio de Janeiro', pais_id))
dep_id = cur.lastrowid
cur.execute('INSERT INTO ciudad (nombre, departamento_id) VALUES (?,?)', ('Rio de Janeiro', dep_id))
city_id = cur.lastrowid
conn.commit()

# Neighbourhoods
neigh_map = {}
for neigh, group in df.groupby('neighbourhood_cleansed', dropna=True):
    nombre = clean_text(neigh)
    if not nombre:
        continue
    lat = pd.to_numeric(group['latitude'], errors='coerce').mean()
    lon = pd.to_numeric(group['longitude'], errors='coerce').mean()
    overview = None
    for val in group['neighborhood_overview'].dropna():
        overview = clean_text(val)
        if overview:
            break
    cur.execute('''INSERT INTO neighbourhoods (nombre, longitud, latitud, neighbourhood_overview, ciudad_id)
                   VALUES (?,?,?,?,?)''', (nombre, None if pd.isna(lon) else float(lon), None if pd.isna(lat) else float(lat), overview, city_id))
    neigh_map[nombre] = cur.lastrowid
conn.commit()

# Ensure unknown neighbourhood exists
if 'Sin barrio' not in neigh_map:
    cur.execute('INSERT INTO neighbourhoods (nombre, longitud, latitud, neighbourhood_overview, ciudad_id) VALUES (?,?,?,?,?)', ('Sin barrio', None, None, None, city_id))
    neigh_map['Sin barrio'] = cur.lastrowid
    conn.commit()

# Personas + Hosts
host_persona_map = {}
host_rows = []
for host_id, group in df.groupby('host_id', sort=False):
    r = group.iloc[0]
    nombre, apellido = split_name(r.get('host_name'))
    neigh_name = clean_text(r.get('host_neighbourhood')) or clean_text(r.get('neighbourhood_cleansed')) or 'Sin barrio'
    neigh_id = neigh_map.get(neigh_name, neigh_map['Sin barrio'])
    cur.execute('''INSERT INTO persona (nombre, apellido, dni, telefono, correo, fecha_nacimiento, neighbourhood_id)
                   VALUES (?,?,?,?,?,?,?)''', (nombre, apellido, None, None, None, None, neigh_id))
    persona_id = cur.lastrowid
    host_persona_map[int(host_id)] = persona_id
    response_id = response_map.get(clean_text(r.get('host_response_time')))
    host_rows.append((
        int(host_id), clean_bool(r.get('host_is_superhost')), clean_text(r.get('host_picture_url')), clean_text(r.get('host_name')),
        clean_text(r.get('host_about')), clean_text(r.get('host_acceptance_rate')), clean_text(r.get('host_response_rate')),
        clean_date(r.get('host_since')), clean_text(r.get('host_thumbnail_url')), clean_bool(r.get('host_has_profile_pic')),
        clean_text(r.get('host_url')), clean_bool(r.get('host_identity_verified')), clean_int(r.get('host_listings_count')),
        clean_int(r.get('host_total_listings_count')), response_id, persona_id
    ))
cur.executemany('''INSERT INTO host (id, is_superhost, picture_url, nombre, about, acceptance_rate, response_rate, since, thumbnail_url, has_profile_pic, url, identity_verified, listing_count, total_listing_count, response_time_id, persona_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', host_rows)
conn.commit()

# Host verifications
hv_pairs = set()
for host_id, group in df.groupby('host_id', sort=False):
    cell = group.iloc[0].get('host_verifications')
    for v in parse_list_cell(cell):
        vid = verification_map.get(v)
        if vid:
            hv_pairs.add((vid, int(host_id)))
cur.executemany('INSERT OR IGNORE INTO host_verifications (verification_id, host_id) VALUES (?,?)', sorted(hv_pairs))
conn.commit()

# Listings
listing_rows = []
for _, r in df.iterrows():
    neigh_name = clean_text(r.get('neighbourhood_cleansed')) or 'Sin barrio'
    listing_rows.append((
        int(r['id']), clean_text(r.get('name')), clean_text(r.get('description')), clean_text(r.get('listing_url')),
        clean_real(r.get('price')), clean_int(r.get('accommodates')), clean_bool(r.get('instant_bookable')),
        clean_date(r.get('calendar_last_scraped')), clean_int(r.get('beds')), clean_date(r.get('last_review')),
        clean_date(r.get('first_review')), clean_int(r.get('number_of_reviews')), clean_bool(r.get('has_availability')),
        clean_int(r.get('bedrooms')), clean_int(r.get('minimum_nights')), clean_int(r.get('maximum_nights')),
        room_map.get(clean_text(r.get('room_type'))), bath_map.get(clean_text(r.get('bathrooms_text'))),
        neigh_map.get(neigh_name, neigh_map['Sin barrio']), property_map.get(clean_text(r.get('property_type'))), int(r['host_id'])
    ))
cur.executemany('''INSERT OR IGNORE INTO listings (id, nombre, description, listing_url, price, accommodates, instant_bookable, calendar_last_scraped, beds, last_review, first_review, number_of_reviews, has_availability, bedrooms, minimum_nights, maximum_nights, room_type_id, bathroom_text_id, neighbourhood_id, property_type_id, host_id)
                   VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''', listing_rows)
conn.commit()

# Imagen
img_rows = []
for _, r in df.iterrows():
    url = clean_text(r.get('picture_url'))
    if url:
        img_rows.append((url, int(r['id'])))
cur.executemany('INSERT INTO imagen (url, listing_id) VALUES (?,?)', img_rows)
conn.commit()

# Listings amenities
la_pairs = set()
for _, r in df.iterrows():
    lid = int(r['id'])
    for a in parse_list_cell(r.get('amenities')):
        aid = amenity_map.get(a)
        if aid:
            la_pairs.add((aid, lid))
cur.executemany('INSERT OR IGNORE INTO listings_amenities (amenity_id, listing_id) VALUES (?,?)', list(la_pairs))
conn.commit()

# Listings payments - synthetic but useful because CSV has no payment method.
lp_pairs = []
payment_ids = sorted(payment_map.values())
for lid in df['id'].tolist():
    pid = payment_ids[int(lid) % len(payment_ids)]
    lp_pairs.append((pid, int(lid)))
cur.executemany('INSERT OR IGNORE INTO listings_payments (payment_id, listing_id) VALUES (?,?)', lp_pairs)
conn.commit()

# Synthetic inquilinos for important relation/reviews/reservations.
sample_names = [
    ('Ana','Silva'),('Bruno','Souza'),('Carla','Oliveira'),('Daniel','Santos'),('Eduardo','Lima'),
    ('Fernanda','Costa'),('Gabriel','Pereira'),('Helena','Ribeiro'),('Igor','Mendes'),('Juliana','Alves'),
    ('Lucas','Ferreira'),('Mariana','Gomes'),('Nicolas','Rocha'),('Patricia','Martins'),('Rafael','Barbosa'),
    ('Sofia','Dias'),('Thiago','Nunes'),('Valeria','Cardoso'),('William','Teixeira'),('Yasmin','Moreira')
]
inq_ids = []
neigh_ids = list(neigh_map.values())
for i in range(200):
    n, a = sample_names[i % len(sample_names)]
    dni = 10000000 + i
    telefono = f'+55 21 9{1000+i:04d}-{2000+i:04d}'
    correo = f'inquilino{i+1}@example.com'
    fecha = f'{1980 + (i % 25):04d}-{1 + (i % 12):02d}-{1 + (i % 27):02d}'
    neigh_id = neigh_ids[i % len(neigh_ids)]
    cur.execute('''INSERT INTO persona (nombre, apellido, dni, telefono, correo, fecha_nacimiento, neighbourhood_id)
                   VALUES (?,?,?,?,?,?,?)''', (n, a, dni, telefono, correo, fecha, neigh_id))
    persona_id = cur.lastrowid
    cur.execute('INSERT INTO inquilinos (persona_id) VALUES (?)', (persona_id,))
    inq_ids.append(cur.lastrowid)
conn.commit()

# Reviews from available rating: real listing score/date + synthetic inquilino id.
review_rows = []
for _, r in df.iterrows():
    rating = clean_real(r.get('review_scores_rating'))
    num_reviews = clean_int(r.get('number_of_reviews')) or 0
    if rating is None or num_reviews <= 0:
        continue
    # Airbnb rating normally 0-5. Convert to integer 1-5.
    score = max(1, min(5, int(round(rating))))
    inq_id = inq_ids[int(r['id']) % len(inq_ids)]
    fecha = clean_date(r.get('last_review')) or clean_date(r.get('first_review')) or clean_date(r.get('calendar_last_scraped'))
    comentario = 'Calificación promedio importada del dataset.'
    review_rows.append((comentario, score, fecha, int(r['id']), inq_id))
cur.executemany('INSERT INTO review (comentario, score, fecha, listing_id, inquilino_id) VALUES (?,?,?,?,?)', review_rows)
conn.commit()

# Simulated bookings for first 1000 listings.
booking_rows = []
base_date = datetime(2026, 1, 1)
for i, (_, r) in enumerate(df.head(1000).iterrows()):
    min_nights = clean_int(r.get('minimum_nights')) or 1
    days = max(1, min(min_nights, 30))
    llegada = base_date + timedelta(days=i % 180)
    retiro = llegada + timedelta(days=days)
    inq_id = inq_ids[i % len(inq_ids)]
    booking_rows.append((days, llegada.date().isoformat(), retiro.date().isoformat(), inq_id, int(r['id'])))
cur.executemany('INSERT OR IGNORE INTO listing_inquilinos (cantidad_dias, llegada, retiro, inquilino_id, listing_id) VALUES (?,?,?,?,?)', booking_rows)
conn.commit()

# Create indexes for speed
indexes = [
'CREATE INDEX IF NOT EXISTS idx_listings_host ON listings(host_id);',
'CREATE INDEX IF NOT EXISTS idx_listings_neighbourhood ON listings(neighbourhood_id);',
'CREATE INDEX IF NOT EXISTS idx_listings_property_type ON listings(property_type_id);',
'CREATE INDEX IF NOT EXISTS idx_review_listing ON review(listing_id);',
'CREATE INDEX IF NOT EXISTS idx_la_listing ON listings_amenities(listing_id);',
'CREATE INDEX IF NOT EXISTS idx_hv_host ON host_verifications(host_id);'
]
for idx in indexes:
    cur.execute(idx)
conn.commit()

# Validate FKs
cur.execute('PRAGMA foreign_key_check;')
fk_errors = cur.fetchall()
if fk_errors:
    raise RuntimeError(f'Foreign key errors: {fk_errors[:10]}')

# Counts
cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('sqlite_sequence','schema_migrations') ORDER BY name")
tables = [r[0] for r in cur.fetchall()]
counts = {}
for t in tables:
    cur.execute(f'SELECT COUNT(*) FROM {t}')
    counts[t] = cur.fetchone()[0]
print('Conteos:', counts)

# schema dump
schema_path = OUT / 'db' / 'schema.sql'
with open(schema_path, 'w', encoding='utf-8') as f:
    for line in conn.iterdump():
        # keep schema only? This dumps data too huge; skip INSERTS for schema.sql
        if line.startswith('INSERT INTO'):
            continue
        f.write(line + '\n')
conn.close()

# Loader script (reusable): embed a simplified message and point to current build script content minus absolute paths? We'll create a portable copy.
portable = Path('/mnt/data/build_clean_project.py').read_text(encoding='utf-8')
portable = portable.replace("SRC_CSV = Path('/mnt/data/listings (1).csv')", "SRC_CSV = Path('listings (1).csv')")
portable = portable.replace("OUT = Path('/mnt/data/airbnb_sqlite_limpio')", "OUT = Path('.')")
portable = portable.replace("DB_PATH = OUT / 'db' / 'database.db'", "DB_PATH = OUT / 'db' / 'database.db'")
# Avoid deleting current directory in portable script; rewrite initial cleanup section lightly
portable = portable.replace("if OUT.exists():\n    shutil.rmtree(OUT)\nMIG_DIR.mkdir(parents=True, exist_ok=True)", "# Este script se ejecuta dentro de la carpeta del proyecto.\n# Borra y reconstruye solo la carpeta db para regenerar la base desde cero.\nif (OUT / 'db').exists():\n    shutil.rmtree(OUT / 'db')\nMIG_DIR.mkdir(parents=True, exist_ok=True)")
(OUT / 'cargar_datos.py').write_text(portable, encoding='utf-8')

# Queries/checks
(OUT / 'consultas_prueba.sql').write_text('''PRAGMA foreign_keys = ON;

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
''', encoding='utf-8')

# README
readme = f'''PROYECTO AIRBNB - SQLITE LIMPIO
================================

Qué se hizo:
1. Se corrigieron las migraciones para SQLite.
2. Se corrigieron las foreign keys mal escritas.
3. Se cambió VARCHAR/BOOLEAN/DATE a tipos compatibles con SQLite:
   - TEXT para textos y fechas.
   - REAL para precios y coordenadas.
   - INTEGER para enteros y booleanos 0/1.
4. Se corrigió el nombre de neighbourhoods y host_verifications.
5. Se creó la base db/database.db desde cero.
6. Se cargaron datos reales desde listings (1).csv cuando el CSV sí los contiene.
7. Se añadieron datos simulados solo donde el CSV no trae información real: inquilinos, reservas y métodos de pago.

Tablas y conteos cargados:
{json.dumps(counts, indent=2, ensure_ascii=False)}

Archivos importantes:
- db/database.db: base SQLite ya creada y poblada.
- db/migrations/: migraciones corregidas.
- db/schema.sql: estructura final de la base.
- cargar_datos.py: script para reconstruir la base desde el CSV.
- consultas_prueba.sql: consultas para validar el trabajo.

Cómo usar en VS Code:
1. Abrir la carpeta del proyecto.
2. Revisar la base db/database.db con una extensión de SQLite.
3. Ejecutar las consultas de consultas_prueba.sql.

Si quieres reconstruir desde cero:
1. Coloca el archivo listings (1).csv en la raíz del proyecto.
2. Ejecuta:
   python cargar_datos.py

Nota importante:
El CSV de Airbnb no trae datos reales de pagos, inquilinos ni reservas. Por eso esas tablas se conservaron porque aparecen en el diagrama, pero se poblaron con datos simulados y coherentes para que las relaciones funcionen.
'''
(OUT / 'README_Eduardo.txt').write_text(readme, encoding='utf-8')

# Zip excluding nothing big; don't include source csv.
zip_out = Path('/mnt/data/airbnb_sqlite_limpio.zip')
if zip_out.exists():
    zip_out.unlink()
with zipfile.ZipFile(zip_out, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in OUT.rglob('*'):
        if p.is_file():
            z.write(p, p.relative_to(OUT.parent))
print('ZIP:', zip_out, zip_out.stat().st_size)
print('DB:', DB_PATH, DB_PATH.stat().st_size)
