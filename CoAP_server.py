#!/usr/bin/env python3
from flask import Flask, request, jsonify, render_template
import csv
import datetime
import os
import threading
from flask import send_file
import requests
app = Flask(__name__)

data_folder = 'box_data'
# Ожидаемые устройства (ESP32)
EXPECTED_DEVICES = ["esp1", "esp2"]

# Буфер для хранения временных данных от ESP
sensor_data_buffer = {}
buffer_lock = threading.Lock()  # Блокировка для работы с буфером

lat = 51.09103211521735
lon = 71.41825457825051


url = (
    "https://api.open-meteo.com/v1/forecast"
    f"?latitude={lat}&longitude={lon}"
    "&current_weather=true"
)

response_weather = requests.get(url)

if response_weather.status_code == 200:
    data = response_weather.json()
    current = data.get("current_weather", {})
    print("Температура:", current.get("temperature"), "°C")
    print("Скорость ветра:", current.get("windspeed"), "км/ч")
    print("Направление ветра:", current.get("winddirection"), "°")
    print("Погодный код (weathercode):", current.get("weathercode"))
    print("Время измерения:", current.get("time"))
else:
    print("Ошибка при запросе:", response_weather.status_code)

# Убедитесь, что папка существует
os.makedirs('box_data', exist_ok=True)
# Заголовки для CSV-файла 23-25
CSV_HEADERS = [
    "timestamp", "device",
    "soil1", "soil2", "soil3", "soil4", "soil5",
    "water_temperature", "air_temperature", "air_humidity", "light_level"
]
@app.route('/sensor/data', methods=['POST'])
def receive_sensor_data():
    global sensor_data_buffer

    try:
        data = request.json  # Получаем JSON
        print(data)
        if not data or "device_id" not in data:
            return jsonify({"error": "Invalid request"}), 400

        device_id = data["device_id"]
        if device_id not in EXPECTED_DEVICES:
            return jsonify({"error": "Unknown device"}), 400

        # Записываем данные в буфер
        with buffer_lock:
            sensor_data_buffer[device_id] = data

        # Проверяем, есть ли данные от обоих ESP
        with buffer_lock:
            if all(device in sensor_data_buffer for device in EXPECTED_DEVICES):
                # Объединяем данные
                timestamp = datetime.datetime.now().isoformat()
                esp1_data = sensor_data_buffer.get("esp1", {})
                esp2_data = sensor_data_buffer.get("esp2", {})

                # Формируем строку CSV (если данных нет — ставим пустое значение)
                row = [
                    timestamp, "both_devices",
                    esp1_data.get("soil1", ""), esp1_data.get("soil2", ""), esp1_data.get("soil3", ""),
                    esp1_data.get("soil4", ""), esp1_data.get("soil5", ""),
                    esp2_data.get("water_temperature", ""), esp2_data.get("air_temperature", ""),
                    esp2_data.get("air_humidity", ""), esp2_data.get("light_level", "")
                ]

                # Определяем имя файла на основе текущей даты
                current_date = datetime.datetime.now().strftime("%Y-%m-%d")
                csv_filename = f'box_data/{current_date}.csv'

                # Проверяем, существует ли файл, и записываем заголовки, если нет
                file_exists = os.path.isfile(csv_filename)

                with open(csv_filename, 'a', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    if not file_exists:
                        writer.writerow(CSV_HEADERS)
                    writer.writerow(row)

                print(f"Записаны данные: {row}")

                # Очищаем буфер
                sensor_data_buffer.clear()

        return jsonify({"message": "Data stored"}), 201

    except Exception as e:
        print(f"Ошибка: {e}")
        return jsonify({"error": "Failed to process request"}), 500
@app.route('/update', methods=['GET'])
def check_update():
    try:
        with open("status.txt", "r") as file:
            status = file.read().strip()
            if status == "1":
                return jsonify({"update_available": True}), 200
            else:
                return jsonify({"update_available": False}), 200
    except FileNotFoundError:
        return jsonify({"update_available": False}), 200

@app.route('/firmware1', methods=['GET'])
def get_firmware1():
    # Укажите путь к файлу прошивки
    firmware_path = "/home/iot/Desktop/CoAP_IOT/Soil_ESP32_5_sens.ino.bin"

    try:
        # Отправляем файл клиенту
        return send_file(firmware_path, as_attachment=True)
    except Exception as e:
        # Обработка ошибок, если файл не найден или произошла другая ошибка
        print(f"Ошибка при отправке файла: {e}")
        return jsonify({"error": "Failed to send firmware file"}), 500

@app.route('/firmware2', methods=['GET'])
def get_firmware2():
    # Укажите путь к файлу прошивки
    firmware_path = "/home/iot/Desktop/CoAP_IOT/soil_humi_temp.ino.bin"

    try:
        # Отправляем файл клиенту
        return send_file(firmware_path, as_attachment=True)
    except Exception as e:
        # Обработка ошибок, если файл не найден или произошла другая ошибка
        print(f"Ошибка при отправке файла: {e}")
        return jsonify({"error": "Failed to send firmware file"}), 500

@app.route('/firmware/status', methods=['GET'])
def get_firmware_status():
    print("Succesfull")
    return jsonify({"message": True}), 200

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/dashboard-new')
def new_dashboard():
    return render_template('new_dashboard.html')

@app.route('/data')
def get_data():
    response_weather = requests.get(url)

    if response_weather.status_code == 200:
        data = response_weather.json()
        current = data.get("current_weather", {})

    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    csv_filename = f'{data_folder}/{current_date}.csv'

    if not os.path.isfile(csv_filename):
        return jsonify({"error": "No data available"}), 404

    # Calculate the time threshold for 15 minutes ago
    fifteen_minutes_ago = datetime.datetime.now() - datetime.timedelta(minutes=5)

    humidity_data = []
    temperature_data = []
    last_row = None

    with open(csv_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            # Parse the timestamp and compare with the threshold
            timestamp = datetime.datetime.fromisoformat(row["timestamp"])
            if timestamp >= fifteen_minutes_ago:
                humidity_data.append({
                    "timestamp": row["timestamp"],
                    "air_humidity": float(row["air_humidity"]) if row["air_humidity"] else 0
                })
                temperature_data.append({
                    "timestamp": row["timestamp"],
                    "air_temperature": float(row["air_temperature"]) if row["air_temperature"] else 0
                })
            last_row = row

    if last_row is None:
        return jsonify({"error": "No data available"}), 404

    data = {
        "soil1": float(last_row["soil1"]) if last_row["soil1"] else 0,
        "soil2": float(last_row["soil2"]) if last_row["soil2"] else 0,
        "soil3": float(last_row["soil3"]) if last_row["soil3"] else 0,
        "soil4": float(last_row["soil4"]) if last_row["soil4"] else 0,
        "soil5": float(last_row["soil5"]) if last_row["soil5"] else 0,
        "air_temperature": float(last_row["air_temperature"]) if last_row["air_temperature"] else 0,
        "air_humidity": float(last_row["air_humidity"]) if last_row["air_humidity"] else 0,
        "light_level": float(last_row["light_level"]) if last_row["light_level"] else 0,
        "humidity_data": humidity_data,
        "temperature_data": temperature_data,
        "weather_temp": current.get("temperature"),
    }

    return jsonify(data)


@app.route('/monitor')
def monitor():
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    csv_filename = f'{data_folder}/{current_date}.csv'

    if not os.path.isfile(csv_filename):
        return "No data available", 404

    last_row = None
    with open(csv_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            last_row = row

    if last_row is None:
        return "No data available", 404

    return render_template('monitor.html', data=last_row)


@app.route('/monitor-data')
def monitor_data():
    current_date = datetime.datetime.now().strftime("%Y-%m-%d")
    csv_filename = f'{data_folder}/{current_date}.csv'

    if not os.path.isfile(csv_filename):
        return jsonify({"error": "No data available"}), 404

    last_row = None
    with open(csv_filename, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            last_row = row

    if last_row is None:
        return jsonify({"error": "No data available"}), 404

    return jsonify(last_row)

@app.route('/data-status')
def data_status():
    return jsonify({"message": True})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)