import pandas as pd
import joblib
import time
import os

# Load the "Brain"
model = joblib.load("trappot_model.pkl")
le = joblib.load("label_encoder.pkl")

# These are the 12 features your model expects
FEATURES = [
    "id.orig_p",
    "id.resp_p",
    "duration",
    "orig_bytes",
    "resp_bytes",
    "orig_pkts",
    "orig_ip_bytes",
    "resp_pkts",
    "resp_ip_bytes",
    "proto",
    "service",
    "conn_state",
]

LOG_FILE = "/logs/conn.log"


def predict_threat(data_row):
    # Prepare data for prediction
    df = pd.DataFrame([data_row], columns=FEATURES)

    # Label Encode categorical strings
    for col in ["proto", "service", "conn_state"]:
        df[col] = le.fit_transform(df[col].astype(str))

    # Prediction
    prediction = model.predict(df)[0]
    print(f"🚨 ALERT: {prediction} detected!")


print("🔍 TrapPot AI is watching the network...")

# Tail the log file
if not os.path.exists(LOG_FILE):
    open(LOG_FILE, "a").close()

with open(LOG_FILE, "r") as f:
    f.seek(0, os.SEEK_END)
    while True:
        line = f.readline()
        if not line:
            time.sleep(1)
            continue

        # Zeek logs are tab-separated. We parse the 12 features here.
        # This is a simplified parser for the demo
        parts = line.split("\t")
        if len(parts) > 10:
            # Map the specific Zeek log columns to your 12 features
            # (Note: Actual column indices depend on Zeek version)
            try:
                # Example mapping logic
                sample = {
                    "id.orig_p": parts[2],
                    "id.resp_p": parts[4],
                    "duration": parts[8],
                    "orig_bytes": parts[9],
                    "resp_bytes": parts[10],
                    "orig_pkts": parts[16],
                    "orig_ip_bytes": parts[17],
                    "resp_pkts": parts[18],
                    "resp_ip_bytes": parts[19],
                    "proto": parts[6],
                    "service": parts[7],
                    "conn_state": parts[11],
                }
                predict_threat(sample)
            except:
                continue
