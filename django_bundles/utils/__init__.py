def get_class(class_string):
    """
    Get a class from a dotted string
    """
    split_string = class_string.encode('ascii').split('.')
    import_path = '.'.join(split_string[:-1])
    class_name = split_string[-1]

    if class_name:
        try:
            if import_path:
                mod = __import__(import_path, globals(), {}, [class_name])
                cls = getattr(mod, class_name)
            else:
                cls = __import__(class_name, globals(), {})
            if cls:
                return cls
        except (ImportError, AttributeError):
            pass

    return None
