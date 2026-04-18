"""
Shared fixtures for LocalFPT parity tests.

Requires:
  - Local server running at http://127.0.0.1:8000
  - Cloud credentials in .env (SG_URL, SCRIPT_NAME, API_KEY)

Data lifecycle:
  1. Pre-session: auto-cleanup of any orphaned SG_TEST_ data on cloud
     (catches leftovers from crashed previous runs)
  2. Session start: test_dataset fixture creates ~17 entities on both
     local and cloud, prefixed with SG_TEST_{timestamp}
  3. Per-test: target_tracker creates/tracks mutation entities, cleans up
     after each test function (one server at a time via parametrized target)
  4. Session end: test_dataset teardown deletes all dataset entities in
     reverse dependency order
  5. Manual: python tests/cleanup_cloud.py --delete
"""
import os
import time
from dataclasses import dataclass, field
from typing import Any

import httpx
import pytest
import shotgun_api3
from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------------------------
# SGTarget — wraps one SG client + its dataset slice for parametrized tests
# ---------------------------------------------------------------------------
@dataclass
class SGTarget:
    """One side of a parity test: either local or cloud ShotGrid."""

    sg: Any         # shotgun_api3.Shotgun client
    data: dict      # test_dataset["local"] or test_dataset["cloud"]
    name: str       # "local" or "cloud"
    prefix: str     # session prefix string

    # Fields that cloud SG rejects on create (empty now — schemas aligned to cloud)
    _CLOUD_STRIP: dict = field(default_factory=dict, repr=False)

    def entity_type(self, name: str) -> str:
        """Map PublishedFile <-> PublishedFiles for this target."""
        if self.name == "local" and name == "PublishedFile":
            return "PublishedFiles"
        if self.name == "cloud" and name == "PublishedFiles":
            return "PublishedFile"
        return name

    def ref(self, entity_type: str, nickname: str) -> dict:
        """Get {"type": ..., "id": ...} for an entity in the dataset."""
        key = self.entity_type(entity_type)
        return {"type": key, "id": self.data[key][nickname]["id"]}

    def create_data(self, entity_type: str, data: dict) -> dict:
        """Strip cloud-incompatible fields when running on cloud."""
        if self.name == "local":
            return data
        strip = self._CLOUD_STRIP.get(entity_type, set())
        return {k: v for k, v in data.items() if k not in strip}

    @property
    def is_cloud(self) -> bool:
        return self.name == "cloud"

    @property
    def is_local(self) -> bool:
        return self.name == "local"


# ---------------------------------------------------------------------------
# Unique prefix for every test session to avoid collisions
# ---------------------------------------------------------------------------
SESSION_PREFIX = f"SG_TEST_{int(time.time())}"


# ---------------------------------------------------------------------------
# Connection fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def local_sg():
    """shotgun_api3 client pointed at the local LocalFPT server."""
    return shotgun_api3.Shotgun(
        "http://127.0.0.1:8000",
        script_name="local_dev",
        api_key="test-key",
    )


@pytest.fixture(scope="session")
def cloud_sg():
    """shotgun_api3 client pointed at cloud ShotGrid.
    Skips the entire session if credentials are missing."""
    sg_url = os.getenv("SG_URL")
    script_name = os.getenv("SCRIPT_NAME")
    api_key = os.getenv("API_KEY")
    if not all([sg_url, script_name, api_key]):
        pytest.skip("Cloud SG credentials not configured in .env")
    return shotgun_api3.Shotgun(sg_url, script_name=script_name, api_key=api_key)


@pytest.fixture(scope="session")
def local_http():
    """httpx client for direct REST calls to local server."""
    with httpx.Client(base_url="http://127.0.0.1:8000", timeout=10) as client:
        yield client


@pytest.fixture(scope="session", autouse=True)
def check_local_server(local_http):
    """Skip all tests if local server is not running."""
    try:
        r = local_http.get("/health")
        r.raise_for_status()
    except Exception:
        pytest.skip("Local LocalFPT server is not running on http://127.0.0.1:8000")


# ---------------------------------------------------------------------------
# Pre-session: clean up orphaned SG_TEST_ data from previous crashed runs
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session", autouse=True)
def cleanup_stale_cloud_data(cloud_sg):
    """Delete any SG_TEST_ prefixed data left on cloud from previous runs.

    Runs before test_dataset creation to ensure a clean starting state.
    Only deletes data from PREVIOUS sessions (different timestamp prefix).
    """
    from tests.cleanup_cloud import cleanup_cloud
    found, deleted = cleanup_cloud(cloud_sg, dry_run=False)
    if found > 0:
        print(f"\n[pre-session cleanup] Removed {deleted}/{found} orphaned "
              f"SG_TEST_ entities from cloud")


# ---------------------------------------------------------------------------
# Validation dataset — session-scoped, covers all 10 entity types
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def prefix():
    return SESSION_PREFIX


