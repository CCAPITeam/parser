from apispecs.base.exceptions import DeserializationException
from .base import BaseDeserializeService
from io import TextIOBase
import json

class JSONDeserializeService(BaseDeserializeService):

    def deserialize_to_dict(self, stream: TextIOBase) -> dict:
        try:
            return json.load(stream)
        except json.decoder.JSONDecodeError as e:
            raise DeserializationException(f'Failed to deserialize JSON: {e}')
