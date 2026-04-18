"""Seed data using the Flask app API."""
import os
import sys

def seed_via_api(app=None, db_path='sg_test.db'):
    if app is None:
        sys.path.insert(0, 'src')
        from local_fpt.app import create_app
        if os.path.exists(db_path):
            os.remove(db_path)
        app = create_app(db_path)

    client = app.test_client()

    def api(method, params):
        resp = client.post('/api3/json', json={
            'method_name': method,
            'params': [params]
        })
        return resp.json

    print("Creating Project...")
    resp = api('create', {
        'type': 'Project',
        'data': {
            'name': 'Demo: Animation',
            'code': 'demo_animation',
            'sg_status_list': 'ip'
        }
    })
    print(f"Project: {resp}")
    project_id = resp['results']['data']['id']

    print("\nCreating Sequences...")
    seq_ids = []
    for code in ['SEQ_001', 'SEQ_002', 'SEQ_003']:
        resp = api('create', {
            'type': 'Sequence',
            'data': {'code': code, 'sg_status_list': 'fin', 'project': {'type': 'Project', 'id': project_id}}
        })
        seq_ids.append(resp['results']['data']['id'])
        print(f"  Sequence {code}: id={seq_ids[-1]}")

    print("\nCreating Episodes...")
    ep_ids = []
    for code in ['EP_001', 'EP_002']:
        resp = api('create', {
            'type': 'Episode',
            'data': {'code': code, 'sg_status_list': 'fin', 'project': {'type': 'Project', 'id': project_id}}
        })
        ep_ids.append(resp['results']['data']['id'])
        print(f"  Episode {code}: id={ep_ids[-1]}")

    print("\nCreating Shots...")
    shot_ids = []
    shots = [
        (seq_ids[0], 'SEQ_001_SHOT_001'),
        (seq_ids[0], 'SEQ_001_SHOT_002'),
        (seq_ids[1], 'SEQ_002_SHOT_001'),
    ]
    for seq_id, code in shots:
        resp = api('create', {
            'type': 'Shot',
            'data': {
                'code': code,
                'sg_status_list': 'fin',
                'project': {'type': 'Project', 'id': project_id},
                'sg_sequence': {'type': 'Sequence', 'id': seq_id}
            }
        })
        shot_ids.append(resp['results']['data']['id'])
        print(f"  Shot {code}: id={shot_ids[-1]}")

    print("\nCreating Assets...")
    asset_ids = []
    assets = [
        ('Hero_Char', 'Character'),
        ('Villain_Char', 'Character'),
        ('Forest_Env', 'Environment'),
    ]
    for code, atype in assets:
        resp = api('create', {
            'type': 'Asset',
            'data': {
                'code': code,
                'sg_asset_type': atype,
                'sg_status_list': 'ip',
                'project': {'type': 'Project', 'id': project_id}
            }
        })
        asset_ids.append(resp['results']['data']['id'])
        print(f"  Asset {code}: id={asset_ids[-1]}")

    print("\nCreating Versions...")
    for i, code in enumerate(['v001', 'v002']):
        resp = api('create', {
            'type': 'Version',
            'data': {
                'code': code,
                'sg_status_list': 'rev',
                'project': {'type': 'Project', 'id': project_id},
                'entity': {'type': 'Shot', 'id': shot_ids[0]}
            }
        })
        print(f"  Version {code}: id={resp['results']['data']['id']}")

    print("\nCreating Tasks...")
    for content in ['Modeling', 'Rigging', 'Animation']:
        resp = api('create', {
            'type': 'Task',
            'data': {
                'content': content,
                'sg_status_list': 'ip',
                'project': {'type': 'Project', 'id': project_id},
                'entity': {'type': 'Asset', 'id': asset_ids[0]}
            }
        })
        print(f"  Task {content}: id={resp['results']['data']['id']}")

    print("\nCreating Playlists...")
    for code in ['PL_001', 'PL_002']:
        resp = api('create', {
            'type': 'Playlist',
            'data': {
                'code': code,
                'sg_status_list': 'ip',
                'project': {'type': 'Project', 'id': project_id}
            }
        })
        print(f"  Playlist {code}: id={resp['results']['data']['id']}")

    print("\nCreating HumanUsers...")
    for name, login in [('Admin User', 'admin'), ('Dev User', 'developer')]:
        resp = api('create', {
            'type': 'HumanUser',
            'data': {
                'name': name,
                'login': login,
                'sg_status_list': 'act'
            }
        })
        print(f"  User {login}: id={resp['results']['data']['id']}")

    print("\nCreating PublishedFiles...")
    for code in ['pub_001', 'pub_002']:
        resp = api('create', {
            'type': 'PublishedFiles',
            'data': {
                'code': code,
                'sg_status_list': 'pub',
                'project': {'type': 'Project', 'id': project_id}
            }
        })
        print(f"  PublishedFile {code}: id={resp['results']['data']['id']}")

    print("\n=== DATA SEEDED ===")
    return project_id, seq_ids, ep_ids, shot_ids, asset_ids


if __name__ == '__main__':
    seed_via_api()
