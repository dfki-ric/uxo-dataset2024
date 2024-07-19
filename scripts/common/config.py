try:
    from collections import Mapping
except ImportError:
    from collections.abc import Mapping

import sys
import os.path as path
import yaml
from typing import Iterator


__sentinel__ = object()

class _FallbackArgs(Mapping):
    def __init__(self) -> None:
        self.args = list(sys.argv[1:])
        self._idx = 0

    def get(self, key, default = __sentinel__):
        try:
            return self[key]
        except IndexError as e:
            if default != __sentinel__:
                return default
            raise ValueError(f"Could not resolve {key}") from e
        
    def reset(self) -> None:
        self._idx = 0

    def __getitem__(self, key):
        # Ignore the key, just try to return the next element
        ret = self.args[self._idx]
        self._idx += 1
        return ret
    
    def __iter__(self) -> Iterator:
        return iter(zip(range(len(self.args)), self.args))
    
    def __len__(self) -> int:
        return len(self.args)
    
    def __repr__(self) -> str:
        return str(self.args)


def get_config(config_path: str = None) -> dict:
    if not config_path and len(sys.argv) > 1:
        config_path = sys.argv[1]

    if not path.isfile(config_path):
        config_path = path.join(path.dirname(path.realpath(__file__)), '..',  'config.yaml')
        print(f"No valid config path given, defaulting to {config_path}")

    if not path.isfile(config_path) and len(sys.argv) > 1:
        # This way the user should still be able to call scripts and pass any arguments as 
        # positional parameters
        print(f"Config '{config_path}' not found, trying fallback method")
        return _FallbackArgs()

    with open(config_path, 'r') as config:
        return yaml.safe_load(config)
    