from apispecs.base.models.singleton import Singleton
from apispecs.base.service.schema.provider import SchemaProvider
from apispecs.base.exceptions import UnknownSchemaException
from collections.abc import Sequence
from marshmallow import Schema

class SchemaService(metaclass=Singleton):
    _providers: Sequence[SchemaProvider] = []

    def register_provider(self, provider: SchemaProvider):
        if provider not in self._providers:
            self._providers.append(provider)

    def find_schema(self, fields: dict) -> Schema:
        for provider in self._providers:
            if provider.is_schema_adequate(fields):
                return provider.get_schema()

        raise UnknownSchemaException('The specification schema could not be determined.')

    def find_schema_by_name(self, name: str) -> Schema:
        for provider in self._providers:
            if provider.get_name() == name:
                return provider.get_schema()
        
        raise UnknownSchemaException('The specification schema could not be found.')