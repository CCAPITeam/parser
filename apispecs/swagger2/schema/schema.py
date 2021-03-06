from marshmallow import Schema, fields, validate, validates, missing, post_load, validates_schema, ValidationError, INCLUDE
from apispecs.base.models import specification
from urllib.parse import urljoin

PARAMETER_LOCATIONS = ['query', 'header', 'path', 'formData', 'body']
COLLECTION_FORMATS = ['csv', 'ssv', 'tsv', 'pipes', 'multi']
SECURITY_SCHEME_TYPES = ['basic', 'apiKey', 'oauth2']
API_KEY_LOCATIONS = ['query', 'header']
OAUTH2_SECURITY_FLOWS = ['implicit', 'password', 'application', 'accessCode']
SCHEMES = ['http', 'https', 'ws', 'wss']

class ReferenceObject(Schema):
    ref = fields.Str(data_key = '$ref')

    @staticmethod
    def is_ref(data):
        return 'ref' in data
    
    @staticmethod
    def resolve_ref(root, data):
        ref = data['ref']
        paths = ref.split('/\\')

        if paths.pop(0) != '#':
            raise ValidationError('References must begin from the root (#).')
        
        for path in paths:
            try:
                data = data[path]
            except KeyError:
                raise ValidationError(f'Invalid reference {ref} found.')
        
        return data

class JSONBaseSchemaObject(Schema):
    format = fields.Str()
    collection_format = fields.Str(data_key = 'collectionFormat', validate = validate.OneOf(COLLECTION_FORMATS), default = 'csv')
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

class ExternalDocumentationObject(Schema):
    description = fields.Str()
    url = fields.Str(required = True)

class ContactObject(Schema):
    name = fields.Str()
    url = fields.Str()
    email = fields.Str()

class LicenseObject(Schema):
    name = fields.Str(required = True)
    url = fields.Str()

class InfoObject(Schema):
    title = fields.Str(required = True)
    description = fields.Str()
    terms_of_service = fields.Str(dataKey = 'termsOfService')
    contact = fields.Nested(ContactObject)
    license = fields.Nested(LicenseObject)
    version = fields.Str(required = True)

class XMLObject(Schema):
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
    properties = fields.Dict(keys = fields.Str(), values = fields.Nested('self'))
    additional_properties = fields.Nested('self', data_key = 'additionalProperties')

class ParameterObject(JSONSchemaObject):
    description = fields.Str()
    name = fields.Str() # Required
    in_location = fields.Str(data_key = 'in', validate = validate.OneOf(PARAMETER_LOCATIONS)) # Required
    required = fields.Boolean(default = False)
    schema = fields.Nested(SchemaObject)
    allow_empty_value = fields.Boolean(data_key = 'allowEmptyValue', default = False)

    @validates_schema
    def validate_ref_required(self, data, **kwargs):
        if self.is_ref(data):
            return
        
        for key in ('name', 'in_location'):
            if key not in data:
                raise ValidationError(f'`{key}` must be set.')

    @validates_schema
    def validate_required(self, data, **kwargs):
        if not self.is_ref(data) and data['in_location'] == 'path' and 'required' not in data:
            raise ValidationError('Required must be true if `in` is set to `path`.')
    
    @validates_schema
    def validate_schema(self, data, **kwargs):
        if not self.is_ref(data) and data['in_location'] == 'body' and 'schema' not in data:
            raise ValidationError('Schema must be set if `in` is set to `body`.')

    @validates_schema
    def validate_type(self, data, **kwargs):
        if not self.is_ref(data) and data['in_location'] != 'body' and 'type' not in data:
            raise ValidationError('Type must be set if `in` is not set to `body`.')

    @staticmethod
    def make_parameter(root, item):
        if ReferenceObject.is_ref(item):
            return ParameterObject.make_parameter(root, ReferenceObject.resolve_ref(root, item))
        
        parameter = specification.Parameter(
            name=item['name'],
            description=item.get('description', ''),
            location=item['in_location'],
            required=item.get('required', False),
            type=item.get('type', ''),
            format=item.get('format', ''),
            default_value=item.get('default_value', ''),
            collection_format=item.get('collection_format', '')
        )

        return parameter

class HeaderObject(JSONSchemaObject):
    description = fields.Str()

class ResponseObject(ReferenceObject):
    description = fields.Str()
    schema = fields.Nested(SchemaObject)
    headers = fields.Dict(keys = fields.Str(), values = fields.Nested(HeaderObject))
    examples = fields.Dict(keys = fields.Str(), values = fields.Dict(keys = fields.Str(), values = fields.Str()))

    @validates_schema
    def validate_ref_required(self, data, **kwargs):
        if self.is_ref(data):
            return
        
        if 'description' not in data:
            raise ValidationError('Description must be set.')

