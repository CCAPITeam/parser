from apispecs.base.models.specification import Specification
from apispecs.base.models.singleton import SingletonABCMeta
from abc import ABC, abstractmethod
from io import TextIOBase
from collections.abc import Sequence

class DeserializationProvider(metaclass=SingletonABCMeta):

    @abstractmethod
    def get_content_types(self) -> Sequence[str]:
        pass

    @abstractmethod
    def deserialize_to_dict(self, stream: TextIOBase) -> dict:
        pass

    @abstractmethod
    def deserialize_to_specification(self, stream: TextIOBase) -> Specification:
        pass

    @abstractmethod
    def serialize_to_dict(self, spec: Specification, schema_name: str) -> dict:
        pass

    @abstractmethod
    def serialize_to_text(self, spec: dict) -> str:
        pass

