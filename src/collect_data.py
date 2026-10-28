# Actively communicates with ESP32 to receive sensor measurements,
# and saves them into a CSV dataset

import serial
import csv
import time
import math

# Import these values from config file
from .config import (
    DATA_PATH,
    SERIAL_PORT,
    BAUD_RATE,
    FEATURE_COLUMNS,
    FLEX_COLUMNS,
    CONTACT_COLUMNS
)


def collect_data():

    # Ask which letter is being recorded
    letter = input("Enter letter (A-Z): ").strip().upper()

    # Checks to see if input is valid
        # one character only
        # has to be a letter
        # rejects non-ASCII chars
    if len(letter) != 1 or not letter.isalpha() or not letter.isascii():
        print("Invalid letter.")
        return

    # Ask how many samples to record
    num_samples = int(
        input("How many samples? ")
    )

    if num_samples <= 0:
        print("Sample count must be positive.")
        return

    # Give each recording attempt a unique identifier to tell each recording apart
    trial_id = time.time_ns()

    # Connect to ESP32 (Make sure Arduino IDE's Serial Monitor is closed)
    esp32 = serial.Serial(
        SERIAL_PORT,
        BAUD_RATE,
        timeout=2 # Max time in sec to wait for read to complete
    )

    # Allow ESP32 to initialize
    time.sleep(2)

    # Clear old serial readings that were in input buffer
    esp32.reset_input_buffer()
    
    DATA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    # Checks whether dataset already exists
    # Do this because we don't want to write a new header for every new measurement
    file_exists = (
        DATA_PATH.exists()
        and DATA_PATH.stat().st_size > 0
    )

    print("Recording letter:", letter)
    print("Hold the gesture steady.")

    with open(DATA_PATH, "a", newline="") as file:

        writer = csv.writer(file)

        if not file_exists:
            writer.writerow([ # Change these headers
                FEATURE_COLUMNS + ["letter", "trial_id"]
            ])

        count = 0

        while count < num_samples:

            line = esp32.readline().decode(
                "utf-8",
                errors="ignore"
            ).strip()

            try:
                # Convert all sensor readings to numbers
                values = [
                    float(value)
                    for value in line.split(",")
                ]

                # Check total number of sensor readings
                if len(values) != len(FEATURE_COLUMNS):
                    print(
                        f"Skipped:expected {len(FEATURE_COLUMNS)} "
                        f"values, got {len(values)}"
                    )
                    continue

                # Validate flex sensors
                flex_values = values[:len(FLEX_COLUMNS)]

                if not all(0 <= value <= 4095 for value in flex_values):
                    print("Skipped: flex value out of range")
                    continue

                # Validate contact sensors
                start = len(FLEX_COLUMNS)
                end = start + len(CONTACT_COLUMNS)

                contact_values = values[start:end]

                if not all(value in (0,1) for value in contact_values):
                    print("Skipped: contact value must be 0 or 1")
                    continue

                # Reject NaN or infinity
                if not all(
                    math.isfinite(value)
                    for value in values
                ):
                    print("Skipped: invalid sensor value")
                    continue

                # First TBD values are the flex sensors
                flex_values = values[:TBD]

                # ESP32 12-bit ADC values should be 0-4095
                if not all(
                    0 <= value <= 4095
                    for value in flex_values
                ):
                    print("Skipped: flex sensor value out of range")
                    continue

                # If we reach here, the sample passed our checks
                writer.writerow(
                    values + [letter, trial_id]
                )

                count += 1

                print(
                    f"Recorded {count}/{num_samples}:",
                    values
                )

            except ValueError:
                print("Skipped: could not convert sensor data to numbers")
                continue

    esp32.close()

    print("Data collection completed!")


if __name__ == "__main__":
    collect_data()


# Put this into terminal
# python -m src.collect_data