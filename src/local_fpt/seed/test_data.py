"""
Seed data for LocalFPT - Phase 1: Test Data (matches cloud structure).
"""
import sqlite3
import json
import os


def seed_test_data(db_path='sg_test.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Project
    cursor.execute('''
        INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
        VALUES (?, ?, 0, datetime('now'), datetime('now'))
    ''', (1, 'Project'))
    cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                   (1, 'name', json.dumps('Demo: Animation')))
    cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                   (1, 'code', json.dumps('demo_animation')))
    cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                   (1, 'sg_status_list', json.dumps('ip')))

    project_link = {"type": "Project", "id": 1}

    # Sequences
    for i, code in enumerate(['SEQ_001', 'SEQ_002', 'SEQ_003'], 1):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'Sequence'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'code', json.dumps(code)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('fin')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))

    # Episodes
    for i, code in enumerate(['EP_001', 'EP_002'], 10):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'Episode'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'code', json.dumps(code)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('fin')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))

    # Shots
    for i, (seq, code) in enumerate([(1, 'SEQ_001_SHOT_001'), (1, 'SEQ_001_SHOT_002'), (2, 'SEQ_002_SHOT_001')], 20):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'Shot'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'code', json.dumps(code)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('fin')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_sequence', json.dumps({"type": "Sequence", "id": seq})))

    # Assets
    for i, (code, atype) in enumerate([('Hero_Char', 'Character'), ('Villain_Char', 'Character'), ('Forest_Env', 'Environment')], 30):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'Asset'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'code', json.dumps(code)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_asset_type', json.dumps(atype)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('ip')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))

    # Versions
    for i, code in enumerate(['v001', 'v002'], 40):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'Version'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'code', json.dumps(code)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('rev')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'entity', json.dumps({"type": "Shot", "id": 20})))

    # Tasks
    for i, content in enumerate(['Modeling', 'Rigging', 'Animation'], 50):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'Task'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'content', json.dumps(content)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('ip')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'entity', json.dumps({"type": "Asset", "id": 30})))

    # Playlists
    for i, code in enumerate(['PL_001', 'PL_002'], 60):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'Playlist'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'code', json.dumps(code)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('ip')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))

    # HumanUsers
    for i, (name, login) in enumerate([('Admin User', 'admin'), ('Dev User', 'developer')], 70):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'HumanUser'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'name', json.dumps(name)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'login', json.dumps(login)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('act')))

    # PublishedFiles
    for i, code in enumerate(['pub_001', 'pub_002'], 80):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'PublishedFiles'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'code', json.dumps(code)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('pub')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))

    conn.commit()
    conn.close()
    print(f"Test data seeded in {db_path}")


if __name__ == '__main__':
    seed_test_data()
