"""Shared runtime configuration for FGSBot cogs."""

import os

from dotenv import load_dotenv

load_dotenv()


def _get_int_env(name: str, default: int, *, minimum: int = 1) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value.strip() == "":
        return default

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer number of minutes") from exc

    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")

    return value
