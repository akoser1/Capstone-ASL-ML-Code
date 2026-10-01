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
        420,
        315,
        510,
        280,
        390
    ]

    letter = predict_letter(
        model,
        sensor_values
    )

    print("Predicted letter:", letter)
