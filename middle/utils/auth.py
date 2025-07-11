import os
import json
import time
import base64
import requests


def get_auth_header() -> str:
    CACHE_FILE = 'token_cache.json'
    URL_COGNITO = os.getenv('URL_COGNITO')
    CONFIG_COGNITO = os.getenv('CONFIG_COGNITO')

    def is_token_valid(token: str) -> bool:
        """Verifica se o token JWT ainda é válido"""
        try:
            payload = token.split('.')[1]
            missing_padding = len(payload) % 4
            if missing_padding:
                payload += '=' * (4 - missing_padding)
            decoded = json.loads(base64.urlsafe_b64decode(payload))
            current_time = int(time.time())
            return decoded.get('exp', 0) > current_time + 300
        except (IndexError,
                ValueError,
                json.JSONDecodeError,
                base64.binascii.Error):
            return False

    def load_token_from_cache():
        """Carrega o token do cache"""
        try:
            with open(CACHE_FILE, 'r') as f:
                cache_data = json.load(f)
                return cache_data.get('access_token')
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def save_token_to_cache(token: str) -> None:
        """Salva o token no cache"""
        try:
            cache_data = {'access_token': token}
            with open(CACHE_FILE, 'w') as f:
                json.dump(cache_data, f)
        except Exception:
            pass

    def request_new_token() -> str:
        """Faz a requisição para obter um novo token"""
        data = CONFIG_COGNITO
        if isinstance(CONFIG_COGNITO, str):
            try:
                data = json.loads(CONFIG_COGNITO)
            except Exception:
                pass
        response = requests.post(
            URL_COGNITO,
            data=data,
            headers={'Content-Type': 'application/x-www-form-urlencoded'}
        )
        response.raise_for_status()
        return response.json()['access_token']

    cached_token = load_token_from_cache()
    if cached_token and is_token_valid(cached_token):
        return {'Authorization': f'Bearer {cached_token}'}

    try:
        new_token = request_new_token()
        save_token_to_cache(new_token)
        return {'Authorization': f'Bearer {new_token}'}
    except requests.RequestException as e:
        raise RuntimeError(f"Erro ao requisitar novo token: {e}")
