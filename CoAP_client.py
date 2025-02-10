#!/usr/bin/env python3
import asyncio
import aiocoap
import json


async def send_sensor_data():
    # Подготовка данных с 5 датчиков (пример значений)
    sensor_data = {
        "sensor1": 100,
        "sensor2": 500,
        "sensor3": 1013,
        "sensor4": 55.6,
        "sensor5": 12.0
    }
    payload = json.dumps(sensor_data).encode('utf-8')

    # Задайте IP-адрес сервера в локальной сети
    # Например, если сервер имеет IP 192.168.1.100:
    uri = "coap://10.1.10.144:5683/sensor/data"

    request = aiocoap.Message(code=aiocoap.POST, payload=payload, uri=uri)

    # Создаем контекст клиента
    protocol = await aiocoap.Context.create_client_context()

    try:
        response = await protocol.request(request).response
        print("Код ответа:", response.code)
        print("Ответ сервера:", response.payload.decode('utf-8'))
    except Exception as e:
        print("Ошибка отправки запроса:", e)


if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(send_sensor_data())
