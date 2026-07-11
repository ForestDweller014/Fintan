import requests
import json
from app_config import *

def get_positions() -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/positions"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def get_position(symbol) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/positions/{symbol}"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def close_all_positions() -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/positions"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 207:  # Multi-status response
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def close_position(symbol) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/positions/{symbol}"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def exercise_option(symbol_or_id) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/positions/{symbol_or_id}/exercise"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.post(url, headers=headers)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")