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
SWAGGER_FLOW_TO_SECURITY_FLOW = {'application': 'clientCredentials', 'accessCode': 'authorizationCode'}

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
        self.headers = {}
    
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
    
    def serialize_header(self, header, ref=True):
        if header is None:
            return None

        if ref and header.name:
            self.headers[header.name] = header
            return {'$ref': f'#/components/headers/{sanitize_ref(header.name)}'}

        style, explode = self.find_style(header.collection_format)

        serialized_header = {
            'description': header.description,
            'type': header.type,
            'format': header.format,
            'style': style,
            'items': self.serialize_schema(header.items)
        }

        if explode:
            serialized_header['explode'] = True

        return serialized_header

    def serialize_schema(self, schema, ref=True):
        if schema is None:
            return None

        if ref and schema.name:
            self.schemas[schema.name] = schema
            return {'$ref': f'#/components/schemas/{sanitize_ref(schema.name)}'}

        style, explode = self.find_style(schema.format)

        serialized_schema = {
            'description': schema.description,
            'type': schema.type,
            'format': schema.format,
            'style': style,
            'required': schema.required,
            'enums': schema.enums,
            'items': self.serialize_schema(schema.items)
        }

        serialized_schema['properties'] = {property.key: self.serialize_schema(property) for property in schema.properties}

        if explode:
            serialized_schema['explode'] = True

        if schema.required:
            serialized_schema['required'] = True

        return serialized_schema

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

    def serialize_response(self, response, ref=True):
        if response is None:
            return None
        
        if ref and response.name:
            self.responses[response.name] = response
            return {'$ref': f'#/components/responses/{sanitize_ref(response.name)}'}

        serialized_body = {
            'description': response.description,
            'headers': {header.name: self.serialize_header(header) for header in response.headers},
            'content': {
                'application/json': {
                    'schema': self.serialize_schema(response.schema)
                }
            }
        }

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
                'responses': {code: self.serialize_response(response) for code, response in method.responses.items()},
                'security': [{requirement.name: requirement.scopes} for requirement in method.security_requirements]
            }

            if method.deprecated:
                serialized_method['deprecated'] = True
            
            serialized[method.method] = serialized_method
        
        return serialized

    def serialize_security_scheme(self, scheme):
        flow_type = SWAGGER_FLOW_TO_SECURITY_FLOW.get(scheme.flow, scheme.flow)
        flows = {}

        if flow_type:
            flows[flow_type] = {
                'authorizationUrl': scheme.authorization_url,
                'refreshUrl': scheme.refresh_url,
                'tokenUrl': scheme.token_url,
                'scopes': {scope.name: scope.description for scope in scheme.scopes}
            }

        return {
            'type': scheme.type,
            'description': scheme.description,
            'name': scheme.name,
            'in': scheme.location,
            'flows': flows
        }

    def serialize_components(self, components, serializer):
        serialized = {}

        while len(serialized) != len(components):
            for title, component in list(components.items()):
                if title not in serialized:
                    serialized[title] = serializer(component, ref=False)

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
                'schemas': self.serialize_components(self.schemas, self.serialize_schema),
                'responses': self.serialize_components(self.responses, self.serialize_response),
                'parameters': self.serialize_components(self.parameters, self.serialize_parameter),
                'requestBodies': self.serialize_components(self.request_bodies, self.serialize_request_body),
                'headers': self.serialize_components(self.headers, self.serialize_header),
                'securitySchemes': {security.title: self.serialize_security_scheme(security) for security in self.spec.security_schemes}
            }
        })