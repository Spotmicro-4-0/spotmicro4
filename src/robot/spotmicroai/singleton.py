class Singleton(type):
    """
    A metaclass that implements the Singleton design pattern.
    Classes using this metaclass will only have one instance throughout the program.
    If an instance of the class already exists, subsequent instantiations will return the same instance.
    Example:
        class MyClass(metaclass=Singleton):
            pass
        a = MyClass()
        b = MyClass()
        assert a is b  # Both variables point to the same instance
    Attributes:
        _instances (dict): A dictionary mapping classes to their singleton instances.
    Methods:
        __call__(cls, *args, **kwargs): Creates a new instance if one does not exist,
            otherwise returns the existing instance.
    """

    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]
