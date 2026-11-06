
import asyncio
import csv
import time
from datetime import datetime
from pathlib import Path
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "ESP32-BLE"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"

NUM_FLEX = 10
RECORD_SECONDS = 5
COUNTDOWN_SECONDS = 3

FLEX_NAMES = [f"MC{i}" for i in range(8)] + [
    "Direct1", "Direct2"
]

CONTACT_NAMES = [
    "C1C2", "C1C3", "C1C4", "C1C5", "C2C3",
    "C2C4", "C2C5", "C3C4", "C3C5", "C4C5"
]

IMU_NAMES = ["qw", "qx", "qy", "qz", "ax", "ay", "az"]

HEADER = (
    ["session", "trial", "label", "timestamp"]
    + FLEX_NAMES + CONTACT_NAMES + IMU_NAMES
)

OUTPUT = Path("asl_training_data.csv")
EXPECTED_VALUES = NUM_FLEX + 1 + len(IMU_NAMES)


async def main():
    print("Searching for ESP32...")
    device = await BleakScanner.find_device_by_name(
        DEVICE_NAME, timeout=15
    )

    if device is None:
        print("ESP32 not found. Check power and Bluetooth.")
        return

    file_exists = OUTPUT.exists() and OUTPUT.stat().st_size > 0

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

    def on_data(_, data):
        nonlocal bad_packets, zero_packets

        if not active:
            return

        try:
            values = data.decode("utf-8").strip().split(",")

            if len(values) != EXPECTED_VALUES:
                bad_packets += 1
                return

            flex = [int(x) for x in values[:NUM_FLEX]]
            mask = int(values[NUM_FLEX])
            imu = [
                float(x) for x in values[NUM_FLEX + 1:]
            ]

            if not 0 <= mask < (1 << len(CONTACT_NAMES)):
                bad_packets += 1
                return

            if any(not 0 <= x <= 4095 for x in flex):
                bad_packets += 1
                return

            if 0 in flex:
                zero_packets += 1

            contacts = [
                (mask >> i) & 1
                for i in range(len(CONTACT_NAMES))
            ]

            rows.append(
                [session, trial, current_label, time.time()]
                + flex + contacts + imu
            )

        except (ValueError, UnicodeDecodeError):
            bad_packets += 1

    current_label = ""

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
                    "\nEnter ASL sign (A-Z), or Q to quit: "
                ).strip().upper()

                if label == "Q":
                    break

                if len(label) != 1 or label not in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
                    print("Enter a single letter A-Z.")
                    continue

                current_label = label
                trial += 1

                print(f"\nPreparing to record {label}...")

                for seconds in range(COUNTDOWN_SECONDS, 0, -1):
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
                    print(f"Malformed packets: {bad_packets}")

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
    asyncio.run(main())
