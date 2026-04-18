# local-fpt: Flow Production Tracking Local Backend

A local development server that implements a functional subset of the Autodesk Flow Production Tracking (formerly ShotGrid) API surface using Flask + SQLite.

**No cloud required** — runs entirely locally with a simple SQLite database.

## Requirements

- Python 3.10+
- `pip` or `poetry`

## Quick Start

```bash
# 1. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
source .venv/bin/activate      # Linux/macOS

# 2. Install dependencies
pip install -e ".[dev]"

# 3. Start the server
python -m local_fpt.app
# Server runs on http://127.0.0.1:8000
```

The server creates `fpt_local.db` (SQLite) on first boot and seeds entity schemas automatically. Set `FPT_DB_PATH` env var to use a different location.

## Connecting a Client

```python
import shotgun_api3

sg = shotgun_api3.Shotgun(
    "http://127.0.0.1:8000",
    script_name="local_dev",
    api_key="any-non-empty-string",
)
project = sg.find_one("Project", [])
print(project)
```

## Supported Entities (11)

| Entity | Key Fields | Relationships |
|---|---|---|
| **Project** | `name`, `code`, `sg_status_list` | Top-level container |
| **Sequence** | `code`, `sg_status_list` | `project` → Project |
| **Episode** | `code`, `sg_status_list` | `project` → Project |
| **Shot** | `code`, `sg_status_list` | `project`, `sg_sequence`, `sg_episode` |
| **Asset** | `code`, `sg_asset_type`, `sg_status_list` | `project` → Project |
| **Task** | `content`, `sg_status_list` | `project`, `entity` → Shot/Asset |
| **Version** | `code`, `sg_status_list` | `project`, `entity` → Shot |
| **Playlist** | `code`, `sg_status_list` | `project` → Project |
| **HumanUser** | `name`, `login`, `email`, `sg_status_list` | No project ref |
| **PublishedFiles** | `code`, `sg_status_list` | `project`, `entity` → Asset |
| **Ticket** | `code`, `name`, `sg_priority`, `sg_status_list` | `project` → Project, `entity` → Shot/Asset |

## API Methods

### Core CRUD
- `find()` — Query entities with filters, sorting, and pagination
- `find_one()` — Get single entity
- `create()` — Create new entity
- `update()` — Update entity fields
- `delete()` — Soft delete (retire) entity
- `revive()` — Restore a deleted entity
- `batch()` — Multiple create/update/delete in one call

### Schema
- `schema_read()` — All entity type and field schemas
- `schema_entity_read()` — Entity type definitions
- `schema_field_read()` — Field definitions for an entity type
- `entity_types()` — List supported entity types

### Info
- `info()` — API version info

## Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api3/json` | POST | JSON-RPC: find, create, update, delete, batch, read, schema, info |
| `/schema/read` | GET | Entity + field schema definitions |
| `/info/api2`, `/info/api3` | GET | Version info |
| `/`, `/health` | GET | Status check |

## Filter Operators

```python
# Comparison
['code', 'is', 'SEQ010']
['code', 'is_not', 'SEQ010']
['code', 'contains', 'SEQ']
['code', 'not_contains', 'SEQ']
['code', 'starts_with', 'SEQ']
['code', 'ends_with', '010']

# List
['sg_status_list', 'in', ['ip', 'fin']]
['sg_status_list', 'not_in', ['fin']]

# Null
['description', 'is_null', None]
['description', 'not_null', None]

# Entity reference
['project', 'is', {'type': 'Project', 'id': 1}]
['sg_sequence', 'is', {'type': 'Sequence', 'id': 5}]

# Logical (via filter_operator kwarg)
sg.find("Shot", [["sg_status_list", "is", "ip"], ["code", "starts_with", "SEQ"]],
        filter_operator="all")  # AND (default)
sg.find("Shot", [["code", "is", "A"], ["code", "is", "B"]],
        filter_operator="any")  # OR
```

## Sorting

