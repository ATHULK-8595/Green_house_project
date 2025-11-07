from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
from datetime import datetime
from flask_socketio import SocketIO

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app)

esp32_ip = None

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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS control_limits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            temp_high REAL,
            humidity_high REAL,
            moisture_low INTEGER
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM control_limits")
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO control_limits (temp_high, humidity_high, moisture_low) VALUES (?, ?, ?)", (28.0, 80.0, 2500))
    conn.commit()
    conn.close()

@app.route('/api/sensor_data', methods=['POST'])
def sensor_data():
    # Accept data from ESP32
    data = request.json
    print(data)
    conn = sqlite3.connect('greenhouse.db')
    cursor = conn.cursor()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    cursor.execute('''
        INSERT INTO logs (timestamp, temperature, humidity, moisture, rain_analog, rain_digital, relay_window, relay_water)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        timestamp,
        data.get('temperature'),
        data.get('humidity'),
        data.get('moisture'),
        data.get('rain_analog'),
        data.get('rain_digital'),
        data.get('relay_window'),
        data.get('relay_water')
    ))
    conn.commit()
    
    # After saving, fetch the newly inserted record to broadcast
    cursor.execute('SELECT * FROM logs ORDER BY id DESC LIMIT 1')
    new_log_row = cursor.fetchone()
    conn.close()

    if new_log_row:
        keys = ['id', 'timestamp', 'temperature', 'humidity', 'moisture', 'rain_analog', 'rain_digital', 'relay_window', 'relay_water']
        new_log_dict = dict(zip(keys, new_log_row))
        socketio.emit('new_data', new_log_dict)

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

@app.route('/api/get_limits', methods=['GET'])
def get_limits():
    conn = sqlite3.connect('greenhouse.db')
    cursor = conn.cursor()
    cursor.execute('SELECT temp_high, humidity_high, moisture_low FROM control_limits ORDER BY id DESC LIMIT 1')
    row = cursor.fetchone()
    conn.close()
    if row:
        keys = ['temp_high', 'humidity_high', 'moisture_low']
        return jsonify(dict(zip(keys, row)))
    else:
        return jsonify({})

@app.route('/api/set_limits', methods=['POST'])
def set_limits():
    data = request.json
    conn = sqlite3.connect('greenhouse.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE control_limits SET temp_high = ?, humidity_high = ?, moisture_low = ? WHERE id = 1", 
                   (data.get('temp_high'), data.get('humidity_high'), data.get('moisture_low')))
    conn.commit()
    conn.close()
    return jsonify({"status": "success"})

    return jsonify({"status": "success"})

@app.route('/api/register_esp', methods=['POST'])
def register_esp():
    global esp32_ip
    data = request.json
    esp32_ip = data.get('ip')
    print(f"ESP32 registered with IP: {esp32_ip}")
    return jsonify({"status": "success"})

@app.route('/api/reboot_esp', methods=['POST'])
def reboot_esp():
    if esp32_ip:
        try:
            import requests
            requests.post(f'http://{esp32_ip}/reboot')
            return jsonify({"status": "success"})
        except Exception as e:
            print(e)
            return jsonify({"status": "error", "message": "Failed to reboot ESP32"})
    return jsonify({"status": "error", "message": "ESP32 IP address not registered"})


if __name__ == '__main__':
    init_db()
    socketio.run(app, debug=True, host='0.0.0.0', port=1234)

# this code is for server