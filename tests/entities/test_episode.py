"""Episode entity parity tests — CRUD, project link."""


class TestEpisode:

    def test_find_by_code(self, target):
        """Find episode by exact code."""
        code = target.prefix + "_EP_001"
        result = target.sg.find_one("Episode", [["code", "is", code]],
                                    ["code", "sg_status_list"])
        assert result is not None
        assert result["type"] == "Episode"
        assert result["code"] == code
        assert result["sg_status_list"] == "ip"

    def test_find_by_project(self, target):
        """Filter episodes by project reference."""
        proj_ref = target.ref("Project", "main")
        results = target.sg.find("Episode",
                                 [["project", "is", proj_ref]],
                                 ["code"])
        test_results = [e for e in results if e["code"].startswith(target.prefix)]
        assert len(test_results) == 1

    def test_find_by_status(self, target):
        """Filter episodes by sg_status_list."""
        results = target.sg.find("Episode",
                                 [["sg_status_list", "is", "ip"],
                                  ["code", "starts_with", target.prefix]],
                                 ["code", "sg_status_list"])
        assert len(results) == 1
        assert results[0]["sg_status_list"] == "ip"

    def test_create_update_delete(self, target, target_tracker):
        """Episode lifecycle: create with project link, update, verify."""
        code = f"{target.prefix}_EP_LIFE"
        data = target.create_data("Episode", {
            "code": code, "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Episode", data)
        target_tracker("Episode", result["id"])

        target.sg.update("Episode", result["id"], {"sg_status_list": "fin"})

        found = target.sg.find_one("Episode", [["id", "is", result["id"]]],
                                   ["code", "sg_status_list"])
        assert found["code"] == code
        assert found["sg_status_list"] == "fin"

    def test_delete_and_revive(self, target, target_tracker):
        """Delete episode → unfindable → revive → findable."""
        code = f"{target.prefix}_EP_DELREV"
        data = target.create_data("Episode", {
            "code": code,
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Episode", data)
        target_tracker("Episode", result["id"])

        target.sg.delete("Episode", result["id"])
        assert target.sg.find_one("Episode", [["id", "is", result["id"]]]) is None

        target.sg.revive("Episode", result["id"])
        found = target.sg.find_one("Episode", [["id", "is", result["id"]]], ["code"])
        assert found is not None
        assert found["code"] == code
