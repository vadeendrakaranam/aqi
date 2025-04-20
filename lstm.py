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

                # If model returns 5 predictions (one for each feature)
                if prediction.shape[1] == 5:
                    results = dict(zip(FEATURES, prediction[0]))
                    print("Real-time Predictions:")
                    for pollutant, value in results.items():
                        print(f"{pollutant}: {value:.2f}")
                else:
                    print(f"Unexpected prediction shape: {prediction.shape}")

            else:
                print(f"Waiting for {SEQUENCE_LENGTH} rows to accumulate... (currently {len(df)})")

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(10)

# 🔥 START REALTIME PREDICTION
predict_realtime()
