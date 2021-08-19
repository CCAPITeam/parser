def format_collection(collection):
    return ', '.join([str(element) for element in collection])

def format_list(array):
    return f'[{format_collection(array)}]'

def format_dict(array):
    items = [f'{key}: {value}' for key, value in array.items()]
    return f'{{{format_collection(items)}}}'
