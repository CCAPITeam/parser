from marshmallow import Schema, fields, validate, validates, missing, post_load, pre_dump, post_dump, validates_schema, ValidationError, INCLUDE
from apispecs.base.models import specification
from apispecs.base.globals import METHOD_TYPES
from apispecs.openapi3.serializer import OpenAPI3Serializer

PARAMETER_LOCATIONS = ['query', 'header', 'path', 'cookie']
SECURITY_SCHEME_TYPES = ['apiKey', 'http', 'oauth2' , 'openIdConnect']
API_KEY_LOCATIONS = ['query', 'header', 'cookie']
OAUTH2_SECURITY_FLOWS = ['implicit', 'password', 'application', 'accessCode']
SCHEMES = ['http', 'https', 'ws', 'wss']

DEFAULT_STYLES_BY_TYPE = {'query': 'form', 'path': 'simple', 'header': 'simple', 'cookie': 'form'}
FORMAT_EQUIVALENTS_TO_SWAGGER = {'form': 'csv', 'simple': 'csv', 'spaceDelimited': 'ssv', 'pipeDelimited': 'pipes'}
SECURITY_FLOW_EQUIVALENTS_TO_SWAGGER = {'clientCredentials': 'application', 'authorizationCode': 'accessCode'}

class BaseSchema(Schema):

    @post_dump
    def remove_empty_values(self, data, **kwargs):
        return {
            key: value for key, value in data.items()
            if value not in (None, '', [], {})
        }

class ReferenceObject(BaseSchema):
    ref = fields.Str(data_key = '$ref')

    @staticmethod
    def is_ref(data):
        return 'ref' in data
    
    @staticmethod
    def resolve_ref(root, data):
        ref = data['ref']
        paths = ref.split('/')

        if paths.pop(0) != '#':
            raise ValidationError('References must begin from the root (#).')
        
        current = root

        for path in paths:
            try:
                current = current[path]
            except KeyError:
                raise ValidationError(f'Invalid reference {ref} found.')

        return current, path

class JSONBaseSchemaObject(BaseSchema):
    format = fields.Str()
    default = fields.Raw()
    maximum = fields.Number()
    exclusive_maximum = fields.Boolean(data_key = 'exclusiveMaximum')
    minimum = fields.Number()
    exclusive_minimum = fields.Boolean(data_key = 'exclusiveMinimum')
    max_length = fields.Number(data_key = 'maxLength')
    min_length = fields.Number(data_key = 'minLength')
    pattern = fields.Str()
    max_items = fields.Number(data_key = 'maxItems')
    min_items = fields.Number(data_key = 'minItems')
    unique_items = fields.Boolean(data_key = 'uniqueItems')
    enum = fields.List(fields.Str)
    multiple_of = fields.Number(data_key = 'multipleOf')

    class Meta:
        unknown = INCLUDE

class ItemsObject(JSONBaseSchemaObject, ReferenceObject):
    type = fields.Str()

class JSONSchemaObject(JSONBaseSchemaObject, ReferenceObject):
    type = fields.Str()
    items = fields.Nested(ItemsObject)

    @validates_schema
    def validate_items(self, data, **kwargs):
        if not self.is_ref(data) and data.get('type') == 'array' and 'items' not in data:
            raise ValidationError('Items must be set if `in` is not set to `body`.')

class ExternalDocumentationObject(BaseSchema):
    description = fields.Str()
    url = fields.Str(required = True)

class ContactObject(BaseSchema):
    name = fields.Str()
    url = fields.Str()
    email = fields.Str()

class LicenseObject(BaseSchema):
    name = fields.Str(required = True)
    url = fields.Str()

class InfoObject(BaseSchema):
    title = fields.Str(required = True)
    description = fields.Str()
    terms_of_service = fields.Str(data_key = 'termsOfService')
    contact = fields.Nested(ContactObject)
    license = fields.Nested(LicenseObject)
    version = fields.Str(required = True)

class XMLObject(BaseSchema):
    name = fields.Str()
    namespace = fields.Str()
    prefix = fields.Str()
    attribute = fields.Boolean(required = False)
    wrapped = fields.Boolean(required = False)

