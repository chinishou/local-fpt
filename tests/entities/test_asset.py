"""Asset entity parity tests — CRUD, sg_asset_type field, project link."""


class TestAsset:

    def test_find_by_code(self, target):
        """Find asset by exact code."""
        code = target.prefix + "_Hero"
        result = target.sg.find_one("Asset", [["code", "is", code]],
                                    ["code", "sg_asset_type", "sg_status_list"])
        assert result is not None
        assert result["type"] == "Asset"
        assert result["code"] == code
        assert result["sg_asset_type"] == "Character"

    def test_find_by_asset_type(self, target):
        """Filter assets by sg_asset_type field."""
        results = target.sg.find("Asset",
                                 [["sg_asset_type", "is", "Character"],
                                  ["code", "starts_with", target.prefix]],
                                 ["code", "sg_asset_type"])
        assert len(results) == 1
        assert results[0]["sg_asset_type"] == "Character"

    def test_find_by_project(self, target):
        """Filter assets by project."""
        proj_ref = target.ref("Project", "main")
        results = target.sg.find("Asset",
                                 [["project", "is", proj_ref]],
                                 ["code", "sg_asset_type"])
        test_results = [a for a in results if a["code"].startswith(target.prefix)]
        assert len(test_results) == 2
        assert all(r["type"] == "Asset" for r in test_results)

    def test_find_multiple_asset_types(self, target):
        """in-filter on sg_asset_type returns assets of both types."""
        results = target.sg.find("Asset",
                                 [["sg_asset_type", "in", ["Character", "Environment"]],
                                  ["code", "starts_with", target.prefix]],
                                 ["code", "sg_asset_type"])
        assert len(results) == 2

    def test_create_update_asset_type(self, target, target_tracker):
        """Create asset then change sg_asset_type."""
        code = f"{target.prefix}_ASSET_LIFE"
        data = target.create_data("Asset", {
            "code": code, "sg_asset_type": "Character",
            "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Asset", data)
        target_tracker("Asset", result["id"])

        updated = target.sg.update("Asset", result["id"], {"sg_asset_type": "Prop"})
        assert updated["sg_asset_type"] == "Prop"

    def test_delete_and_revive(self, target, target_tracker):
        """Asset delete → unfindable → revive → findable."""
        code = f"{target.prefix}_ASSET_DELREV"
        data = target.create_data("Asset", {
            "code": code, "sg_asset_type": "Prop",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Asset", data)
        target_tracker("Asset", result["id"])

        target.sg.delete("Asset", result["id"])
        assert target.sg.find_one("Asset", [["id", "is", result["id"]]]) is None

        target.sg.revive("Asset", result["id"])
        found = target.sg.find_one("Asset", [["id", "is", result["id"]]], ["code"])
        assert found is not None
        assert found["code"] == code
