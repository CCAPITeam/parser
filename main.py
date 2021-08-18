from apispecs import deserialization_service

with open('data/swagger2.json', 'r') as f:
    spec = deserialization_service.deserialize_to_specification('application/json', f)
    print(spec)