class SchemaObject(JSONSchemaObject):
    title = fields.Str()
    description = fields.Str()
    discriminator = fields.Str()
    read_only = fields.Boolean(data_key = 'readOnly', default = False)
    xml = fields.Nested(XMLObject)
    external_docs = fields.Nested(ExternalDocumentationObject, data_key='externalDocs')
    example = fields.Raw()
    required = fields.List(fields.Str)
    properties = fields.Dict(keys = fields.Str(), values = fields.Nested('self'))
    additional_properties = fields.Nested('self', data_key = 'additionalProperties')

    @staticmethod
    def make_schema(root, item, name=None, key=None, visited_nodes=None):
        if item is None:
            return None
        
        if visited_nodes is None:
            visited_nodes = {}

        if ReferenceObject.is_ref(item):
            ref, name = ReferenceObject.resolve_ref(root, item)

            if (name or key) and (name, key) in visited_nodes:
                return visited_nodes[(name, key)]

            return SchemaObject.make_schema(root, ref, name, key, visited_nodes)

        description = item.get('description')

        if description is None:
            description = item.get('title', '')

        schema = specification.ResponseProperty(
            name=name,
            key=key,
            description=description,
            type=item.get('type', ''),
            format=item.get('format', ''),
            default_value=item.get('default', ''),
            required=item.get('required', []),
            enums=item.get('enum', []),
            properties=None,
            items=None
        )

        visited_nodes[(name, key)] = schema

        schema.properties = [SchemaObject.make_schema(root, property_item, key=property_key, visited_nodes=visited_nodes) for property_key, property_item in item.get('properties', {}).items()]
        schema.items = SchemaObject.make_schema(root, item.get('items'), visited_nodes=visited_nodes)
        return schema

class ParameterObject(JSONSchemaObject):
    description = fields.Str()
    name = fields.Str() # Required
    in_location = fields.Str(data_key = 'in', validate = validate.OneOf(PARAMETER_LOCATIONS)) # Required
    required = fields.Boolean(default = False)
    deprecated = fields.Boolean(default = False)
    allow_empty_value = fields.Boolean(data_key = 'allowEmptyValue', default = False)
    style = fields.Str()
    explode = fields.Boolean()
    allow_reserved = fields.Boolean(data_key = 'alowReserved', default = False)
    example = fields.Raw()

    @validates_schema
    def validate_ref_required(self, data, **kwargs):
        if self.is_ref(data):
            return
        
        if data.get('in_location') == 'path' and 'required' not in data:
            raise ValidationError('Required must be true if `in` is set to `path`.')

    @staticmethod
    def get_collection_format(item):
        type = item.get('type', '')

        if not type:
            return None

        style = item.get('style', DEFAULT_STYLES_BY_TYPE.get(type, 'simple'))
        collection_format = FORMAT_EQUIVALENTS_TO_SWAGGER.get(style, style)
        return collection_format

    @staticmethod
    def make_parameter(root, item, title=None):
        if ReferenceObject.is_ref(item):
            ref, name = ReferenceObject.resolve_ref(root, item)
            return ParameterObject.make_parameter(root, ref, name)
        
        parameter = specification.Parameter(
            title=title,
            name=item.get('name', ''),
            description=item.get('description', ''),
            location=item.get('in_location', 'header'),
            required=item.get('required', False),
            type=item.get('type', ''),
            format=item.get('format', ''),
            default_value='',
            collection_format=ParameterObject.get_collection_format(item),
            items=SchemaObject.make_schema(root, item.get('items'))
        )

        return parameter

class HeaderObject(ParameterObject):

    @staticmethod
    def make_header(root, name, item):
        if ReferenceObject.is_ref(item):
            ref, name = ReferenceObject.resolve_ref(root, item)
            return HeaderObject.make_header(root, ref, name)

        schema = item['schema']

        header = specification.Header(
            name=name,
            description=item.get('description', ''),
            type=schema.get('type', ''),
            format=schema.get('format', ''),
            default_value='',
            collection_format=ParameterObject.get_collection_format(schema),
            items=SchemaObject.make_schema(root, schema.get('items'))
        )

        return header

class MediaTypeObject(BaseSchema):
    schema = fields.Nested(SchemaObject)
    example = fields.Raw()
    examples = fields.Dict(keys = fields.Str(), values = fields.Dict(keys = fields.Str(), values = fields.Str()))

class ResponseObject(ReferenceObject):
    description = fields.Str()
    headers = fields.Dict(keys = fields.Str(), values = fields.Nested(HeaderObject))
    content = fields.Dict(keys = fields.Str(), values = fields.Nested(MediaTypeObject))

    @validates_schema
    def validate_ref_required(self, data, **kwargs):
        if self.is_ref(data):
            return
        
        if 'description' not in data:
            raise ValidationError('Description must be set.')

    @staticmethod
    def make_response(root, item, name=None):
        if ReferenceObject.is_ref(item):
            ref, name = ReferenceObject.resolve_ref(root, item)
            return ResponseObject.make_response(root, ref, name)

        # Choose the first available schema
        try:
            schema = next(iter(item['content'].values()))
        except:
            schema = None
        
        schema = SchemaObject.make_schema(root, schema)
        response = specification.Response(
            name=name,
            description=item.get('description', ''),
            schema=schema,
            headers=[HeaderObject.make_header(root, name, item) for name, item in item.get('headers', {}).items()],
            examples=[]
        )

        return response

