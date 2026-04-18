"""Task entity parity tests — uses 'content' not 'code', polymorphic 'entity' link."""


class TestTask:

    def test_find_by_content(self, target):
        """Find task by content field (Task uses content, not code)."""
        content = target.prefix + "_Anim"
        result = target.sg.find_one("Task", [["content", "is", content]],
                                    ["content", "sg_status_list"])
        assert result is not None
        assert result["type"] == "Task"
        assert result["content"] == content
        assert result["sg_status_list"] == "ip"

    def test_find_by_status(self, target):
        """Filter tasks by sg_status_list."""
        results = target.sg.find("Task",
                                 [["sg_status_list", "is", "wtg"],
                                  ["content", "starts_with", target.prefix]],
                                 ["content", "sg_status_list"])
        assert len(results) == 1
        assert results[0]["sg_status_list"] == "wtg"

    def test_find_by_project(self, target):
        """Filter tasks by project."""
        proj_ref = target.ref("Project", "main")
        results = target.sg.find("Task",
                                 [["project", "is", proj_ref]],
                                 ["content", "sg_status_list"])
        test_results = [t for t in results if t["content"].startswith(target.prefix)]
        assert len(test_results) == 2

    def test_find_linked_to_shot(self, target):
        """Filter tasks by entity (Shot) reference — polymorphic link."""
        shot_ref = target.ref("Shot", "shot1")
        results = target.sg.find("Task",
                                 [["entity", "is", shot_ref]],
                                 ["content", "entity"])
        test_results = [t for t in results if t["content"].startswith(target.prefix)]
        assert len(test_results) == 1
        assert test_results[0]["content"] == target.prefix + "_Anim"

    def test_find_linked_to_asset(self, target):
        """Filter tasks by entity (Asset) reference — polymorphic link."""
        asset_ref = target.ref("Asset", "asset1")
        results = target.sg.find("Task",
                                 [["entity", "is", asset_ref]],
                                 ["content"])
        test_results = [t for t in results if t["content"].startswith(target.prefix)]
        assert len(test_results) == 1

    def test_create_on_shot(self, target, target_tracker):
        """Create task linked to a shot."""
        content = f"{target.prefix}_Comp"
        data = target.create_data("Task", {
            "content": content, "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
            "entity": target.ref("Shot", "shot1"),
        })
        result = target.sg.create("Task", data)
        target_tracker("Task", result["id"])
        assert result["type"] == "Task"
        assert result["content"] == content
        assert result["sg_status_list"] == "ip"

    def test_create_on_asset(self, target, target_tracker):
        """Create task linked to an asset."""
        content = f"{target.prefix}_Rig"
        data = target.create_data("Task", {
            "content": content, "sg_status_list": "wtg",
            "project": target.ref("Project", "main"),
            "entity": target.ref("Asset", "asset1"),
        })
        result = target.sg.create("Task", data)
        target_tracker("Task", result["id"])
        assert result["type"] == "Task"
        assert result["content"] == content
        assert result["sg_status_list"] == "wtg"

    def test_update_status(self, target, target_tracker):
        """Update task sg_status_list."""
        data = target.create_data("Task", {
            "content": f"{target.prefix}_TaskUpd", "sg_status_list": "ip",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Task", data)
        target_tracker("Task", result["id"])

        updated = target.sg.update("Task", result["id"], {"sg_status_list": "fin"})
        assert updated["sg_status_list"] == "fin"
