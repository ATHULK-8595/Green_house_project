# Smart Greenhouse Monitoring System

A full-stack IoT solution to **monitor** and **control** your greenhouse with real-time dashboards, historical logging, and automated actions.

---

## Features

- Live real-time dashboard of temperature, humidity, soil moisture, and rain status.
- Automated control of window/cooling and irrigation via relays based on sensor thresholds.
- All data and relay actions logged in an SQLite database for historical viewing.
- Easily review historical sensor and actuator activity in the dashboard log table.
- ESP32 microcontroller sends sensor and relay updates to a Python Flask server over Wi-Fi.
- Dual-core ESP32 programming: sensors and controls on one core, HTTP uploads on another.
- RESTful API endpoints for posting sensor data and fetching current/logged records.
- Responsive frontend built with HTML/CSS/JS (Tailwind).

---

## Hardware

- ESP32 development board
- Adafruit SHT31 sensor (Temp/Humidity)
- Capacitive soil moisture sensor
- Rain sensor (analog+digital)
- 2x relay modules (window/cooling, water/irrigation)

---

## Software Components

### 1. ESP32 Arduino Code

- Reads sensors (every second).
- Controls relays based on thresholds (continuously).
- Posts latest readings and relay statuses as JSON via HTTP to Flask (~every 5 seconds).
- Dual-core tasks: sensor/relay (Core 0), data upload (Core 1).

### 2. Flask Server (`app.py`)

- Receives data at `/api/sensor_data` (POST, from ESP32).
- Serves current sensor data at `/api/latest` (GET).
- Serves historical log at `/api/logs` (GET, last 100 records).
- Serves dashboard frontend at root (`/`).
- Stores all information in `greenhouse.db` using SQLite.

### 3. Dashboard Frontend (`dashboard.html`)

- Shows current sensor readings and relay statuses.
- Shows historical log table for last 100 entries.
- JavaScript fetches `/api/latest` and `/api/logs` and auto-updates, no reload needed.
- Mobile-responsive interface (Tailwind CSS).

---

## Quick Start

1. **Clone and Setup**

    ```
    git clone https://github.com/yourusername/smart-greenhouse-monitor.git
    cd smart-greenhouse-monitor
    python3 -m venv env
    source env/bin/activate
    pip install flask flask_cors
    ```

2. **Run Flask Server**

    ```
    python app.py
    # Visit http://localhost:5000/ in your browser.
    ```

3. **Flash ESP32 Code**

    - Edit WiFi and server IP in the Arduino sketch.
    - Upload to ESP32.

4. **View the Dashboard**

    - Open `http://localhost:5000/`
    - Watch real-time data and log updates.

---

## API Endpoints

- `POST /api/sensor_data` — ESP32 posts readings/relay state here.
- `GET /api/latest` — Get latest sensor and relay data.
- `GET /api/logs` — Get the last 100 data records for logging/historical view.

---

## Customization

- Change sensor thresholds in ESP32 code as needed.
- Adjust polling intervals for dashboard and ESP32 HTTP uploads.
- Add more sensor/relay support in software and hardware.

---

## TODO

- Add alerts/notifications (email/push)
- Add manual controls for relays from dashboard
- Add chart/graph history for trends

---

## Authors & License

Built by Athulkbs

