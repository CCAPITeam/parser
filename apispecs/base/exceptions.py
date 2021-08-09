"""
Thrown when the deserialization service
fails to deserialize the specification in some way.
"""
class DeserializationException(Exception):
    pass

"""
Thrown when the schema service cannot figure out
which schema the specification belongs to.
"""
class UnknownSchemaException(DeserializationException):
    pass
