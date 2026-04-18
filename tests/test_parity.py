"""
SDK parity tests — every test runs against both local LocalFPT and cloud ShotGrid
via the parametrized `target` fixture. Each test is written once and pytest runs it
twice: once as [local] and once as [cloud].

Requires:
  - Local server running on http://127.0.0.1:8000
  - Cloud credentials in .env (optional — cloud tests auto-skip if absent)
  - ``test_dataset`` fixture (see conftest.py) for pre-seeded data
"""
import pytest


# =========================================================================
# A. Connection & Info
# =========================================================================
class TestInfo:
    """sg.info() — returns server metadata."""

    def test_info_returns_dict(self, target):
        """info() returns a dict."""
        result = target.sg.info()
        assert isinstance(result, dict)

    def test_info_has_version(self, target):
        """info() result contains 'version' key with a list value."""
        result = target.sg.info()
        assert "version" in result
        assert isinstance(result["version"], list)


# =========================================================================
# B. Schema Methods
# =========================================================================
class TestSchema:
    """Schema read methods — compare structure, not exact content."""

    def test_schema_entity_read(self, target):
        """schema_entity_read() returns a dict keyed by entity type names."""
        result = target.sg.schema_entity_read()
        assert isinstance(result, dict)
        for etype in ["Project", "Shot", "Asset", "Sequence", "Task", "Version"]:
            assert etype in result, f"{etype} missing from schema"

    def test_schema_field_read_shot(self, target):
        """schema_field_read('Shot') returns field definitions for Shot."""
        result = target.sg.schema_field_read("Shot")
        assert isinstance(result, dict)
        assert "code" in result, "code missing from Shot fields"

    def test_schema_field_read_single_field(self, target):
        """schema_field_read('Shot', field_name='code') returns only that field."""
        result = target.sg.schema_field_read("Shot", field_name="code")
        assert isinstance(result, dict)
        assert "code" in result

    def test_schema_read(self, target):
        """schema_read() returns nested dict with entity types and fields."""
        result = target.sg.schema_read()
        assert isinstance(result, dict)
        assert "Shot" in result


# =========================================================================
# C. find_one — basic queries
# =========================================================================
class TestFindOne:
    """sg.find_one(entity_type, filters, fields) — single entity retrieval."""

    def test_find_one_project(self, target):
        """find_one('Project', filter_by_code) returns the test project."""
        code = target.prefix + "_tp"
        result = target.sg.find_one("Project", [["code", "is", code]], ["code", "name"])
        assert result is not None, "find_one returned None"
        assert result["type"] == "Project"
        assert result["code"] == code

    def test_find_one_nonexistent(self, target):
        """find_one with impossible filter returns None."""
        result = target.sg.find_one("Project", [["id", "is", 999999999]])
        assert result is None

    def test_find_one_with_fields(self, target):
        """find_one with explicit fields returns only those fields + type + id."""
        code = target.prefix + "_tp"
        result = target.sg.find_one("Project", [["code", "is", code]], ["code"])
        assert result is not None
        assert "code" in result
        assert result["code"] == code

    def test_find_one_empty_filters(self, target):
        """find_one with empty filter list returns a project (or None)."""
        result = target.sg.find_one("Project", [])
        if result is not None:
            assert result["type"] == "Project"


