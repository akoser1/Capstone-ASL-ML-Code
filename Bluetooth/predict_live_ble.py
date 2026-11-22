
import asyncio
from collections import Counter, deque

import joblib
import pandas as pd
from bleak import BleakScanner, BleakClient

from src.config import MODEL_PATH, FEATURE_COLUMNS


# ---------- Bluetooth settings ----------
DEVICE_NAME = "ESP32-BLE"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"


# ---------- Sensor configuration ----------
NUM_FLEX = 10
NUM_CONTACT = 4
NUM_IMU = 7

# ESP32 sends:
# 10 flex readings
# 4 contact readings (0 or 1)
# 7 IMU readings
EXPECTED_VALUES = NUM_FLEX + NUM_CONTACT + NUM_IMU

# Model uses 10 flex + 4 contact = 14 features
EXPECTED_FEATURES = NUM_FLEX + NUM_CONTACT

# Contact order:
# C1C2 = Thumb + Index
# C1C3 = Thumb + Middle
# C1C4 = Thumb + Ring
# C1C5 = Thumb + Pinky

SENSOR_COLUMNS = [
    "MC0", "MC1", "MC2", "MC3",
    "MC4", "MC5", "MC6", "MC7",
    "Direct1", "Direct2",
    "C1C2", "C1C3", "C1C4", "C1C5",
]

# Smooth the last 5 predictions
prediction_history = deque(maxlen=5)


async def main():
    print("Loading trained Random Forest...")

    model = joblib.load(MODEL_PATH)

    # Verify model and configuration match the glove
    if len(FEATURE_COLUMNS) != EXPECTED_FEATURES:
        raise ValueError(
            "config.py must define 14 features: "
            "10 flex + 4 contact."
        )

    if list(FEATURE_COLUMNS) != SENSOR_COLUMNS:
        raise ValueError(
            "FEATURE_COLUMNS in config.py must match "
            "the ESP32 sensor order."
        )

    if model.n_features_in_ != EXPECTED_FEATURES:
        raise ValueError(
            f"Trained model expects {model.n_features_in_} "
            f"features, but the glove provides "
            f"{EXPECTED_FEATURES}. Run python main.py "
            f"to retrain."
        )

    print("Searching for ESP32...")

    device = await BleakScanner.find_device_by_name(
        DEVICE_NAME,
        timeout=15,
    )

    if device is None:
        print("ESP32 not found. Check Bluetooth and power.")
        return

    print("Connecting to ESP32...")

    packet_count = 0

    def on_data(sender, data):
        nonlocal packet_count

        try:
            # Decode comma-separated BLE packet
            values = data.decode("utf-8").strip().split(",")

            if len(values) != EXPECTED_VALUES:
                print(
                    f"Skipped packet: expected "
                    f"{EXPECTED_VALUES} values, "
                    f"received {len(values)}"
                )
                return

            # ---------- Flex sensors ----------
            flex_values = [
                int(value)
                for value in values[:NUM_FLEX]
            ]

            # ---------- Contact sensors ----------
            contact_values = [
                int(value)
                for value in values[
                    NUM_FLEX:NUM_FLEX + NUM_CONTACT
                ]
            ]

            # ---------- IMU ----------
            # Parse IMU readings, but don't use them
            # for prediction because the IMU is disabled.
            imu_values = [
                float(value)
                for value in values[
                    NUM_FLEX + NUM_CONTACT:
                ]
            ]

            # ---------- Validate readings ----------
            if any(
                value < 0 or value > 4095
                for value in flex_values
            ):
                return

            if any(
                value not in (0, 1)
                for value in contact_values
            ):
                return

            # ---------- Build model input ----------
            sensor_values = flex_values + contact_values

            X_live = pd.DataFrame(
                [sensor_values],
                columns=SENSOR_COLUMNS,
            )

            # ---------- Predict ----------
            prediction = model.predict(X_live)[0]

            probabilities = model.predict_proba(X_live)[0]
            confidence = max(probabilities)

            # ---------- Smooth predictions ----------
            prediction_history.append(prediction)

            stable_prediction = Counter(
                prediction_history
            ).most_common(1)[0][0]

            packet_count += 1

            # Print every 5th prediction
            if packet_count % 5 == 0:
                print(
                    f"Predicted: {prediction} | "
                    f"Smoothed: {stable_prediction} | "
                    f"RF probability: {confidence:.1%}"
                )

        except (ValueError, UnicodeDecodeError) as error:
            print("Invalid BLE data:", error)

    try:
        async with BleakClient(device, timeout=30) as client:
            await client.start_notify(CHAR_UUID, on_data)

            print("Connected!")
            print("Waiting for sensor readings...")
            print("Make an ASL handshape.")
            print("Press Ctrl+C to stop.\n")

            while True:
                await asyncio.sleep(1)

    except asyncio.CancelledError:
        pass

    except KeyboardInterrupt:
        pass

    print("\nLive prediction stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nDisconnected.")
