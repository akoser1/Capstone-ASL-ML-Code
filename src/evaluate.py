# Determine how well your model identifies letters 
# it hasn't previously encountered

from sklearn.metrics import (
    accuracy_score, # Calculates overall percentage correct
    classification_report, # Gives detailed results for each letter
    confusion_matrix, # Shows which letters get confused with each other
    ConfusionMatrixDisplay # Turns the confusion matrix into a graph
)

import matplotlib.pyplot as plt

from .config import MODEL_DIR

# X_test = the measurements
# Y_test = the letters
def evaluate_model(model, X_test, y_test):

    # Generate predictions
    predictions = model.predict(X_test)

    # Calculate accuracy
    accuracy = accuracy_score(
        y_test,
        predictions
    )

    print(f"\nModel Accuracy: {accuracy * 100:.2f}")

    # Detailed evaluation
    print("\nClassification Report:")

    print(
        classification_report(
            y_test,
            predictions,
            zero_division=0
        )
    )

    # Confusion matrix = shows which letters our model is confusing with other letters
    labels = model.classes_

    cm = confusion_matrix(
        y_test,
        predictions,
        labels=labels
    )


    display = ConfusionMatrixDisplay(
        confusion_matrix=cm,
        display_labels=labels
    )

    display.plot(
        cmap="Blues",
        xticks_rotation=90
    )

    plt.title("ASL Letter Classification")

    MODEL_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    plt.savefig(
        MODEL_DIR / "confusion_matrix.png",
        bbox_inches="tight"
    )

    plt.close()

    return accuracy
