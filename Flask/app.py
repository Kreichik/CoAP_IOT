from flask import Flask, jsonify, render_template
import pandas as pd
import os

app = Flask(__name__)

# Укажи правильный путь к CSV
CSV_PATH = "/home/iot/Desktop/CoAP_IOT/sensor_data.csv"

# Функция для чтения данных из CSV
def get_csv_data():
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)

        # Преобразуем данные в формат словаря для JSON-ответа
        return {
            "timestamp": df["timestamp"].tolist(),
            "sensor1": df["sensor1"].tolist(),
            "sensor2": df["sensor2"].tolist(),
            "sensor3": df["sensor3"].tolist(),
            "sensor4": df["sensor4"].tolist(),
            "sensor5": df["sensor5"].tolist(),
        }
    else:
        return {
            "timestamp": [],
            "sensor1": [],
            "sensor2": [],
            "sensor3": [],
            "sensor4": [],
            "sensor5": [],
        }

@app.route('/')
def home():
    return render_template('animated_chart.html')

@app.route('/api/data')
def get_data():
    data = get_csv_data()
    return jsonify(data)

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=80, debug=True)
