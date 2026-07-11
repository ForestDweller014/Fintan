import requests
import json
from app_config import *

def get_assets(query_params=None) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/assets"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.get(url, headers=headers, params=query_params)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def get_asset(symbol_or_asset_id) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/assets/{symbol_or_asset_id}"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def get_options(query_params=None) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/options/contracts"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.get(url, headers=headers, params=query_params)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def get_option(symbol_or_id) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/options/contracts/{symbol_or_id}"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")