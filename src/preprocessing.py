# Load the CSV
# Separate the sensor readings from the letter labels
# Split the data into training and testing sets
# Keep entire recording trials together


import pandas as pd
import numpy as np

from .config import (
    DATA_PATH,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    RANDOM_STATE
)


def load_data():

    df = pd.read_csv(DATA_PATH)

    if df[FEATURE_COLUMNS].isnull().any().any():
        raise ValueError(
            "Dataset contains missing sensor values."
        )

    print("Dataset loaded successfully.")
    print("Dataset shape:", df.shape)

    print("\nLetter distribution:")
    print(df[TARGET_COLUMN].value_counts())

    return df


def split_data(df):

    rng = np.random.default_rng(RANDOM_STATE)

    train_indices = []
    test_indices = []

    # Split recording trials separately for each letter.
    for letter in sorted(df[TARGET_COLUMN].unique()):

        letter_df = df[df[TARGET_COLUMN] == letter]

        # Get independent recording attempts.
        trials = letter_df["trial_id"].unique()

        if len(trials) < 2:
            raise ValueError(
                f"Letter {letter} needs at least 2 trials."
            )

        # Randomize trial order.
        trials = rng.permutation(trials)

        # Approximately 20% of trials for testing.
        n_test = max(1, int(np.ceil(len(trials) * 0.2)))

        test_trials = trials[:n_test]
        train_trials = trials[n_test:]

        train_rows = letter_df[
            letter_df["trial_id"].isin(train_trials)
        ].index

        test_rows = letter_df[
            letter_df["trial_id"].isin(test_trials)
        ].index

        train_indices.extend(train_rows)
        test_indices.extend(test_rows)

    X_train = df.loc[train_indices, FEATURE_COLUMNS]
    X_test = df.loc[test_indices, FEATURE_COLUMNS]

    y_train = df.loc[train_indices, TARGET_COLUMN]
    y_test = df.loc[test_indices, TARGET_COLUMN]

    # Verify that recording trials do not overlap.
    train_trials = set(df.loc[train_indices, "trial_id"])
    test_trials = set(df.loc[test_indices, "trial_id"])

    assert train_trials.isdisjoint(test_trials), (
        "Data leakage: training and testing trials overlap!"
    )

    print("\nTraining samples:", len(X_train))
    print("Testing samples:", len(X_test))

    print("\nTraining letters:")
    print(y_train.value_counts().sort_index())

    print("\nTesting letters:")
    print(y_test.value_counts().sort_index())

    return X_train, X_test, y_train, y_test
