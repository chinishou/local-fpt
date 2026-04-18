"""
Seed data for LocalFPT - Phase 2: User Sample Data.
"""
import sqlite3
import json
import os


def seed_sample_data(db_path='sg_sample.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Sample Project
    cursor.execute('''
        INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
        VALUES (?, ?, 0, datetime('now'), datetime('now'))
    ''', (1, 'Project'))
    cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                   (1, 'name', json.dumps('Sample Studio Project')))
    cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                   (1, 'code', json.dumps('sample_proj')))
    cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                   (1, 'sg_status_list', json.dumps('ip')))

    project_link = {"type": "Project", "id": 1}

    # Sequences
    for i, name in enumerate(['Sequence_A', 'Sequence_B', 'Sequence_C'], 1):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'Sequence'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'code', json.dumps(name)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('fin')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))

    # Shots
    for i, (seq, name) in enumerate([
        (1, 'SEQ_A_SHOT_001'), (1, 'SEQ_A_SHOT_002'),
        (2, 'SEQ_B_SHOT_001'), (2, 'SEQ_B_SHOT_002'), (2, 'SEQ_B_SHOT_003'),
        (3, 'SEQ_C_SHOT_001'),
    ], 10):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'Shot'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'code', json.dumps(name)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('fin' if i < 14 else 'ip')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_sequence', json.dumps({"type": "Sequence", "id": seq})))

    # Assets
    for i, (code, atype) in enumerate([
        ('Hero_Character', 'Character'),
        ('Villain_Character', 'Character'),
        ('Forest_Environment', 'Environment'),
        ('Props_Pack', 'Prop'),
    ], 20):
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

    # Tasks
    task_content = ['Modeling', 'Texturing', 'Rigging', 'Animation', 'Lighting', 'Comp']
    for i, content in enumerate(task_content, 30):
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
                       (i, 'entity', json.dumps({"type": "Asset", "id": 20})))

    # Versions
    for i, code in enumerate(['v001', 'v002', 'v003'], 40):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'Version'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'code', json.dumps(f'SEQ_A_SHOT_001_{code}')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('rev')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))

    # Notes
    for i, content in enumerate(['Fix lighting issue', 'Update character rig', 'Review animation'], 50):
        cursor.execute('''
            INSERT INTO entity_records (id, entity_type, retired, created_at, updated_at)
            VALUES (?, ?, 0, datetime('now'), datetime('now'))
        ''', (i, 'Note'))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'content', json.dumps(content)))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'sg_status_list', json.dumps('opn')))
        cursor.execute('INSERT INTO field_values (record_id, field_name, value) VALUES (?, ?, ?)',
                       (i, 'project', json.dumps(project_link)))

    conn.commit()
    conn.close()
    print(f"Sample data seeded in {db_path}")


if __name__ == '__main__':
    seed_sample_data()
