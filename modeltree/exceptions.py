class ModelLookupError(Exception):
    pass


class ModelNotUnique(ModelLookupError):
    pass


class ModelDoesNotExist(ModelLookupError):
    pass


class ModelNotRelated(ModelLookupError):
    pass


class InvalidLookup(Exception):
    pass
