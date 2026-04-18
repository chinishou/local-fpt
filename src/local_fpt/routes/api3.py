"""
API3 JSON-RPC routes for LocalFPT.
"""
from flask import Blueprint, request, jsonify

from local_fpt.db.database import get_session
from local_fpt.services.entity_service import EntityService
from local_fpt.services.schema_service import SchemaService


api3_bp = Blueprint('api3', __name__)


def _get_entity_service():
    return EntityService(get_session())


def _fields_list_to_dict(fields_list):
    """Convert SDK field list [{"field_name":"x","value":"v"},...] to {"x":"v",...}."""
    if not fields_list or not isinstance(fields_list, list):
        return {}
    result = {}
    for item in fields_list:
        if isinstance(item, dict) and 'field_name' in item:
            result[item['field_name']] = item.get('value')
    return result


def _extract_data(params):
    """Extract entity data from params, handling both SDK and simple formats."""
    if 'data' in params and isinstance(params['data'], dict):
        return params['data']
    if 'fields' in params and isinstance(params['fields'], list):
        return _fields_list_to_dict(params['fields'])
    return params.get('data', {})


def _extract_return_fields(params):
    """Extract return_fields from params."""
    rf = params.get('return_fields')
    if rf:
        return rf
    cols = params.get('columns')
    if cols:
        return cols
    return None


@api3_bp.route('/json', methods=['POST'])
def jsonrpc():
    data = request.get_json()
    method_name = data.get('method_name')
    raw_params = data.get('params')
    if isinstance(raw_params, list):
        params = raw_params[-1] if len(raw_params) > 1 else (raw_params[0] if raw_params else {})
    else:
        params = raw_params or {}

    svc = _get_entity_service()

    try:
        if method_name == 'find_one':
            result = svc.find_one(
                params.get('type'),
                params.get('filters'),
                _extract_return_fields(params),
            )
            return jsonify({'results': result})

        elif method_name == 'find':
            if not params.get('type'):
                return jsonify({'error': 'Missing required parameter: type'}), 400
            filters = params.get('filters')
            return_fields = _extract_return_fields(params)
            paging = params.get('paging', {})
            limit = paging.get('entities_per_page') or params.get('limit', 25)
            page = paging.get('current_page') or params.get('page', 0)
            offset = params.get('offset', 0)
            if page and page > 0:
                offset = (page - 1) * limit
            order = params.get('sorts') or params.get('order')

            result = svc.find(
                params.get('type'),
                filters,
                return_fields,
                limit,
                offset,
                order,
            )
            return jsonify({'results': result})

        elif method_name == 'create':
            entity_data = _extract_data(params)
            result = svc.create(params.get('type'), entity_data)
            return jsonify({'results': result})

        elif method_name == 'update':
            entity_data = _extract_data(params)
            entity_id = params.get('id') or params.get('entity_id')
            result = svc.update(params.get('type'), entity_id, entity_data)
            return jsonify({'results': result})

        elif method_name == 'delete':
            entity_id = params.get('id') or params.get('entity_id')
            result = svc.delete(params.get('type'), entity_id)
            return jsonify({'results': result.get('success', False)})

        elif method_name == 'revive':
            entity_id = params.get('id') or params.get('entity_id')
            result = svc.revive(params.get('type'), entity_id)
            return jsonify({'results': result})

        elif method_name == 'batch':
            raw_requests = params if isinstance(params, list) else params.get('requests', [])
            results = []
            for req in raw_requests:
                req_type = req.get('request_type')
                etype = req.get('entity_type') or req.get('type')
                if req_type == 'create':
                    req_data = _extract_data(req)
                    r = svc.create(etype, req_data)
                    results.append(r)
                elif req_type == 'update':
                    req_data = _extract_data(req)
                    eid = req.get('entity_id') or req.get('id')
                    r = svc.update(etype, eid, req_data)
                    results.append(r)
                elif req_type == 'delete':
                    eid = req.get('entity_id') or req.get('id')
                    r = svc.delete(etype, eid)
                    results.append(r.get('success', False))
            return jsonify({'results': results})

        elif method_name == 'entity_types':
            return jsonify({'results': [
                'Project', 'Sequence', 'Episode', 'Shot', 'Asset',
                'Version', 'Task', 'Playlist', 'HumanUser', 'PublishedFiles',
                'Ticket',
            ]})

        elif method_name == 'info':
            return jsonify({
                'user_authentication_method': 'api_session',
                'version': [2024, 1, 0],
            })

        elif method_name in ('schema_entity_read', 'schema_read', 'schema_field_read'):
            schema_svc = SchemaService(get_session())
            schema = schema_svc.get_schema()

            if method_name == 'schema_entity_read':
                result = {}
                for etype, edata in schema.items():
                    result[etype] = {
                        'name': {'value': etype, 'editable': False},
                        'visible': {'value': True, 'editable': False},
                    }
                return jsonify({'results': result})

            elif method_name == 'schema_read':
                result = {}
                for etype, edata in schema.items():
                    fields = {}
                    for fname, fdata in edata.get('fields', {}).items():
                        fields[fname] = {
                            'data_type': {'value': fdata.get('type', 'text')},
                            'name': {'value': fname},
                            'properties': {},
                        }
                    result[etype] = fields
                return jsonify({'results': result})

            elif method_name == 'schema_field_read':
                entity_type = params.get('type')
                field_name = params.get('field_name')
                edata = schema.get(entity_type, {})
                fields = edata.get('fields', {})
                if field_name:
                    fdata = fields.get(field_name, {})
                    return jsonify({'results': {field_name: {
                        'data_type': {'value': fdata.get('type', 'text')},
                        'name': {'value': field_name},
                        'properties': {},
                    }}})
                result = {}
                for fname, fdata in fields.items():
                    result[fname] = {
                        'data_type': {'value': fdata.get('type', 'text')},
                        'name': {'value': fname},
                        'properties': {},
                    }
                return jsonify({'results': result})

        elif method_name == 'read':
            limit = params.get('paging', {}).get('entities_per_page', 25)
            current_page = params.get('paging', {}).get('current_page', 1)
            offset = (current_page - 1) * limit if current_page > 0 else 0
            order = params.get('sorts') or params.get('order')

            result = svc.find(
                params.get('type'),
                params.get('filters'),
                _extract_return_fields(params) or params.get('fields', []),
                limit,
                offset,
                order,
            )
            return jsonify({
                'entities': result,
                'paging_info': {
                    'has_next_page': len(result) == limit,
                    'current_page': current_page,
                }
            })

        else:
            return jsonify({'error': f'Unknown method: {method_name}'}), 400

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
