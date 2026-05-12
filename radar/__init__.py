from __future__ import annotations

import sys
from importlib import import_module


_MODULE_ALIASES = {
    "analyzer": "trustradar.analyzer",
    "collector": "trustradar.collector",
    "exceptions": "trustradar.exceptions",
    "models": "trustradar.models",
    "nl_query": "trustradar.nl_query",
    "search_index": "trustradar.search_index",
    "storage": "trustradar.storage",
}

for _module_name, _target in _MODULE_ALIASES.items():
    sys.modules[f"{__name__}.{_module_name}"] = import_module(_target)


RadarStorage = import_module("trustradar.storage").RadarStorage


__all__ = ["RadarStorage"]