@pytest.fixture(scope="session")
def test_dataset(local_sg, cloud_sg, prefix):
    """Create a full hierarchy of test entities on both local and cloud.

    Yields a dict:
        {
            "prefix": str,
            "local": { entity_type: { nickname: entity_dict } },
            "cloud": { entity_type: { nickname: entity_dict } },
        }

    Teardown deletes everything in reverse dependency order.
    """
    local_ids = {}  # {entity_type: {nickname: full_entity_dict}}
    cloud_ids = {}
    # Track for cleanup: list of (entity_type, local_id, cloud_id)
    cleanup = []

    def _create(entity_type, nickname, local_data, cloud_data,
                cloud_entity_type=None):
        cloud_type = cloud_entity_type or entity_type
        le = local_sg.create(entity_type, local_data)
        ce = cloud_sg.create(cloud_type, cloud_data)
        local_ids.setdefault(entity_type, {})[nickname] = le
        cloud_ids.setdefault(cloud_type, {})[nickname] = ce
        cleanup.append((entity_type, le["id"], cloud_type, ce["id"]))
        return le, ce

    def _proj_ref(target):
        ids = local_ids if target == "local" else cloud_ids
        p = ids["Project"]["main"]
        return {"type": "Project", "id": p["id"]}

    def _ref(target, etype, nickname):
        ids = local_ids if target == "local" else cloud_ids
        e = ids[etype][nickname]
        return {"type": etype, "id": e["id"]}

    # --- Phase 1: HumanUser (no dependencies) ---
    # Cloud SG restricts HumanUser creation — create on local only, find existing on cloud
    local_hu = local_sg.create("HumanUser", {
        "name": f"{prefix}_TestUser", "login": f"{prefix}_testuser",
        "email": f"{prefix}_test@example.com", "sg_status_list": "act",
    })
    local_ids.setdefault("HumanUser", {})["user1"] = local_hu
    cleanup.append(("HumanUser", local_hu["id"], None, None))
    # Find an existing active user on cloud for parity
    cloud_hu = cloud_sg.find_one("HumanUser", [["sg_status_list", "is", "act"]], ["name", "login", "email"])
    if cloud_hu:
        cloud_ids.setdefault("HumanUser", {})["user1"] = cloud_hu
    else:
        cloud_ids.setdefault("HumanUser", {})["user1"] = {"type": "HumanUser", "id": -1}

    # --- Phase 2: Project ---
    _create("Project", "main",
            {"name": f"{prefix}_TestProject", "code": f"{prefix}_tp",
             "sg_status": "Active"},
            {"name": f"{prefix}_TestProject", "code": f"{prefix}_tp",
             "sg_status": "Active"})

    # --- Phase 3: Sequence + Episode (depend on Project) ---
    for nick, code, status in [("seq1", "SEQ_010", "ip"), ("seq2", "SEQ_020", "fin")]:
        _create("Sequence", nick,
                {"code": f"{prefix}_{code}",
                 "sg_status_list": status, "project": _proj_ref("local")},
                {"code": f"{prefix}_{code}",
                 "sg_status_list": status, "project": _proj_ref("cloud")})

    _create("Episode", "ep1",
            {"code": f"{prefix}_EP_001",
             "sg_status_list": "ip", "project": _proj_ref("local")},
            {"code": f"{prefix}_EP_001",
             "sg_status_list": "ip", "project": _proj_ref("cloud")})

    # --- Phase 4: Shot (depend on Project, Sequence) ---
    shot_defs = [
        ("shot1", "SEQ010_0010", "seq1", "ip"),
        ("shot2", "SEQ010_0020", "seq1", "fin"),
        ("shot3", "SEQ020_0010", "seq2", "ip"),
    ]
    for nick, code, seq_nick, status in shot_defs:
        base = {"code": f"{prefix}_{code}", "sg_status_list": status}
        _create("Shot", nick,
                {**base, "project": _proj_ref("local"),
                 "sg_sequence": _ref("local", "Sequence", seq_nick)},
                {**base, "project": _proj_ref("cloud"),
                 "sg_sequence": _ref("cloud", "Sequence", seq_nick)})

    # --- Phase 5: Asset (depend on Project) ---
    for nick, code, atype in [("asset1", "Hero", "Character"), ("asset2", "Forest", "Environment")]:
        _create("Asset", nick,
                {"code": f"{prefix}_{code}",
                 "sg_asset_type": atype, "sg_status_list": "ip",
                 "project": _proj_ref("local")},
                {"code": f"{prefix}_{code}",
                 "sg_asset_type": atype, "sg_status_list": "ip",
                 "project": _proj_ref("cloud")})

    # --- Phase 6: Task (depend on Project + Shot/Asset) ---
    _create("Task", "task1",
            {"content": f"{prefix}_Anim", "sg_status_list": "ip",
             "project": _proj_ref("local"),
             "entity": _ref("local", "Shot", "shot1")},
            {"content": f"{prefix}_Anim", "sg_status_list": "ip",
             "project": _proj_ref("cloud"),
             "entity": _ref("cloud", "Shot", "shot1")})

    _create("Task", "task2",
            {"content": f"{prefix}_Model", "sg_status_list": "wtg",
             "project": _proj_ref("local"),
             "entity": _ref("local", "Asset", "asset1")},
            {"content": f"{prefix}_Model", "sg_status_list": "wtg",
             "project": _proj_ref("cloud"),
             "entity": _ref("cloud", "Asset", "asset1")})

    # --- Phase 7: Version (depend on Project + Shot) ---
    for nick, code, status in [("ver1", "anim_v001", "rev"), ("ver2", "anim_v002", "na")]:
        _create("Version", nick,
                {"code": f"{prefix}_{code}", "sg_status_list": status,
                 "project": _proj_ref("local"),
                 "entity": _ref("local", "Shot", "shot1")},
                {"code": f"{prefix}_{code}", "sg_status_list": status,
                 "project": _proj_ref("cloud"),
                 "entity": _ref("cloud", "Shot", "shot1")})

    # --- Phase 8: Playlist (depend on Project) ---
    _create("Playlist", "pl1",
            {"code": f"{prefix}_DailyReview",
             "project": _proj_ref("local")},
            {"code": f"{prefix}_DailyReview",
             "project": _proj_ref("cloud")})

    # --- Phase 9: PublishedFile (depend on Project + Asset) ---
    # NOTE: Local uses "PublishedFiles" (plural), cloud uses "PublishedFile" (singular).
    local_pf = local_sg.create("PublishedFiles", {
        "code": f"{prefix}_hero_model_v001", "name": f"{prefix}_hero_model_v001",
        "sg_status_list": "pub",
        "project": _proj_ref("local"),
        "entity": _ref("local", "Asset", "asset1"),
    })
    cloud_pf = cloud_sg.create("PublishedFile", {
        "code": f"{prefix}_hero_model_v001", "name": f"{prefix}_hero_model_v001",
        "project": _proj_ref("cloud"),
        "entity": _ref("cloud", "Asset", "asset1"),
    })
    local_ids.setdefault("PublishedFiles", {})["pf1"] = local_pf
    cloud_ids.setdefault("PublishedFile", {})["pf1"] = cloud_pf
    cleanup.append(("PublishedFiles", local_pf["id"], None, None))
    cleanup.append((None, None, "PublishedFile", cloud_pf["id"]))

    # --- Phase 10: Ticket (depend on Project) ---
    # Ticket uses 'title' (not 'code'), same pattern as Task/'content'.
    _create("Ticket", "ticket1",
            {"title": f"{prefix}_T_001",
             "sg_status_list": "opn", "sg_priority": "2",
             "sg_ticket_type": "Bug",
             "project": _proj_ref("local")},
            {"title": f"{prefix}_T_001",
             "sg_status_list": "opn", "sg_priority": "2",
             "sg_ticket_type": "Bug",
             "project": _proj_ref("cloud")})

    yield {
        "prefix": prefix,
        "local": local_ids,
        "cloud": cloud_ids,
    }

    # --- Cleanup in reverse order ---
    # Each entry: (local_entity_type, local_id, cloud_entity_type, cloud_id)
    for local_type, local_id, cloud_type, cloud_id in reversed(cleanup):
        if local_id is not None and local_type is not None:
            try:
                local_sg.delete(local_type, local_id)
            except Exception:
                pass
        if cloud_id is not None and cloud_type is not None:
            try:
                cloud_sg.delete(cloud_type, cloud_id)
            except Exception:
                pass


