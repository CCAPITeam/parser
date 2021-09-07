from apispecs import deserialization_service

with open('data/openapi3.json', 'r') as f:
    spec = deserialization_service.deserialize_to_specification('application/json', f)
    text = deserialization_service.serialize_to_dict('openapi3', spec)

    print(spec)
    print(text)