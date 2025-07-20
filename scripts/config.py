# config.py
import os
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "..", "config.yaml")

def load_config():
    with open(CONFIG_PATH, "r") as f:
        return yaml.safe_load(f)

config = load_config()

OLLAMA_MODEL = config["ollama"]["model"]
OLLAMA_HOST = config["ollama"]["host"]
DB_PATH = os.path.join(BASE_DIR, "..", config["paths"]["db"])
CHATS_DIR = os.path.join(BASE_DIR, "..", config["paths"]["chats_dir"])
TZ_OFFSET = int(config["timezone"]["offset"])