from __future__ import annotations

import importlib
import sys


_ALIASES = {
    "analyzer": "trustradar.analyzer",
    "collector": "trustradar.collector",
    "exceptions": "trustradar.exceptions",
    "models": "trustradar.models",
    "nl_query": "trustradar.nl_query",
    "reporter": "trustradar.reporter",
    "search_index": "trustradar.search_index",
    "storage": "trustradar.storage",
}


for _name, _target in _ALIASES.items():
    sys.modules[f"{__name__}.{_name}"] = importlib.import_module(_target)


__all__ = sorted(_ALIASES)
