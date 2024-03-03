from dataclasses import asdict
from pathlib import Path

import yaml

from storage.classes import Configuration

_configuration = Configuration()


def write_config(config: Configuration):
    with open("config/config.yml", 'w') as file:
        yaml.dump(asdict(config), file)


def read_config() -> Configuration:
    with open("config/config.yml", 'r') as file:
        data = yaml.safe_load(file)
    return Configuration(**data)


def setup_config() -> None:
    global _configuration
    config_dir = Path.cwd() / "config/"
    config_file = config_dir / "config.yml"
    config_dir.mkdir(exist_ok=True)

    if not config_file.exists():
        config = Configuration()
        write_config(config)
    else:
        config = read_config()
        _configuration = config


def get_config() -> Configuration:
    return _configuration
