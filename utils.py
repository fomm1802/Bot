import json
import os
import logging
import base64
import requests

def get_server_config(guild_id):
    path = f"configs/{guild_id}.json"
    if os.path.exists(path):
        try:
            with open(path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            logging.error(f"❌ อ่านไฟล์ {guild_id}.json ไม่ได้")
    return {"notify_channel_id": None}

def save_server_config(guild_id, server_config):
    url = f"https://api.github.com/repos/fomm1802/Bot/contents/configs/{guild_id}.json"
    headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}
    response = requests.get(url, headers=headers)
    data = {
        "message": f"Update config for guild {guild_id}",
        "content": base64.b64encode(json.dumps(server_config, indent=4).encode()).decode(),
        "branch": "main",
        "sha": response.json().get('sha') if response.status_code == 200 else None
    }
    res = requests.put(url, headers=headers, json=data)
    logging.info(f"✅ อัปเดตไฟล์สำเร็จ" if res.status_code in (200, 201) else f"❌ อัปเดตล้มเหลว {res.text}")

    path = f"configs/{guild_id}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        json.dump(server_config, file, indent=4)

async def exists_on_github(guild_id):
    url = f"https://api.github.com/repos/fomm1802/Bot/contents/configs/{guild_id}.json"
    headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}
    response = requests.get(url, headers=headers)
    return response.status_code == 200
