import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import time
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras

# === Settings ===
CSV_PATH = 'livedata.csv'
SEQUENCE_LENGTH = 24
FEATURES = ['PM2.5', 'PM10', 'NO2', 'CO', 'O3']

# Load model
model = keras.models.load_model('model.h5', compile=False)

# Normalizer
scaler = MinMaxScaler()

# AQI Calculation function
def calculate_aqi(concentration, pollutant):
    """
    Calculate AQI based on concentration for each pollutant.
    """
    if pollutant == "PM2.5":
        breakpoints = [(0, 12, 50), (12.1, 35.4, 100), (35.5, 55.4, 150), (55.5, 150.4, 200), (150.5, 250.4, 300), (250.5, 500.4, 400)]
    elif pollutant == "PM10":
        breakpoints = [(0, 54, 50), (55, 154, 100), (155, 254, 150), (255, 354, 200), (355, 424, 300), (425, 604, 400)]
    elif pollutant == "CO":
        breakpoints = [(0, 4.4, 50), (4.5, 9.4, 100), (9.5, 12.4, 150), (12.5, 15.4, 200), (15.5, 30.4, 300), (30.5, 50, 400)]
    elif pollutant == "NO2":
        breakpoints = [(0, 53, 50), (54, 100, 100), (101, 360, 150), (361, 649, 200), (650, 1249, 300), (1250, 2049, 400)]
    elif pollutant == "O3":
        breakpoints = [(0, 54, 50), (55, 70, 100), (71, 85, 150), (86, 105, 200), (106, 200, 300), (201, 604, 400)]
    else:
        return 0  # For unrecognized pollutants

    # Find the appropriate AQI value based on the concentration
    for low, high, aqi in breakpoints:
        if low <= concentration <= high:
            return aqi
    return 0  # If concentration is out of range, return 0

def calculate_total_aqi(pm25_aqi, pm10_aqi, co_aqi, no2_aqi, o3_aqi):
    """
    Calculate the total AQI as the maximum AQI from all pollutants.
    """
    return max(pm25_aqi, pm10_aqi, co_aqi, no2_aqi, o3_aqi)

def predict_realtime():
    while True:
        try:
            df = pd.read_csv(CSV_PATH)
            print(f"Loaded {len(df)} rows.")

            if len(df) >= SEQUENCE_LENGTH:
                latest_data = df[FEATURES].tail(SEQUENCE_LENGTH)
                scaled = scaler.fit_transform(latest_data)
                X_input = np.expand_dims(scaled, axis=0)

                print("Running prediction...")
                prediction = model.predict(X_input)
                print(f"Real-time Prediction → {prediction[0]}")

                # Assuming the model's prediction corresponds to the same pollutants in the same order
                pm25_pred = prediction[0][0]  # Predicted value for PM2.5
                pm10_pred = prediction[0][1]  # Predicted value for PM10
                co_pred = prediction[0][2]    # Predicted value for CO
                no2_pred = prediction[0][3]   # Predicted value for NO2
                o3_pred = prediction[0][4]    # Predicted value for O3

                # Calculate AQI for each pollutant
                pm25_aqi = calculate_aqi(pm25_pred, "PM2.5")
                pm10_aqi = calculate_aqi(pm10_pred, "PM10")
                co_aqi = calculate_aqi(co_pred, "CO")
                no2_aqi = calculate_aqi(no2_pred, "NO2")
                o3_aqi = calculate_aqi(o3_pred, "O3")

                # Calculate the total AQI
                total_aqi = calculate_total_aqi(pm25_aqi, pm10_aqi, co_aqi, no2_aqi, o3_aqi)

                print(f"PM2.5 AQI: {pm25_aqi}, PM10 AQI: {pm10_aqi}, CO AQI: {co_aqi}, NO2 AQI: {no2_aqi}, O3 AQI: {o3_aqi}")
                print(f"Total AQI: {total_aqi}")

            else:
                print(f"Waiting for {SEQUENCE_LENGTH} rows to accumulate... (currently {len(df)})")

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(10)

# 🔥 START REALTIME PREDICTION
predict_realtime()
