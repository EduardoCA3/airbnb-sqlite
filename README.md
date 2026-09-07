# Airbnb SQLite

Proyecto de modelado y carga de una base de datos relacional para alojamientos de Airbnb usando Python, SQL y SQLite.

## Funcionalidades

- Esquema relacional normalizado con 21 migraciones.
- Importación y limpieza de un conjunto de datos de alojamientos.
- Relaciones entre propiedades, anfitriones, reseñas, servicios, pagos e inquilinos.
- Generación de datos ficticios para tablas que no existen en el conjunto original.
- Consultas SQL de validación.

## Uso

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python fill_database.py
```

Coloca el archivo de datos como `listings (1).csv` en la raíz antes de ejecutar el cargador.

## Privacidad

El repositorio no incluye la base de datos generada ni conjuntos de datos descargados. Los inquilinos creados por los scripts son ficticios y usan direcciones de correo `example.com`.
