CREATE TABLE IF NOT EXISTS kernel_schema_version (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    schema_name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS snapshot_manifest (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    timestamp TEXT NOT NULL,
    entity_count INTEGER NOT NULL,
    purpose TEXT NOT NULL
);
