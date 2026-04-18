# Compatibility Matrix

Current implementation status of ShotGrid API features in LocalFPT.

## SDK Methods (`shotgun_api3` → `/api3/json`)

| SDK Method | RPC Method | Status | Notes |
|---|---|---|---|
| `sg.info()` | `info` | ✅ | Returns version `[2024, 1, 0]` |
| `sg.find()` | `read` | ✅ | Filters, pagination, field selection, sorting |
| `sg.find_one()` | `read` | ✅ | Single-record fetch (limit=1) |
| `sg.create()` | `create` | ✅ | Supports SDK `fields` list and simple `data` dict |
| `sg.update()` | `update` | ✅ | Full field updates |
| `sg.delete()` | `delete_one` | ✅ | Soft-delete (retired flag) |
| `sg.revive()` | `revive` | ✅ | Restore soft-deleted entity |
| `sg.batch()` | `batch` | ✅ | Mixed create/update/delete |
| `sg.schema_read()` | `schema_read` | ✅ | All entity + field schemas |
| `sg.schema_entity_read()` | `schema_entity_read` | ✅ | Entity type definitions |
| `sg.schema_field_read()` | `schema_field_read` | ✅ | Per-entity field definitions |
| `sg.upload()` | — | ❌ | No file storage layer |
| `sg.upload_thumbnail()` | — | ❌ | No file storage layer |
| `sg.download_attachment()` | — | ❌ | No file storage layer |
| `sg.share_thumbnail()` | — | ❌ | Not implemented |
| `sg.follow()` / `sg.unfollow()` | — | ❌ | Social features not implemented |
| `sg.followers()` / `sg.following()` | — | ❌ | Social features not implemented |
| `sg.activity_stream_read()` | — | ❌ | Not implemented |
| `sg.note_thread_read()` | — | ❌ | Note entity not supported |
| `sg.summarize()` | — | ❌ | Aggregation not implemented |
| `sg.text_search()` | — | ❌ | Full-text search not implemented |
| `sg.preferences_read()` | — | ❌ | Not implemented |
| `sg.work_schedule_read()` | — | ❌ | Not implemented |

## Entity Types

| Entity | Status | Key Fields |
|---|---|---|
| Project | ✅ | `name`, `code`, `description`, `sg_status_list` |
| Sequence | ✅ | `code`, `sg_status_list`, `project` |
| Episode | ✅ | `code`, `sg_status_list`, `project` |
| Shot | ✅ | `code`, `sg_status_list`, `project`, `sg_sequence`, `sg_episode` |
| Asset | ✅ | `code`, `sg_asset_type`, `sg_status_list`, `project` |
| Task | ✅ | `content`, `sg_status_list`, `project`, `entity` |
| Version | ✅ | `code`, `sg_status_list`, `project`, `entity` |
| Playlist | ✅ | `code`, `sg_status_list`, `project` |
| HumanUser | ✅ | `name`, `login`, `email`, `sg_status_list` |
| PublishedFiles | ✅ | `code`, `sg_status_list`, `project`, `entity` |
| Ticket | ✅ | `code`, `name`, `sg_priority`, `sg_status_list`, `project`, `entity` |
| Step | ❌ | Pipeline steps not implemented |
| Note | ❌ | Notes not implemented |
| Attachment | ❌ | File attachments not implemented |
| Group | ❌ | Permission groups not implemented |
| CustomEntity* | ❌ | Custom entities not implemented |

## Filter Operators

| Operator | Status | Notes |
|---|---|---|
| `is` | ✅ | Text, entity ref, JSON-encoded comparison |
| `is_not` | ✅ | |
| `contains` | ✅ | Uses `json_extract()` for LIKE |
| `not_contains` | ✅ | |
| `starts_with` | ✅ | Uses `json_extract()` for LIKE |
| `ends_with` | ✅ | Uses `json_extract()` for LIKE |
| `in` | ✅ | List of JSON-encoded values |
| `not_in` | ✅ | |
| `is_null` | ✅ | Checks for absence of FieldValue row |
| `not_null` | ✅ | Checks for presence of FieldValue row |
| `greater_than` | ❌ | Not implemented |
| `less_than` | ❌ | Not implemented |
| `between` | ❌ | Not implemented |
| `in_last` / `in_next` | ❌ | Date-relative operators not implemented |

## Query Features

| Feature | Status | Notes |
|---|---|---|
| Single-field filter | ✅ | EXISTS subquery per field |
| Multi-field AND | ✅ | Multiple EXISTS subqueries |
| `filter_operator="any"` (OR) | ✅ | OR across conditions |
| `filter_operator="all"` (AND) | ✅ | AND across conditions (default) |
| Entity reference filter | ✅ | `["project", "is", {"type":"Project","id":1}]` |
| ID filter operators | ✅ | `is`, `is_not`, `in`, `not_in` on `id` field |
| Ordering (ASC/DESC) | ✅ | Via aliased FieldValue outerjoin |
| Pagination (limit + page) | ✅ | Via `limit`/`page` or `paging` dict |
| Return field selection | ✅ | Only requested fields returned |
| Field hopping (`project.Project.name`) | ❌ | Not implemented |
| Additional filter presets | ❌ | Not implemented |
| Include archived projects | ❌ | Not tracked |

## Authentication

| Feature | Status | Notes |
|---|---|---|
| Script-key auth | ✅ | Stub — always accepts any key |
| Session-based auth | ❌ | Not implemented |
| OAuth / SSO | ❌ | Not implemented |
| Permission groups | ❌ | Dev mode: all access |

## Parity Test Coverage

284 tests verify local-vs-cloud behavior parity:

| Category | Tests | Verified Operations |
|---|---|---|
| Info / Schema | 5 | `info()`, `schema_read()`, `schema_entity_read()`, `schema_field_read()` |
| Find / FindOne | 8 | Project filter, nonexistent, fields, empty filter, limit, page, order |
| ID Filters | 4 | `is`, `is_not`, `in`, `not_in` on ID |
| Text Filters | 6 | `is`, `is_not`, `contains`, `not_contains`, `starts_with`, `ends_with` |
| List Filters | 2 | `in`, `not_in` on status field |
| Entity Ref Filters | 2 | Project ref, Sequence ref |
| Logical Filters | 2 | `filter_operator="all"`, `filter_operator="any"` |
| Create | 3 | Basic, with return_fields, minimal |
| Update | 3 | Single field, multiple fields, entity reference |
| Delete | 3 | Returns true, unfindable, nonexistent |
| Revive | 1 | Delete → revive → findable |
| Batch | 3 | Create multiple, mixed ops, delete |
| All Entity Types | 11 | Each of 11 types findable by ID |
| Edge Cases | 3 | Empty result, type+id always present, create roundtrip |
| Per-Entity CRUD | 70+ | Entity-specific fields, relationships, lifecycle |
| REST Endpoints | 20 | Health, JSON-RPC, errors, pagination |
