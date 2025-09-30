import os
from pathlib import Path
from typing import Optional

import yaml
from pydantic import BaseModel, SecretStr, ValidationError

from frarber.enums.exchange_type import ExchangeType


class ExchangeConfig(BaseModel):
    """Pydantic model for a single exchange's configuration."""

    api_key: SecretStr
    api_secret: SecretStr
    password: Optional[SecretStr] = None
    slow: bool = False
    hedge_mode: bool = False


class Config(BaseModel):
    """Pydantic model for the main configuration."""

    exchanges: dict[ExchangeType, ExchangeConfig] = {}


CONFIG_PATH = Path(os.environ.get("FRARBER_CONFIG_PATH", "./frarber.yaml"))


def load_config() -> Config:
    """Loads and validates the configuration from config.yaml using Pydantic."""
    if not CONFIG_PATH.is_file():
        return Config()
    with open(CONFIG_PATH, "r") as f:
        config_data = yaml.safe_load(f)
    if not config_data:
        return Config()
    try:
        return Config(**config_data)
    except ValidationError as e:
        print(f"Error validating arbitrageur.yaml: {e}")
        raise
