import os
from pathlib import Path

import yaml


def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def load_config() -> dict:
    config_path = get_project_root() / "config" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    env_from_system = os.getenv("TEST_ENV")
    if env_from_system:
        config["env"] = env_from_system
    return config


def get_base_url() -> str:
    config = load_config()
    return config["host"][config["env"]]
