import pandas as pd
import numpy as np
import time
import tflite_runtime.interpreter as tflite
from sklearn.preprocessing import MinMaxScaler

# === SETTINGS ===
CSV_PATH = '/home/project/Desktop/livedata.csv'
TFLITE_MODEL_PATH = '/home/project/Desktop/aqi_lstm_model.h5'
SEQUENCE_LENGTH = 24  # same as training
FEATURES = ['PM2.5', 'PM10', 'NO2', 'CO', 'O3']

# === Load TFLite Model ===
interpreter = tflite.Interpreter(model_path=TFLITE_MODEL_PATH)
interpreter.allocate_tensors()

# Get input/output details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()

# Initialize MinMaxScaler (load original scaler if saved during training)
scaler = MinMaxScaler()

# === Real-time Prediction Function ===
def predict_realtime():
    while True:
        try:
            df = pd.read_csv(CSV_PATH)

            if len(df) >= SEQUENCE_LENGTH:
                latest_data = df[FEATURES].tail(SEQUENCE_LENGTH)

                # Normalize based on current sample (OR use stored scaler)
                scaled = scaler.fit_transform(latest_data)

                # Reshape for model: (1, sequence_len, features)
                input_data = np.expand_dims(scaled, axis=0).astype(np.float32)

                # Set input tensor
                interpreter.set_tensor(input_details[0]['index'], input_data)

                # Run inference
                interpreter.invoke()

                # Get result
                prediction = interpreter.get_tensor(output_details[0]['index'])
                print(f"🧠 Real-time Prediction: {prediction[0]}")

            else:
                print(f"Waiting for {SEQUENCE_LENGTH} samples in {CSV_PATH}...")

        except Exception as e:
            print(f"❗ Error: {e}")

        time.sleep(10)
