"""
REST API endpoint tests — direct HTTP calls to the local LocalFPT server.

These tests verify the raw HTTP interface (JSON-RPC protocol, REST endpoints,
error handling) independently of the shotgun_api3 SDK.  ShotGrid API parity
(functional CRUD operations on all entity types) is covered by test_parity.py
and tests/entities/, which run against both local and cloud targets.
"""
import pytest


def rpc(local_http, method_name, params):
    r = local_http.post("/api3/json", json={"method_name": method_name, "params": params})
    return r


class TestHealthAndInfo:
    def test_root_status(self, local_http):
        r = local_http.get("/")
        assert r.status_code == 200
        data = r.json()
        assert data["status"] == "ok"
        assert "db" in data

    def test_health(self, local_http):
        r = local_http.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "healthy"

    def test_info_api2(self, local_http):
        r = local_http.get("/api2")
        assert r.status_code == 200
        data = r.json()
        assert "version" in data

    def test_info_api3(self, local_http):
        r = local_http.get("/api3")
        assert r.status_code == 200
        data = r.json()
        assert "version" in data


class TestSchemaEndpoint:
    def test_schema_read_returns_entities(self, local_http):
        r = local_http.get("/schema/read")
        assert r.status_code == 200
        data = r.json()
        for etype in ["Project", "Shot", "Asset", "Sequence", "Episode",
                      "Task", "Version", "Playlist", "HumanUser", "PublishedFiles",
                      "Ticket"]:
            assert etype in data, f"{etype} missing from schema"

    def test_schema_has_field_definitions(self, local_http):
        r = local_http.get("/schema/read")
        data = r.json()
        shot = data["Shot"]
        assert "fields" in shot
        assert "code" in shot["fields"]
        assert "type" in shot["fields"]["code"]

    def test_schema_shot_has_project_field(self, local_http):
        r = local_http.get("/schema/read")
        data = r.json()
        assert "project" in data["Shot"]["fields"]

    def test_schema_ticket_fields(self, local_http):
        r = local_http.get("/schema/read")
        data = r.json()
        ticket = data["Ticket"]
        assert "fields" in ticket
        assert "title" in ticket["fields"]
        assert "sg_status_list" in ticket["fields"]
        assert "sg_priority" in ticket["fields"]


class TestJsonRpcInfo:
    def test_rpc_info(self, local_http):
        r = rpc(local_http, "info", {})
        assert r.status_code == 200
        data = r.json()
        assert "version" in data
        assert data["version"] == [2024, 1, 0]


class TestJsonRpcEntityTypes:
    def test_rpc_entity_types_returns_list(self, local_http):
        r = rpc(local_http, "entity_types", {})
        assert r.status_code == 200
        data = r.json()
        types = data["results"]
        assert isinstance(types, list)
        assert "Project" in types
        assert "Shot" in types

    def test_rpc_entity_types_includes_ticket(self, local_http):
        r = rpc(local_http, "entity_types", {})
        data = r.json()
        types = data["results"]
        assert "Ticket" in types
        assert len(types) == 11


class TestJsonRpcSchemaMethods:
    def test_rpc_schema_entity_read(self, local_http):
        r = rpc(local_http, "schema_entity_read", {})
        assert r.status_code == 200
        data = r.json()
        result = data["results"]
        assert isinstance(result, dict)
        assert "Project" in result
        assert "Shot" in result
        assert result["Project"]["name"]["value"] == "Project"

    def test_rpc_schema_field_read_shot(self, local_http):
        r = rpc(local_http, "schema_field_read", {"type": "Shot"})
        assert r.status_code == 200
        data = r.json()
        result = data["results"]
        assert "code" in result
        assert result["code"]["name"]["value"] == "code"

    def test_rpc_schema_field_read_single_field(self, local_http):
        r = rpc(local_http, "schema_field_read", {"type": "Shot", "field_name": "code"})
        assert r.status_code == 200
        data = r.json()
        result = data["results"]
        assert "code" in result

    def test_rpc_schema_read(self, local_http):
        r = rpc(local_http, "schema_read", {})
        assert r.status_code == 200
        data = r.json()
        result = data["results"]
        assert isinstance(result, dict)
        assert "Shot" in result
        assert "code" in result["Shot"]
        assert result["Shot"]["code"]["data_type"]["value"] == "text"


class TestJsonRpcReadPagination:
    def test_rpc_read_with_paging(self, local_http, test_dataset):
        pfx = test_dataset["prefix"]
        r = rpc(local_http, "read", {
            "type": "Shot",
            "filters": [["code", "starts_with", pfx]],
            "fields": ["code"],
            "paging": {"entities_per_page": 2, "current_page": 1},
        })
        assert r.status_code == 200
        data = r.json()
        assert "entities" in data
        assert "paging_info" in data
        assert len(data["entities"]) == 2
        assert data["paging_info"]["current_page"] == 1
        assert data["paging_info"]["has_next_page"] is True

    def test_rpc_read_page_2(self, local_http, test_dataset):
        pfx = test_dataset["prefix"]
        r = rpc(local_http, "read", {
            "type": "Shot",
            "filters": [["code", "starts_with", pfx]],
            "fields": ["code"],
            "paging": {"entities_per_page": 2, "current_page": 2},
        })
        assert r.status_code == 200
        data = r.json()
        assert len(data["entities"]) == 1
        assert data["paging_info"]["has_next_page"] is False

    def test_rpc_read_default_paging(self, local_http, test_dataset):
        pfx = test_dataset["prefix"]
        r = rpc(local_http, "read", {
            "type": "Shot",
            "filters": [["code", "starts_with", pfx]],
            "fields": ["code"],
        })
        assert r.status_code == 200
        data = r.json()
        assert "entities" in data
        assert data["paging_info"]["current_page"] == 1


class TestErrorHandling:
    def test_unknown_method(self, local_http):
        r = local_http.post("/api3/json", json={
            "method_name": "nonexistent_method",
            "params": {}
        })
        assert r.status_code == 400
        assert "error" in r.json()

    def test_missing_method_name(self, local_http):
        r = local_http.post("/api3/json", json={"params": {}})
        assert r.status_code == 400 or "error" in r.json()

    def test_find_missing_type(self, local_http):
        r = local_http.post("/api3/json", json={
            "method_name": "find",
            "params": {"filters": []}
        })
        assert r.status_code in (400, 500)

    def test_delete_nonexistent(self, local_http):
        r = rpc(local_http, "delete", {"type": "Shot", "id": 999999999})
        assert r.status_code == 500
        assert "error" in r.json()
