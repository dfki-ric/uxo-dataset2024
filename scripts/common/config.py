import os.path as path
from collections import Mapping
import sys
import json


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
    
    def __len__(self) -> int:
        return len(self.args)
    
    def __repr__(self) -> str:
        return str(self.args)


def get_config() -> dict:
    if len(sys.argv) > 1:
        config_path = sys.argv[1]
    else:
        config_path = path.join(path.dirname(path.realpath(__file__)), '..',  'config.json')

    if not path.isfile(config_path):
        # This way the user should still be able to call scripts and pass any arguments as 
        # positional parameters
        return _FallbackArgs()

    with open(config_path, 'r') as config:
        return json.loads(config.read())
    