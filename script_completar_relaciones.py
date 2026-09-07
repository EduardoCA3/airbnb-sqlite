import sqlite3, pandas as pd, ast, re, json, shutil, zipfile, os
from pathlib import Path
from datetime import datetime, timedelta

OUT=Path('/mnt/data/airbnb_sqlite_limpio')
DB=OUT/'db/database.db'
CSV=Path('/mnt/data/listings (1).csv')

def clean_text(x):
    if pd.isna(x): return None
    s=str(x).strip()
    if not s or s.lower()=='nan': return None
    return re.sub(r'\s+',' ',s)

def clean_int(x):
    if pd.isna(x): return None
    try: return int(float(str(x).replace(',','').strip()))
    except Exception: return None

def clean_real(x):
    if pd.isna(x): return None
    try:
        s=str(x).replace('$','').replace(',','').strip()
        return float(s) if s else None
    except Exception: return None

def clean_date(x):
    s=clean_text(x)
    return s[:19] if s else None

def parse_list_cell(x):
    s=clean_text(x)
    if not s: return []
    try:
        v=ast.literal_eval(s)
        if isinstance(v,list):
            return [clean_text(i) for i in v if clean_text(i)]
    except Exception:
        pass
    return [p.strip().strip('"\'') for p in s.strip('[]').split(',') if p.strip().strip('"\'')]

print('Read CSV')
df=pd.read_csv(CSV, usecols=['id','amenities','minimum_nights','number_of_reviews','review_scores_rating','last_review','first_review','calendar_last_scraped'], low_memory=False)
df=df.dropna(subset=['id']).copy()
df['id']=df['id'].apply(clean_int)
df=df.dropna(subset=['id']).drop_duplicates('id')
df['id']=df['id'].astype(int)

conn=sqlite3.connect(DB)
c=conn.cursor()
# speed mode
c.execute('PRAGMA foreign_keys=OFF')
c.execute('PRAGMA synchronous=OFF')
c.execute('PRAGMA journal_mode=MEMORY')
c.execute('PRAGMA temp_store=MEMORY')
c.execute('PRAGMA cache_size=-200000')
conn.commit()

# reset dependent/simulated tables
for t in ['review','listing_inquilinos','listings_payments','listings_amenities','inquilinos']:
    c.execute(f'DELETE FROM {t}')
conn.commit()

# Remove old synthetic tenant personas if script reruns? Our first run didn't add, but safe with correo domain.
c.execute("DELETE FROM persona WHERE correo LIKE 'inquilino%@example.com'")
conn.commit()

# Amenities map
c.execute('SELECT id,nombre FROM amenities')
amenity_map={name:id_ for id_,name in c.fetchall()}
print('Build amenity pairs')
pairs=[]
for lid, amenities in df[['id','amenities']].itertuples(index=False, name=None):
    for a in parse_list_cell(amenities):
        aid=amenity_map.get(a)
        if aid:
            pairs.append((aid,int(lid)))
# remove duplicates while preserving reasonable memory
pairs=list(set(pairs))
print('Insert amenity pairs', len(pairs))
c.execute('BEGIN')
c.executemany('INSERT OR IGNORE INTO listings_amenities (amenity_id, listing_id) VALUES (?,?)', pairs)
conn.commit()

# Payments relation
c.execute('SELECT id FROM payments ORDER BY id')
pids=[r[0] for r in c.fetchall()]
lp=[(pids[int(lid)%len(pids)], int(lid)) for lid in df['id'].tolist()]
print('Insert payment pairs', len(lp))
c.execute('BEGIN')
c.executemany('INSERT OR IGNORE INTO listings_payments (payment_id, listing_id) VALUES (?,?)', lp)
conn.commit()

# tenants
c.execute('SELECT id FROM neighbourhoods ORDER BY id')
neigh_ids=[r[0] for r in c.fetchall()]
sample_names=[('Ana','Silva'),('Bruno','Souza'),('Carla','Oliveira'),('Daniel','Santos'),('Eduardo','Lima'),('Fernanda','Costa'),('Gabriel','Pereira'),('Helena','Ribeiro'),('Igor','Mendes'),('Juliana','Alves'),('Lucas','Ferreira'),('Mariana','Gomes'),('Nicolas','Rocha'),('Patricia','Martins'),('Rafael','Barbosa'),('Sofia','Dias'),('Thiago','Nunes'),('Valeria','Cardoso'),('William','Teixeira'),('Yasmin','Moreira')]
inq_ids=[]
for i in range(200):
    n,a=sample_names[i%len(sample_names)]
    dni=10000000+i
    tel=f'+55 21 9{1000+i:04d}-{2000+i:04d}'
    correo=f'inquilino{i+1}@example.com'
    fecha=f'{1980+(i%25):04d}-{1+(i%12):02d}-{1+(i%27):02d}'
    nid=neigh_ids[i%len(neigh_ids)]
    c.execute('INSERT INTO persona (nombre, apellido, dni, telefono, correo, fecha_nacimiento, neighbourhood_id) VALUES (?,?,?,?,?,?,?)',(n,a,dni,tel,correo,fecha,nid))
    pid=c.lastrowid
    c.execute('INSERT INTO inquilinos (persona_id) VALUES (?)',(pid,))
    inq_ids.append(c.lastrowid)
conn.commit()

# reviews
reviews=[]
for lid,num,rating,last,first,cal in df[['id','number_of_reviews','review_scores_rating','last_review','first_review','calendar_last_scraped']].itertuples(index=False, name=None):
    num=clean_int(num) or 0
    rating=clean_real(rating)
    if rating is None or num<=0: continue
    score=max(1,min(5,int(round(rating))))
    fecha=clean_date(last) or clean_date(first) or clean_date(cal)
    reviews.append(('Calificación promedio importada del dataset.',score,fecha,int(lid),inq_ids[int(lid)%len(inq_ids)]))
