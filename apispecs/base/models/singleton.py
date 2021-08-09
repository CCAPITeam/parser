from abc import ABCMeta

class Singleton(type):
    _instances = {}

    def __call__(cls, *args: tuple, **kwargs: dict):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)

        return cls._instances[cls]

class SingletonABCMeta(ABCMeta, Singleton):
    pass
