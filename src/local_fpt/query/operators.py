"""
Query filter operators - Synchronous version.
"""
from sqlalchemy import and_, or_


def apply_filter(query, filter_item):
    if isinstance(filter_item, list) and len(filter_item) == 3:
        field, op, value = filter_item
        return _apply_single_filter(query, field, op, value)
    elif isinstance(filter_item, list) and filter_item[0] == 'and':
        conditions = [_apply_single_filter(query, f[0], f[1], f[2]) for f in filter_item[1:]]
        return query.filter(and_(*conditions))
    elif isinstance(filter_item, list) and filter_item[0] == 'or':
        conditions = [_apply_single_filter(query, f[0], f[1], f[2]) for f in filter_item[1:]]
        return query.filter(or_(*conditions))
    return query


def _apply_single_filter(query, field, op, value):
    from local_fpt.db.models import FieldValue, EntityRecord

    if op == 'is':
        return query.filter(
            EntityRecord.field_values.any(
                and_(
                    FieldValue.field_name == field,
                    FieldValue.value == value
                )
            )
        )
    elif op == 'is_not':
        return query.filter(
            EntityRecord.field_values.any(
                and_(
                    FieldValue.field_name == field,
                    FieldValue.value != value
                )
            )
        )
    elif op == 'contains':
        return query.filter(
            EntityRecord.field_values.any(
                and_(
                    FieldValue.field_name == field,
                    FieldValue.value.contains(value)
                )
            )
        )
    elif op == 'not_contains':
        return query.filter(
            EntityRecord.field_values.any(
                and_(
                    FieldValue.field_name == field,
                    ~FieldValue.value.contains(value)
                )
            )
        )
    elif op == 'starts_with':
        return query.filter(
            EntityRecord.field_values.any(
                and_(
                    FieldValue.field_name == field,
                    FieldValue.value.startswith(value)
                )
            )
        )
    elif op == 'ends_with':
        return query.filter(
            EntityRecord.field_values.any(
                and_(
                    FieldValue.field_name == field,
                    FieldValue.value.endswith(value)
                )
            )
        )
    elif op == 'in':
        return query.filter(
            EntityRecord.field_values.any(
                and_(
                    FieldValue.field_name == field,
                    FieldValue.value.in_(value)
                )
            )
        )
    elif op == 'not_in':
        return query.filter(
            EntityRecord.field_values.any(
                and_(
                    FieldValue.field_name == field,
                    ~FieldValue.value.in_(value)
                )
            )
        )
    elif op == 'is_null':
        return query.filter(
            ~EntityRecord.field_values.any(FieldValue.field_name == field)
        )
    elif op == 'not_null':
        return query.filter(
            EntityRecord.field_values.any(FieldValue.field_name == field)
        )
    return query
