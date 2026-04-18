# API Coverage

What's implemented, what's not, and what's different from cloud ShotGrid.

## Implemented RPC Methods (13)

| RPC Method | SDK Method | Notes |
|---|---|---|
| `info` | `sg.info()` | Returns `{"version": [2024, 1, 0]}` |
| `read` | `sg.find()`, `sg.find_one()` | Full filter/sort/pagination support |
| `find` | (direct HTTP) | Alternative to `read` for non-SDK callers |
| `find_one` | (direct HTTP) | Convenience wrapper |
| `create` | `sg.create()` | Handles SDK `fields` list and `data` dict |
| `update` | `sg.update()` | Same format handling as create |
| `delete_one` | `sg.delete()` | Soft-delete via `retired` flag |
| `revive` | `sg.revive()` | Restores soft-deleted entities |
| `batch` | `sg.batch()` | Mixed create/update/delete operations |
| `schema_read` | `sg.schema_read()` | Full schema for all entity types |
| `schema_entity_read` | `sg.schema_entity_read()` | Entity type definitions |
| `schema_field_read` | `sg.schema_field_read()` | Per-entity field definitions |
| `entity_types` | (direct HTTP) | Returns list of 11 entity type names |

## Not Implemented

### File Operations (5)

No file storage layer exists. Would require local filesystem/object store and multipart upload handling.

| Operation | Description |
|---|---|
| `upload()` | Upload file to any field |
| `upload_thumbnail()` | Upload entity thumbnail |
| `upload_filmstrip_thumbnail()` | Version filmstrip |
| `share_thumbnail()` | Share thumbnail across entities |
| `download_attachment()` | Retrieve file content |

### Social / Activity (6)

| Operation | Description |
|---|---|
| `follow` / `unfollow` | Entity subscription |
| `followers` / `following` | List subscriptions |
| `activity_stream_read` | Entity activity stream |
| `note_thread_contents` | Note reply threads |

### Aggregation (1)

| Operation | Description |
|---|---|
| `summarize` | `record_count`, `sum`, `average`, `min`, `max` with grouping |

### Other (6)

| Operation | Description |
|---|---|
| `text_search` | Full-text search across entity names |
| `work_schedule_read` / `update` | Working/non-working days |
| `preferences_read` | User preferences |
| `get_session_token` | Session authentication |
| `schema_field_create` / `update` / `delete` | Schema modification |

## Filter Operators

### Implemented (10)

| Operator | Example | Notes |
|---|---|---|
| `is` | `["code", "is", "SEQ010"]` | JSON-encoded equality |
| `is_not` | `["code", "is_not", "SEQ010"]` | |
| `contains` | `["code", "contains", "SEQ"]` | `json_extract()` + LIKE |
| `not_contains` | `["code", "not_contains", "SEQ"]` | |
| `starts_with` | `["code", "starts_with", "SEQ"]` | `json_extract()` + LIKE |
| `ends_with` | `["code", "ends_with", "010"]` | `json_extract()` + LIKE |
| `in` | `["status", "in", ["ip", "fin"]]` | Per-element JSON encoding |
| `not_in` | `["status", "not_in", ["fin"]]` | |
| `is_null` | `["desc", "is_null", None]` | No FieldValue row exists |
| `not_null` | `["desc", "not_null", None]` | FieldValue row exists |

### Not Implemented (8)

| Operator | Notes |
|---|---|
| `greater_than` / `less_than` | Numeric comparison |
| `greater_than_or_equal` / `less_than_or_equal` | Numeric comparison |
| `between` | Range check |
| `in_last` / `not_in_last` | Date-relative range |
| `in_next` / `not_in_next` | Date-relative range |

## Entity Types — Local vs Cloud Differences

| Entity | Local Name | Cloud Name | Notes |
|---|---|---|---|
| PublishedFile | `PublishedFiles` | `PublishedFile` | Plural vs singular |
| HumanUser | ✅ Create allowed | ❌ Create restricted | Tests find existing on cloud |

### Field Differences

| Entity | Field | Local | Cloud |
|---|---|---|---|
| Most entities | `name` | ✅ Exists | ❌ Doesn't exist on Shot, Sequence, Episode, etc. |
| Project | `sg_status_list` | ✅ Used | Uses `sg_status` instead |
| Playlist | `sg_status_list` | ✅ Used | ❌ Doesn't exist |
| Version | `sg_status_list` | Any value | Only `na`, `rev`, `vwd`, `apr` |

## REST Endpoints

| Endpoint | Method | Status | Notes |
|---|---|---|---|
| `/api3/json` | POST | ✅ | All JSON-RPC methods above |
| `/schema/read` | GET | ✅ | Entity + field schema |
| `/info/api2` | GET | ✅ | Version info |
| `/info/api3` | GET | ✅ | Version info |
| `/` | GET | ✅ | Status page |
| `/health` | GET | ✅ | Health check |
| `/api/v1/entity/*` | * | ❌ | REST v1 CRUD not implemented |
| `/api/v1/schema/*` | * | ❌ | REST v1 schema not implemented |
| `/api/v2/*` | * | ❌ | REST v2 not implemented |

## Unsupported Query Features

- **Field hopping** — `project.Project.name` style dot-path references
- **Multi-entity ordering** — ordering by related entity fields
- **Grouping** — `summarize` with `grouping` parameter
- **Additional filter presets** — `additional_filter_presets` in `find()`
- **Archived projects** — `include_archived_projects` flag
- **Timezone-adjusted calendar filters** — date-relative operators
