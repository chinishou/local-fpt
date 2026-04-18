"""Ticket entity parity tests — title, status, priority, ticket_type, project."""


class TestTicket:

    def test_find_by_title(self, target):
        """Find ticket by exact title."""
        title = target.prefix + "_T_001"
        result = target.sg.find_one("Ticket", [["title", "is", title]],
                                    ["title", "sg_status_list", "sg_priority"])
        assert result is not None
        assert result["type"] == "Ticket"
        assert result["title"] == title
        assert result["sg_status_list"] == "opn"

    def test_find_by_project(self, target):
        """Filter tickets by project."""
        proj_ref = target.ref("Project", "main")
        results = target.sg.find("Ticket",
                                 [["project", "is", proj_ref]],
                                 ["title"])
        test_results = [t for t in results if t["title"].startswith(target.prefix)]
        assert len(test_results) >= 1

    def test_find_by_status(self, target):
        """Filter tickets by sg_status_list."""
        results = target.sg.find("Ticket",
                                 [["sg_status_list", "is", "opn"],
                                  ["title", "starts_with", target.prefix]],
                                 ["title", "sg_status_list"])
        assert len(results) >= 1
        assert all(t["sg_status_list"] == "opn" for t in results)

    def test_find_by_priority(self, target):
        """Filter tickets by sg_priority."""
        results = target.sg.find("Ticket",
                                 [["sg_priority", "is", "2"],
                                  ["title", "starts_with", target.prefix]],
                                 ["title", "sg_priority"])
        assert len(results) == 1
        assert results[0]["sg_priority"] == "2"

    def test_find_by_ticket_type(self, target):
        """Filter tickets by sg_ticket_type."""
        results = target.sg.find("Ticket",
                                 [["sg_ticket_type", "is", "Bug"],
                                  ["title", "starts_with", target.prefix]],
                                 ["title", "sg_ticket_type"])
        assert len(results) == 1
        assert results[0]["sg_ticket_type"] == "Bug"

    def test_create_and_delete(self, target, target_tracker):
        """Create ticket linked to project, then delete."""
        title = f"{target.prefix}_T_new"
        data = target.create_data("Ticket", {
            "title": title,
            "sg_status_list": "opn",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Ticket", data)
        target_tracker("Ticket", result["id"])
        assert result["type"] == "Ticket"
        assert result["title"] == title

        deleted = target.sg.delete("Ticket", result["id"])
        assert deleted is True

    def test_update_status(self, target, target_tracker):
        """Update ticket status from opn to res."""
        title = f"{target.prefix}_T_upd"
        data = target.create_data("Ticket", {
            "title": title,
            "sg_status_list": "opn",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Ticket", data)
        target_tracker("Ticket", result["id"])

        updated = target.sg.update("Ticket", result["id"], {"sg_status_list": "res"})
        assert updated["sg_status_list"] == "res"

    def test_update_priority(self, target, target_tracker):
        """Update ticket priority field."""
        title = f"{target.prefix}_T_pri"
        data = target.create_data("Ticket", {
            "title": title,
            "sg_priority": "3",
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Ticket", data)
        target_tracker("Ticket", result["id"])

        updated = target.sg.update("Ticket", result["id"], {"sg_priority": "1"})
        assert updated["sg_priority"] == "1"

    def test_update_description(self, target, target_tracker):
        """Update ticket description field."""
        title = f"{target.prefix}_T_desc"
        data = target.create_data("Ticket", {
            "title": title,
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Ticket", data)
        target_tracker("Ticket", result["id"])

        updated = target.sg.update("Ticket", result["id"],
                                   {"description": "Steps to reproduce the bug."})
        assert updated["description"] == "Steps to reproduce the bug."

    def test_delete_and_revive(self, target, target_tracker):
        """Ticket delete -> unfindable -> revive -> findable again."""
        title = f"{target.prefix}_T_rev"
        data = target.create_data("Ticket", {
            "title": title,
            "project": target.ref("Project", "main"),
        })
        result = target.sg.create("Ticket", data)
        target_tracker("Ticket", result["id"])

        target.sg.delete("Ticket", result["id"])
        assert target.sg.find_one("Ticket", [["id", "is", result["id"]]]) is None

        target.sg.revive("Ticket", result["id"])
        found = target.sg.find_one("Ticket", [["id", "is", result["id"]]], ["title"])
        assert found is not None
        assert found["title"] == title
