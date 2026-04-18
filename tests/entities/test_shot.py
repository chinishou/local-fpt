"""Shot entity parity tests — CRUD, sequence/episode links, multi-field filters."""


class TestShot:

    def test_find_by_code(self, target):
        """Find shot by exact code."""
        code = target.prefix + "_SEQ010_0010"
        result = target.sg.find_one("Shot", [["code", "is", code]],
                                    ["code", "sg_status_list"])
        assert result is not None
        assert result["type"] == "Shot"
        assert result["code"] == code
        assert result["sg_status_list"] == "ip"

    def test_find_by_sequence(self, target):
        """Filter shots by sg_sequence reference."""
        seq_ref = target.ref("Sequence", "seq1")
        results = target.sg.find("Shot",
                                 [["sg_sequence", "is", seq_ref]],
                                 ["code", "sg_sequence"])
        test_results = [s for s in results if s["code"].startswith(target.prefix)]
        assert len(test_results) == 2
        assert all(r["type"] == "Shot" for r in test_results)

    def test_find_by_project_and_status(self, target):
        """Multi-field filter: project + status on shots."""
        proj_ref = target.ref("Project", "main")
        results = target.sg.find("Shot",
                                 [["project", "is", proj_ref],
                                  ["sg_status_list", "is", "ip"]],
                                 ["code", "sg_status_list"])
        test_results = [s for s in results if s["code"].startswith(target.prefix)]
        assert len(test_results) == 2
        assert all(s["sg_status_list"] == "ip" for s in test_results)

    def test_find_shots_ordered_by_code(self, target):
        """Shots sorted by code descending."""
        results = target.sg.find("Shot",
                                 [["code", "starts_with", target.prefix]],
                                 ["code"],
                                 order=[{"field_name": "code", "direction": "desc"}])
        codes = [s["code"] for s in results]
        assert codes == sorted(codes, reverse=True)

    def test_create_with_sequence_ref(self, target, target_tracker):
        """Create shot linked to a sequence."""
        code = f"{target.prefix}_SHOT_CSEQ"
        data = target.create_data("Shot", {
            "code": code, "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
            "sg_sequence": target.ref("Sequence", "seq1"),
        })
        result = target.sg.create("Shot", data)
        target_tracker("Shot", result["id"])
        assert result["type"] == "Shot"
        assert result["code"] == code
        assert result["sg_status_list"] == "ip"

    def test_update_status(self, target, target_tracker):
        """Update shot status field."""
        code = f"{target.prefix}_SHOT_UST"
        data = target.create_data("Shot", {
            "code": code, "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Shot", data)
        target_tracker("Shot", result["id"])

        updated = target.sg.update("Shot", result["id"], {"sg_status_list": "fin"})
        assert updated["sg_status_list"] == "fin"

    def test_update_sequence_ref(self, target, target_tracker):
        """Re-assign shot to a different sequence."""
        code = f"{target.prefix}_SHOT_RESEQ"
        data = target.create_data("Shot", {
            "code": code, "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
            "sg_sequence": target.ref("Sequence", "seq1"),
        })
        result = target.sg.create("Shot", data)
        target_tracker("Shot", result["id"])

        seq2_ref = target.ref("Sequence", "seq2")
        updated = target.sg.update("Shot", result["id"], {"sg_sequence": seq2_ref})
        assert updated["sg_sequence"]["id"] == seq2_ref["id"]

    def test_delete_and_revive(self, target, target_tracker):
        """Shot delete → unfindable → revive → findable again."""
        code = f"{target.prefix}_SHOT_DELREV"
        data = target.create_data("Shot", {
            "code": code,
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Shot", data)
        target_tracker("Shot", result["id"])

        target.sg.delete("Shot", result["id"])
        assert target.sg.find_one("Shot", [["id", "is", result["id"]]]) is None

        target.sg.revive("Shot", result["id"])
        found = target.sg.find_one("Shot", [["id", "is", result["id"]]], ["code"])
        assert found is not None
        assert found["code"] == code
