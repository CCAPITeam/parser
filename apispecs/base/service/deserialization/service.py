from apispecs.base.models.singleton import Singleton
from apispecs.base.models.specification import Specification
from apispecs.base.service.deserialization.provider import DeserializationProvider
from apispecs.base.exceptions import UnknownDeserializerException
from collections.abc import Sequence
from io import TextIOBase

class DeserializationService(metaclass=Singleton):
    _providers: Sequence[DeserializationProvider] = []

    def register_provider(self, provider: DeserializationProvider):
        if provider not in self._providers:
            self._providers.append(provider)

    def find_provider(self, content_type: str) -> DeserializationProvider:
        for provider in self._providers:
            if content_type in provider.get_content_types():
                return provider
        
        raise UnknownDeserializerException('The file format could not be recognized.')

    def deserialize_to_dict(self, content_type: str, stream: TextIOBase) -> dict:
        return self.find_provider(content_type).deserialize_to_dict(stream)

    def deserialize_to_specification(self, content_type: str, stream: TextIOBase) -> Specification:
        return self.find_provider(content_type).deserialize_to_specification(stream)

    def serialize_to_dict(self, content_type: str, schema_name: str, spec: Specification) -> dict:
        return self.find_provider(content_type).serialize_to_dict(spec, schema_name)
    
    def serialize_to_text(self, content_type: str, schema_name: str, spec: Specification) -> str:
        provider = self.find_provider(content_type)
        return provider.serialize_to_text(provider.serialize_to_dict(spec, schema_name))