```python
sg.find("Shot", [], ["code"], order=[{"field_name": "code", "direction": "asc"}])
sg.find("Shot", [], ["code"], order=[{"field_name": "code", "direction": "desc"}])
```

## Testing

**284 tests total** — local-only tests run always; cloud parity tests require a paid ShotGrid site.

| Suite | Tests | Scope |
|---|---|---|
| `tests/test_parity.py` | 56+ | SDK parity: same operation on local + cloud, assert results match |
| `tests/entities/` (11 files) | 70+ | Per-entity: CRUD, relationships, field-specific filters |
| `tests/test_rest_api.py` | 20 | REST endpoints: health, JSON-RPC, errors, pagination |

```bash
# Run local-only tests (no cloud needed)
pytest tests/test_rest_api.py -v

# Run full test suite (requires cloud credentials in .env)
python -m local_fpt.app &
pytest tests/ -v
```

### Cloud Credentials (required for parity tests)

A **paid ShotGrid site** is required — the parity tests run every operation against both local and cloud to verify behavioral equivalence.

Create `.env` from `.env.example`:
```
SG_URL=https://your-site.shotgrid.autodesk.com
SCRIPT_NAME=your_script
API_KEY=your_api_key_here
```

Parity tests are **skipped automatically** if cloud credentials are missing.

### Test Data Lifecycle

- Tests use the `shotgun_api3` SDK's `local_sg` fixture pointing to `http://127.0.0.1:8000`
- Each test session creates prefixed entities (`SG_TEST_{timestamp}_*`) on both local and cloud
- Entities are cleaned up automatically at session end
- Cloud orphan cleanup: `python tests/cleanup_cloud.py --delete`

See [docs/testing.md](docs/testing.md) for full details.

## Project Structure

```
src/local_fpt/
├── app.py                  # Flask app factory (create_app)
├── db/
│   ├── database.py         # Engine/session setup (SQLite, WAL, StaticPool)
│   └── models.py           # ORM: EntityRecord, FieldValue, EntityMeta, FieldMeta, EventLogEntry
├── query/
│   └── operators.py        # 14 filter operators
├── routes/
│   ├── api3.py             # /api3/json JSON-RPC handler (find, create, read, batch, schema)
│   ├── info.py             # /info endpoints
│   └── schema.py           # /schema/read endpoint
├── seed/                   # Data seeding scripts
└── services/
    ├── entity_service.py   # CRUD logic (EXISTS-based EAV filtering)
    └── schema_service.py   # Schema definitions + DB seeding (CORE_ENTITIES)

tests/
├── conftest.py             # Session fixtures, validation dataset, cloud cleanup
├── helpers.py              # normalize(), assert_same_entity(), assert_same_list()
├── cleanup_cloud.py        # Standalone orphan cleanup script
├── test_parity.py          # 56 SDK parity tests (local vs cloud)
├── test_rest_api.py        # 20 REST endpoint tests (local-only)
└── entities/               # 70+ per-entity parity tests
    ├── test_project.py
    ├── test_sequence.py
    ├── test_episode.py
    ├── test_shot.py
    ├── test_asset.py
    ├── test_task.py
    ├── test_version.py
    ├── test_playlist.py
    ├── test_humanuser.py
    ├── test_publishedfile.py
    └── test_ticket.py
```

## Architecture

- **Flask** — Sync web framework
- **SQLite** — WAL mode, StaticPool — zero-config database
- **SQLAlchemy 2.0** — Sync sessions, EAV pattern (EntityRecord + FieldValue)
- **EAV storage** — No per-entity-type columns; all fields stored as JSON in `field_values`
- **Soft delete** — `retired=True` on EntityRecord, never hard-deleted
- **Schema-driven** — Entity types/fields defined in `CORE_ENTITIES`, seeded to DB on startup
- **Event log** — All mutations logged to `event_log_entries`
- **shotgun_api3 compatible** — SDK connects via `/api3/json` (method: `read`)

See [docs/development.md](docs/development.md) for architecture details.
