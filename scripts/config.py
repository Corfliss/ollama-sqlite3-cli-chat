"""The configuration of the settings running with yaml"""
import os
import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.abspath(os.path.join(BASE_DIR, "config.yaml"))

def load_config():
    try:
        with open(CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(f"❌ Config file not found at: {CONFIG_PATH}")
        exit(1)
    except yaml.YAMLError as e:
        print(f"❌ Error parsing config.yaml: {e}")
        exit(1)

config = load_config()

OLLAMA_MODEL = config["ollama"]["model"]
OLLAMA_HOST = config["ollama"]["host"]
DB_PATH = os.path.join(BASE_DIR, "..", config["paths"]["db"])
CHATS_DIR = os.path.join(BASE_DIR, "..", config["paths"]["chats_dir"])
TZ_OFFSET = int(config["timezone"]["offset"])