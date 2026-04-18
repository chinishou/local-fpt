"""PublishedFile entity parity tests.
Local uses 'PublishedFiles' (plural), cloud uses 'PublishedFile' (singular).
target.entity_type('PublishedFile') resolves to the correct name per server."""


class TestPublishedFile:

    def test_find_by_code(self, target):
        """Find published file by code."""
        etype = target.entity_type("PublishedFile")
        code = target.prefix + "_hero_model_v001"
        result = target.sg.find_one(etype, [["code", "is", code]], ["code"])
        assert result is not None
        assert result["code"] == code

    def test_find_by_project(self, target):
        """Filter published files by project."""
        etype = target.entity_type("PublishedFile")
        proj_ref = target.ref("Project", "main")
        results = target.sg.find(etype,
                                 [["project", "is", proj_ref]],
                                 ["code"])
        test_results = [p for p in results if p["code"].startswith(target.prefix)]
        assert len(test_results) >= 1

    def test_find_by_entity_asset(self, target):
        """Filter published files by entity (Asset) reference."""
        etype = target.entity_type("PublishedFile")
        asset_ref = target.ref("Asset", "asset1")
        results = target.sg.find(etype,
                                 [["entity", "is", asset_ref]],
                                 ["code"])
        test_results = [p for p in results if p["code"].startswith(target.prefix)]
        assert len(test_results) == 1

    def test_find_by_code_contains(self, target):
        """Contains filter on published file code."""
        etype = target.entity_type("PublishedFile")
        results = target.sg.find(etype,
                                 [["code", "contains", "hero_model"],
                                  ["code", "starts_with", target.prefix]],
                                 ["code"])
        assert len(results) == 1

    def test_create_and_delete(self, target, target_tracker):
        """Create published file linked to asset, then delete."""
        etype = target.entity_type("PublishedFile")
        code = f"{target.prefix}_pf_test_v001"
        data = {
            "code": code,
            "project": target.ref("Project", "main"),
            "entity": target.ref("Asset", "asset1"),
        }
        if target.is_local:
            data["name"] = code
        result = target.sg.create(etype, data)
        target_tracker("PublishedFile", result["id"])

        deleted = target.sg.delete(etype, result["id"])
        assert deleted is True

    def test_update_code(self, target, target_tracker):
        """Update published file code field."""
        etype = target.entity_type("PublishedFile")
        code = f"{target.prefix}_pf_upd_v001"
        data = {
            "code": code,
            "project": target.ref("Project", "main"),
        }
        if target.is_local:
            data["name"] = code
        result = target.sg.create(etype, data)
        target_tracker("PublishedFile", result["id"])

        new_code = f"{target.prefix}_pf_upd_v002"
        updated = target.sg.update(etype, result["id"], {"code": new_code})
        assert updated["code"] == new_code
