# Testing Guide

## Test Suite Overview

**138 tests total** — all passing against both local LocalFPT and cloud ShotGrid.

| Suite | Tests | Purpose |
|---|---|---|
| `tests/test_parity.py` | 56 | SDK parity: same operation on local + cloud, assert results match |
| `tests/entities/` (10 files) | 62 | Per-entity CRUD, relationships, field-specific filters |
| `tests/test_rest_api.py` | 20 | REST endpoints: health, JSON-RPC, error handling, pagination |
| **Total** | **138** | |

## Running Tests

```bash
# Start the local server (required for all tests)
python -m local_fpt.app &

# Run all tests
pytest tests/ -v

# Run only per-entity tests
pytest tests/entities/ -v

# Run a single entity's tests
pytest tests/entities/test_shot.py -v

# Run only REST tests (no cloud needed)
pytest tests/test_rest_api.py -v
```

## Cloud Credentials

Parity tests (`test_parity.py` and `tests/entities/`) run every operation against both local and cloud ShotGrid. Cloud credentials go in `.env`:

```
SG_URL=https://your-site.shotgrid.autodesk.com
SCRIPT_NAME=your_script
API_KEY=your_key
```

If credentials are missing, all parity tests are **skipped automatically** (not failed).

## Test Data Lifecycle

```
┌─ Pre-session ──────────────────────────────────────────────┐
│  cleanup_stale_cloud_data (autouse fixture)                │
│  Scans cloud for any SG_TEST_* left from crashed runs      │
│  Deletes them in reverse dependency order                   │
└────────────────────────────────────────────────────────────┘
         │
┌─ Session start ────────────────────────────────────────────┐
│  test_dataset fixture creates ~17 entities on both:        │
│                                                            │
│  HumanUser (local create, cloud finds existing)            │
│    └→ Project                                              │
│         ├→ Sequence x2 (ip, fin)                           │
│         ├→ Episode x1                                      │
│         ├→ Shot x3 (linked to sequences)                   │
│         ├→ Asset x2 (Character, Environment)               │
│         ├→ Task x2 (→Shot, →Asset)                         │
│         ├→ Version x2 (→Shot, statuses: rev, na)           │
│         ├→ Playlist x1                                     │
│         └→ PublishedFile x1 (→Asset)                       │
│                                                            │
│  All prefixed: SG_TEST_{timestamp}_                        │
└────────────────────────────────────────────────────────────┘
         │
┌─ Each test ────────────────────────────────────────────────┐
│  Read-only tests: use test_dataset directly                │
│  Mutation tests: temp_tracker auto-deletes after each test │
│  PublishedFile tests: manual try/finally (type name diff)  │
└────────────────────────────────────────────────────────────┘
         │
┌─ Session end ──────────────────────────────────────────────┐
│  test_dataset teardown: reverse-order delete on both       │
└────────────────────────────────────────────────────────────┘
         │
┌─ Emergency cleanup ───────────────────────────────────────┐
│  python tests/cleanup_cloud.py           # dry-run         │
│  python tests/cleanup_cloud.py --delete  # actually purge  │
└────────────────────────────────────────────────────────────┘
```

### Session Prefix

Every test session generates `SG_TEST_{unix_timestamp}` as a prefix for all entity codes. This prevents collisions between concurrent or overlapping test runs.

### temp_tracker Fixture

Tests that create entities use `temp_tracker` for automatic cleanup:

```python
def test_something(self, local_sg, cloud_sg, test_dataset, temp_tracker):
    le = local_sg.create("Shot", {"code": "TEST_SHOT", ...})
    ce = cloud_sg.create("Shot", {"code": "TEST_SHOT", ...})
    temp_tracker("Shot", le["id"], ce["id"])   # auto-deleted after test
```

### Cloud Cleanup Script

If a test session crashes mid-run, orphaned `SG_TEST_*` entities may remain on cloud. Clean them up:

```bash
python tests/cleanup_cloud.py              # list orphaned entities (dry-run)
python tests/cleanup_cloud.py --delete     # delete them
```

This is also run automatically at the start of each test session.

## Per-Entity Test Files

Each entity type has its own test file covering that entity's specific fields and relationships:

| File | Entity | Tests | Covers |
|---|---|---|---|
| `test_project.py` | Project | 5 | code, name, starts_with, lifecycle, delete |
| `test_sequence.py` | Sequence | 5 | code, project ref, status, not_in, lifecycle |
| `test_episode.py` | Episode | 5 | code, project ref, status, lifecycle, revive |
| `test_shot.py` | Shot | 8 | code, sequence ref, project+status, order, create, update ref, revive |
| `test_asset.py` | Asset | 6 | code, sg_asset_type, project ref, in-filter, update type, revive |
| `test_task.py` | Task | 8 | content (not code), status, project, entity→Shot, entity→Asset, create on both |
| `test_version.py` | Version | 7 | code, project, entity→Shot, status, in-status, create, update |
| `test_playlist.py` | Playlist | 6 | code, project, contains, create+delete, update, revive |
| `test_humanuser.py` | HumanUser | 6 | id, active status, login, email, create+update, revive (local-only) |
| `test_publishedfile.py` | PublishedFile | 6 | code, project, entity→Asset, contains, create+delete, update |

## Cloud ShotGrid Compatibility Notes

Some field/status differences between local and cloud:

| Entity | Difference |
|---|---|
| All | Cloud doesn't have `name` field on most entities — only use `code` for cloud creates |
| Version | Cloud valid statuses: `na`, `rev`, `vwd`, `apr` (not `ip`, `fin`) |
| Playlist | Cloud doesn't have `sg_status_list` |
| HumanUser | Cloud restricts creation — tests find existing active user instead |
| PublishedFile | Local uses `PublishedFiles` (plural), cloud uses `PublishedFile` (singular) |
| Project | Cloud uses `sg_status` not `sg_status_list` |

## Debugging Tips

### JSON value matching

All `FieldValue.value` entries are JSON-encoded. The string `ip` is stored as `'"ip"'`. When debugging filter issues, check that comparisons use `json.dumps()`:

```python
# Wrong — will never match
FieldValue.value == "ip"

# Correct
FieldValue.value == json.dumps("ip")   # == '"ip"'
```

### EAV cross-join bug

If a multi-field filter returns unexpected results, check that `_build_field_condition` uses `.correlate(EntityRecord)` in the EXISTS subquery. Without it, SQLAlchemy adds `entity_records` to the subquery's FROM clause.

### SDK uses 'read' not 'find'

The shotgun_api3 SDK's `sg.find()` sends method `read` (not `find`). If ordering or filtering works in direct HTTP tests but not via the SDK, check the `read` handler in `api3.py`.

### Windows server process management

On Windows, Flask debug mode spawns a reloader subprocess. Use `taskkill /F /IM python.exe` to reliably kill all server processes. `pkill`/`kill` from Git Bash may not find them.
