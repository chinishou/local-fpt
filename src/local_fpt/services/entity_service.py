"""
Entity service for CRUD operations - Synchronous.
"""
from datetime import datetime
import json

from local_fpt.db.models import EntityRecord, FieldValue, EventLogEntry
from local_fpt.db.database import get_session


class EntityService:
    def __init__(self, session=None):
        self.session = session or get_session()

    def find_one(self, entity_type, filters=None, fields=None):
        results = self._find(entity_type, filters, fields, limit=1)
        return results[0] if results else None

    def find(self, entity_type, filters=None, fields=None, limit=25, offset=0, order=None):
        return self._find(entity_type, filters, fields, limit, offset, order)

    def _find(self, entity_type, filters, fields, limit=25, offset=0, order=None):
        from sqlalchemy import and_, or_, exists
        from sqlalchemy.orm import aliased

        query = self.session.query(EntityRecord).filter_by(
            entity_type=entity_type, retired=False
        )

        if filters:
            if isinstance(filters, dict) and 'conditions' in filters:
                logical_op = filters.get('logical_operator', 'and')
                filter_conditions = filters.get('conditions', [])
                if logical_op == 'or' and len(filter_conditions) > 1:
                    conds = []
                    for f in filter_conditions:
                        f = self._normalize_condition(f)
                        cond = self._build_field_condition(f[0], f[1], f[2])
                        if cond is not None:
                            conds.append(cond)
                    if conds:
                        query = query.filter(or_(*conds))
                else:
                    for f in filter_conditions:
                        f = self._normalize_condition(f)
                        cond = self._build_field_condition(f[0], f[1], f[2])
                        if cond is not None:
                            query = query.filter(cond)
            elif isinstance(filters, list):
                for f in filters:
                    f = self._normalize_condition(f)
                    cond = self._build_field_condition(f[0], f[1], f[2])
                    if cond is not None:
                        query = query.filter(cond)

        if order:
            for o in order:
                fname = o.get('field_name', 'id')
                direction = o.get('direction', 'asc')
                if fname == 'id':
                    query = query.order_by(EntityRecord.id.desc() if direction == 'desc' else EntityRecord.id.asc())
                else:
                    fv_o = aliased(FieldValue)
                    query = query.outerjoin(fv_o, and_(
                        fv_o.record_id == EntityRecord.id,
                        fv_o.field_name == fname,
                    ))
                    query = query.order_by(fv_o.value.desc() if direction == 'desc' else fv_o.value.asc())
        else:
            query = query.order_by(EntityRecord.id)

        if offset:
            query = query.offset(offset)

        if limit:
            query = query.limit(limit)

        records = query.all()
        return [r.to_dict(fields) for r in records]

    @staticmethod
    def _normalize_condition(f):
        """Convert SDK dict conditions {path,relation,values} to [field,op,value] lists."""
        if isinstance(f, dict) and 'path' in f:
            field = f['path']
            op = f['relation']
            values = f.get('values', [])
            # in/not_in expect a list value — preserve it regardless of element count.
            # All other operators take a single value — unpack single-element lists.
            if op in ('in', 'not_in'):
                value = values
            else:
                value = values[0] if len(values) == 1 else values
            return [field, op, value]
        return f

    def _build_field_condition(self, field, op, value):
        import json as _json
        from sqlalchemy import exists, select, func

        if field == 'id':
            if op == 'is':
                return EntityRecord.id == value
            elif op == 'is_not':
                return EntityRecord.id != value
            elif op == 'in':
                return EntityRecord.id.in_(value)
            elif op == 'not_in':
                return ~EntityRecord.id.in_(value)
            return None

        # Base correlated subquery — matches the specific field row for this entity.
        # Use non-aliased FieldValue so SQLAlchemy applies JSON type bind-param processing.
        # .correlate(EntityRecord) prevents entity_records from appearing in the subquery FROM.
        def _base():
            return (
                select(FieldValue.id)
                .where(FieldValue.record_id == EntityRecord.id)
                .where(FieldValue.field_name == field)
                .correlate(EntityRecord)
            )

        # SQLite stores all JSON values as JSON-encoded text (strings get surrounding quotes).
        # For equality operators we must encode the comparison value the same way.
        # For LIKE operators we use json_extract($, '$') to get the unquoted string.
        jv = _json.dumps(value, sort_keys=True)           # e.g. '"hello"' or '{"id":...,"type":...}'
        val_list = value if isinstance(value, list) else [value]
        jv_list = [_json.dumps(v, sort_keys=True) for v in val_list]
        jx = func.json_extract(FieldValue.value, '$')   # strips JSON quotes for LIKE ops

        if op == 'is':
            return exists(_base().where(FieldValue.value == jv))
        elif op == 'is_not':
            return exists(_base().where(FieldValue.value != jv))
        elif op == 'contains':
            return exists(_base().where(jx.contains(value)))
        elif op == 'not_contains':
            return exists(_base().where(~jx.contains(value)))
        elif op == 'starts_with':
            return exists(_base().where(jx.startswith(value)))
        elif op == 'ends_with':
            return exists(_base().where(jx.endswith(value)))
        elif op == 'in':
            return exists(_base().where(FieldValue.value.in_(jv_list)))
        elif op == 'not_in':
            return exists(_base().where(~FieldValue.value.in_(jv_list)))
        elif op == 'is_null':
            return ~exists(_base())
        elif op == 'not_null':
            return exists(_base())
        return None

    def _apply_filter(self, query, filter_item):
        if isinstance(filter_item, list) and len(filter_item) == 3:
            field, op, value = filter_item
            cond = self._build_field_condition(field, op, value)
            if cond is not None:
                return query.filter(cond)
            return query
        elif isinstance(filter_item, list) and filter_item[0] in ('and', 'or'):
            logical_op = filter_item[0]
            conditions = []
            for f in filter_item[1:]:
                cond = self._build_field_condition(f[0], f[1], f[2])
                if cond is not None:
                    conditions.append(cond)
            if logical_op == 'and':
                return query.filter(*conditions) if conditions else query
            else:
                from sqlalchemy import or_
                return query.filter(or_(*conditions)) if conditions else query
        return query

    def create(self, entity_type, data):
        record = EntityRecord(entity_type=entity_type)
        self.session.add(record)
        self.session.flush()

        for field_name, value in data.items():
            if field_name in ('type', 'id'):
                continue
            if isinstance(value, dict) and 'type' in value and 'id' in value:
                value = dict(sorted(value.items()))
            fv = FieldValue(record_id=record.id, field_name=field_name, value=value)
            self.session.add(fv)

        self.session.commit()
        return record.to_dict()

    def update(self, entity_type, entity_id, data):
        record = self.session.query(EntityRecord).filter_by(
            id=entity_id, entity_type=entity_type, retired=False
        ).first()

        if not record:
            return None

        for fv in record.field_values:
            if fv.field_name in data:
                new_val = data[fv.field_name]
                if isinstance(new_val, dict) and 'type' in new_val and 'id' in new_val:
                    new_val = dict(sorted(new_val.items()))
                self._log_event(entity_type, entity_id, 'update', fv.field_name, fv.value, new_val)
                fv.value = new_val

        for field_name, value in data.items():
            if field_name in ('type', 'id'):
                continue
            if isinstance(value, dict) and 'type' in value and 'id' in value:
                value = dict(sorted(value.items()))
            existing = next((fv for fv in record.field_values if fv.field_name == field_name), None)
            if not existing:
                fv = FieldValue(record_id=record.id, field_name=field_name, value=value)
                self.session.add(fv)

        record.updated_at = datetime.utcnow()
        self.session.commit()
        return record.to_dict()

    def delete(self, entity_type, entity_id):
        record = self.session.query(EntityRecord).filter_by(
            id=entity_id, entity_type=entity_type
        ).first()

        if not record:
            raise ValueError(f"No entity of type {entity_type} with id {entity_id}")

        record.retired = True
        record.updated_at = datetime.utcnow()
        self._log_event(entity_type, entity_id, 'delete', None, None, None)
        self.session.commit()
        return {'success': True}

    def revive(self, entity_type, entity_id):
        record = self.session.query(EntityRecord).filter_by(
            id=entity_id, entity_type=entity_type, retired=True
        ).first()

        if not record:
            return False

        record.retired = False
        record.updated_at = datetime.utcnow()
        self._log_event(entity_type, entity_id, 'revive', None, None, None)
        self.session.commit()
        return True

    def _log_event(self, entity_type, entity_id, event_type, attribute_name, old_value, new_value):
        entry = EventLogEntry(
            entity_type=entity_type,
            entity_id=entity_id,
            event_type=event_type,
            attribute_name=attribute_name,
            old_value=old_value,
            new_value=new_value,
        )
        self.session.add(entry)

    def batch(self, operations):
        results = []
        for op in operations:
            if op.get('request_type') == 'create':
                result = self.create(op['entity_type'], op['data'])
                results.append({'data': result})
            elif op.get('request_type') == 'update':
                result = self.update(op['entity_type'], op['id'], op.get('data', {}))
                results.append({'data': result})
            elif op.get('request_type') == 'delete':
                result = self.delete(op['entity_type'], op['id'])
                results.append(result)
        return results
