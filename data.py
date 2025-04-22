import serial
import time
import csv
from datetime import datetime
import os
import glob
import threading

# === Global Variables ===
latest_pm25 = None
latest_pm10 = None
latest_co = None
latest_no2 = None
latest_o3 = None

# === CSV Setup ===
csv_file = "livedata.csv"
MAX_ROWS = 1440  # 1 day of data at 1-minute intervals

# Initialize the CSV file if it doesn't exist or is empty
if not os.path.exists(csv_file) or os.stat(csv_file).st_size == 0:
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "PM2.5", "PM10", "NO2", "CO", "O3"])

# === Read PM2.5 and PM10 from SDS011 ===
def read_pm_sensor():
    global latest_pm25, latest_pm10
    try:
        ser_pm = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=2)
        while True:
            data = ser_pm.read(10)
            if len(data) == 10 and data[0] == 0xAA and data[1] == 0xC0 and data[9] == 0xAB:
                checksum = sum(data[2:8]) % 256
                if checksum == data[8]:
                    latest_pm25 = (data[2] + data[3] * 256) / 10.0
                    latest_pm10 = (data[4] + data[5] * 256) / 10.0
            time.sleep(2)
    except Exception as e:
        print("Error in PM sensor thread:", e)

# === Read CO, NO2, O3 from Arduino ===
def read_gas_sensor():
    global latest_co, latest_no2, latest_o3
    try:
        ports = glob.glob('/dev/ttyACM0') + glob.glob('/dev/ttyACM*')
        if len(ports) == 0:
            print("No Arduino device found.")
            return
        ser_gas = serial.Serial(ports[0], 9600)

        while True:
            if ser_gas.in_waiting > 0:
                line = ser_gas.readline().decode('utf-8').strip()
                parts = line.split(',')
                if len(parts) == 3:
                    try:
                        latest_co = float(parts[0])
                        latest_no2 = float(parts[1])
                        latest_o3 = float(parts[2])
                    except ValueError:
                        print("Invalid float values:", parts)
            time.sleep(1)
    except Exception as e:
        print("Error in Gas sensor thread:", e)

# === Combine, Save Data ===
def write_combined_csv(interval=15, max_rows=MAX_ROWS):
    while True:
        if all(val is not None for val in [latest_pm25, latest_pm10, latest_no2, latest_co, latest_o3]):
            timestamp = datetime.now().strftime("%d-%m-%Y %H:%M")
            row = [timestamp, latest_pm25, latest_pm10, latest_no2, latest_co, latest_o3]

            try:
                # Read existing rows
                with open(csv_file, 'r') as f:
                    lines = f.readlines()

                if len(lines) > 1:
                    data_lines = lines[1:]
                else:
                    data_lines = []

                data_lines.append(','.join(map(str, row)) + '\n')

                # Keep only the latest max_rows
                trimmed_data = data_lines[-max_rows:]

                # Write updated data with proper cleaning of columns
                with open(csv_file, 'w', newline='') as f:
                    f.write(lines[0])  # header
                    f.writelines(trimmed_data)

                print("Saved:", row)
            except Exception as e:
                print("Error writing CSV:", e)
        else:
            print("Waiting for all sensors to initialize...")
        time.sleep(interval)

# === Start Threads ===
threading.Thread(target=read_pm_sensor, daemon=True).start()
threading.Thread(target=read_gas_sensor, daemon=True).start()
threading.Thread(target=write_combined_csv, daemon=True).start()

# === Keep Main Thread Alive ===
while True:
    time.sleep(60)
