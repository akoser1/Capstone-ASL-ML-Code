# Loads saved model and classifies new sensor measurements

import pandas as pd
import joblib

from .config import (
    MODEL_PATH,
    FEATURE_COLUMNS
)


def load_model():

    model = joblib.load(MODEL_PATH)

    return model


def predict_letter(model, sensor_values):

    # Convert sensor readings into DataFrame
    data = pd.DataFrame(
        [sensor_values],
        columns=FEATURE_COLUMNS
    )

    # Generate prediction
    prediction = model.predict(data)

    return prediction[0]


if __name__ == "__main__":

    model = load_model()

    # Example sensor readings (change this)
    sensor_values = [
        # 11 flex sensors
        1200, 1500, 1800, 1400, 1600,
        1300, 1700, 1900, 1250, 1550, 1450,

        # 5 contact sensors
        1, 0, 1, 0, 0,

        # Accelerometer X, Y, Z
        0.0, 0.0, 9.81,

        # Gyroscope X, Y, Z
        0.0, 0.0, 0.0,

        # Quaternion W, X, Y, Z
        1.0, 0.0, 0.0, 0.0
    ]

    letter = predict_letter(
        model,
        sensor_values
    )

    print("Predicted letter:", letter)
