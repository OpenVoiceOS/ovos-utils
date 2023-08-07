from ovos_utils.log import deprecated


@deprecated("imported deprecation", "0.1.0")
def deprecated_function():
    pass


class Deprecated:
    @deprecated("Class Deprecated", "0.2.0")
    def __init__(self):
        pass
