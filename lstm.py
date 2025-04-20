import pandas as pd
import numpy as np
from tensorflow.keras.models import load_model
import time
from sklearn.preprocessing import MinMaxScaler

# === Settings ===
CSV_PATH = 'livedata.csv'
MODEL_PATH = 'model.h5'
SEQUENCE_LENGTH = 24  # same as your training sequence length
FEATURES = ['PM2.5', 'PM10', 'NO2', 'CO', 'O3']

# === Load the model ===
model = load_model(MODEL_PATH)

# === Normalizer (should be same used during training) ===
scaler = MinMaxScaler()

def predict_realtime():
    while True:
        try:
            df = pd.read_csv(CSV_PATH)

            # Make sure we have enough rows
            if len(df) >= SEQUENCE_LENGTH:
                latest_data = df[FEATURES].tail(SEQUENCE_LENGTH)

                # Normalize input based on the current window (better if same scaler used during training)
                scaled = scaler.fit_transform(latest_data)

                X_input = np.expand_dims(scaled, axis=0)  # shape: (1, sequence_len, num_features)

                prediction = model.predict(X_input)
                print(f"Real-time Prediction → {prediction[0]}")

            else:
                print(f"Waiting for {SEQUENCE_LENGTH} rows to accumulate...")

        except Exception as e:
            print(f"Error: {e}")

        time.sleep(10)  # every 10 seconds
