
import asyncio
import csv
import time
from datetime import datetime
from pathlib import Path

from bleak import BleakScanner, BleakClient


# ---------- Bluetooth settings ----------
DEVICE_NAME = "ESP32-BLE"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"


# ---------- Recording settings ----------
NUM_FLEX = 10
RECORD_SECONDS = 5
COUNTDOWN_SECONDS = 3


# ---------- Sensor columns ----------
FLEX_NAMES = [f"MC{i}" for i in range(8)] + [
    "Direct1",
    "Direct2",
]

# C1 = Thumb
# C2 = Index
# C3 = Middle
# C4 = Ring
# C5 = Pinky
#
# Each contact value is 0 (not touching) or 1 (touching).
CONTACT_NAMES = [
    "C1C2",  # Thumb + Index
    "C1C3",  # Thumb + Middle
    "C1C4",  # Thumb + Ring
    "C1C5",  # Thumb + Pinky
]

IMU_NAMES = [
    "qw", "qx", "qy", "qz",
    "ax", "ay", "az",
]

HEADER = (
    ["session", "trial", "label", "timestamp"]
    + FLEX_NAMES
    + CONTACT_NAMES
    + IMU_NAMES
)

# Use a new file to preserve your original training data.
OUTPUT = Path("asl_training_data_with_contacts.csv")

# 10 flex + 4 contact + 7 IMU = 21 values
EXPECTED_VALUES = (
    NUM_FLEX
    + len(CONTACT_NAMES)
    + len(IMU_NAMES)
)


async def main():
    print("Searching for ESP32...")

    device = await BleakScanner.find_device_by_name(
        DEVICE_NAME,
        timeout=15,
    )

    if device is None:
        print("ESP32 not found. Check power and Bluetooth.")
        return

    file_exists = OUTPUT.exists() and OUTPUT.stat().st_size > 0

    # Prevent accidentally mixing different CSV formats.
    if file_exists:
        with OUTPUT.open("r", newline="") as f:
            existing_header = next(csv.reader(f), None)

        if existing_header != HEADER:
            print("Existing CSV has different columns.")
            print("Rename or move it before collecting.")
            return

    session = datetime.now().strftime("%Y%m%d_%H%M%S")
    trial = 0

    active = False
    rows = []
    bad_packets = 0
    zero_packets = 0
    current_label = ""

    def on_data(sender, data):
        nonlocal bad_packets, zero_packets

        if not active:
            return

        try:
            values = data.decode("utf-8").strip().split(",")

            if len(values) != EXPECTED_VALUES:
                bad_packets += 1
                return

            # ---------- 10 flex sensor values ----------
            flex = [
                int(x)
                for x in values[:NUM_FLEX]
            ]

            # ---------- 4 contact sensor values ----------
            contact_start = NUM_FLEX
            contact_end = contact_start + len(CONTACT_NAMES)

            contacts = [
                int(x)
                for x in values[contact_start:contact_end]
            ]

            # ---------- 7 IMU values ----------
            imu = [
                float(x)
                for x in values[contact_end:]
            ]

            # ---------- Validate sensor data ----------
            if any(not 0 <= x <= 4095 for x in flex):
                bad_packets += 1
                return

            if any(x not in (0, 1) for x in contacts):
                bad_packets += 1
                return

            if 0 in flex:
                zero_packets += 1

                if zero_packets == 1:
                    print("\nZero reading detected!")
                    for name, value in zip(FLEX_NAMES, flex):
                        print(f"{name}: {value}")

            # ---------- Store sample ----------
            rows.append(
                [session, trial, current_label, time.time()]
                + flex
                + contacts
                + imu
            )

        except (ValueError, UnicodeDecodeError):
            bad_packets += 1

    print("Connecting...")

    async with BleakClient(device, timeout=30) as client:
        await client.start_notify(CHAR_UUID, on_data)

        print("Connected!")
        print("Waiting for BLE readings to start...")
        await asyncio.sleep(5)

        with OUTPUT.open("a", newline="") as f:
            writer = csv.writer(f)

            if not file_exists:
                writer.writerow(HEADER)
                f.flush()

            while True:
                label = input(
                    "\nEnter ASL sign (A-Z), or EXIT to quit: "
                ).strip().upper()

                if label == "EXIT":
                    break

                if (
                    len(label) != 1
                    or label not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
                ):
                    print("Enter a single letter A-Z.")
                    continue

                current_label = label
                trial += 1

                print(f"\nPreparing to record {label}...")

                for seconds in range(
                    COUNTDOWN_SECONDS, 0, -1
                ):
                    print(f"{seconds}...")
                    await asyncio.sleep(1)

                rows = []
                bad_packets = 0
                zero_packets = 0

                print(f"RECORDING {label}!")

                active = True
                await asyncio.sleep(RECORD_SECONDS)
                active = False

                print(f"Captured {len(rows)} samples.")

                if bad_packets:
                    print(
                        f"Malformed packets: {bad_packets}"
                    )

                if zero_packets:
                    print(
                        f"WARNING: {zero_packets} samples "
                        "contain a zero flex reading."
                    )

                if not rows:
                    print("No valid data received. Try again.")
                    continue

                choice = input(
                    "Save this trial? (Y/N): "
                ).strip().upper()

                if choice == "Y":
                    writer.writerows(rows)
                    f.flush()

                    print(
                        f"Saved {len(rows)} rows to {OUTPUT}"
                    )
                else:
                    print("Trial discarded.")

        await client.stop_notify(CHAR_UUID)

    print("\nCollection complete!")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCollection stopped.")
