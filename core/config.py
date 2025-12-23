import os
import tomllib

_PATH = os.path.join(os.path.dirname(__file__), "..", "config", "brand.toml")


def brand():
    with open(_PATH, "rb") as f:
        return tomllib.load(f)
