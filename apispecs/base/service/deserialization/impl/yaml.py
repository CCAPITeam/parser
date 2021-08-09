from apispecs.base.exceptions import DeserializationException
from .base import BaseDeserializeService
from io import TextIOBase
import yaml

class YAMLDeserializeService(BaseDeserializeService):

    def deserialize_to_dict(self, stream: TextIOBase) -> dict:
        try:
            return yaml.safe_load(stream)
        except yaml.YAMLError as e:
            raise DeserializationException(f'Failed to deserialize YAML: {e}')
