#!/usr/bin/env python3
from flask import Flask, request, jsonify
import csv
import datetime
import os

app = Flask(__name__)

CSV_FILENAME = "sensor_data.csv"
SENSOR_KEYS = ["sensor1", "sensor2", "sensor3", "sensor4", "sensor5"]

# Если файла CSV нет, создаем его и записываем заголовок (первая строка)
if not os.path.exists(CSV_FILENAME):
    with open(CSV_FILENAME, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        header = ["timestamp"] + SENSOR_KEYS
        writer.writerow(header)


@app.route('/sensor/data', methods=['POST'])
def receive_sensor_data():
    """
    Ожидается JSON формата:
    {
        "sensor1": 25.3,
        "sensor2": 40.2,
        "sensor3": 1013,
        "sensor4": 55.6,
        "sensor5": 12.0
    }
    """
    try:
        data = request.json  # Получаем JSON-данные
        if not data:
            return jsonify({"error": "Empty request"}), 400

        timestamp = datetime.datetime.now().isoformat()
        row = [timestamp] + [data.get(key, "") for key in SENSOR_KEYS]

        # Записываем в CSV
        with open(CSV_FILENAME, 'a', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(row)

        print(f"Приняты данные: {row}")
        return jsonify({"message": "Data stored"}), 201

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({"error": "Failed to process request"}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
