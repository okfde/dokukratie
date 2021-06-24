from importlib import import_module


def parse(value, method_name):
    if ":" not in method_name:
        raise ValueError("Unknown method: %s", method_name)
    package, method = method_name.rsplit(":", 1)
    module = import_module(package)
    func = getattr(module, method)
    return func(value)