# =========================================================================
# D. find — list queries, pagination, ordering
# =========================================================================
class TestFind:
    """sg.find(entity_type, filters, fields, order, limit, page) — multi-entity."""

    def test_find_shots_in_project(self, target):
        """find('Shot', project_filter) returns all 3 test shots."""
        proj_ref = target.ref("Project", "main")
        results = target.sg.find("Shot",
                                 [["project", "is", proj_ref]],
                                 ["code", "sg_status_list"])
        test_results = [s for s in results if s["code"].startswith(target.prefix)]
        assert len(test_results) == 3, f"Expected 3 shots, got {len(test_results)}"
        assert all(r["type"] == "Shot" for r in test_results)

    def test_find_with_limit(self, target):
        """find with limit=1 returns exactly 1 result."""
        results = target.sg.find("Shot",
                                 [["code", "starts_with", target.prefix]],
                                 ["code"], limit=1)
        assert len(results) == 1

    def test_find_with_limit_and_page(self, target):
        """find with limit=2, page=1 returns first page; page=2 returns remainder."""
        results_p1 = target.sg.find("Shot",
                                    [["code", "starts_with", target.prefix]],
                                    ["code"], limit=2, page=1)
        assert len(results_p1) == 2

        results_p2 = target.sg.find("Shot",
                                    [["code", "starts_with", target.prefix]],
                                    ["code"], limit=2, page=2)
        assert len(results_p2) == 1

    def test_find_with_order_asc(self, target):
        """find with order asc returns sorted results."""
        results = target.sg.find("Shot",
                                 [["code", "starts_with", target.prefix]],
                                 ["code"],
                                 order=[{"field_name": "code", "direction": "asc"}])
        codes = [s["code"] for s in results]
        assert codes == sorted(codes)

    def test_find_with_order_desc(self, target):
        """find with order desc returns reverse-sorted results."""
        results = target.sg.find("Shot",
                                 [["code", "starts_with", target.prefix]],
                                 ["code"],
                                 order=[{"field_name": "code", "direction": "desc"}])
        codes = [s["code"] for s in results]
        assert codes == sorted(codes, reverse=True)

    def test_find_returns_type_and_id(self, target):
        """find always includes 'type' and 'id' in each result."""
        results = target.sg.find("Shot",
                                 [["code", "starts_with", target.prefix]],
                                 ["code"])
        for e in results:
            assert "type" in e, f"Missing 'type' in {e}"
            assert "id" in e, f"Missing 'id' in {e}"


# =========================================================================
# E. ID Filter Operators
# =========================================================================
class TestIdFilters:
    """Filter operators on the 'id' field: is, is_not, in, not_in."""

    def test_id_is(self, target):
        """[['id', 'is', X]] returns the exact entity."""
        eid = target.data["Shot"]["shot1"]["id"]
        result = target.sg.find_one("Shot", [["id", "is", eid]], ["code"])
        assert result is not None
        assert result["id"] == eid
        assert result["code"] == target.data["Shot"]["shot1"]["code"]

    def test_id_is_not(self, target):
        """[['id', 'is_not', X]] excludes that entity."""
        eid = target.data["Shot"]["shot1"]["id"]
        results = target.sg.find("Shot",
                                 [["id", "is_not", eid],
                                  ["code", "starts_with", target.prefix]],
                                 ["code"])
        ids = {s["id"] for s in results}
        assert eid not in ids
        assert len(results) == 2

    def test_id_in(self, target):
        """[['id', 'in', [X, Y]]] returns those specific entities."""
        eids = [target.data["Shot"][n]["id"] for n in ("shot1", "shot2")]
        results = target.sg.find("Shot", [["id", "in", eids]], ["code"])
        assert len(results) == 2
        assert {r["id"] for r in results} == set(eids)

    def test_id_not_in(self, target):
        """[['id', 'not_in', [X]]] excludes that entity."""
        eid = target.data["Shot"]["shot1"]["id"]
        results = target.sg.find("Shot",
                                 [["id", "not_in", [eid]],
                                  ["code", "starts_with", target.prefix]],
                                 ["code"])
        assert len(results) == 2
        assert eid not in {r["id"] for r in results}


# =========================================================================
# F. Text Filter Operators
# =========================================================================
class TestTextFilters:
    """Filter operators on text fields."""

    def test_is(self, target):
        """[['code', 'is', exact_value]] returns exact match."""
        code = target.prefix + "_SEQ010_0010"
        result = target.sg.find_one("Shot", [["code", "is", code]], ["code"])
        assert result is not None
        assert result["code"] == code

    def test_is_not(self, target):
        """[['code', 'is_not', X]] excludes that value."""
        code = target.prefix + "_SEQ010_0010"
        results = target.sg.find("Shot",
                                 [["code", "is_not", code],
                                  ["code", "starts_with", target.prefix]],
                                 ["code"])
        assert len(results) == 2
        assert all(r["code"] != code for r in results)

    def test_contains(self, target):
        """[['code', 'contains', substring]] matches substring."""
        results = target.sg.find("Shot",
                                 [["code", "contains", target.prefix + "_SEQ010"]],
                                 ["code"])
        assert len(results) == 2
        assert all("SEQ010" in r["code"] for r in results)

    def test_not_contains(self, target):
        """[['code', 'not_contains', substring]] excludes matching entries."""
        results = target.sg.find("Shot",
                                 [["code", "not_contains", "SEQ010"],
                                  ["code", "starts_with", target.prefix]],
                                 ["code"])
        assert len(results) == 1
        assert "SEQ010" not in results[0]["code"]

    def test_starts_with(self, target):
        """[['code', 'starts_with', prefix]] matches prefix."""
        results = target.sg.find("Shot",
                                 [["code", "starts_with", target.prefix]],
                                 ["code"])
        assert len(results) == 3

    def test_ends_with(self, target):
        """[['code', 'ends_with', suffix]] matches suffix."""
        results = target.sg.find("Shot", [["code", "ends_with", "_0010"]], ["code"])
        assert len(results) >= 2