class OperationObject(Schema):
    tags = fields.List(fields.Str)
    summary = fields.Str()
    description = fields.Str()
    external_docs = fields.Nested(ExternalDocumentationObject, data_key = 'externalDocs')
    operation_id = fields.Str(data_key = 'operationId')
    consumes = fields.List(fields.Str)
    produces = fields.List(fields.Str)
    parameters = fields.List(fields.Nested(ParameterObject))
    responses = fields.Dict(keys=fields.Str(), values=fields.Nested(ResponseObject))
    schemes = fields.List(fields.Str)
    deprecated = fields.Boolean(default = False)
    security = fields.List(fields.Dict(keys=fields.Str(), values=fields.List(fields.Str))) 

    @staticmethod
    def make_method(root, type, item):
        method = specification.Method(
            method=type,
            operation_id=item.get('operation_id', ''),
            summary=item.get('summary', ''),
            description=item.get('description', ''),
            deprecated=item.get('deprecated', False),
            parameters=[ParameterObject.make_parameter(root, parameter) for parameter in item.get('parameters', [])]
        )

        return method

class PathItemObject(ReferenceObject):
    get = fields.Nested(OperationObject)
    put = fields.Nested(OperationObject)
    post = fields.Nested(OperationObject)
    delete = fields.Nested(OperationObject)
    options = fields.Nested(OperationObject)
    head = fields.Nested(OperationObject)
    patch = fields.Nested(OperationObject)
    parameters = fields.List(fields.Nested(ParameterObject))
    
    @staticmethod
    def make_endpoint(root, url, item):
        if ReferenceObject.is_ref(item):
            return PathItemObject.make_endpoint(root, url, ReferenceObject.resolve_ref(root, item))

        types = ('get', 'put', 'post', 'delete', 'options', 'head', 'patch')

        endpoint = specification.Endpoint(
            url=url,
            parameters=[ParameterObject.make_parameter(root, parameter) for parameter in item.get('parameters', [])],
            methods=[OperationObject.make_method(root, method, item[method]) for method in types if method in item]
        )

        return endpoint

class SecuritySchemeObject(Schema):
    type = fields.Str(validate = validate.OneOf(SECURITY_SCHEME_TYPES), required = True)
    description = fields.Str()
    name = fields.Str()
    in_location = fields.Str(data_key = 'in', validate = validate.OneOf(API_KEY_LOCATIONS))
    flow = fields.Str(validate = validate.OneOf(OAUTH2_SECURITY_FLOWS))
    authorization_url = fields.Str(data_key = 'authorizationUrl')
    token_url = fields.Str(data_key = 'tokenUrl')
    scopes = fields.Dict(keys = fields.Str(), values = fields.Str())

    @validates_schema
    def validate_name(self, data, **kwargs):
        if data['type'] == 'apiKey' and 'name' not in data:
            raise ValidationError('Name must be set when using API key authentication.')
    
    @validates_schema
    def validate_in_location(self, data, **kwargs):
        if data['type'] == 'apiKey' and 'in_location' not in data:
            raise ValidationError('In location must be set when using API key authentication.')

    @validates_schema
    def validate_authorization_url(self, data, **kwargs):
        if data['type'] == 'oauth2' and data['flow'] in ['implicit', 'accessCode'] and 'authorization_url' not in data:
            raise ValidationError('Authorization URL must be set when using OAuth2 authentication.')

    @validates_schema
    def validate_token_url(self, data, **kwargs):
        if data['type'] == 'oauth2' and data['flow'] in ['password', 'application', 'accessCode'] and 'token_url' not in data:
            raise ValidationError('Token URL must be set when using OAuth2 authentication.')

    @validates_schema
    def validate_scopes(self, data, **kwargs):
        if data['type'] == 'oauth2' and 'scopes' not in data:
            raise ValidationError('Scopes must be set when using OAuth2 authentication.')

class TagObject(Schema):
    name = fields.Str(required = True)
    description = fields.Str()
    external_docs = fields.Nested(ExternalDocumentationObject, data_key = 'externalDocs')

# https://github.com/OAI/OpenAPI-Specification/blob/main/versions/2.0.md#swagger-object
class Swagger2Schema(Schema):
    swagger = fields.Str(required = True)
    info = fields.Nested(InfoObject, required = True)
    host = fields.Str()
    base_path = fields.Str(data_key = 'basePath')
    schemes = fields.List(fields.Str)
    consumes = fields.List(fields.Str)
    produces = fields.List(fields.Str)
    paths = fields.Dict(keys=fields.Str(), values=fields.Nested(PathItemObject), required = True)
    definitions = fields.Dict(keys=fields.Str(), values=fields.Nested(SchemaObject))
    parameters = fields.Dict(keys=fields.Str(), values=fields.Nested(ParameterObject))
    responses = fields.Dict(keys=fields.Str(), values=fields.Nested(ResponseObject))
    security_definitions = fields.Dict(data_key = 'securityDefinitions', keys=fields.Str(), values=fields.Nested(SecuritySchemeObject))
    security = fields.List(fields.Dict(keys=fields.Str(), values=fields.List(fields.Str)))
    tags = fields.List(fields.Nested(TagObject))
    external_docs = fields.Nested(ExternalDocumentationObject, data_key = 'externalDocs')

    @post_load
    def make_schema(self, data, **kwargs):
        info = data['info']
        license = info.get('license', {})
        license_name = license.get('name', '')
        license_url = license.get('url', '')
        base_url = urljoin(data.get('host'), data.get('base_path'))

        spec = specification.Specification(
            title=info['title'],
            description=info['description'],
            license_name=license_name,
            license_url=license_url,
            version=info['version'],
            base_url=base_url,
            endpoints=[PathItemObject.make_endpoint(data, url, endpoint) for url, endpoint in data['paths'].items()]
        )

        return spec
