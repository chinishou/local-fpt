"""HumanUser entity parity tests — no project ref, cloud restricts creation.
Cloud-side tests use existing active users; creation/login tests are local-only."""
import pytest


class TestHumanUser:

    def test_find_by_id(self, target):
        """Find user by ID from dataset."""
        uid = target.data["HumanUser"]["user1"]["id"]
        result = target.sg.find_one("HumanUser", [["id", "is", uid]], ["name"])
        assert result is not None
        assert result["type"] == "HumanUser"

    def test_find_active_users(self, target):
        """Find active users."""
        results = target.sg.find("HumanUser",
                                 [["sg_status_list", "is", "act"]],
                                 ["name", "sg_status_list"], limit=5)
        assert len(results) >= 1
        for u in results:
            assert u["sg_status_list"] == "act"

    def test_find_by_login(self, target):
        """Find user by login field (local only — cloud login values differ)."""
        if target.is_cloud:
            pytest.skip("Cloud login values differ from test data")
        login = f"{target.prefix}_testuser"
        result = target.sg.find_one("HumanUser", [["login", "is", login]],
                                    ["name", "login", "email"])
        assert result is not None
        assert result["login"] == login

    def test_find_by_email(self, target):
        """Find user by email field (local only)."""
        if target.is_cloud:
            pytest.skip("Cloud email values differ from test data")
        email = f"{target.prefix}_test@example.com"
        result = target.sg.find_one("HumanUser", [["email", "is", email]],
                                    ["name", "email"])
        assert result is not None
        assert result["email"] == email

    def test_create_and_update(self, target, target_tracker):
        """Create and update user (local only — cloud restricts HumanUser creation)."""
        if target.is_cloud:
            pytest.skip("Cloud restricts HumanUser creation")
        result = target.sg.create("HumanUser", {
            "name": f"{target.prefix}_NewUser",
            "login": f"{target.prefix}_newuser",
            "email": f"{target.prefix}_new@test.com",
            "sg_status_list": "act",
        })
        target_tracker("HumanUser", result["id"])

        updated = target.sg.update("HumanUser", result["id"],
                                   {"name": f"{target.prefix}_NewUser_v2"})
        assert updated["name"] == f"{target.prefix}_NewUser_v2"

        found = target.sg.find_one("HumanUser", [["id", "is", result["id"]]],
                                   ["name", "login", "email"])
        assert found["name"] == f"{target.prefix}_NewUser_v2"
        assert found["login"] == f"{target.prefix}_newuser"

    def test_delete_and_revive(self, target, target_tracker):
        """HumanUser delete → revive cycle (local only)."""
        if target.is_cloud:
            pytest.skip("Cloud restricts HumanUser creation/deletion")
        result = target.sg.create("HumanUser", {
            "name": f"{target.prefix}_DelRevUser",
            "login": f"{target.prefix}_delrevuser",
            "sg_status_list": "act",
        })
        target_tracker("HumanUser", result["id"])

        target.sg.delete("HumanUser", result["id"])
        assert target.sg.find_one("HumanUser", [["id", "is", result["id"]]]) is None

        target.sg.revive("HumanUser", result["id"])
        found = target.sg.find_one("HumanUser", [["id", "is", result["id"]]], ["name"])
        assert found is not None
        assert found["name"] == f"{target.prefix}_DelRevUser"
