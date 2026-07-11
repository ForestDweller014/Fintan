import requests
import json
from app_config import *

def get_orders(query_params=None) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/orders"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.get(url, headers=headers, params=query_params)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def get_order(order_id, query_params=None) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/orders/{order_id}"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.get(url, headers=headers, params=query_params)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def place_order(body_params) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/orders"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.post(url, headers=headers, json=body_params)
    if response.status_code in [200, 201]:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def cancel_all_orders() -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/orders"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        return "All open orders have been successfully canceled."
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def cancel_order(order_id) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/orders/{order_id}"
    headers = {
        "accept": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.delete(url, headers=headers)
    if response.status_code == 204:
        return f"Order with ID {order_id} has been successfully canceled."
    return json.dumps(f"Error: {response.status_code} - {response.text}")

def update_order(order_id, body_params) -> str:
    url = f"https://{APISERVER_DOMAIN}/v2/orders/{order_id}"
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "APCA-API-KEY-ID": API_KEY_ID,
        "APCA-API-SECRET-KEY": API_SECRET_KEY,
    }
    response = requests.patch(url, headers=headers, json=body_params)
    if response.status_code == 200:
        return response.json()
    return json.dumps(f"Error: {response.status_code} - {response.text}")