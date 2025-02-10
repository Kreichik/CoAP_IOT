import eventlet

eventlet.monkey_patch()  # Должен быть до всех остальных импортов!

from flask import Flask, render_template
from flask_socketio import SocketIO
import pandas as pd
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

CSV_FILE = "/home/iot/Desktop/CoAP_IOT/sensor_data.csv"


@app.route("/")
def index():
    return render_template("index.html")


def stream_data():
    """Функция для чтения данных из CSV и отправки в браузер."""
    last_row_count = 0  # Количество строк в последнем чтении
    while True:
        try:
            df = pd.read_csv(CSV_FILE)  # Читаем CSV-файл
            new_row_count = len(df)

            if new_row_count > last_row_count:  # Если появились новые данные
                latest_data = df.iloc[-1].to_dict()  # Берём последнюю строку
                socketio.emit("update_chart", latest_data)  # Отправляем в браузер
                last_row_count = new_row_count

            time.sleep(2)  # Обновляем данные каждые 2 секунды
        except Exception as e:
            print("Ошибка при чтении CSV:", e)


@socketio.on("connect")
def on_connect():
    print("Клиент подключился!")


if __name__ == "__main__":
    socketio.start_background_task(stream_data)  # Запускаем поток обновления данных
    socketio.run(app, host="0.0.0.0", port=80, debug=True)
