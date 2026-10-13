
# PAX Calima BLE — Security Assessment PoC

---

> [!CAUTION]
> **⚠️ EDUCATIONAL PURPOSE ONLY — READ BEFORE USING**
>
> This tool is provided **strictly for educational and research purposes**. It is intended to help security researchers, students, and IoT enthusiasts understand how BLE authentication mechanisms work (and can fail) on consumer devices.
>
> **Do NOT use this tool on any device you do not own or for which you do not have explicit written authorisation to test.** Unauthorized access to computer systems or electronic devices is **illegal** in most jurisdictions and may result in civil or criminal liability.
>
> The author(s) accept **no responsibility** whatsoever for any misuse, damage, or legal consequences arising from the use of this code. **You are solely responsible for how you use it.**

---

## Overview

This is a **Proof of Concept (PoC)** security assessment tool targeting the **PAX Calima** smart bathroom fan, which communicates over **Bluetooth Low Energy (BLE)**.

The tool demonstrates a full attack chain composed of two phases:

| Phase | Description |
|-------|-------------|
| **Phase 1** | BLE PIN brute-force (uint32 Little-Endian, 8 digits, range 00000000–99999999) |
| **Phase 2** | Authenticated post-exploitation — full remote control of the device |

This experiment was conducted for **educational and research purposes** to highlight the lack of brute-force protection in the PAX Calima BLE authentication mechanism.

---

## Technical Background

The PAX Calima fan exposes a set of **GATT characteristics** for control and monitoring. Authentication is done by writing a PIN (as a 4-byte uint32 Little-Endian) to a specific characteristic and reading back a confirmation characteristic.

The device does **not implement**:
- Rate limiting or lockout after failed attempts
- Exponential backoff
- Any challenge-response mechanism

This makes it vulnerable to sequential brute-force over BLE.

---

## Requirements

- Python 3.8+
- A Bluetooth adapter (BLE capable)
- Linux, macOS, or Windows (with appropriate BLE stack)

```bash
pip install bleak
```

Or use the provided `requirements.txt`:

```bash
pip install -r requirements.txt
```

---

## Installation

```bash
git clone https://github.com/YOUR_USERNAME/pax_calima_ble_poc.git
cd pax_calima_ble_poc
pip install -r requirements.txt
```

---

## Configuration

Edit `Poc_Pax_Calima.py` and set the MAC address of your target device:

```python
TARGET = "XX:XX:XX:XX:XX:XX"  # Replace with your PAX Calima BLE MAC address
```

To find the MAC address, you can use:
```bash
# Linux
bluetoothctl scan on

```

---

## Usage

```bash
python3 Poc_Pax_Calima.py
```

You will be presented with an interactive menu:

```
  Select mode:
  [1] Full attack chain (brute-force + remote control)
  [2] Brute-force only
  [3] Remote control only (known PIN)
```

### Mode 1 — Full Chain
Runs the brute-force from a given offset, and upon success launches the post-exploitation control panel.

### Mode 2 — Brute-Force only
Useful to discover the PIN without proceeding to remote control. Supports resume via offset.

### Mode 3 — Remote Control (known PIN)
Skips brute-force. Connects directly using a known PIN for authenticated device control.

### Post-Exploitation Menu

Once authenticated, a control panel allows you to:
- Read live sensor data (temperature, humidity, light, fan RPM)
- Activate/deactivate boost mode
- Configure speed levels (high/medium/low RPM thresholds)
- Read boost status
- Read device information (firmware, hardware, software versions)

---

## Responsible Disclosure

This vulnerability was identified through reverse engineering of the BLE protocol. The findings have been shared publicly as a PoC to raise awareness about BLE security in consumer IoT devices.

---

## Credits

> [!NOTE]
> **Acknowledgement — pycalima**
>
> The BLE GATT characteristic UUIDs and the sensor data encoding/decoding logic used in this tool were derived through reverse engineering of the PAX Calima BLE protocol, greatly aided by the open-source project **[pycalima](https://github.com/PatrickE94/pycalima)** by [@PatrickE94](https://github.com/PatrickE94).
>
> Full credit goes to that project for the groundwork. This PoC builds on that knowledge to demonstrate the authentication vulnerability.
