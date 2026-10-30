
"""
Live ASL letter prediction.

Currently uses simulated glove readings.
Later, replace the input with Bluetooth readings.
"""

from collections import deque, Counter

import joblib
import numpy as np
import pandas as pd

from .config import MODEL_PATH, FEATURE_COLUMNS
from .simulated_glove import simulated_sensor_stream


def validate_sensor_data(sensor_data):

    # Check that all expected features are present.
    if set(sensor_data) != set(FEATURE_COLUMNS):
        raise ValueError(
            "Sensor data does not match expected features."
        )

    # Preserve the exact training feature order.
    values = np.array(
        [sensor_data[name] for name in FEATURE_COLUMNS],
        dtype=float
    )

    if not np.isfinite(values).all():
        raise ValueError(
            "Sensor data contains invalid numbers."
        )

    return pd.DataFrame(
        [values],
        columns=FEATURE_COLUMNS
    )


def main():

    print("Starting Live ASL Prediction...")

    # Load the previously trained Random Forest.
    model = joblib.load(MODEL_PATH)

    # Store the last 5 predictions for smoothing.
    prediction_history = deque(maxlen=5)

    # Change this to test another letter.
    selected_letter = "B"

    print("Simulating letter:", selected_letter)
    print("Press Ctrl+C to stop.\n")

    try:

        stream = simulated_sensor_stream(
            letter=selected_letter,
            sample_rate=20
        )

        for sensor_data in stream:

            X = validate_sensor_data(sensor_data)

            # Predict the letter.
            prediction = model.predict(X)[0]

            # Get the model's probability estimate.
            probabilities = model.predict_proba(X)[0]
            confidence = float(np.max(probabilities))

            prediction_history.append(prediction)

            # Most common prediction from recent readings.
            stable_prediction = Counter(
                prediction_history
            ).most_common(1)[0][0]

            print(
                f"Raw: {prediction} | "
                f"Smoothed: {stable_prediction} | "
                f"RF probability: {confidence:.1%}"
            )

    except KeyboardInterrupt:
        print("\nLive prediction stopped.")


if __name__ == "__main__":
    main()
