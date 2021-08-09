import yaml

from apispecs.swagger2.provider import Swagger2SchemaProvider
from apispecs.openapi3.provider import OpenAPI3SchemaProvider
from apispecs.base.service.schema.service import SchemaService
from apispecs.base.service.deserialization.impl.json import JSONDeserializeService

schema_service = SchemaService()
schema_service.register_provider(Swagger2SchemaProvider())
schema_service.register_provider(OpenAPI3SchemaProvider())

deserialization_service = JSONDeserializeService()

with open('data/swagger2.json', 'r') as f:
    spec = deserialization_service.deserialize_to_specification(f)
    print(spec)
