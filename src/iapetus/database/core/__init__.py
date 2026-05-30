"""Core kernel database layer (connections, schema bootstrap, versioning).

Domain repositories (e.g. learning runs) build on this package; they should not
open raw ``sqlite3`` connections except via :func:`kernel_connection` or
:class:`~iapetus.database.core.kernel_database.KernelDatabase`.
"""
from __future__ import annotations

from iapetus.database.core.constants import KERNEL_SCHEMA_VERSION, SCHEMA_VERSION
from iapetus.database.core.bootstrap import (
    apply_kernel_schema,
    apply_schema,
    init_kernel_database,
    init_learning_index_database,
)
from iapetus.database.core.connection import (
    KERNEL_DB_FILENAME,
    LEARNING_INDEX_DB_FILENAME,
    connect_learning_index,
    default_kernel_db_path,
    default_learning_index_db_path,
    kernel_connection,
    learning_index_connection,
    open_connection,
)
from iapetus.database.core.health import kernel_database_health
from iapetus.database.core.kernel_database import KernelDatabase, default_kernel_database
from iapetus.database.core.migrations import (
    SchemaAheadError,
    SchemaVersionError,
    ensure_schema_compatible,
    reconcile_schema_version,
)
from iapetus.database.core.registry import (
    DomainSchema,
    apply_registered_domain_schemas,
    clear_domain_schemas_for_tests,
    iter_domain_schemas,
    register_domain_schema,
)
from iapetus.database.core.schema_meta import (
    SCHEMA_META_TABLE,
    SCHEMA_VERSION_KEY,
    apply_schema_meta,
    read_schema_version,
    write_schema_version,
)

__all__ = [
    "KERNEL_DB_FILENAME",
    "KERNEL_SCHEMA_VERSION",
    "LEARNING_INDEX_DB_FILENAME",
    "SCHEMA_META_TABLE",
    "SCHEMA_VERSION",
    "SCHEMA_VERSION_KEY",
    "DomainSchema",
    "KernelDatabase",
    "SchemaAheadError",
    "SchemaVersionError",
    "apply_kernel_schema",
    "apply_registered_domain_schemas",
    "apply_schema",
    "apply_schema_meta",
    "clear_domain_schemas_for_tests",
    "connect_learning_index",
    "default_kernel_database",
    "default_kernel_db_path",
    "default_learning_index_db_path",
    "ensure_schema_compatible",
    "init_kernel_database",
    "init_learning_index_database",
    "iter_domain_schemas",
    "kernel_connection",
    "kernel_database_health",
    "learning_index_connection",
    "open_connection",
    "read_schema_version",
    "reconcile_schema_version",
    "register_domain_schema",
    "write_schema_version",
]
