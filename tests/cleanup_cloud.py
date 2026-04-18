#!/usr/bin/env python
"""
Cleanup orphaned SG_TEST_ data from cloud ShotGrid.

Run this manually if a test session crashed and left data behind:

    python tests/cleanup_cloud.py              # dry-run (list only)
    python tests/cleanup_cloud.py --delete     # actually delete

Also called automatically by conftest.py before each test session.
"""
import os
import sys

import shotgun_api3
from dotenv import load_dotenv

load_dotenv()

# Entity types to scan, in reverse dependency order (children first)
ENTITY_TYPES = [
    ("PublishedFile", "code"),
    ("Version", "code"),
    ("Task", "content"),
    ("Playlist", "code"),
    ("Shot", "code"),
    ("Asset", "code"),
    ("Episode", "code"),
    ("Sequence", "code"),
    ("Project", "code"),
]

PREFIX = "SG_TEST_"


def find_orphaned(sg, entity_type, field_name):
    """Find all entities with the test prefix."""
    return sg.find(entity_type,
                   [[field_name, "starts_with", PREFIX]],
                   [field_name],
                   limit=200)


def cleanup_cloud(sg, dry_run=True):
    """Scan and optionally delete all SG_TEST_ prefixed entities.

    Returns (total_found, total_deleted).
    """
    total_found = 0
    total_deleted = 0

    for entity_type, field_name in ENTITY_TYPES:
        entities = find_orphaned(sg, entity_type, field_name)
        if not entities:
            continue

        total_found += len(entities)
        label = "would delete" if dry_run else "deleting"
        print(f"{entity_type}: {len(entities)} orphaned")

        for e in entities:
            code = e.get(field_name, "?")
            print(f"  {label} id={e['id']} {field_name}={code}")
            if not dry_run:
                try:
                    sg.delete(entity_type, e["id"])
                    total_deleted += 1
                except Exception as exc:
                    print(f"    FAILED: {exc}")

    return total_found, total_deleted


def get_cloud_sg():
    """Connect to cloud ShotGrid. Returns None if credentials missing."""
    sg_url = os.getenv("SG_URL")
    script_name = os.getenv("SCRIPT_NAME")
    api_key = os.getenv("API_KEY")
    if not all([sg_url, script_name, api_key]):
        return None
    return shotgun_api3.Shotgun(sg_url, script_name=script_name, api_key=api_key)


def main():
    dry_run = "--delete" not in sys.argv

    sg = get_cloud_sg()
    if sg is None:
        print("Cloud SG credentials not configured in .env — nothing to clean.")
        return

    if dry_run:
        print("=== DRY RUN (pass --delete to actually remove) ===\n")
    else:
        print("=== DELETING orphaned test data from cloud ===\n")

    found, deleted = cleanup_cloud(sg, dry_run=dry_run)

    if found == 0:
        print("Cloud is clean — no orphaned SG_TEST_ data found.")
    elif dry_run:
        print(f"\nFound {found} orphaned entities. Run with --delete to remove.")
    else:
        print(f"\nDeleted {deleted}/{found} entities.")


if __name__ == "__main__":
    main()
