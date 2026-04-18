"""Version entity parity tests — CRUD, Shot entity link, cloud-safe statuses."""


class TestVersion:

    def test_find_by_code(self, target):
        """Find version by exact code."""
        code = target.prefix + "_anim_v001"
        result = target.sg.find_one("Version", [["code", "is", code]],
                                    ["code", "sg_status_list"])
        assert result is not None
        assert result["type"] == "Version"
        assert result["code"] == code
        assert result["sg_status_list"] == "rev"

    def test_find_by_project(self, target):
        """Filter versions by project."""
        proj_ref = target.ref("Project", "main")
        results = target.sg.find("Version",
                                 [["project", "is", proj_ref]],
                                 ["code", "sg_status_list"])
        test_results = [v for v in results if v["code"].startswith(target.prefix)]
        assert len(test_results) == 2
        assert all(r["type"] == "Version" for r in test_results)

    def test_find_by_entity_shot(self, target):
        """Filter versions by entity (Shot) reference."""
        shot_ref = target.ref("Shot", "shot1")
        results = target.sg.find("Version",
                                 [["entity", "is", shot_ref]],
                                 ["code"])
        test_results = [v for v in results if v["code"].startswith(target.prefix)]
        assert len(test_results) == 2

    def test_find_by_status(self, target):
        """Filter versions by sg_status_list (cloud-valid: na, rev, vwd, apr)."""
        results = target.sg.find("Version",
                                 [["sg_status_list", "is", "rev"],
                                  ["code", "starts_with", target.prefix]],
                                 ["code", "sg_status_list"])
        assert len(results) == 1
        assert results[0]["sg_status_list"] == "rev"

    def test_find_versions_in_status(self, target):
        """in-filter on version statuses."""
        results = target.sg.find("Version",
                                 [["sg_status_list", "in", ["rev", "na"]],
                                  ["code", "starts_with", target.prefix]],
                                 ["code", "sg_status_list"])
        assert len(results) == 2

    def test_create_on_shot(self, target, target_tracker):
        """Create version linked to a shot."""
        code = f"{target.prefix}_anim_v003"
        data = target.create_data("Version", {
            "code": code, "sg_status_list": "rev",
            "project": target.ref("Project", "main"),
            "entity": target.ref("Shot", "shot1"),
        })
        result = target.sg.create("Version", data)
        target_tracker("Version", result["id"])
        assert result["type"] == "Version"
        assert result["code"] == code
        assert result["sg_status_list"] == "rev"

    def test_update_status(self, target, target_tracker):
        """Update version status (using cloud-valid statuses only)."""
        code = f"{target.prefix}_ver_upd"
        data = target.create_data("Version", {
            "code": code, "sg_status_list": "na",
            "project": target.ref("Project", "main"),
            "entity": target.ref("Shot", "shot1"),
        })
        result = target.sg.create("Version", data)
        target_tracker("Version", result["id"])

        updated = target.sg.update("Version", result["id"], {"sg_status_list": "rev"})
        assert updated["sg_status_list"] == "rev"
