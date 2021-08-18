from apispecs.base.exceptions import DeserializationException
from .base import BaseDeserializationProvider
from io import TextIOBase
from collections.abc import Sequence
import yaml

class YAMLDeserializationProvider(BaseDeserializationProvider):

    def get_content_types(self) -> Sequence[str]:
        return ['text/yaml']

    def deserialize_to_dict(self, stream: TextIOBase) -> dict:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as e:
            raise DeserializationException(f'Failed to deserialize YAML: {e}')
