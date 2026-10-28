
"""Synthetic ASL-like measurements ONLY for testing software, not actual gesture patterns."""

import numpy as np
import pandas as pd
from src.config import DATA_PATH, FEATURE_COLUMNS

rng = np.random.default_rng(42) # Creates reproducible random numbers
rows = []

# Generates data for letters A-Z
for letter_idx, letter in enumerate("ABCDEFGHIJKLMNOPQRSTUVWXYZ"): 
    flex_center = rng.integers(500, 3500, size=11) # Creates 11 baseline flex sensor readings for each letter
    contact_center = rng.integers(0, 2, size=5) # Creates 5 binary contac sensor states
    accel_center = rng.normal([0, 0, 9.81], [2, 2, 2]) # Generates 3 acceleration values
    gyro_center = rng.normal(0, 0.6, size=3)  # rad/s and generates 3 gyroscope values

    quat_center = rng.normal(size=4) # Generates 4 normalized orientation values
    quat_center /= np.linalg.norm(quat_center)

    for trial in range(10): # Simulates 10 separate recording atempts per letter
        trial_flex = flex_center + rng.normal(0, 55, size=11)
        trial_accel = accel_center + rng.normal(0, 0.25, size=3)
        trial_gyro = gyro_center + rng.normal(0, 0.04, size=3)

        trial_quat = quat_center + rng.normal(0, 0.02, size=4)
        trial_quat /= np.linalg.norm(trial_quat)

        for sample in range(20): # Generates 20 measurements per recording attempt
            flex = np.clip(
                np.rint(trial_flex + rng.normal(0, 25, size=11)),
                0,
                4095
            ).astype(int)

            contacts = contact_center.copy()

            if rng.random() < 0.025:
                j = rng.integers(0, 5)
                contacts[j] = 1 - contacts[j]

            accel = trial_accel + rng.normal(0, 0.12, size=3)
            gyro = trial_gyro + rng.normal(0, 0.02, size=3)

            quat = trial_quat + rng.normal(0, 0.01, size=4)
            quat /= np.linalg.norm(quat)

            rows.append([
                *flex,
                *contacts,
                *accel,
                *gyro,
                *quat,
                letter,
                f"{letter}_{trial}"
            ])

DATA_PATH.parent.mkdir(parents=True, exist_ok=True)

df = pd.DataFrame(
    rows,
    columns=FEATURE_COLUMNS + ["letter", "trial_id"]
)

df.to_csv(DATA_PATH, index=False) # Saves everything into datatset.csv

print(
    f"Generated {len(df)} dummy samples "
    f"with {len(FEATURE_COLUMNS)} features: {DATA_PATH}"
)
