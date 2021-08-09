from apispecs.base.models.specification import Specification
from apispecs.base.models.singleton import SingletonABCMeta
from abc import ABC, abstractmethod
from io import TextIOBase

class DeserializeService(metaclass=SingletonABCMeta):

    @abstractmethod
    def deserialize_to_dict(self, stream: TextIOBase) -> dict:
        pass

    @abstractmethod
    def deserialize_to_specification(self, stream: TextIOBase) -> Specification:
        pass
