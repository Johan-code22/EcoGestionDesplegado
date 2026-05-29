"""
database.py — Configuración de SQLite con sqlite3 nativo
Principio SOLID: Single Responsibility — solo maneja conexión/esquema
"""

import sqlite3
import os

DB_PATH = os.environ.get("DB_PATH", "ecogestion.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    # SCRUM-20: Mejoras de rendimiento y concurrencia
    conn.execute("PRAGMA journal_mode = WAL")      # Permite lecturas concurrentes
    conn.execute("PRAGMA synchronous = NORMAL")    # Balance entre seguridad y velocidad
    conn.execute("PRAGMA cache_size = -8000")      # 8MB de caché en memoria
    conn.execute("PRAGMA temp_store = MEMORY")     # Tablas temporales en RAM
    return conn


def get_db():
    """Dependency injection para FastAPI: abre y cierra la conexión por request."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


DDL = """
-- 1. Municipios (sin dependencias)
CREATE TABLE IF NOT EXISTS municipios (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre        TEXT    NOT NULL,
    departamento  TEXT    NOT NULL DEFAULT '',
    codigo        TEXT    NOT NULL DEFAULT '',
    activo        INTEGER NOT NULL DEFAULT 0,
    creado_en     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 2. Usuarios (sin dependencias)
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT    NOT NULL,
    rol         TEXT    NOT NULL CHECK(rol IN ('administrador', 'operador')),
    password    TEXT    NOT NULL DEFAULT '',
    creado_en   TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 3. Diagnósticos (depende de usuarios)
CREATE TABLE IF NOT EXISTS diagnosticos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    anio            INTEGER NOT NULL,
    periodo         TEXT    NOT NULL,
    organico        REAL    NOT NULL DEFAULT 0,
    reciclable      REAL    NOT NULL DEFAULT 0,
    no_aprovechable REAL    NOT NULL DEFAULT 0,
    especial        REAL    NOT NULL DEFAULT 0,
    observaciones   TEXT,
    usuario_id      INTEGER REFERENCES usuarios(id),
    municipio_id    INTEGER DEFAULT 1,
    creado_en       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 4. Metas (depende de diagnósticos y usuarios)
CREATE TABLE IF NOT EXISTS metas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    periodo         TEXT    NOT NULL,
    tipo_residuo    TEXT    NOT NULL,
    valor_meta      REAL    NOT NULL CHECK(valor_meta >= 0),
    indicador       TEXT,
    diagnostico_id  INTEGER REFERENCES diagnosticos(id),
    usuario_id      INTEGER REFERENCES usuarios(id),
    municipio_id    INTEGER DEFAULT 1,
    creado_en       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 5. Clasificaciones (depende de usuarios)
CREATE TABLE IF NOT EXISTS clasificaciones (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo_residuo      TEXT    NOT NULL,
    fecha_recoleccion TEXT    NOT NULL,
    ruta_zona         TEXT,
    vehiculo          TEXT,
    observaciones     TEXT,
    usuario_id        INTEGER REFERENCES usuarios(id),
    municipio_id      INTEGER DEFAULT 1,
    creado_en         TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 6. Cantidades (depende de usuarios)
CREATE TABLE IF NOT EXISTS cantidades (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha           TEXT    NOT NULL,
    organico        REAL    NOT NULL DEFAULT 0 CHECK(organico >= 0),
    reciclable      REAL    NOT NULL DEFAULT 0 CHECK(reciclable >= 0),
    no_aprovechable REAL    NOT NULL DEFAULT 0 CHECK(no_aprovechable >= 0),
    especial        REAL    NOT NULL DEFAULT 0 CHECK(especial >= 0),
    total           REAL    GENERATED ALWAYS AS
                    (organico + reciclable + no_aprovechable + especial) STORED,
    usuario_id      INTEGER REFERENCES usuarios(id),
    municipio_id    INTEGER DEFAULT 1,
    creado_en       TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 7. Acciones log (depende de usuarios)
CREATE TABLE IF NOT EXISTS acciones_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    accion      TEXT    NOT NULL,
    entidad     TEXT    NOT NULL,
    detalle     TEXT,
    usuario_id  INTEGER REFERENCES usuarios(id),
    fecha_hora  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 8. Alertas (depende de clasificaciones)
CREATE TABLE IF NOT EXISTS alertas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo                TEXT    NOT NULL DEFAULT 'organico_48h',
    mensaje             TEXT    NOT NULL,
    entidad             TEXT    NOT NULL,
    entidad_id          INTEGER NOT NULL,
    horas_transcurridas REAL    NOT NULL DEFAULT 0,
    resuelta            INTEGER NOT NULL DEFAULT 0,
    generada_en         TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 9. Horarios de recolección
CREATE TABLE IF NOT EXISTS horarios_recoleccion (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    zona         TEXT    NOT NULL,
    dias         TEXT    NOT NULL,
    hora_inicio  TEXT    NOT NULL,
    hora_fin     TEXT    NOT NULL,
    tipo_residuo TEXT    NOT NULL DEFAULT 'General',
    activo       INTEGER NOT NULL DEFAULT 1,
    creado_en    TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 10. Campañas
CREATE TABLE IF NOT EXISTS campanas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    titulo      TEXT    NOT NULL,
    descripcion TEXT    NOT NULL,
    periodo     TEXT    NOT NULL DEFAULT '',
    activa      INTEGER NOT NULL DEFAULT 1,
    municipio_id INTEGER DEFAULT 1,
    creado_en   TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 11. Puntos críticos
CREATE TABLE IF NOT EXISTS puntos_criticos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion TEXT    NOT NULL,
    ubicacion   TEXT    NOT NULL DEFAULT 'Sin especificar',
    imagen_url  TEXT    NOT NULL DEFAULT '',
    estado      TEXT    NOT NULL DEFAULT 'pendiente'
                CHECK(estado IN ('pendiente', 'en_proceso', 'resuelto')),
    municipio_id INTEGER DEFAULT 1,
    creado_en   TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

-- 12. Índices SCRUM-20
CREATE INDEX IF NOT EXISTS idx_cantidades_fecha
    ON cantidades(fecha);
CREATE INDEX IF NOT EXISTS idx_clasificaciones_tipo
    ON clasificaciones(tipo_residuo, fecha_recoleccion);
CREATE INDEX IF NOT EXISTS idx_alertas_resuelta
    ON alertas(resuelta);
CREATE INDEX IF NOT EXISTS idx_acciones_fecha
    ON acciones_log(fecha_hora DESC);
CREATE INDEX IF NOT EXISTS idx_diagnosticos_anio
    ON diagnosticos(anio DESC);
"""

SEED_SQL = """
INSERT OR IGNORE INTO municipios (id, nombre, departamento, codigo, activo)
VALUES
    (1, 'Municipio Demo',    'Cundinamarca', '25001', 1),
    (2, 'Municipio Norte',   'Boyacá',       '15001', 0),
    (3, 'Municipio Sur',     'Tolima',       '73001', 0);

INSERT OR IGNORE INTO usuarios (id, nombre, rol, password) VALUES
    (1, 'Admin', 'administrador',
     '240be518fabd2724ddb6f04eeb1da5967448d7e831c08c8fa822809f74c720a9'),
    (2, 'Martínez', 'operador',
     '1725165c9a0b3698a3d01016e0d8205155820b8d7f21835ca64c0f81c728d880'),
    (3, 'López', 'operador',
     '1725165c9a0b3698a3d01016e0d8205155820b8d7f21835ca64c0f81c728d880');

INSERT OR IGNORE INTO diagnosticos
    (id, anio, periodo, organico, reciclable, no_aprovechable, especial, usuario_id)
VALUES
    (1, 2024, 'II Semestre', 72.4, 130.1, 105.3, 0.0, 1),
    (2, 2024, 'I Semestre',  68.0, 120.5,  98.2, 0.0, 1);

INSERT OR IGNORE INTO metas (id, periodo, tipo_residuo, valor_meta, diagnostico_id, usuario_id) VALUES
    (1, '2025 — I Semestre', 'Reciclable', 150.0, 1, 1),
    (2, '2025 — I Semestre', 'Orgánico',    80.0, 1, 1);

INSERT OR IGNORE INTO cantidades (id, fecha, organico, reciclable, no_aprovechable, especial, usuario_id) VALUES
    (1, '2025-03-24', 4.2, 8.1, 6.3, 0.0, 2),
    (2, '2025-03-23', 3.8, 7.5, 5.9, 0.0, 2),
    (3, '2025-03-22', 4.0, 7.9, 6.1, 0.0, 3);

INSERT OR IGNORE INTO clasificaciones (id, tipo_residuo, fecha_recoleccion, ruta_zona, usuario_id) VALUES
    (1, 'Reciclable',      '2025-03-24', 'Zona Norte',  2),
    (2, 'Orgánico',        '2025-03-24', 'Zona Centro', 3),
    (3, 'No Aprovechable', '2025-03-23', 'Zona Sur',    2);

INSERT OR IGNORE INTO acciones_log (id, accion, entidad, detalle, usuario_id) VALUES
    (1, 'CREATE', 'diagnosticos',    'Diagnóstico 2024-II creado',            1),
    (2, 'CREATE', 'clasificaciones', 'Clasificación reciclable — Zona Norte', 2),
    (3, 'CREATE', 'metas',           'Meta 2025-I reciclable: 150 t',         1),
    (4, 'CREATE', 'cantidades',      'Cantidad registrada: 18.6 t',           2);

-- Alertas por almacenamiento orgánico >48h
CREATE TABLE IF NOT EXISTS alertas (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo                TEXT    NOT NULL DEFAULT 'organico_48h',
    mensaje             TEXT    NOT NULL,
    entidad             TEXT    NOT NULL,
    entidad_id          INTEGER NOT NULL,
    horas_transcurridas REAL    NOT NULL DEFAULT 0,
    resuelta            INTEGER NOT NULL DEFAULT 0,
    generada_en         TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
);

INSERT OR IGNORE INTO horarios_recoleccion
    (id, zona, dias, hora_inicio, hora_fin, tipo_residuo, activo)
VALUES
    (1, 'Zona Norte',  'Lunes, Miércoles, Viernes', '06:00', '10:00', 'General',    1),
    (2, 'Zona Norte',  'Martes, Jueves',             '14:00', '18:00', 'Reciclable', 1),
    (3, 'Zona Centro', 'Lunes a Viernes',            '07:00', '11:00', 'General',    1),
    (4, 'Zona Centro', 'Sábado',                     '08:00', '12:00', 'Reciclable', 1),
    (5, 'Zona Sur',    'Martes, Jueves, Sábado',     '06:00', '10:00', 'General',    1),
    (6, 'Zona Sur',    'Miércoles',                  '14:00', '17:00', 'Orgánico',   1);

INSERT OR IGNORE INTO campanas (id, titulo, descripcion, periodo, activa) VALUES
    (1, 'Separa y Recicla',
     'Aprende a separar correctamente tus residuos en la fuente. Usa bolsa verde para orgánicos y bolsa blanca para reciclables.',
     '2025 — I Semestre', 1),
    (2, 'Residuos Orgánicos al Compost',
     'Los residuos de cocina como cáscaras y restos de comida deben ir separados para facilitar el compostaje municipal.',
     '2025 — I Semestre', 1),
    (3, 'Día de Reciclaje',
     'Cada martes y jueves es día de reciclaje en tu zona. Recuerda sacar tus materiales limpios y secos.',
     '2025 — II Semestre', 0);

INSERT OR IGNORE INTO puntos_criticos
    (id, descripcion, ubicacion, estado)
VALUES
    (1, 'Acumulación de bolsas sin clasificar en esquina',
     'Calle 15 con Carrera 8, Zona Norte', 'pendiente'),
    (2, 'Residuos de construcción sobre el andén',
     'Avenida Principal 45, Zona Centro', 'en_proceso'),
    (3, 'Punto de reciclaje desbordado',
     'Parque Central, Zona Sur', 'resuelto');
"""


def init_db():
    conn = get_connection()
    conn.executescript(DDL)
    conn.executescript(SEED_SQL)

    # SCRUM-19: Agrega municipio_id a tablas existentes si no existe
    tablas = [
        "cantidades", "diagnosticos", "clasificaciones",
        "metas", "campanas", "puntos_criticos"
    ]
    for tabla in tablas:
        try:
            conn.execute(
                f"ALTER TABLE {tabla} ADD COLUMN municipio_id INTEGER DEFAULT 1"
            )
            conn.commit()
            print(f"[EcoGestión] Columna municipio_id agregada a {tabla}")
        except Exception:
            pass  # La columna ya existe, no hace falta agregarla

    # Asigna municipio_id=1 a todos los registros sin municipio
    for tabla in tablas:
        try:
            conn.execute(
                f"UPDATE {tabla} SET municipio_id = 1 WHERE municipio_id IS NULL"
            )
            conn.commit()
        except Exception:
            pass

    conn.close()
    print("[EcoGestión] Base de datos SQLite inicializada.")
