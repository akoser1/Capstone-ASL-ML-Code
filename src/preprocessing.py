# Load the CSV
# Separate the sensor readings from the letter labels
# Split the data into training and testing sets
# Keep entire recording trials together

import pandas as pd

# Purpose is to divide the dataset into training and testing data
from sklearn.model_selection import GroupShuffleSplit

from .config import (
    DATA_PATH,
    FEATURE_COLUMNS,
    TARGET_COLUMN,
    TEST_SIZE,
    RANDOM_STATE
)

def load_data():

    df = pd.read_csv(DATA_PATH)

    # Stop training if any sensor values are missing
    if df[FEATURE_COLUMNS].isnull().any().any():
        raise ValueError(
            "Dataset contains missing sensor values."
        )

    print("Dataset loaded successfully.")
    # Tells you (number of rows, number of columns)
    print("Dataset shape:", df.shape)

    print("\nLetter distribution:")
    print(df[TARGET_COLUMN].value_counts())

    return df


def split_data(df):

    # Sensor measurements
    X = df[FEATURE_COLUMNS]

    # Correct letter labels
    y = df[TARGET_COLUMN]

    # Recording attempt identifiers
    groups = df["trial_id"]

    # Keep each trial entirely in one split
    splitter = GroupShuffleSplit(
        n_splits=1,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE
    )

    train_idx, test_idx = next(
        splitter.split(X, y, groups=groups) # Which rows should belong to training and which to testing
    )

    # Sensor measurements used to train
    X_train = X.iloc[train_idx]
    # Correct letters used to train
    X_test = X.iloc[test_idx]

    # Sensor measurements used to Test
    y_train = y.iloc[train_idx]
    # Correct letters used to check the test predictions
    y_test = y.iloc[test_idx]
    # Ensure every test class was represented in training
    # Which letters exist in the test set but don't exist in the training set
    missing_classes = set(y_test) - set(y_train)

    if missing_classes:
        raise ValueError(
            f"Letters missing from training: {missing_classes}. "
            "Collect more independent trials per letter."
        )

    print("\nTraining samples:", len(X_train))
    print("Testing samples:", len(X_test))

    return X_train, X_test, y_train, y_test
