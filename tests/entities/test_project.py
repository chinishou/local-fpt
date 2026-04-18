"""Project entity parity tests — CRUD, fields, filters."""
import pytest


class TestProject:

    def test_find_by_code(self, target):
        """Find project by exact code."""
        code = target.prefix + "_tp"
        result = target.sg.find_one("Project", [["code", "is", code]], ["code", "name"])
        assert result is not None
        assert result["type"] == "Project"
        assert result["code"] == code

    def test_find_by_name(self, target):
        """Find project by name field."""
        name = target.prefix + "_TestProject"
        result = target.sg.find_one("Project", [["name", "is", name]], ["name"])
        assert result is not None
        assert result["name"] == name

    def test_find_with_starts_with(self, target):
        """Find all projects whose code starts with the test prefix."""
        results = target.sg.find("Project", [["code", "starts_with", target.prefix]], ["code"])
        assert len(results) >= 1
        assert all(r["code"].startswith(target.prefix) for r in results)

    def test_create_update_delete(self, target, target_tracker):
        """Full lifecycle: create → update → read-back → delete."""
        code = f"{target.prefix}_PRJ_LIFECYCLE"
        result = target.sg.create("Project", {"name": code, "code": code})
        target_tracker("Project", result["id"])

        target.sg.update("Project", result["id"], {"name": f"{code}_v2"})

        found = target.sg.find_one("Project", [["id", "is", result["id"]]], ["name", "code"])
        assert found["code"] == code
        assert found["name"] == f"{code}_v2"

    def test_delete_and_unfindable(self, target):
        """Deleted project is no longer findable."""
        code = f"{target.prefix}_PRJ_DEL"
        result = target.sg.create("Project", {"name": code, "code": code})

        target.sg.delete("Project", result["id"])
        assert target.sg.find_one("Project", [["id", "is", result["id"]]]) is None