class RequestBodyObject(ReferenceObject):
    description = fields.Str()
    content = fields.Dict(keys = fields.Str(), values = fields.Nested(MediaTypeObject))
    required = fields.Boolean(default = False)

    @validates_schema
    def validate_content(self, data, **kwargs):
        if not self.is_ref(data) and 'content' not in data:
            raise ValidationError('Content must be provided for each request body.')

    @staticmethod
    def make_request_body(root, item, title=None):
        if ReferenceObject.is_ref(item):
            ref, name = ReferenceObject.resolve_ref(root, item)
            return RequestBodyObject.make_request_body(root, ref, name)

        schema = next(iter(item['content'].values()))

        parameter = specification.Parameter(
            title=title,
            name='body',
            description=item.get('description', ''),
            location='body',
            required=item.get('required', False),
            type=schema.get('type', ''),
            format=schema.get('format', ''),
            default_value='',
            collection_format=ParameterObject.get_collection_format(schema),
            items=SchemaObject.make_schema(root, schema.get('items'))
        )

        return parameter

class OperationObject(BaseSchema):
    tags = fields.List(fields.Str)
    summary = fields.Str()
    description = fields.Str()
    external_docs = fields.Nested(ExternalDocumentationObject, data_key = 'externalDocs')
    operation_id = fields.Str(data_key = 'operationId')
    parameters = fields.List(fields.Nested(ParameterObject))
    request_body = fields.Nested(RequestBodyObject, data_key = 'requestBody')
    responses = fields.Dict(keys=fields.Str(), values=fields.Nested(ResponseObject))
    deprecated = fields.Boolean(default = False)
    security = fields.List(fields.Dict(keys=fields.Str(), values=fields.List(fields.Str))) 

    @staticmethod
    def make_method(root, type, item):
        parameters = [ParameterObject.make_parameter(root, parameter) for parameter in item.get('parameters', [])]
        request_body = item.get('request_body')

        if request_body:
            parameters.append(RequestBodyObject.make_request_body(root, request_body))

        method = specification.Method(
            method=type,
            operation_id=item.get('operation_id', ''),
            summary=item.get('summary', ''),
            description=item.get('description', ''),
            deprecated=item.get('deprecated', False),
            parameters=parameters,
            responses={code: ResponseObject.make_response(root, response) for code, response in item['responses'].items()},
            security_requirements=[specification.SecurityRequirement(name, scopes) for security in item.get('security', []) for name, scopes in security.items()]
        )

        return method

    @validates_schema
    def validate_empty_response(self, data, **kwargs):
        if 'responses' not in data:
            raise ValidationError('Responses must be provided for each operation.')
        if not data['responses']:
            raise ValidationError('At least one response must be provided for each operation.')

class ServerVariableObject(BaseSchema):
    enum = fields.List(fields.Str)
    default = fields.Str(required = True)
    description = fields.Str()

class ServerObject(BaseSchema):
    url = fields.Str(required = True)
    description = fields.Str()
    variables = fields.Dict(keys=fields.Str(), values=fields.Nested(ServerVariableObject))

class PathItemObject(ReferenceObject):
    summary = fields.Str()
    description = fields.Str()
    get = fields.Nested(OperationObject)
    put = fields.Nested(OperationObject)
    post = fields.Nested(OperationObject)
    delete = fields.Nested(OperationObject)
    options = fields.Nested(OperationObject)
    head = fields.Nested(OperationObject)
    patch = fields.Nested(OperationObject)
    trace = fields.Nested(OperationObject)
    parameters = fields.List(fields.Nested(ParameterObject))
    servers = fields.List(fields.Nested(ServerObject))
    
    @staticmethod
    def make_endpoint(root, url, item):
        if ReferenceObject.is_ref(item):
            ref, name = ReferenceObject.resolve_ref(root, item)
            return PathItemObject.make_endpoint(root, url, ref)

        endpoint = specification.Endpoint(
            url=url,
            parameters=[ParameterObject.make_parameter(root, parameter) for parameter in item.get('parameters', [])],
            methods=[OperationObject.make_method(root, method, item[method]) for method in METHOD_TYPES if method in item]
        )

        return endpoint

class OAuthFlowObject(BaseSchema):
    authorization_url = fields.Str(data_key = 'authorizationUrl')
    token_url = fields.Str(data_key = 'tokenUrl')
    refresh_url = fields.Str(data_key = 'refreshUrl')
    scopes = fields.Dict(keys = fields.Str(), values = fields.Str())

class OAuthFlowsObject(BaseSchema):
    implicit = fields.Nested(OAuthFlowObject)
    password = fields.Nested(OAuthFlowObject)
    client_credentials = fields.Nested(OAuthFlowObject, data_key = 'clientCredentials')
    authorization_code = fields.Nested(OAuthFlowObject, data_key = 'authorizationCode')

