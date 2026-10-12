# PAX Calima BLE — Security Assessment PoC

> **⚠️ DISCLAIMER / AVVERTENZA LEGALE** — See bottom of this file / Vedi in fondo al file.

---

## 🌐 English

### Overview

This is a **Proof of Concept (PoC)** security assessment tool targeting the **PAX Calima** smart bathroom fan, which communicates over **Bluetooth Low Energy (BLE)**.

The tool demonstrates a full attack chain composed of two phases:

| Phase | Description |
|-------|-------------|
| **Phase 1** | BLE PIN brute-force (uint32 Little-Endian, 8 digits, range 00000000–99999999) |
| **Phase 2** | Authenticated post-exploitation — full remote control of the device |

This experiment was conducted for **educational and research purposes** to highlight the lack of brute-force protection in the PAX Calima BLE authentication mechanism.

---

### Technical Background

The PAX Calima fan exposes a set of **GATT characteristics** for control and monitoring. Authentication is done by writing a PIN (as a 4-byte uint32 Little-Endian) to a specific characteristic and reading back a confirmation characteristic.

The device does **not implement**:
- Rate limiting or lockout after failed attempts
- Exponential backoff
- Any challenge-response mechanism

This makes it vulnerable to sequential brute-force over BLE.

#### Key GATT Characteristics

| Characteristic | UUID | Purpose |
|----------------|------|---------|
| PIN Code | `4cad343a-...` | Write PIN for authentication |
| PIN Confirmation | `d1ae6b70-...` | Read result (non-zero = success) |
| Sensor Data | `528b80e8-...` | Temperature, humidity, light, fan RPM |
| Fan Speed | `faa49e09-...` | Current fan speed settings |
| Boost | `1488a757-...` | Activate/deactivate boost mode |
| Sensitivity | `e782e131-...` | Humidity threshold and speed levels |
| Mode | `b5836b55-...` | Current operating mode |

