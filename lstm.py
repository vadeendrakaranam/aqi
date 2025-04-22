import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import time
from sklearn.preprocessing import MinMaxScaler
from tensorflow import keras
import requests
import logging
import os

# === Settings ===
CSV_PATH = 'livedata.csv'
SEQUENCE_LENGTH = 10  # Change to 10 for testing
FEATURES = ['PM2.5', 'PM10', 'NO2', 'CO', 'O3']
LABEL_COLUMN = 'AQI'
THINGSPEAK_API_KEY = '3K3DQZMFW585P1U0'
THINGSPEAK_URL = 'https://api.thingspeak.com/update.json'

# Logging setup
logging.basicConfig(filename="error_log.txt", level=logging.ERROR, 
                    format="%(asctime)s - %(levelname)s - %(message)s")

# Load model
try:
    model = keras.models.load_model('model.h5', compile=False)
    print("✅ Model loaded successfully.")
except Exception as e:
    logging.error(f"Error loading model: {e}")
    print(f"❌ Error loading model: {e}")
    exit()

scaler = MinMaxScaler()

# AQI Calculation
def calculate_aqi(concentration, pollutant):
    try:
        breakpoints = {
            "PM2.5": [(0, 12, 50), (12.1, 35.4, 100), (35.5, 55.4, 150), (55.5, 150.4, 200), (150.5, 250.4, 300), (250.5, 500.4, 400)],
            "PM10": [(0, 54, 50), (55, 154, 100), (155, 254, 150), (255, 354, 200), (355, 424, 300), (425, 604, 400)],
            "CO": [(0, 4.4, 50), (4.5, 9.4, 100), (9.5, 12.4, 150), (12.5, 15.4, 200), (15.5, 30.4, 300), (30.5, 50, 400)],
            "NO2": [(0, 53, 50), (54, 100, 100), (101, 360, 150), (361, 649, 200), (650, 1249, 300), (1250, 2049, 400)],
            "O3": [(0, 54, 50), (55, 70, 100), (71, 85, 150), (86, 105, 200), (106, 200, 300), (201, 604, 400)]
        }
        bp = breakpoints.get(pollutant, [])
        for c_low, c_high, i_low, i_high in bp:
            if c_low <= concentration <= c_high:
                aqi = ((i_high - i_low) / (c_high - c_low)) * (concentration - c_low) + i_low
                return round(aqi)
        return 0
    except Exception as e:
        logging.error(f"Error in calculate_aqi for {pollutant}: {e}")
        print(f"❌ Error calculating AQI for {pollutant}: {e}")
        return 0

# Send to ThingSpeak
def send_aqi_to_thingspeak(sensor_values, overall_aqi):
    try:
        params = {
            'api_key': THINGSPEAK_API_KEY,
            'field1': sensor_values['PM2.5'],
            'field2': sensor_values['PM10'],
            'field3': sensor_values['NO2'],
            'field4': sensor_values['CO'],
            'field5': sensor_values['O3'],
            'field6': overall_aqi
        }
        response = requests.post(THINGSPEAK_URL, params=params)
        response.raise_for_status()
        print("✅ Data sent to ThingSpeak successfully.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Error sending data to ThingSpeak: {e}")
        print(f"❌ Failed to send data to ThingSpeak. Error: {e}")

# Realtime loop
def predict_realtime():
    first_run = True
    while True:
        try:
            if not os.path.exists(CSV_PATH):
                raise FileNotFoundError(f"The CSV file at {CSV_PATH} does not exist.")
            
            df = pd.read_csv(CSV_PATH, usecols=FEATURES + ['Timestamp'])

            df.columns = df.columns.str.strip()
            df = df.drop(columns=['Timestamp'])

            print(f"\n📥 Loaded {len(df)} rows.")

            if len(df) >= SEQUENCE_LENGTH:
                latest_data = df[FEATURES].tail(SEQUENCE_LENGTH)

                if first_run:
                    scaler.fit(latest_data)
                    first_run = False

                scaled = scaler.transform(latest_data)
                X_input = np.expand_dims(scaled, axis=0)

                print("🔮 Running prediction...")

                aqi_values = {}
                for pollutant in FEATURES:
                    value = latest_data.iloc[-1][pollutant]
                    aqi = calculate_aqi(value, pollutant)
                    aqi_values[pollutant] = aqi

                print("\n📊 Individual AQI Values:")
                for key, val in aqi_values.items():
                    print(f"   • {key} AQI: {val}")

                prediction = model.predict(X_input)

                if prediction.shape != (1, 1):
                    raise ValueError(f"Expected a single value for overall AQI, but got {prediction.shape}.")
                overall_aqi = prediction[0][0]

                print(f"\n🌍 Predicted Overall AQI: {overall_aqi:.2f}")

                send_aqi_to_thingspeak(latest_data.iloc[-1], overall_aqi)

                # Model Update Step (Training with new data)
                if LABEL_COLUMN in df.columns:
                    train_data = df.dropna(subset=FEATURES + [LABEL_COLUMN]).tail(50)
                    if not train_data.empty:
                        X_train = scaler.transform(train_data[FEATURES])
                        y_train = train_data[LABEL_COLUMN].values
                        if not np.isnan(X_train).any() and not np.isnan(y_train).any():
                            model.fit(np.expand_dims(X_train[-SEQUENCE_LENGTH:], axis=0), 
                                      np.array([y_train[-1]]), 
                                      epochs=1, verbose=0)
                            model.save("model.h5")
                            print("🔁 Model weights updated with latest data.")
                        else:
                            print("⚠️ Skipping update: NaNs in training data.")
                    else:
                        print("⚠️ Skipping update: Not enough clean data to train.")
                else:
                    print("ℹ️ Skipping training: No AQI label column in CSV.")
            else:
                print(f"⏳ Waiting for {SEQUENCE_LENGTH} rows... (currently {len(df)})")

        except Exception as e:
            logging.error(f"Error in prediction loop: {e}")
            print(f"❌ Error: {e}")

        time.sleep(10)

# 🔁 START
predict_realtime()
