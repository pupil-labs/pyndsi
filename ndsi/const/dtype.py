DTYPE_UNKNOWN             = "unknown"
DTYPE_INT                 = "int"
DTYPE_FLOAT               = "float"
DTYPE_BOOL                = "bool"
DTYPE_SELECT              = "selector"
DTYPE_BITMAP              = "bitmap"

__all__ = []
for name in dir():
    if name.startswith('DTYPE_'):
        __all__.append(name)