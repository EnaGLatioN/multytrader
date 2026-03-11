import requests


def check_proxy(proxies):
    try:
        response = requests.get("https://api.ipify.org", proxies=proxies, timeout=5)
        return response.status_code == 200
    except:
        return False
