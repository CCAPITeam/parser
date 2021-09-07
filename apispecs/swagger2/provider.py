from marshmallow import Schema
from apispecs.base.service.schema.provider import SchemaProvider
from apispecs.swagger2.schema.schema import Swagger2Schema

class Swagger2SchemaProvider(SchemaProvider):

    def is_schema_adequate(self, fields: dict) -> bool:
        return self.find_major_version(fields.get('swagger')) == '2'

    def get_name(self) -> str:
        return 'swagger2'

    def get_schema(self) -> Schema:
        return Swagger2Schema()
