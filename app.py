from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime

app = Flask(__name__)
CORS(app)

def init_db():
    conn = sqlite3.connect('greenhouse.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            temperature REAL,
            humidity REAL,
            moisture INTEGER,
            rain_analog INTEGER,
            rain_digital INTEGER,
            relay_window TEXT,
            relay_water TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/api/sensor_data', methods=['POST'])
def sensor_data():
    # Accept data from ESP32
    data = request.json
    conn = sqlite3.connect('greenhouse.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO logs (timestamp, temperature, humidity, moisture, rain_analog, rain_digital, relay_window, relay_water)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        data.get('temperature'),
        data.get('humidity'),
        data.get('moisture'),
        data.get('rain_analog'),
        data.get('rain_digital'),
        data.get('relay_window'),
        data.get('relay_water')
    ))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

@app.route('/api/latest', methods=['GET'])
def latest():
    # Return the most recent record
    conn = sqlite3.connect('greenhouse.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    if row:
        keys = ['id', 'timestamp', 'temperature', 'humidity', 'moisture', 'rain_analog', 'rain_digital', 'relay_window', 'relay_water']
        return jsonify(dict(zip(keys, row)))
    else:
        return jsonify({})

@app.route('/api/logs', methods=['GET'])
def logs():
    conn = sqlite3.connect('greenhouse.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 100')
    rows = cursor.fetchall()
    conn.close()
    keys = ['id', 'timestamp', 'temperature', 'humidity', 'moisture', 'rain_analog', 'rain_digital', 'relay_window', 'relay_water']
    logs = [dict(zip(keys, row)) for row in rows]
    return jsonify(logs)

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port="1234")

