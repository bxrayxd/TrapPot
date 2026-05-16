import pandas as pd
import joblib
import time
import os
import sys

sys.stdout.reconfigure(line_buffering=True)

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


def clean_number(value):
    if value in ["-", "", "(empty)"]:
        return 0
    return value


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

# Wait until Zeek creates conn.log with its header.
while not os.path.exists(LOG_FILE) or os.path.getsize(LOG_FILE) == 0:
    time.sleep(1)

with open(LOG_FILE, "r") as f:
    while True:
        line = f.readline()
        if not line:
            time.sleep(1)
            continue
        if line.startswith("#"):
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
                    "id.orig_p": parts[3],
                    "id.resp_p": parts[5],
                    "duration": clean_number(parts[8]),
                    "orig_bytes": clean_number(parts[9]),
                    "resp_bytes": clean_number(parts[10]),
                    "orig_pkts": clean_number(parts[16]),
                    "orig_ip_bytes": clean_number(parts[17]),
                    "resp_pkts": clean_number(parts[18]),
                    "resp_ip_bytes": clean_number(parts[19]),
                    "proto": parts[6],
                    "service": parts[7],
                    "conn_state": parts[11],
                }
                predict_threat(sample)
            except:
                continue
