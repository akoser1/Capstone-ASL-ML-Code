import asyncio
import csv
import time
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "ESP32-BLE"
CHAR_UUID = "beb5483e-36e1-4688-b7f5-ea07361b26a8"
RUN_SECONDS = 60

FLEX_NAMES = ["F1_idx_MCP", "F2_idx_PIP", "F3_mid_MCP", "F4_mid_PIP",
              "F5_ring_MCP", "F6_ring_PIP", "F7_pnk_MCP", "F8_pnk_PIP",
              "F9_thumb_CMC", "F10_thumb_MCP", "F11_thumb_IP"]
PAIRS = ["C1C2", "C1C3", "C1C4", "C1C5", "C2C3",
         "C2C4", "C2C5", "C3C4", "C3C5", "C4C5"]
IMU = ["qw", "qx", "qy", "qz", "ax", "ay", "az"]

NUM_VALUES = len(FLEX_NAMES) + 1 + len(IMU)   # 11 flex + mask + 7 imu = 19
HEADER = ["time"] + FLEX_NAMES + PAIRS + IMU


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
            if len(vals) != NUM_VALUES:
                print(f"bad packet ({len(vals)} values, expected {NUM_VALUES}):", text)
                return
            try:
                flex = [int(v) for v in vals[:11]]
                mask = int(vals[11])
                imu = [float(v) for v in vals[12:]]
            except ValueError:
                print("unparseable packet:", text)
                return

            pair_bits = [(mask >> b) & 1 for b in range(len(PAIRS))]
            writer.writerow([round(time.time(), 3)] + flex + pair_bits + imu)
            f.flush()
            count += 1

            touching = [p for p, b in zip(PAIRS, pair_bits) if b]
            print(" ".join(f"{v:4d}" for v in flex), "| touch:", touching or "-")

        async with BleakClient(dev, timeout=30,
                               winrt=dict(use_cached_services=False)) as client:
            print("Connected. Data starts after about 4 s...")
            await client.start_notify(CHAR_UUID, on_data)
            await asyncio.sleep(RUN_SECONDS)
            await client.stop_notify(CHAR_UUID)

        print(f"Done. Saved {count} packets to glove_data.csv")


asyncio.run(main())