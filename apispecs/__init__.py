from apispecs.base.service.schema.service import SchemaService
from apispecs.swagger2.provider import Swagger2SchemaProvider
from apispecs.openapi3.provider import OpenAPI3SchemaProvider

from apispecs.base.service.deserialization.service import DeserializationService
from apispecs.base.service.deserialization.impl.json import JSONDeserializationProvider
from apispecs.base.service.deserialization.impl.yaml import YAMLDeserializationProvider

schema_service = SchemaService()
schema_service.register_provider(Swagger2SchemaProvider())
schema_service.register_provider(OpenAPI3SchemaProvider())

deserialization_service = DeserializationService()
deserialization_service.register_provider(JSONDeserializationProvider())
deserialization_service.register_provider(YAMLDeserializationProvider())
