# GPS Spoofer
> **Academic project – GNSS signal simulation and transmission using SDR**

⚠️ **Legal & Ethical Notice**

This project is strictly intended for **academic, educational and research purposes**. GNSS/GPS signal spoofing is **illegal** in many countries when used outside controlled laboratory environments. The author does **not** take responsibility for any misuse of this software.

---

## 📌 Project Overview

This project implements a **GPS spoofing system** using:

* `gps-sdr-sim` to generate simulated GNSS I/Q samples based on user-defined coordinates
* **GNU Radio** to transmit the generated signal via **Software Defined Radio (SDR)** hardware
* A **PyQt5 graphical interface** with an interactive map for coordinate selection

The user can:

1. Select coordinates on a map
2. Generate a GPS signal (`gpssim.bin`)
3. Transmit the signal using SDR hardware

---

## 🧰 Technologies Used

* **Python 3**
* **GNU Radio 3.10+**
* **PyQt5 & QtWebEngine**
* **Leaflet.js** (interactive map)
* **gps-sdr-sim**
* **Software Defined Radio** (HackRF / RTL-SDR / similar)

---

## 📁 Repository Structure

```
GPS-Spoofer/
├── spoofer_gui.py        # PyQt5 GUI with interactive map
│
├── GPS_Spoofer.py        # GNU Radio flowgraph (generated from GRC)
│
├── gps-sdr-sim-master/
│   ├── gpssim.c
│   ├── gps-sdr-sim
│   └── brdc*.n           # Broadcast ephemeris files
│
├── Spoofing_para_GPS.pdf # Project report
│    
├── README.md
└── LICENSE
```

---

## ⚙️ Installation

### 1️⃣ System Requirements

* Linux (recommended) or Windows (advanced setup)
* SDR hardware (HackRF recommended)
* GNU Radio 3.10+

---

### 2️⃣ Install GNU Radio

**Linux (Ubuntu):**

```bash
sudo apt update
sudo apt install gnuradio
```

**Windows:**

* Install GNU Radio using **Radioconda** or official installer
* Ensure GNU Radio Python interpreter is used

---

### 3️⃣ Install Python Dependencies

```bash
pip install PyQt5 PyQtWebEngine
```

---

### 4️⃣ Build gps-sdr-sim

```bash
git clone https://github.com/osqzss/gps-sdr-sim.git
cd gps-sdr-sim-master
gcc gpssim.c -lm -O3 -o gps-sdr-sim
./gps-sdr-sim -b 8 -e brdcXXXX.XXn -l LATITUDE,LONGITUDE,100
```

---

## ▶️ Running the Project

1️⃣ Start the GUI:

```bash
python spoofer_gui.py
```

2️⃣ Click on the map to select coordinates

3️⃣ Click **Confirm coordinates** to generate `gpssim.bin`

4️⃣ Click **Start Transmission** to transmit using SDR

---

## 🛰 Supported SDR Devices

* HackRF One ✅ (recommended)
* RTL-SDR (limited)
* LimeSDR

---

## ❗ Important Notes

* This project **must only be used in shielded environments**
* Transmitting GPS frequencies without authorization is illegal
* Ensure correct sample rate and frequency configuration

---

## 👤 Author

**Tiago Matos**
Master Academic Project

---

## ⭐ Acknowledgements

* `gps-sdr-sim` by osqzss
* GNU Radio community
* OpenStreetMap & Leaflet.js

