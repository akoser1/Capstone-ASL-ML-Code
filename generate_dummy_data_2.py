# More realistic and noise
#


"""Synthetic ASL-like sensor measurements for software testing only.

This data does NOT represent real ASL hand gestures.
Some letters intentionally have overlapping sensor patterns.
"""

import numpy as np
import pandas as pd

from src.config import DATA_PATH, FEATURE_COLUMNS

rng = np.random.default_rng(42)

LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
TRIALS_PER_LETTER = 10
SAMPLES_PER_TRIAL = 20

rows = []

# Create shared prototype patterns.
# Letters in the same group have similar measurements.
NUM_GROUPS = 7

group_flex = rng.uniform(900, 3100, size=(NUM_GROUPS, 11))
group_accel = rng.normal(
    [0, 0, 9.81], [1.2, 1.2, 1.2],
    size=(NUM_GROUPS, 3)
)
group_gyro = rng.normal(0, 0.3, size=(NUM_GROUPS, 3))

group_contacts = rng.integers(
    0, 2, size=(NUM_GROUPS, 5)
)

group_quat = rng.normal(size=(NUM_GROUPS, 4))
group_quat /= np.linalg.norm(
    group_quat, axis=1, keepdims=True
)


def normalize_quat(q):
    """Normalize a quaternion to unit length."""
    return q / np.linalg.norm(q)


for letter_idx, letter in enumerate(LETTERS):

    # Assign multiple letters to similar sensor groups.
    group_idx = letter_idx % NUM_GROUPS

    # Each letter differs slightly from its group prototype.
    flex_center = (
        group_flex[group_idx]
        + rng.normal(0, 110, size=11)
    )

    accel_center = (
        group_accel[group_idx]
        + rng.normal(0, 0.25, size=3)
    )

    gyro_center = (
        group_gyro[group_idx]
        + rng.normal(0, 0.06, size=3)
    )

    contact_center = group_contacts[group_idx].copy()

    quat_center = normalize_quat(
        group_quat[group_idx]
        + rng.normal(0, 0.04, size=4)
    )

    for trial in range(TRIALS_PER_LETTER):

        # Trial-level variation simulates different attempts.
        trial_flex = (
            flex_center
            + rng.normal(0, 150, size=11)
        )

        trial_accel = (
            accel_center
            + rng.normal(0, 0.4, size=3)
        )

        trial_gyro = (
            gyro_center
            + rng.normal(0, 0.08, size=3)
        )

        trial_quat = normalize_quat(
            quat_center
            + rng.normal(0, 0.05, size=4)
        )

        # Small chance of different contact states per trial.
        trial_contacts = contact_center.copy()

        for j in range(5):
            if rng.random() < 0.08:
                trial_contacts[j] = 1 - trial_contacts[j]

        for sample in range(SAMPLES_PER_TRIAL):

            # Flex sensors: 0-4095 ADC readings.
            flex = np.clip(
                np.rint(
                    trial_flex
                    + rng.normal(0, 75, size=11)
                ),
                0,
                4095
            ).astype(int)

            # Contact sensor noise.
            contacts = trial_contacts.copy()

            for j in range(5):
                if rng.random() < 0.03:
                    contacts[j] = 1 - contacts[j]

            # Accelerometer readings.
            accel = (
                trial_accel
                + rng.normal(0, 0.18, size=3)
            )

            # Gyroscope readings.
            gyro = (
                trial_gyro
                + rng.normal(0, 0.035, size=3)
            )

            # Quaternion orientation.
            quat = normalize_quat(
                trial_quat
                + rng.normal(0, 0.015, size=4)
            )

            rows.append([
                *flex,
                *contacts,
                *accel,
                *gyro,
                *quat,
                letter,
                f"{letter}_{trial}"
            ])


# Save generated dataset.
DATA_PATH.parent.mkdir(
    parents=True,
    exist_ok=True
)

df = pd.DataFrame(
    rows,
    columns=FEATURE_COLUMNS + ["letter", "trial_id"]
)

df.to_csv(DATA_PATH, index=False)

print(f"Generated {len(df)} synthetic samples")
print(f"Number of features: {len(FEATURE_COLUMNS)}")
print(f"Number of letters: {df['letter'].nunique()}")
print(f"Number of trials: {df['trial_id'].nunique()}")
print(f"Saved to: {DATA_PATH}")
