class CatalogError(Exception):
    pass

class InvalidEntityError(CatalogError):
    pass

class DuplicateIdError(CatalogError):
    pass

class NotFoundError(CatalogError):
    pass

class UnsupportedFormatVersionError(CatalogError):
    pass

class CorruptedFileError(CatalogError):
    pass

class NothingToUndoError(CatalogError):
    pass