from apispecs.base.service.deserialization.service import DeserializeService
from apispecs.base.models.specification import Specification
from apispecs.base.service.schema.service import SchemaService
from apispecs.base.exceptions import DeserializationException
from marshmallow.exceptions import ValidationError
from io import TextIOBase

class BaseDeserializeService(DeserializeService):

    def deserialize_to_specification(self, stream: TextIOBase) -> Specification:
        fields = self.deserialize_to_dict(stream)
        schema = SchemaService().find_schema(fields)

        try:
            return schema.load(fields)
        except ValidationError as e:
            raise DeserializationException(f'Failed to validate specification: {e}')
