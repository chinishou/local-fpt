"""Playlist entity parity tests — CRUD, project link."""


class TestPlaylist:

    def test_find_by_code(self, target):
        """Find playlist by exact code."""
        code = target.prefix + "_DailyReview"
        result = target.sg.find_one("Playlist", [["code", "is", code]], ["code"])
        assert result is not None
        assert result["type"] == "Playlist"
        assert result["code"] == code

    def test_find_by_project(self, target):
        """Filter playlists by project."""
        proj_ref = target.ref("Project", "main")
        results = target.sg.find("Playlist",
                                 [["project", "is", proj_ref]],
                                 ["code"])
        test_results = [p for p in results if p["code"].startswith(target.prefix)]
        assert len(test_results) >= 1

    def test_find_by_code_contains(self, target):
        """Find playlist using contains filter."""
        results = target.sg.find("Playlist",
                                 [["code", "contains", "DailyReview"],
                                  ["code", "starts_with", target.prefix]],
                                 ["code"])
        assert len(results) == 1

    def test_create_and_delete(self, target, target_tracker):
        """Create playlist then delete it."""
        code = f"{target.prefix}_PL_LIFE"
        data = target.create_data("Playlist", {
            "code": code,
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Playlist", data)
        target_tracker("Playlist", result["id"])
        assert result["type"] == "Playlist"

        deleted = target.sg.delete("Playlist", result["id"])
        assert deleted is True

    def test_update_code(self, target, target_tracker):
        """Update playlist code field."""
        code = f"{target.prefix}_PL_UPD"
        data = target.create_data("Playlist", {
            "code": code,
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Playlist", data)
        target_tracker("Playlist", result["id"])

        new_code = f"{target.prefix}_PL_UPD_v2"
        updated = target.sg.update("Playlist", result["id"], {"code": new_code})
        assert updated["code"] == new_code

    def test_delete_and_revive(self, target, target_tracker):
        """Playlist delete → revive cycle."""
        code = f"{target.prefix}_PL_DELREV"
        data = target.create_data("Playlist", {
            "code": code,
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Playlist", data)
        target_tracker("Playlist", result["id"])

        target.sg.delete("Playlist", result["id"])
        assert target.sg.find_one("Playlist", [["id", "is", result["id"]]]) is None

        target.sg.revive("Playlist", result["id"])
        found = target.sg.find_one("Playlist", [["id", "is", result["id"]]], ["code"])
        assert found is not None
        assert found["code"] == code
