from marshmallow import Schema
from apispecs.base.service.schema.provider import SchemaProvider
from apispecs.openapi3.schema.schema import OpenAPI3Schema

class OpenAPI3SchemaProvider(SchemaProvider):

    def is_schema_adequate(self, fields: dict) -> bool:
        return self.find_major_version(fields.get('openapi')) == '3'

    def get_schema(self) -> Schema:
        return OpenAPI3Schema()
