import serial
import time
import csv
from datetime import datetime
import os

# Connect to SDS011 via ttyUSB0
ser = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=2)

csv_file = "pm_data.csv"

# Write header only if file is new or empty
write_header = not os.path.exists(csv_file) or os.stat(csv_file).st_size == 0

def read_sds011():
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        if write_header:
            writer.writerow(["Timestamp", "PM2.5 (µg/m³)", "PM10 (µg/m³)"])
            file.flush()  # Flush header immediately

        while True:
            data = ser.read(10)
            if len(data) == 10 and data[0] == 0xAA and data[1] == 0xC0 and data[9] == 0xAB:
                checksum = sum(data[2:8]) % 256
                if checksum == data[8]:
                    pm25 = (data[2] + data[3]*256) / 10.0
                    pm10 = (data[4] + data[5]*256) / 10.0
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"[{timestamp}] PM2.5: {pm25} µg/m³, PM10: {pm10} µg/m³")
                    writer.writerow([timestamp, pm25, pm10])
                    file.flush()  # 💾 Flush to save instantly
                else:
                    print(f"Checksum error: {checksum} != {data[8]}")
            else:
                print("Data format error or not a sensor packet")

            time.sleep(2)

read_sds011()
