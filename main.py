# Connects preprocessing, training, evaluation, and model-saving functions

from src.preprocessing import (
    load_data,
    split_data
)

from src.train import (
    create_model,
    train_model,
    save_model
)

from src.evaluate import evaluate_model


def main():

    print("Starting ASL ML Project")

    # Load dataset
    df = load_data()

    # Split dataset
    X_train, X_test, y_train, y_test = split_data(df)

    # Create Random Forest
    model = create_model()

    # Train Random Forest
    model = train_model(
        model,
        X_train,
        y_train
    )

    # Evaluate performance
    evaluate_model(
        model,
        X_test,
        y_test
    )

    # Save trained model
    save_model(model)

    print("\nMachine learning workflow completed!")


if __name__ == "__main__":
    main()
