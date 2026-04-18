"""
Schema service for LocalFPT - Reduced entity set.
"""
from local_fpt.db.models import EntityMeta, FieldMeta
from local_fpt.db.database import get_session


CORE_ENTITIES = {
    'Project': {
        'fields': {
            'name': {'type': 'text'},
            'code': {'type': 'text'},
            'sg_description': {'type': 'text'},
            'sg_status': {'type': 'list'},
        }
    },
    'Sequence': {
        'fields': {
            'code': {'type': 'text'},
            'sg_status_list': {'type': 'list'},
            'project': {'type': 'entity_type'},
        }
    },
    'Episode': {
        'fields': {
            'code': {'type': 'text'},
            'sg_status_list': {'type': 'list'},
            'project': {'type': 'entity_type'},
        }
    },
    'Shot': {
        'fields': {
            'code': {'type': 'text'},
            'sg_status_list': {'type': 'list'},
            'project': {'type': 'entity_type'},
            'sg_sequence': {'type': 'entity_type'},
        }
    },
    'Asset': {
        'fields': {
            'code': {'type': 'text'},
            'sg_asset_type': {'type': 'list'},
            'sg_status_list': {'type': 'list'},
            'project': {'type': 'entity_type'},
        }
    },
    'Task': {
        'fields': {
            'content': {'type': 'text'},
            'sg_status_list': {'type': 'list'},
            'project': {'type': 'entity_type'},
            'entity': {'type': 'entity_type'},
        }
    },
    'Version': {
        'fields': {
            'code': {'type': 'text'},
            'sg_status_list': {'type': 'list'},
            'project': {'type': 'entity_type'},
            'entity': {'type': 'entity_type'},
        }
    },
    'Playlist': {
        'fields': {
            'code': {'type': 'text'},
            'project': {'type': 'entity_type'},
        }
    },
    'HumanUser': {
        'fields': {
            'name': {'type': 'text'},
            'email': {'type': 'text'},
            'login': {'type': 'text'},
            'sg_status_list': {'type': 'list'},
        }
    },
    'PublishedFiles': {
        'fields': {
            'code': {'type': 'text'},
            'name': {'type': 'text'},
            'sg_status_list': {'type': 'list'},
            'project': {'type': 'entity_type'},
            'entity': {'type': 'entity_type'},
        }
    },
    'Ticket': {
        'fields': {
            'title': {'type': 'text'},
            'description': {'type': 'text'},
            'sg_status_list': {'type': 'list'},
            'sg_priority': {'type': 'list'},
            'sg_ticket_type': {'type': 'list'},
            'project': {'type': 'entity_type'},
        }
    },
}


class SchemaService:
    def __init__(self, session=None):
        self.session = session or get_session()

    def seed_schema(self):
        for entity_type, entity_data in CORE_ENTITIES.items():
            existing = self.session.query(EntityMeta).filter_by(entity_type=entity_type).first()
            if not existing:
                meta = EntityMeta(entity_type=entity_type)
                self.session.add(meta)

            for field_name, field_info in entity_data.get('fields', {}).items():
                existing_field = self.session.query(FieldMeta).filter_by(
                    entity_type=entity_type, field_name=field_name
                ).first()
                if not existing_field:
                    fm = FieldMeta(
                        entity_type=entity_type,
                        field_name=field_name,
                        data_type=field_info.get('type', 'text'),
                        properties=field_info.get('properties', {})
                    )
                    self.session.add(fm)

        self.session.commit()

    def get_schema(self):
        result = {}
        entities = self.session.query(EntityMeta).all()
        for em in entities:
            result[em.entity_type] = {
                'name': em.entity_type,
                'fields': {}
            }
            fields = self.session.query(FieldMeta).filter_by(entity_type=em.entity_type).all()
            for f in fields:
                result[em.entity_type]['fields'][f.field_name] = {
                    'name': f.field_name,
                    'type': f.data_type,
                    'properties': f.properties or {}
                }
        return result