class SecuritySchemeObject(BaseSchema):
    type = fields.Str(validate = validate.OneOf(SECURITY_SCHEME_TYPES), required = True)
    description = fields.Str()
    name = fields.Str()
    in_location = fields.Str(data_key = 'in', validate = validate.OneOf(API_KEY_LOCATIONS))
    scheme = fields.Str()
    bearer_format = fields.Str(data_key = 'bearerFormat')
    flows = fields.List(fields.Nested(OAuthFlowObject))
    open_id_connect_url = fields.Str(data_key = 'openIdConnectUrl')

    @validates_schema
    def validate_name(self, data, **kwargs):
        if data['type'] == 'apiKey' and 'name' not in data:
            raise ValidationError('Name must be set when using API key authentication.')
    
    @validates_schema
    def validate_in_location(self, data, **kwargs):
        if data['type'] == 'apiKey' and 'in_location' not in data:
            raise ValidationError('In location must be set when using API key authentication.')

    @validates_schema
    def validate_flows(self, data, **kwargs):
        if data['type'] == 'oauth2' and not data.get('flows'):
            raise ValidationError('Flows must be set when using OAuth2 authentication.')

    @validates_schema
    def validate_openid_connect(self, data, **kwargs):
        if data['type'] == 'openIdConnect' and 'openIdConnectUrl' not in data:
            raise ValidationError('OpenID connection URL must be set when using OpenID authentication.')

    @staticmethod
    def make_scheme(root, title, item):
        try:
            flow, oauth = next(iter(item['flows'].items()))
            flow = SECURITY_FLOW_EQUIVALENTS_TO_SWAGGER.get(flow, flow)
        except:
            flow, oauth = '', {}

        type = item['type']

        # In our specification standard, HTTP is named Basic
        if type == 'http':
            type = 'basic'

        scheme = specification.SecurityScheme(
            title=title,
            name=item.get('name', ''),
            description=item.get('description', ''),
            type=type,
            location=item.get('in_location', ''),
            flow=flow,
            authorization_url=oauth.get('authorization_url', ''),
            refresh_url=oauth.get('refresh_url', ''),
            token_url=oauth.get('token_url', ''),
            scopes=[specification.OAuthScope(name, description) for name, description in oauth.get('scopes', {}).items()]
        )

        return scheme

class TagObject(BaseSchema):
    name = fields.Str(required = True)
    description = fields.Str()
    external_docs = fields.Nested(ExternalDocumentationObject, data_key = 'externalDocs')

# https://github.com/OAI/OpenAPI-Specification/blob/main/versions/2.0.md#swagger-object
class ComponentsObject(BaseSchema):
    schemas = fields.Dict(keys=fields.Str(), values=fields.Nested(SchemaObject))
    requestBodies = fields.Dict(keys=fields.Str(), values=fields.Nested(RequestBodyObject))
    securitySchemes = fields.Dict(keys=fields.Str(), values=fields.Nested(SecuritySchemeObject))
    responses = fields.Dict(keys=fields.Str(), values=fields.Nested(ResponseObject))

class OpenAPI3Schema(BaseSchema):
    openapi = fields.Str(required = True)
    info = fields.Nested(InfoObject, required = True)
    servers = fields.List(fields.Nested(ServerObject))
    paths = fields.Dict(keys=fields.Str(), values=fields.Nested(PathItemObject), required = True)
    definitions = fields.Dict(keys=fields.Str(), values=fields.Nested(SchemaObject))
    parameters = fields.Dict(keys=fields.Str(), values=fields.Nested(ParameterObject))
    responses = fields.Dict(keys=fields.Str(), values=fields.Nested(ResponseObject))
    components = fields.Nested(ComponentsObject)
    security = fields.List(fields.Dict(keys=fields.Str(), values=fields.List(fields.Str)))
    tags = fields.List(fields.Nested(TagObject))
    external_docs = fields.Nested(ExternalDocumentationObject, data_key = 'externalDocs')

    @post_load
    def make_schema(self, data, **kwargs):
        info = data['info']
        license = info.get('license', {})
        license_name = license.get('name', '')
        license_url = license.get('url', '')

        try:
            base_url = data['servers'][0]['url']
        except KeyError:
            base_url = '/'
        
        components = data.get('components', {})

        spec = specification.Specification(
            title=info['title'],
            description=info['description'],
            license_name=license_name,
            license_url=license_url,
            version=info['version'],
            base_url=base_url,
            endpoints=[PathItemObject.make_endpoint(data, url, endpoint) for url, endpoint in data['paths'].items()],
            security_schemes=[SecuritySchemeObject.make_scheme(data, title, scheme) for title, scheme in components.get('securitySchemes', {}).items()]
        )

        return spec
    
    def dump_schema(self, spec):
        return OpenAPI3Serializer(spec).serialize()
