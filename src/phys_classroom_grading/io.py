"""Simple functions for abstracting file input/output."""
try:
    import tomllib

except ImportError:
    # Needed for python < 3.11 support
    import tomli as tomllib

import pandas as pd


def load_excel(path):
    """Load an excel file at `path` into a Pandas DataFrame."""
    with open(path, "rb") as f:
        out = pd.read_excel(f)

    return out


def load_csv(path):
    """Load a csv file at `path` into a Pandas DataFrame."""
    with open(path, "r") as f:
        out = pd.read_csv(f, dtype="object")

    return out


def load_toml(path):
    """Load a toml file at `path` into a dictionary."""
    with open(path, "rb") as f:
        out = tomllib.load(f)

    return out


def write_csv(df, path):
    """Write a DataFrame to a csv file at `path`."""
    df.to_csv(path, header=True)