# =========================================================================
# G. List/Set Filter Operators
# =========================================================================
class TestListFilters:
    """in/not_in on non-id fields."""

    def test_in_status_list(self, target):
        """[['sg_status_list', 'in', ['ip', 'fin']]] matches multiple values."""
        results = target.sg.find("Shot",
                                 [["sg_status_list", "in", ["ip", "fin"]],
                                  ["code", "starts_with", target.prefix]],
                                 ["code", "sg_status_list"])
        assert len(results) == 3

    def test_not_in_status_list(self, target):
        """[['sg_status_list', 'not_in', ['fin']]] excludes those values."""
        results = target.sg.find("Shot",
                                 [["sg_status_list", "not_in", ["fin"]],
                                  ["code", "starts_with", target.prefix]],
                                 ["code", "sg_status_list"])
        assert len(results) == 2
        assert all(e["sg_status_list"] != "fin" for e in results)


# =========================================================================
# H. Entity Reference Filters
# =========================================================================
class TestEntityRefFilters:
    """Filtering by entity reference fields (project, sg_sequence, etc.)."""

    def test_project_is(self, target):
        """[['project', 'is', {type, id}]] filters by project reference."""
        proj_ref = target.ref("Project", "main")
        results = target.sg.find("Sequence",
                                 [["project", "is", proj_ref]],
                                 ["code"])
        test_results = [s for s in results if s["code"].startswith(target.prefix)]
        assert len(test_results) == 2

    def test_sequence_is(self, target):
        """Filter shots by sg_sequence reference."""
        seq_ref = target.ref("Sequence", "seq1")
        results = target.sg.find("Shot",
                                 [["sg_sequence", "is", seq_ref]],
                                 ["code"])
        test_results = [s for s in results if s["code"].startswith(target.prefix)]
        assert len(test_results) == 2
        assert all(r["type"] == "Shot" for r in test_results)


# =========================================================================
# I. Logical Filter Combinations (AND / OR via filter_operator)
# =========================================================================
class TestLogicalFilters:

    def test_filter_operator_all_and(self, target):
        """filter_operator='all' (AND) — both conditions must match."""
        results = target.sg.find("Shot",
                                 [["code", "starts_with", target.prefix],
                                  ["sg_status_list", "is", "ip"]],
                                 ["code", "sg_status_list"],
                                 filter_operator="all")
        assert len(results) == 2
        assert all(e["sg_status_list"] == "ip" for e in results)

    def test_filter_operator_any_or(self, target):
        """filter_operator='any' (OR) — either condition suffices."""
        results = target.sg.find("Shot",
                                 [["code", "is", target.prefix + "_SEQ010_0010"],
                                  ["code", "is", target.prefix + "_SEQ020_0010"]],
                                 ["code"],
                                 filter_operator="any")
        assert len(results) == 2


