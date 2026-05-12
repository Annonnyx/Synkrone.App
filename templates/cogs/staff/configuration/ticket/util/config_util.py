import json
import os

def get_config_path(guild_id):
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", f"{guild_id}.json")

def get_config(guild_id):
    path = get_config_path(guild_id)
    if not os.path.exists(path):
        # Configuration par défaut
        return {
            "enabled": False,
            "channel_id": None,
            "category_id": None,
            "archive_id": None,
            "support_role_id": None,
            "msg_id": None,
            "categories": [],
            "custom_description": None,
            "local_image_path": None,
            "ticket_count": 0
        }
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_config(guild_id, data):
    path = get_config_path(guild_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)