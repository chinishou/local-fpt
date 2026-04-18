# Development Guide

## Architecture

```
src/local_fpt/
├── app.py                    # Flask factory: create_app() → registers blueprints, init_db
├── db/
│   ├── database.py           # init_db(), get_session() — SQLite, WAL mode, StaticPool
│   └── models.py             # SQLAlchemy ORM models
├── query/
│   └── operators.py          # Filter operator implementations
├── routes/
│   ├── api3.py               # POST /api3/json — JSON-RPC dispatcher
│   ├── info.py               # GET /info/api2, /info/api3
│   └── schema.py             # GET /schema/read
├── seed/                     # Data seeding scripts
└── services/
    ├── entity_service.py     # EntityService — all CRUD + query logic
    └── schema_service.py     # SchemaService — CORE_ENTITIES + DB seeding
```

## Key Design Decisions

### EAV (Entity-Attribute-Value) Pattern

Instead of per-entity-type tables (one table for Shot, one for Asset, etc.), all entities share two tables:

- **`entity_records`** — One row per entity: `id`, `entity_type`, `retired`, timestamps
- **`field_values`** — One row per field: `record_id`, `field_name`, `value` (JSON)

This means adding a new entity type requires zero schema migrations — just add it to `CORE_ENTITIES` in `schema_service.py`.

**Trade-off:** Filtering across multiple fields requires correlated EXISTS subqueries instead of simple `WHERE col = val`. Each field condition becomes:

```sql
EXISTS (
    SELECT 1 FROM field_values fv
    WHERE fv.record_id = entity_records.id
      AND fv.field_name = 'code'
      AND fv.value = '"SEQ010"'   -- JSON-encoded
)
```

### JSON Column Storage

All field values are stored as JSON text in SQLite. A string `"hello"` is stored as `'"hello"'` (with JSON quotes). This requires:

- **Equality comparisons:** `json.dumps(value)` before comparing with `FieldValue.value`
- **LIKE operators (contains, starts_with, ends_with):** `func.json_extract(FieldValue.value, '$')` to strip JSON quotes before pattern matching
- **in/not_in:** Each list element must be `json.dumps()`-encoded

### Correlated EXISTS for Multi-Field Filtering

The EAV pattern means filtering by two fields (e.g., `code = X AND status = Y`) requires two separate EXISTS subqueries, each correlating back to `EntityRecord.id`:

```python
exists(
    select(FieldValue.id)
    .where(FieldValue.record_id == EntityRecord.id)
    .where(FieldValue.field_name == field)
    .correlate(EntityRecord)          # critical — prevents cross-join
    .where(FieldValue.value == json.dumps(value))
)
```

The `.correlate(EntityRecord)` is essential — without it, SQLAlchemy adds `entity_records` to the subquery's FROM clause, creating a Cartesian product.

### SDK Wire Format

The `shotgun_api3` SDK does NOT call the `find` RPC method — it uses `read`:

| SDK Method | RPC Method | Notes |
|---|---|---|
| `sg.find()` | `read` | Filters as dict-format, sorts via `sorts` key |
| `sg.find_one()` | `read` | Same as find with limit=1 |
| `sg.create()` | `create` | Data sent as `fields` list, not `data` dict |
| `sg.update()` | `update` | Same format as create |
| `sg.delete()` | `delete_one` | Returns boolean |
| `sg.batch()` | `batch` | Params is a list (not dict with `requests` key) |

The `api3.py` handler normalizes both formats (SDK and simple dict).

### Soft Delete

`delete` sets `retired=True` on `EntityRecord`. `revive` clears it. Queries filter `retired=False` by default. This matches ShotGrid behavior.

### Event Log

Every mutation (create, update, delete, revive) is logged to `event_log_entries` with old/new values.

## Extending the Backend

### Adding a new entity type

1. Add entry to `CORE_ENTITIES` in `src/local_fpt/services/schema_service.py`
2. Restart the server — schema is seeded on startup
3. No migration needed — EAV pattern handles it

### Adding a new API method

1. Add `elif method_name == 'your_method':` block in `api3.py`'s `jsonrpc()` handler
2. Add service method to `entity_service.py` if needed

### Adding a new filter operator

1. Add `elif op == 'your_op':` in `_build_field_condition()` in `entity_service.py`
2. Handle JSON encoding as needed

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `FPT_DB_PATH` | `fpt_local.db` | SQLite database file path |

## Running the Server

```bash
python -m local_fpt.app          # http://127.0.0.1:8000
```

The server auto-creates the DB and seeds schema on first boot. Delete `fpt_local.db` to reset — it will be recreated on next startup.