UUIDs reverse-engineered from the [pycalima](https://github.com/PatrickE94/pycalima) library.

---

### Requirements

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

### Installation

```bash
git clone https://github.com/YOUR_USERNAME/pax_calima_ble_poc.git
cd pax_calima_ble_poc
pip install -r requirements.txt
```

---

### Configuration

Edit `Poc_Pax_Calima.py` and set the MAC address of your target device:

```python
TARGET = "XX:XX:XX:XX:XX:XX"  # Replace with your PAX Calima BLE MAC address
```

To find the MAC address, you can use:
```bash
# Linux
bluetoothctl scan on

# macOS (UUID is used instead of MAC)
python3 -c "import asyncio; from bleak import BleakScanner; asyncio.run(BleakScanner.discover())"
```

> **Note for macOS users:** Apple's CoreBluetooth framework does not expose raw MAC addresses. You will see a UUID instead. Use that UUID as the `TARGET` value.

---

### Usage

```bash
python3 Poc_Pax_Calima.py
```

You will be presented with an interactive menu:

```
  Select mode:
  [1] Full attack chain (brute-force + remote control)
  [2] Only brute-force
  [3] Only remote control (known PIN)
```

#### Mode 1 — Full Chain
Runs the brute-force from a given offset, and upon success launches the post-exploitation control panel.

#### Mode 2 — Brute-Force only
Useful to discover the PIN without proceeding to remote control. Supports resume via offset.

#### Mode 3 — Remote Control (known PIN)
Skips brute-force. Connects directly using a known PIN for authenticated device control.

#### Post-Exploitation Menu

Once authenticated, a control panel allows you to:
- Read live sensor data (temperature, humidity, light, fan RPM)
- Activate/deactivate boost mode
- Configure speed levels (high/medium/low RPM thresholds)
- Read boost status
- Read device information (firmware, hardware, software versions)

---

### Estimated Brute-Force Time

The PIN space is 10^8 (100 million combinations). Based on observed BLE throughput:

| Speed | Estimated time (worst case) |
|-------|-----------------------------|
| ~20 attempts/s | ~58 days |
| ~50 attempts/s | ~23 days |

In practice, the PIN is often short or predictable, significantly reducing the search space.

---

### Responsible Disclosure

This vulnerability was identified through reverse engineering of the BLE protocol. The findings have been shared publicly as a PoC to raise awareness about BLE security in consumer IoT devices.

---

---

## Italiano

### Panoramica

Questo è uno strumento **Proof of Concept (PoC)** per la valutazione della sicurezza del **ventilatore bagno smart PAX Calima**, che comunica tramite **Bluetooth Low Energy (BLE)**.

Il tool dimostra una catena di attacco completa composta da due fasi:

| Fase | Descrizione |
|------|-------------|
| **Fase 1** | Brute-force del PIN BLE (uint32 Little-Endian, 8 cifre, range 00000000–99999999) |
| **Fase 2** | Post-exploitation autenticata — controllo remoto completo del dispositivo |

Questo esperimento è stato condotto a **scopo educativo e di ricerca** per evidenziare la mancanza di protezione contro il brute-force nel meccanismo di autenticazione BLE del PAX Calima.

---

### Contesto Tecnico

Il ventilatore PAX Calima espone un insieme di **caratteristiche GATT** per il controllo e il monitoraggio. L'autenticazione avviene scrivendo un PIN (come uint32 Little-Endian a 4 byte) su una caratteristica specifica e leggendo una caratteristica di conferma.

Il dispositivo **non implementa**:
- Rate limiting o blocco dopo tentativi falliti
- Backoff esponenziale
- Nessun meccanismo challenge-response

Questo lo rende vulnerabile a un attacco brute-force sequenziale via BLE.

#### Caratteristiche GATT Principali

| Caratteristica | UUID | Scopo |
|----------------|------|-------|
| PIN Code | `4cad343a-...` | Scrittura PIN per l'autenticazione |
| PIN Confirmation | `d1ae6b70-...` | Lettura risultato (non-zero = successo) |
| Sensor Data | `528b80e8-...` | Temperatura, umidità, luce, RPM ventola |
| Fan Speed | `faa49e09-...` | Impostazioni velocità ventola |
| Boost | `1488a757-...` | Attiva/disattiva modalità boost |
| Sensitivity | `e782e131-...` | Soglia umidità e livelli di velocità |
| Mode | `b5836b55-...` | Modalità operativa corrente |

UUID ricavati tramite reverse engineering dalla libreria [pycalima](https://github.com/PatrickE94/pycalima).

---

### Requisiti

- Python 3.8+
- Adattatore Bluetooth (compatibile BLE)
- Linux, macOS o Windows (con stack BLE appropriato)

```bash
pip install bleak
```

Oppure usa il file `requirements.txt` incluso:

```bash
pip install -r requirements.txt
```

---

### Installazione

```bash
git clone https://github.com/YOUR_USERNAME/pax_calima_ble_poc.git
cd pax_calima_ble_poc
pip install -r requirements.txt
```

---

### Configurazione

Modifica `Poc_Pax_Calima.py` e imposta il MAC address del tuo dispositivo target:

```python
TARGET = "XX:XX:XX:XX:XX:XX"  # Sostituisci con il MAC address BLE del tuo PAX Calima
```

Per trovare il MAC address:
```bash
# Linux
bluetoothctl scan on

# macOS (viene esposto un UUID al posto del MAC)
python3 -c "import asyncio; from bleak import BleakScanner; asyncio.run(BleakScanner.discover())"
```

> **Nota per utenti macOS:** Il framework CoreBluetooth di Apple non espone i MAC address raw. Vedrai un UUID — usa quello come valore di `TARGET`.

---

### Utilizzo

```bash
python3 Poc_Pax_Calima.py
```

Verrà mostrato un menu interattivo:

```
  Select mode:
  [1] Full attack chain (brute-force + remote control)
  [2] Only brute-force
  [3] Only remote control (known PIN)
```

#### Modalità 1 — Catena completa
Esegue il brute-force a partire da un offset configurabile, e al successo avvia il pannello di controllo post-exploitation.

#### Modalità 2 — Solo Brute-Force
Utile per scoprire il PIN senza procedere al controllo remoto. Supporta la ripresa tramite offset.

#### Modalità 3 — Controllo Remoto (PIN noto)
Salta il brute-force. Si connette direttamente con un PIN noto per il controllo autenticato.

#### Menu Post-Exploitation

Una volta autenticato, il pannello di controllo permette di:
- Leggere i dati live dei sensori (temperatura, umidità, luce, RPM ventola)
- Attivare/disattivare la modalità boost
- Configurare i livelli di velocità (soglie RPM alto/medio/basso)
- Leggere lo stato boost
- Leggere le informazioni del dispositivo (versioni firmware, hardware, software)

---

### Tempo Stimato per il Brute-Force

Lo spazio dei PIN è 10^8 (100 milioni di combinazioni). In base alla throughput BLE osservata:

| Velocità | Tempo stimato (caso peggiore) |
|----------|-----------------------------|
| ~20 tentativi/s | ~58 giorni |
| ~50 tentativi/s | ~23 giorni |

Nella pratica, il PIN è spesso breve o prevedibile, riducendo significativamente lo spazio di ricerca.

---

### Responsible Disclosure

Questa vulnerabilità è stata identificata tramite reverse engineering del protocollo BLE. I risultati sono stati condivisi pubblicamente come PoC per sensibilizzare sulla sicurezza BLE nei dispositivi IoT consumer.

---

---

## Legal Disclaimer / Avvertenza Legale

**[EN]** This tool is provided **for educational and research purposes only**. Use it **only on devices you own or have explicit written permission to test**. Unauthorized access to computer systems or electronic devices is illegal in most jurisdictions. The author(s) assume **no responsibility** for any misuse of this code.

**[IT]** Questo strumento è fornito **esclusivamente a scopo educativo e di ricerca**. Usarlo **solo su dispositivi di tua proprietà o per cui hai esplicita autorizzazione scritta a effettuare test**. L'accesso non autorizzato a sistemi informatici o dispositivi elettronici è illegale nella maggior parte delle giurisdizioni. L'autore/gli autori declinano **ogni responsabilità** per un utilizzo improprio di questo codice.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
