import asyncio
import csv
import time
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "ESP32-BLE"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
NUM_FLEX = 11
NUM_PRESS = 6
RUN_SECONDS = 30
HEADER = (["time"]
          + [f"flex{i}" for i in range(1, NUM_FLEX + 1)]
          + [f"press{i}" for i in range(1, NUM_PRESS + 1)])


async def main():
    print(f"Scanning for {DEVICE_NAME}...")
    dev = await BleakScanner.find_device_by_name(DEVICE_NAME, timeout=10)
    if dev is None:
        print(f"{DEVICE_NAME} not found. Is the phone disconnected and the ESP32 powered?")
        return

    with open("glove_data.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        count = 0

        def on_data(_, data):
            nonlocal count
            text = data.decode(errors="ignore")
            vals = text.split(",")
            if len(vals) != NUM_FLEX + NUM_PRESS:
                print("bad packet:", text)   # truncated = MTU problem
                return
            writer.writerow([round(time.time(), 3)] + vals)
            count += 1
            print("flex:", vals[:NUM_FLEX], "| press:", vals[NUM_FLEX:])

        async with BleakClient(dev, timeout=30, winrt=dict(use_cached_services=False)) as client:
            print("Connected. Receiving data...")
            await client.start_notify(CHAR_UUID, on_data)
            await asyncio.sleep(RUN_SECONDS)
            await client.stop_notify(CHAR_UUID)

        print(f"Done. Saved {count} packets to glove_data.csv")


asyncio.run(main())