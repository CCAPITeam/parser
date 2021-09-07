from apispecs.base.service.deserialization.provider import DeserializationProvider
from apispecs.base.models.specification import Specification
from apispecs.base.service.schema.service import SchemaService
from apispecs.base.exceptions import DeserializationException
from marshmallow.exceptions import ValidationError
from io import TextIOBase

class BaseDeserializationProvider(DeserializationProvider):

    def deserialize_to_specification(self, stream: TextIOBase) -> Specification:
        fields = self.deserialize_to_dict(stream)
        schema = SchemaService().find_schema(fields)

        try:
            return schema.load(fields)
        except ValidationError as e:
            raise DeserializationException(f'Failed to validate specification: {e}')

    def serialize_to_dict(self, spec: Specification, schema_name: str) -> dict:
        schema = SchemaService().find_schema_by_name(schema_name)
        return schema.dump_schema(spec)