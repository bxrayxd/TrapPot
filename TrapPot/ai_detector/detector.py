import os
import sys
import time
import json
from datetime import datetime, timezone

import joblib
import pandas as pd

sys.stdout.reconfigure(line_buffering=True)

model = joblib.load("trappot_model.pkl")
le = joblib.load("label_encoder.pkl")

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

NUMERIC_FEATURES = [
    "id.orig_p",
    "id.resp_p",
    "duration",
    "orig_bytes",
    "resp_bytes",
    "orig_pkts",
    "orig_ip_bytes",
    "resp_pkts",
    "resp_ip_bytes",
]

CATEGORY_MAPS = {
    "proto": {"icmp": 0, "tcp": 1, "udp": 2},
    "service": {"-": 0, "dhcp": 1, "dns": 2, "http": 3, "irc": 4, "ssh": 5, "ssl": 6},
    "conn_state": {value: index for index, value in enumerate(le.classes_)},
}

LOG_FILE = "/logs/conn.log"
DETECTION_LOG_FILE = "/logs/detections.json"


def clean_number(value):
    if value in ["-", "", "(empty)"]:
        return 0
    return value


def encode_category(column, value):
    mapping = CATEGORY_MAPS[column]
    return mapping.get(str(value), mapping.get("-", 0))


def predict_threat(data_row):
    df = pd.DataFrame([data_row], columns=FEATURES)

    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    for col in ["proto", "service", "conn_state"]:
        df[col] = df[col].apply(lambda value: encode_category(col, value))

    prediction = model.predict(df)[0]
    print(f"ALERT: {prediction} detected!")
    with open(DETECTION_LOG_FILE, "a") as detections:
        detections.write(json.dumps({
            "detected_at": datetime.now(timezone.utc).isoformat(),
            "prediction": str(prediction),
            **data_row,
        }) + "\n")


print("TrapPot AI is watching the network...")

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

        parts = line.split("\t")
        if len(parts) > 19:
            try:
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
            except Exception:
                continue
