import subprocess
import csv
from datetime import datetime
import os
import re

# CSV File name
csv_file = "livedata.csv"

# Create CSV file with header if it doesn't exist
if not os.path.exists(csv_file):
    with open(csv_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Time", "PM2.5", "PM10", "NO2", "CO", "O3"])

def extract_values(text, keys):
    values = {}
    for key in keys:
        match = re.search(fr"{key}[:=]?\s*([\d.]+)", text)
        values[key] = float(match.group(1)) if match else None
    return values

def get_pm_data():
    output = subprocess.check_output(["python3", "pm.py"], universal_newlines=True)
    values = extract_values(output, ["PM2.5", "PM10"])
    return values.get("PM2.5"), values.get("PM10")

def get_gas_data():
    output = subprocess.check_output(["python3", "11.py"], universal_newlines=True)
    values = extract_values(output, ["NO2", "CO", "O3"])
    return values.get("NO2"), values.get("CO"), values.get("O3")

def write_to_csv(data_row):
    with open(csv_file, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data_row)

def main():
    try:
        pm25, pm10 = get_pm_data()
        no2, co, o3 = get_gas_data()
        current_time = datetime.now().strftime("%d-%m-%Y %H:%M")

        row = [current_time, pm25, pm10, no2, co, o3]
        print("Collected Data:", row)

        write_to_csv(row)

    except Exception as e:
        print("Error collecting data:", e)

if __name__ == "__main__":
    main()