print('Insert reviews', len(reviews))
c.execute('BEGIN')
c.executemany('INSERT INTO review (comentario, score, fecha, listing_id, inquilino_id) VALUES (?,?,?,?,?)', reviews)
conn.commit()

# bookings
base=datetime(2026,1,1)
book=[]
for i,(lid,minn) in enumerate(df[['id','minimum_nights']].head(1000).itertuples(index=False, name=None)):
    days=max(1,min(clean_int(minn) or 1,30))
    llegada=base+timedelta(days=i%180)
    retiro=llegada+timedelta(days=days)
    book.append((days,llegada.date().isoformat(),retiro.date().isoformat(),inq_ids[i%len(inq_ids)],int(lid)))
print('Insert bookings', len(book))
c.executemany('INSERT OR IGNORE INTO listing_inquilinos (cantidad_dias, llegada, retiro, inquilino_id, listing_id) VALUES (?,?,?,?,?)', book)
conn.commit()

# indexes
for idx in [
'CREATE INDEX IF NOT EXISTS idx_listings_host ON listings(host_id);',
'CREATE INDEX IF NOT EXISTS idx_listings_neighbourhood ON listings(neighbourhood_id);',
'CREATE INDEX IF NOT EXISTS idx_listings_property_type ON listings(property_type_id);',
'CREATE INDEX IF NOT EXISTS idx_review_listing ON review(listing_id);',
'CREATE INDEX IF NOT EXISTS idx_la_listing ON listings_amenities(listing_id);',
'CREATE INDEX IF NOT EXISTS idx_hv_host ON host_verifications(host_id);'
]:
    c.execute(idx)
conn.commit()

# verify after enabling fk
c.execute('PRAGMA foreign_keys=ON')
fk=c.execute('PRAGMA foreign_key_check').fetchall()
print('FK errors', len(fk))
if fk:
    print(fk[:10])
# counts
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT IN ('schema_migrations','sqlite_sequence') ORDER BY name")
tabs=[r[0] for r in c.fetchall()]
counts={}
for t in tabs:
    c.execute(f'SELECT COUNT(*) FROM {t}')
    counts[t]=c.fetchone()[0]
print(json.dumps(counts,indent=2,ensure_ascii=False))

# vacuum to compact
conn.commit()
# schema no data
with open(OUT/'db/schema.sql','w',encoding='utf-8') as f:
    for line in conn.iterdump():
        if line.startswith('INSERT INTO'):
            continue
        f.write(line+'\n')
conn.close()

# files
(OUT/'consultas_prueba.sql').write_text('''PRAGMA foreign_keys = ON;

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
''',encoding='utf-8')

readme=f'''PROYECTO AIRBNB - SQLITE LIMPIO
================================

Qué se hizo:
1. Se corrigieron las migraciones para SQLite.
2. Se corrigieron las claves foráneas mal escritas:
   - listing -> listings
   - inquilino -> inquilinos
   - verification -> verifications
3. Se cambió la estructura a tipos correctos para SQLite:
   - TEXT para textos, urls y fechas.
   - REAL para precios y coordenadas.
   - INTEGER para enteros y booleanos 0/1.
   - INTEGER PRIMARY KEY AUTOINCREMENT para IDs internos.
4. Se normalizó la tabla neighbourhoods.
5. Se creó la base db/database.db desde cero.
6. Se cargaron datos reales desde listings (1).csv cuando el CSV sí los contiene.
7. Se añadieron datos simulados solo donde el CSV no trae información real: inquilinos, reservas y métodos de pago.

Tablas y conteos cargados:
{json.dumps(counts, indent=2, ensure_ascii=False)}

Archivos importantes:
- db/database.db: base SQLite ya creada y poblada.
- db/migrations/: migraciones corregidas.
- db/schema.sql: estructura final de la base.
- consultas_prueba.sql: consultas para validar el trabajo.
- script_generacion_base.py y script_completar_relaciones.py: scripts usados para generar la base.

Cómo usar en VS Code:
1. Abrir esta carpeta.
2. Instalar una extensión de SQLite si no la tienes.
3. Abrir db/database.db.
4. Ejecutar consultas_prueba.sql para verificar que todo funciona.

Nota importante:
El CSV de Airbnb no contiene pagos reales, inquilinos reales ni reservas reales. Esas tablas aparecen en tu diagrama, por eso se conservaron. Para que no queden vacías, se poblaron con datos simulados y coherentes, manteniendo las relaciones por foreign key.
'''
(OUT/'README_Eduardo.txt').write_text(readme,encoding='utf-8')
# copy scripts
for src,dst in [('/mnt/data/build_clean_project.py','script_generacion_base.py'),('/mnt/data/finalize_fast.py','script_completar_relaciones.py')]:
    shutil.copy(src, OUT/dst)
# ensure .env exists
(OUT/'.env').write_text('DB=sqlite:db/database.db\n',encoding='utf-8')
# zip no csv
zip_out=Path('/mnt/data/airbnb_sqlite_limpio.zip')
if zip_out.exists(): zip_out.unlink()
with zipfile.ZipFile(zip_out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in OUT.rglob('*'):
        if p.is_file():
            z.write(p,p.relative_to(OUT.parent))
print('ZIP', zip_out, zip_out.stat().st_size)
print('DB', DB, DB.stat().st_size)
