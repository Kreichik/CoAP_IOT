#!/usr/bin/env python3
import asyncio
import aiocoap.resource as resource
import aiocoap
import csv
import datetime
import os
import json

# Директория для хранения CSV файлов
CSV_DIR = "csv_data"

# Создаем директорию, если её нет
os.makedirs(CSV_DIR, exist_ok=True)

# Определяем фиксированный порядок датчиков
SENSOR_KEYS = ["sensor1", "sensor2", "sensor3", "sensor4", "sensor5"]


class SensorDataResource(resource.Resource):
    async def render_post(self, request):
        """
        Ожидается, что payload запроса имеет формат JSON, например:
          {
            "sensor1": 25.3,
            "sensor2": 40.2,
            "sensor3": 1013,
            "sensor4": 55.6,
            "sensor5": 12.0
          }
        Данные будут записаны в CSV файл для текущего дня.
        Имя файла формируется по схеме DD-MM-YYYY.csv, например, 10-02-2025.csv.
        """
        try:
            payload_str = request.payload.decode('utf-8')
            data = json.loads(payload_str)
        except Exception as e:
            print("Ошибка при разборе JSON:", e)
            return aiocoap.Message(code=aiocoap.BAD_REQUEST, payload=b"Invalid JSON payload")

        now = datetime.datetime.now()
        timestamp = now.isoformat()
        # Формируем имя файла по текущей дате (например, "10-02-2025.csv")
        date_str = now.strftime("%d-%m-%Y")
        csv_filename = os.path.join(CSV_DIR, f"{date_str}.csv")

        # Формируем строку: [timestamp, sensor1, sensor2, sensor3, sensor4, sensor5]
        row = [timestamp] + [data.get(key, "") for key in SENSOR_KEYS]

        # Если файл еще не существует, запишем заголовок
        file_exists = os.path.exists(csv_filename)
        try:
            with open(csv_filename, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile)
                if not file_exists:
                    header = ["timestamp"] + SENSOR_KEYS
                    writer.writerow(header)
                writer.writerow(row)
            print(f"Записаны данные в {csv_filename}: {row}")
        except Exception as e:
            print("Ошибка записи в CSV:", e)
            return aiocoap.Message(code=aiocoap.INTERNAL_SERVER_ERROR, payload=b"Failed to write to CSV")

        return aiocoap.Message(code=aiocoap.CREATED, payload=b"Data stored")


def main():
    root = resource.Site()
    # Регистрируем ресурс по пути /sensor/data
    root.add_resource(['sensor', 'data'], SensorDataResource())

    # Создаем сервер, чтобы он слушал на всех интерфейсах (IPv4) на порту 5683
    asyncio.Task(aiocoap.Context.create_server_context(root, bind=('0.0.0.0', 5683)))

    print("CoAP сервер запущен и слушает на 0.0.0.0:5683")
    asyncio.get_event_loop().run_forever()


if __name__ == '__main__':
    main()