# ---------------------------------------------------------------------------
# Parametrized target fixture — one test, two servers
# ---------------------------------------------------------------------------
@pytest.fixture(params=["local", "cloud"])
def target(request, local_sg, cloud_sg, test_dataset) -> SGTarget:
    """Parametrized: yields SGTarget for local server, then cloud server.

    Cloud is automatically skipped if cloud_sg credentials are absent.
    """
    if request.param == "local":
        return SGTarget(local_sg, test_dataset["local"], "local", test_dataset["prefix"])
    return SGTarget(cloud_sg, test_dataset["cloud"], "cloud", test_dataset["prefix"])


@pytest.fixture
def target_tracker(target):
    """Auto-cleanup for entities created during a parametrized test.

    Usage: target_tracker("Shot", result["id"])
    Cleans up on the same server the test ran against.
    """
    tracked = []

    def track(entity_type: str, entity_id: int):
        tracked.append((target.entity_type(entity_type), entity_id))

    yield track

    for etype, eid in reversed(tracked):
        try:
            target.sg.delete(etype, eid)
        except Exception:
            pass


# ---------------------------------------------------------------------------
# Per-test temporary entity tracker for dual-client tests (legacy)
# ---------------------------------------------------------------------------
@pytest.fixture
def temp_tracker(local_sg, cloud_sg):
    """Track entities created during a single test for automatic cleanup."""
    tracked = []

    def track(entity_type, local_id=None, cloud_id=None):
        tracked.append((entity_type, local_id, entity_type, cloud_id))

    yield track

    for local_type, local_id, cloud_type, cloud_id in reversed(tracked):
        if local_id is not None:
            try:
                local_sg.delete(local_type, local_id)
            except Exception:
                pass
        if cloud_id is not None:
            try:
                cloud_sg.delete(cloud_type, cloud_id)
            except Exception:
                pass
