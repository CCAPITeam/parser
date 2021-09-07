from apispecs.base.globals import METHOD_TYPES
import json

EMPTY_FIELDS = [None, '', (), [], {}]
SWAGGER_FORMATS_TO_STYLE = {
    'csv': ('form', False),
    'ssv': ('spaceDelimited', False),
    'pipes': ('pipeDelimited', False),
    'multi': ('form', True),
    'matrix': ('matrix', False),
    'label': ('label', False),
    'deepObject': ('deepObject', False)
}

def clean_empty(d):
    if isinstance(d, dict):
        return {
            k: v 
            for k, v in ((k, clean_empty(v)) for k, v in d.items())
            if v not in EMPTY_FIELDS
        }

    if isinstance(d, list):
        return [v for v in map(clean_empty, d) if v not in EMPTY_FIELDS]

    return d

def sanitize_ref(ref):
    return json.dumps(ref).strip('"')

class OpenAPI3Serializer(object):

    def __init__(self, spec):
        self.spec = spec
        self.schemas = {}
        self.responses = {}
        self.parameters = {}
        self.request_bodies = {}
    
    def sanitize_ref(self, ref):
        return json.dumps(ref)

    def find_style(self, collection_format):
        """
        Converts Swagger 2.0-style collection formats to styles.
        """
        return SWAGGER_FORMATS_TO_STYLE.get(collection_format, (None, None))

    def serialize_parameter(self, parameter, ref=True):
        if parameter is None:
            return None

        if ref and parameter.title:
            self.parameters[parameter.title] = parameter
            return {'$ref': f'#/components/parameters/{sanitize_ref(parameter.title)}'}

        style, explode = self.find_style(parameter.collection_format)

        serialized_parameter = {
            'name': parameter.name,
            'in': parameter.location,
            'description': parameter.description,
            'type': parameter.type,
            'format': parameter.format,
            'style': style,
            'items': self.serialize_schema(parameter.items)
        }

        if explode:
            serialized_parameter['explode'] = True

        if parameter.required:
            serialized_parameter['required'] = True

        return serialized_parameter

    def serialize_schema(self, schema):
        return None

    def serialize_request_body(self, request_body, ref=True):
        if request_body is None:
            return None
        
        if ref and request_body.title:
            self.request_bodies[request_body.title] = request_body
            return {'$ref': f'#/components/requestBodies/{sanitize_ref(request_body.title)}'}

        style, explode = self.find_style(request_body.collection_format)

        content = {
            'type': request_body.type,
            'format': request_body.format,
            'style': style,
            'items': self.serialize_schema(request_body.items)
        }

        if explode:
            content['explode'] = True

        serialized_body = {
            'description': request_body.description,
            'content': {
                'application/json': content
            }
        }

        if request_body.required:
            serialized_body['required'] = True
        
        return serialized_body

    def serialize_endpoint(self, endpoint):
        serialized = {
            'parameters': [self.serialize_parameter(parameter) for parameter in endpoint.parameters if parameter.location != 'body']
        }

        for method in endpoint.methods:
            request_body = next((parameter for parameter in method.parameters if parameter.location == 'body'), None)
            serialized_method = {
                'summary': method.summary,
                'description': method.description,
                'operationId': method.operation_id,
                'parameters': [self.serialize_parameter(parameter) for parameter in method.parameters if parameter.location != 'body'],
                'requestBody': self.serialize_request_body(request_body),
                'responses': {}, # to do
                'security': [] # to do
            }

            if method.deprecated:
                serialized_method['deprecated'] = True
            
            serialized[method.method] = serialized_method
        
        return serialized

    def serialize(self):
        return clean_empty({
            'openapi': '3.1.0',
            'info': {
                'title': self.spec.title, 'description': self.spec.description, 'version': self.spec.version,
                'license': {
                    'name': self.spec.license_name, 'url': self.spec.license_url
                }
            },
            'servers': [{'url': self.spec.base_url}],
            'paths': {endpoint.url: self.serialize_endpoint(endpoint) for endpoint in self.spec.endpoints},
            'components': {
                'schemas': {title: self.serialize_schema(schema, ref=False) for title, schema in self.schemas.items()},
                'responses': {title: self.serialize_response(response, ref=False) for title, response in self.responses.items()},
                'parameters': {title: self.serialize_parameter(parameter, ref=False) for title, parameter in self.parameters.items()},
                'requestBodies': {title: self.serialize_request_body(request_body, ref=False) for title, request_body in self.request_bodies.items()}
            },
            'security': [] # to do
        })