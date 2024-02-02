import json
from dataclasses import dataclass, asdict
from pathlib import Path
import os
from enum import Enum


@dataclass
class ModelInfo:
    model_name: str
    input_cost: float
    output_cost: float


@dataclass
class GPTUser:
    userid: int
    channelid: int


@dataclass
class Configuration:
    discord_token: str
    openai_token: str
    guildid: int
    gptcategoryid: int
    timeout: int


class Model(Enum):
    GPT_4_8K = ModelInfo("gpt-4", 0.03, 0.06)
    GPT_4_TURBO_NO_VISION = ModelInfo("gpt-4-1106-preview", 0.01, 0.03)
    GPT_4_TURBO_VISION = ModelInfo("gpt-4-1106-vision-preview", 0.01, 0.03)
    GPT_3_5_TURBO_1106 = ModelInfo("gpt-3.5-turbo-1106", 0.001, 0.002)
    GPT_3_5_TURBO_4K = ModelInfo("gpt-3.5-turbo", 0.003, 0.006)
    DALL_E_3 = ModelInfo("dall-e-3", 0.04, 0.08)

    @property
    def modelname(self):
        return self.value.model_name

    @property
    def inputcost(self):
        return self.value.input_cost

    @property
    def outputcost(self):
        return self.value.output_cost


@dataclass
class GPTRequest:
    model: Model
    input_tokens: int
    output_tokens: int


def load_configuration() -> Configuration:
    config_path = Path.cwd()
    config_file = config_path / "config.json"

    config_path.mkdir(parents=True, exist_ok=True)

    try:
        with config_file.open('x') as f:
            print("Successfully created data file...")

            configuration = Configuration("", "", 0, 0, 120)
            json.dump(asdict(configuration), f, indent=4)
            print("Please fill in the configuration file and restart the bot.")
            exit(0)
    except FileExistsError:
        print("Loading previously saved data...")

    try:
        with config_file.open('r') as f:
            configuration = Configuration(**json.load(f))
    except Exception as e:
        print(f"Error occured while reading {config_file.name}")
        print(e)
        exit(0)
    return configuration


def load_gpt_users() -> list[GPTUser]:
    gpt_users_path = Path.cwd()
    gpt_users_file = gpt_users_path / "gpt_users.json"

    gpt_users_path.mkdir(parents=True, exist_ok=True)

    try:
        with gpt_users_file.open('x') as f:
            print("Successfully created data file...")

            gpt_users = []
            json.dump(gpt_users, f, indent=4)
    except FileExistsError:
        print("Loading previously saved data...")

    try:
        with gpt_users_file.open('r') as f:
            gpt_users = [GPTUser(**user) for user in json.load(f)]
    except Exception as e:
        print(f"Error occured while reading {gpt_users_file.name}")
        print(e)
        exit(0)
    return gpt_users


def load_requests_map() -> dict[int, GPTRequest]:
    requests_filepath = Path.cwd()
    requests_file = requests_filepath / "requests.json"

    requests_filepath.mkdir(parents=True, exist_ok=True)

    try:
        with requests_file.open('x') as f:
            print("Successfully created data file...")

            requests_map = {}
            json.dump(requests_map, f, indent=4)
    except FileExistsError:
        print("Loading previously saved data...")

    try:
        with requests_file.open('r') as f:
            requests_map = {int(k): GPTRequest(**v) for k, v in json.load(f).items()}
    except Exception as e:
        print(f"Error occured while reading {requests_file.name}")
        print(e)
        exit(0)
    return requests_map


def save_configuration_file(configuration: Configuration, path: str, filename: str):
    with open(os.path.join(path, filename), 'w') as f:
        json.dump(asdict(configuration), f)


def save_gpt_users_file(gpt_users: list[GPTUser], path: str, filename: str):
    with open(os.path.join(path, filename), 'w') as f:
        json.dump([asdict(user) for user in gpt_users], f)


def save_requests_map(requests_map: dict[int, GPTRequest], path: str, filename: str):
    with open(os.path.join(path, filename), 'w') as f:
        json.dump({k: asdict(v) for k, v in requests_map.items()}, f)
