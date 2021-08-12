from apispecs.base.utils import format_list

"""
Denotes a single specification.
All specification implementations must extend this class.
"""
class Specification(object):
    
    def __init__(self, title, description, license_name, license_url, version, base_url, endpoints):
        self.title = title
        self.description = description
        self.license_name = license_name
        self.license_url = license_url
        self.version = version
        self.base_url = base_url
        self.endpoints = endpoints

    def __str__(self):
        return (
            f'Specification(title={self.title}, description={self.description}, license_name={self.license_name}, '
            f'license_url={self.license_url}, version={self.version}, base_url={self.base_url}, '
            f'endpoints={format_list(self.endpoints)}'
        )

class Endpoint(object):

    def __init__(self, url, parameters, methods):
        self.url = url
        self.parameters = parameters
        self.methods = methods
    
    def __str__(self):
        return (
            f'Endpoint(url={self.url}, parameters={format_list(self.parameters)}, methods={format_list(self.methods)}'
        )

class Method(object):

    def __init__(self, method, operation_id, summary, description, deprecated, parameters):
        self.method = method
        self.operation_id = operation_id
        self.summary = summary
        self.description = description
        self.deprecated = deprecated
        self.parameters = parameters

    def __str__(self):
        return (
            f'{self.method.upper()}(operation_id={self.operation_id}, summary={self.summary}, '
            f'description={self.description}, deprecated={self.deprecated}, '
            f'parameters={format_list(self.parameters)}'
        )

class Parameter(object):
    
    def __init__(self, name, description, location, required, type, format, default_value, collection_format):
        self.name = name
        self.description = description
        self.location = location
        self.required = required
        self.type = type
        self.format = format
        self.default_value = default_value
        self.collection_format = collection_format

    def __str__(self):
        return (
            f'Parameter(name={self.name}, description={self.description}, location={self.location}, '
            f'required={self.required}, type={self.type}, format={self.format}, '
            f'default_value={self.default_value}, collection_format={self.collection_format}'
        )
