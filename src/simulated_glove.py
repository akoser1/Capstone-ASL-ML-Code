
"""
Simulates live sensor readings from an ASL glove.

Uses the existing synthetic dataset until real
Bluetooth hardware is available.
"""

import time
import pandas as pd

from .config import DATA_PATH, FEATURE_COLUMNS


def simulated_sensor_stream(
    letter="A",
    sample_rate=20
):
    df = pd.read_csv(DATA_PATH)

    # Select measurements for the chosen letter.
    samples = df[df["letter"] == letter]

    if samples.empty:
        raise ValueError(
            f"No samples found for letter {letter}"
        )

    delay = 1.0 / sample_rate

    # Continuously simulate sensor measurements.
    while True:

        for _, row in samples.iterrows():

            sensor_values = {
                feature: row[feature]
                for feature in FEATURE_COLUMNS
            }

            yield sensor_values

            time.sleep(delay)
