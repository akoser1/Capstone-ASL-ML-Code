# Where Random Forest is created and trained

# RF classifier
from sklearn.ensemble import RandomForestClassifier

import joblib

from .config import (
    N_ESTIMATORS,
    MAX_DEPTH,
    MIN_SAMPLES_SPLIT,
    MIN_SAMPLES_LEAF,
    RANDOM_STATE,
    MODEL_DIR,
    MODEL_PATH
)


def create_model():

    model = RandomForestClassifier(
        n_estimators=N_ESTIMATORS,
        max_depth=MAX_DEPTH,
        min_samples_split=MIN_SAMPLES_SPLIT,
        min_samples_leaf=MIN_SAMPLES_LEAF,
        random_state=RANDOM_STATE,
        n_jobs=-1
    )

    return model


def train_model(model, X_train, y_train):

    print("\nTraining Random Forest...")

    # This is where the model learns
    model.fit(X_train, y_train)

    print("Training completed!")

    return model


def save_model(model):

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    joblib.dump(model, MODEL_PATH)

    print("Model saved:", MODEL_PATH)
