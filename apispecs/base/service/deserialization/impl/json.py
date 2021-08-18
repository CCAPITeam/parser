from apispecs.base.exceptions import DeserializationException
from .base import BaseDeserializationProvider
from io import TextIOBase
from collections.abc import Sequence
import json

class JSONDeserializationProvider(BaseDeserializationProvider):

    def get_content_types(self) -> Sequence[str]:
        return ['application/json']

    def deserialize_to_dict(self, stream: TextIOBase) -> dict:
        try:
            return json.load(stream)
        except json.decoder.JSONDecodeError as e:
            raise DeserializationException(f'Failed to deserialize JSON: {e}')
