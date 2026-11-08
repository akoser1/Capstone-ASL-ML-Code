
import asyncio
from collections import Counter, deque

import joblib
import pandas as pd
from bleak import BleakScanner, BleakClient

from src.config import MODEL_PATH, FEATURE_COLUMNS

# Same Bluetooth settings as your collection script
DEVICE_NAME = "ESP32-BLE"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

# Your glove currently has 10 flex sensors
NUM_FLEX = 10

# ESP32 sends:
# 10 flex readings + 1 contact mask + 7 IMU values
EXPECTED_VALUES = 18

# Use the last 5 predictions for smoothing
prediction_history = deque(maxlen=5)


async def main():
    print("Loading trained Random Forest...")

    model = joblib.load(MODEL_PATH)

    if len(FEATURE_COLUMNS) != NUM_FLEX:
        raise ValueError(
            "Your config.py must define exactly 10 flex features."
        )

    print("Searching for ESP32...")

    device = await BleakScanner.find_device_by_name(
        DEVICE_NAME,
        timeout=15
    )

    if device is None:
        print("ESP32 not found. Check Bluetooth and power.")
        return

    print("Connecting to ESP32...")

    packet_count = 0

    def on_data(sender, data):
        nonlocal packet_count

        try:
            # Convert BLE message into a list of values
            values = data.decode("utf-8").strip().split(",")

            if len(values) != EXPECTED_VALUES:
                print(
                    f"Skipped packet: expected {EXPECTED_VALUES} "
                    f"values, received {len(values)}"
                )
                return

            # Extract only the first 10 flex sensor readings
            flex_values = [
                int(value)
                for value in values[:NUM_FLEX]
            ]

            if any(value < 0 or value > 4095 for value in flex_values):
                return

            # Create the same input format used for training
            X_live = pd.DataFrame(
                [flex_values],
                columns=FEATURE_COLUMNS
            )

            # Predict ASL letter
            prediction = model.predict(X_live)[0]

            # Get Random Forest probability estimate
            probabilities = model.predict_proba(X_live)[0]
            confidence = max(probabilities)

            # Smooth predictions
            prediction_history.append(prediction)

            stable_prediction = Counter(
                prediction_history
            ).most_common(1)[0][0]

            packet_count += 1

            # Print every 5th reading to avoid flooding terminal
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
