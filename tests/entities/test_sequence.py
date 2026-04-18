"""Sequence entity parity tests — CRUD, project link, status filters."""


class TestSequence:

    def test_find_by_code(self, target):
        """Find sequence by exact code."""
        code = target.prefix + "_SEQ_010"
        result = target.sg.find_one("Sequence", [["code", "is", code]], ["code", "sg_status_list"])
        assert result is not None
        assert result["type"] == "Sequence"
        assert result["code"] == code
        assert result["sg_status_list"] == "ip"

    def test_find_by_project(self, target):
        """Filter sequences by project reference."""
        proj_ref = target.ref("Project", "main")
        results = target.sg.find("Sequence",
                                 [["project", "is", proj_ref]],
                                 ["code", "sg_status_list"])
        test_results = [s for s in results if s["code"].startswith(target.prefix)]
        assert len(test_results) == 2
        assert all(r["type"] == "Sequence" for r in test_results)

    def test_find_by_status(self, target):
        """Filter sequences by sg_status_list."""
        results = target.sg.find("Sequence",
                                 [["sg_status_list", "is", "ip"],
                                  ["code", "starts_with", target.prefix]],
                                 ["code", "sg_status_list"])
        assert len(results) == 1
        assert results[0]["sg_status_list"] == "ip"

    def test_find_with_not_in_status(self, target):
        """not_in filter on sg_status_list excludes specified values."""
        results = target.sg.find("Sequence",
                                 [["sg_status_list", "not_in", ["fin"]],
                                  ["code", "starts_with", target.prefix]],
                                 ["code", "sg_status_list"])
        assert len(results) == 1
        assert results[0]["sg_status_list"] != "fin"

    def test_create_update_delete(self, target, target_tracker):
        """Sequence lifecycle: create with project link, update status, verify."""
        code = f"{target.prefix}_SEQ_LIFE"
        data = target.create_data("Sequence", {
            "code": code, "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Sequence", data)
        target_tracker("Sequence", result["id"])

        target.sg.update("Sequence", result["id"], {"sg_status_list": "fin"})

        found = target.sg.find_one("Sequence", [["id", "is", result["id"]]],
                                   ["code", "sg_status_list"])
        assert found["code"] == code
        assert found["sg_status_list"] == "fin"
