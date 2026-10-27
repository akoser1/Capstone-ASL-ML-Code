import asyncio
import csv
import time
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "ESP32-BLE"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
RUN_SECONDS = 60

# Column names match the pin order in the sketch
PINS = ["GPIO36(VP)", "GPIO39(VN)", "GPIO34", "GPIO35", "GPIO32", "GPIO33",
        "GPIO25", "GPIO26", "GPIO27", "GPIO14", "GPIO12"]
NUM_FLEX = len(PINS)
HEADER = ["time"] + [f"flex{i+1}_{p}" for i, p in enumerate(PINS)]


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
            if len(vals) != NUM_FLEX or not all(v.strip().isdigit() for v in vals):
                print("bad packet:", text)   # truncated = MTU problem
                return
            writer.writerow([round(time.time(), 3)] + vals)
            f.flush()
            count += 1
            print(" ".join(f"{int(v):4d}" for v in vals))

        async with BleakClient(dev, timeout=30,
                               winrt=dict(use_cached_services=False)) as client:
            print("Connected. Receiving data (first packets arrive after about 4 s)...")
            await client.start_notify(CHAR_UUID, on_data)
            await asyncio.sleep(RUN_SECONDS)
            await client.stop_notify(CHAR_UUID)

        print(f"Done. Saved {count} packets to glove_data.csv")


asyncio.run(main())