# =========================================================================
# J. create Method
# =========================================================================
class TestCreate:
    """sg.create(entity_type, data, return_fields) — entity creation."""

    def test_create_basic(self, target, target_tracker):
        """create('Shot', data) returns entity with matching field values."""
        code = f"{target.prefix}_CREATE_TEST"
        data = target.create_data("Shot", {
            "code": code, "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Shot", data)
        target_tracker("Shot", result["id"])
        assert result["type"] == "Shot"
        assert result["id"] is not None
        assert result["code"] == code
        assert result["sg_status_list"] == "ip"

    def test_create_with_return_fields(self, target, target_tracker):
        """create with return_fields limits which fields come back."""
        code = f"{target.prefix}_CREATE_RF"
        data = target.create_data("Shot", {
            "code": code, "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Shot", data, return_fields=["code"])
        target_tracker("Shot", result["id"])
        assert "code" in result
        assert result["code"] == code

    def test_create_minimal(self, target, target_tracker):
        """create with minimal data — only required fields."""
        code = f"{target.prefix}_MINIMAL_PL"
        data = target.create_data("Playlist", {
            "code": code,
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Playlist", data)
        target_tracker("Playlist", result["id"])
        assert result["type"] == "Playlist"


# =========================================================================
# K. update Method
# =========================================================================
class TestUpdate:
    """sg.update(entity_type, entity_id, data) — entity modification."""

    def test_update_single_field(self, target, target_tracker):
        """update changes one field and returns the updated entity."""
        data = target.create_data("Shot", {
            "code": f"{target.prefix}_UPD1", "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Shot", data)
        target_tracker("Shot", result["id"])

        updated = target.sg.update("Shot", result["id"], {"sg_status_list": "fin"})
        assert updated["sg_status_list"] == "fin"

    def test_update_multiple_fields(self, target, target_tracker):
        """update changes multiple fields at once."""
        data = target.create_data("Asset", {
            "code": f"{target.prefix}_UPD_MULTI", "sg_status_list": "ip",
            "sg_asset_type": "Character",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Asset", data)
        target_tracker("Asset", result["id"])

        updated = target.sg.update("Asset", result["id"],
                                   {"sg_status_list": "fin", "sg_asset_type": "Prop"})
        assert updated["sg_status_list"] == "fin"
        assert updated["sg_asset_type"] == "Prop"

    def test_update_entity_reference(self, target, target_tracker):
        """update can change an entity reference field (sg_sequence)."""
        data = target.create_data("Shot", {
            "code": f"{target.prefix}_UPD_REF", "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
            "sg_sequence": target.ref("Sequence", "seq1"),
        })
        result = target.sg.create("Shot", data)
        target_tracker("Shot", result["id"])

        seq2_ref = target.ref("Sequence", "seq2")
        updated = target.sg.update("Shot", result["id"], {"sg_sequence": seq2_ref})
        assert updated["sg_sequence"]["type"] == "Sequence"
        assert updated["sg_sequence"]["id"] == seq2_ref["id"]


# =========================================================================
# L. delete Method
# =========================================================================
class TestDelete:
    """sg.delete(entity_type, entity_id) — soft-delete (retire)."""

    def test_delete_returns_true(self, target):
        """delete() returns True on success."""
        data = target.create_data("Shot", {
            "code": f"{target.prefix}_DEL1",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Shot", data)
        deleted = target.sg.delete("Shot", result["id"])
        assert deleted is True

    def test_delete_makes_entity_unfindable(self, target):
        """After delete, find_one returns None for that entity."""
        data = target.create_data("Shot", {
            "code": f"{target.prefix}_DEL2",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Shot", data)
        target.sg.delete("Shot", result["id"])
        assert target.sg.find_one("Shot", [["id", "is", result["id"]]]) is None

    def test_delete_nonexistent_returns_false(self, target):
        """delete() for a nonexistent ID raises an exception."""
        raised = False
        try:
            target.sg.delete("Shot", 999999999)
        except Exception:
            raised = True
        assert raised, "Expected exception for nonexistent entity"


# =========================================================================
# M. revive Method
# =========================================================================
class TestRevive:
    """sg.revive(entity_type, entity_id) — un-retire a deleted entity."""

    def test_revive_restores_entity(self, target, target_tracker):
        """After revive, find_one finds the entity again."""
        code = f"{target.prefix}_REVIVE"
        data = target.create_data("Shot", {
            "code": code,
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Shot", data)
        target_tracker("Shot", result["id"])

        target.sg.delete("Shot", result["id"])
        revived = target.sg.revive("Shot", result["id"])
        assert revived is True

        found = target.sg.find_one("Shot", [["id", "is", result["id"]]], ["code"])
        assert found is not None, "revive failed — entity still retired"
        assert found["code"] == code


# =========================================================================
# N. batch Method
# =========================================================================
class TestBatch:
    """sg.batch(requests) — execute multiple operations in one call."""

    def test_batch_create_multiple(self, target, target_tracker):
        """batch with multiple create requests returns a list of created entities."""
        proj_ref = target.ref("Project", "main")
        batch = [
            {"request_type": "create", "entity_type": "Shot",
             "data": {"code": f"{target.prefix}_BATCH_A", "project": proj_ref}},
            {"request_type": "create", "entity_type": "Shot",
             "data": {"code": f"{target.prefix}_BATCH_B", "project": proj_ref}},
        ]
        results = target.sg.batch(batch)
        assert len(results) == 2
        for r in results:
            target_tracker("Shot", r["id"])
        assert results[0]["code"] == f"{target.prefix}_BATCH_A"
        assert results[1]["code"] == f"{target.prefix}_BATCH_B"

    def test_batch_mixed_operations(self, target, target_tracker):
        """batch with create + update returns results for each operation."""
        proj_ref = target.ref("Project", "main")
        existing = target.sg.create("Shot", {
            "code": f"{target.prefix}_BATCH_MIX",
            "project": proj_ref,
        })
        target_tracker("Shot", existing["id"])

        batch = [
            {"request_type": "create", "entity_type": "Shot",
             "data": {"code": f"{target.prefix}_BATCH_MIX2", "project": proj_ref}},
            {"request_type": "update", "entity_type": "Shot",
             "entity_id": existing["id"],
             "data": {"sg_status_list": "fin"}},
        ]
        results = target.sg.batch(batch)
        assert len(results) == 2
        target_tracker("Shot", results[0]["id"])

    def test_batch_with_delete(self, target):
        """batch with delete operation returns True for the delete."""
        proj_ref = target.ref("Project", "main")
        existing = target.sg.create("Shot", {
            "code": f"{target.prefix}_BATCH_DEL",
            "project": proj_ref,
        })
        results = target.sg.batch([{
            "request_type": "delete",
            "entity_type": "Shot",
            "entity_id": existing["id"],
        }])
        assert len(results) == 1


# =========================================================================
# O. All Entity Types — verify dataset covers every type
# =========================================================================
class TestAllEntityTypes:
    """Verify every supported entity type can be queried."""

    @pytest.mark.parametrize("entity_type,nickname", [
        ("Project", "main"),
        ("Sequence", "seq1"),
        ("Episode", "ep1"),
        ("Shot", "shot1"),
        ("Asset", "asset1"),
        ("Task", "task1"),
        ("Version", "ver1"),
        ("Playlist", "pl1"),
        ("HumanUser", "user1"),
        ("PublishedFile", "pf1"),
        ("Ticket", "ticket1"),
    ])
    def test_entity_findable(self, target, entity_type, nickname):
        """Each entity type in the dataset is findable by ID."""
        etype = target.entity_type(entity_type)
        eid = target.data[etype][nickname]["id"]
        result = target.sg.find_one(etype, [["id", "is", eid]])
        assert result is not None, f"{etype}:{nickname} not found"
        assert result["type"] == etype


# =========================================================================
# P. Edge Cases
# =========================================================================
class TestEdgeCases:

    def test_find_empty_result(self, target):
        """find with impossible filter returns empty list."""
        results = target.sg.find("Shot", [["code", "is", "NONEXISTENT_CODE_XYZ_999"]])
        assert results == []

    def test_find_one_always_returns_type_id(self, target):
        """find_one result always has 'type' and 'id' even with minimal fields."""
        result = target.sg.find_one("Shot",
                                    [["code", "starts_with", target.prefix]],
                                    [])
        assert result is not None
        assert "type" in result
        assert "id" in result

    def test_create_then_find_roundtrip(self, target, target_tracker):
        """Created entity is immediately findable."""
        code = f"{target.prefix}_ROUNDTRIP"
        data = target.create_data("Sequence", {
            "code": code,
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Sequence", data)
        target_tracker("Sequence", result["id"])

        found = target.sg.find_one("Sequence", [["code", "is", code]], ["code"])
        assert found is not None
        assert found["code"] == code
