from marshmallow import Schema
from abc import ABC, abstractmethod

class SchemaProvider(ABC):

    @abstractmethod
    def is_schema_adequate(self, fields: dict) -> bool:
        pass

    @abstractmethod
    def get_schema(self) -> Schema:
        pass

    def find_major_version(self, version_string: str) -> str:
        if isinstance(version_string, str):
            return version_string.split('.')[0]
