import requests

def login(base_url: str, email: str, password: str) -> str:
    """
    Отправляет запрос на /login и возвращает JWT-токен.
    Если авторизация неуспешна, выбрасывает исключение.
    """
    url = f"{base_url}/login"
    payload = {
        "email": email,
        "password": password
    }
    headers = {
        "Content-Type": "application/json"
    }

    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code == 200:
        data = resp.json()
        token = data.get("token")
        print("Успешный логин! Токен:", token)
        return token
    else:
        # Выводим код ошибки и тело ответа для отладки
        print(f"Ошибка {resp.status_code}: {resp.text}")
        resp.raise_for_status()

if __name__ == "__main__":
    # Пример использования
    BASE_URL = "http://localhost:9100"
    EMAIL = "user@example.com"
    PASSWORD = "your_password"

    try:
        jwt_token = login(BASE_URL, EMAIL, PASSWORD)
        # дальше можно использовать jwt_token для авторизованных запросов
    except Exception as e:
        print("Не удалось залогиниться:", e)
