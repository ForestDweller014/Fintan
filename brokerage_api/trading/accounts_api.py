import requests
import json
from app_config import *

def get_account() -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/account"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")