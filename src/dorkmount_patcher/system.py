"""Launch OS tools without the frozen application's private library search path."""

import os


def environment():
    result = dict(os.environ)
    if "LD_LIBRARY_PATH_ORIG" in result:
        result["LD_LIBRARY_PATH"] = result.pop("LD_LIBRARY_PATH_ORIG")
    else:
        result.pop("LD_LIBRARY_PATH", None)
    return result
