🤖 This program is built with assist by AI.

# 🚗 SEAVS: Smart Emotion-Aware Vehicle System
> **AI Emotion Analysis & Drowsiness Detection Based Smart Vehicle Cockpit Dashboard Simulator**

[🌐 한국어 버전 (Korean Version)](README.ko.md)

---

## 🌟 Key Features

* **🧠 Real-time AI Emotion Analysis**
  - Utilizes the ONNX-based **FER+ model** (`emotion_ferplus.onnx`) to perform real-time driver emotion recognition.
  - Emotion Categories: `Angry`, `Happy`, `Sad`, `Neutral`, `Surprise`, `Disgust`, `Fear`
  - Provides real-time dominant emotion analysis and a chart displaying the top 3 emotion probability scores.

* **👁️ Precise Drowsiness Detection**
  - Embedded with **MediaPipe Face Mesh (468 Landmarks)** technology to capture the coordinate points of both eyes in real-time.
  - Continuously calculates **EAR (Eye Aspect Ratio)** to evaluate the driver's drowsiness.
  - If the driver keeps their eyes closed below the threshold for more than 3 seconds, it diagnoses the state as `Drowsy` and triggers the safety interlock instantly.

* **🔌 Virtual CAN Bus Network (`python-can` Integration)**
  - Replaces direct internal function calls with standard CAN message frame-based communication (mimicking real vehicle network ECUs).
  - Encodes telemetry and control signals into standard 8-byte payloads. Broadcasts `0x110` (Driver State), `0x120` (Face Metrics), and `0x210` (ECU Control Commands) frames over a virtual CAN channel.

* **📡 IoT Digital Twin & Fleet Telemetry (MQTT)**
  - Implements a digital twin telemetry pipeline that assigns a random Vehicle ID (e.g., `SEAVS-EV-1234`) and publishes real-time vehicle parameters (SOC, Cabin Temp, speed, CO2, etc.) to a public broker (`broker.hivemq.com`) on a background thread.
  - **Independent Fleet Monitor**: Features a separate dashboard (`fleet_monitor.py`) subscribing to live telemetry data to visualize fleet connectivity and real-time statuses.

* **🔋 Cabin Power Physics & Multi-Objective HVAC Solver**
  - Realistically models cabin power draw under cooling (compressor), heating (PTC heater), and simple ventilation.
  - Optimizes climate settings under critical driver states using a weighted Grid Search solver—automatically balancing Battery SOC ($w_1$) and Driver Alertness ($w_2$) to select optimal temperature and fan settings.
  - Includes a quick charge button to restore the virtual battery to 100% on demand.

* **📊 Premium Dark-Themed Cockpit GUI**
  - Built with **CustomTkinter** for a sleek, modern, and high-tech dark-themed cockpit design.
  - **Live Video Feed**: Displays the real-time camera stream rendered with bounding boxes and landmark points. Optimized with high-speed bilinear interpolation to eliminate resize lag.
  - **Layout Optimization**: Utilizes a tabbed control console (`🔋 Battery` and `🌍 Environment` tabs) to optimize vertical screen space for low-resolution/high-scaling displays.
  - **Air Vent Animation**: Displays interactive airflow motion graphics and spinning fan animations reacting to the current fan speed and cooling status.

---

## 🛠️ Tech Stack

* **Language:** `Python 3.10+`
* **UI Framework:** `CustomTkinter`, `Pillow`
* **AI & Computer Vision:** `OpenCV (opencv-python)` (DNN module for ONNX model inference), `MediaPipe`
* **Protocols & Utilities:** `python-can` (Virtual CAN Bus network layer), `paho-mqtt` (IoT telemetry client), `pygrabber` (for automated camera device list querying)

---

## 📂 Project Folder Structure

```text
OpenCV_CarManage/
│
├── requirements.txt      # Project library dependencies
├── run.bat              # One-click virtualenv builder & launches both Simulator + Fleet Monitor
├── settings.txt         # Saved configuration/preferences
├── fleet_monitor.py     # IoT Fleet Management Dashboard GUI (MQTT client)
│
└── src/
    ├── main.py          # Application entry point (Initializes UI and main loop)
    │
    ├── core/            # Core business logic and states
    │   ├── config_manager.py  # Handles system preferences (saving/loading config)
    │   ├── safety_system.py   # Analyzes drowsiness and flags critical hazard warnings
    │   ├── vehicle_env.py     # Models virtual cabin physical environments (temp, AC states, SOC)
    │   └── can_bus.py         # [NEW] VirtualCANBus interface wrapper using python-can
    │
    ├── vision/          # Computer vision and AI pipelines
    │   ├── camera.py          # Multi-threaded camera device frames capture
    │   ├── detectors.py       # Implements MediaPipe Face Mesh & ONNX Emotion Detector
    │   ├── visualizer.py      # Vision rendering helpers (drawing face box & mesh landmarks)
    │   ├── face_landmarker.task  # MediaPipe landmark model file
    │   └── emotion_ferplus.onnx  # Deep learning emotion recognition model weights
    │
    ├── simulation/      # Virtual environment simulation
    │   └── simulation_manager.py # Controls CAN/MQTT tasks and multi-objective A/C optimizer solver
    │
    └── ui/              # CustomTkinter dashboard elements
        ├── header.py          # Top navigation (Auto Mode toggle, Audio toggle)
        ├── driver_seat.py     # Camera viewport and driver status monitoring panel (optimized Bilinear)
        ├── center_display.py  # Logs screen, detail charts, tabbed control & battery panel
        ├── ac_panel.py        # Interactive HVAC system controls & air motion graphics
        └── tooltip.py         # CustomTkinter hover tooltip utility
```

---

## 🚀 How to Run

This project provides a one-click batch script (`run.bat`) for Windows users to automatically prepare the virtual environment, install dependencies, and launch both screens concurrently.

### 1. Prerequisites
* A PC with a connected webcam.
* Python 3.10 or higher installed (Make sure Python is added to your PATH env).
* (Optional) An active internet connection for the public HiveMQ MQTT broker telemetric updates.

### 2. Execution
Run **`run.bat`** in the project root folder (Double-click or run from CLI):
```bash
# Double-click run.bat, or run via PowerShell/CMD
./run.bat
```
* **What it does:**
  1. Detects and builds a Python virtual environment (`venv`) if not present.
  2. Activates the virtual environment and installs required libraries (`python-can`, `paho-mqtt`, etc.) silently.
  3. Launches **both** the Cockpit Simulator (`src/main.py`) and the IoT Fleet Monitor (`fleet_monitor.py`) in separate processes simultaneously.

---

## 🛡️ Multi-Hazard Safety Responses

The system continuously evaluates telemetric and behavioral data in the background to apply preventive safety actions.

| Driver State | Safety Evaluation | Vehicle Action (in AI Auto Mode) |
| :--- | :--- | :--- |
| **Normal (Neutral)** | 😊 Safe Driving Condition | Maintained default/standard settings (22°C, auto HVAC) |
| **Happy** | 😊 Pleasant Driving Status | Standard settings with Green ambient light |
| **Anger / Disgust (Stress)** | 😤 Stress / Fatigue Accumulation | Amber ambient light, 21°C external ventilation (indirect airflow), Classic genre (35% vol), Seat ventilation level 1 |
| **Yawning (Warning)** | 🥱 Yawning Detected (Drowsiness Precursor) | Orange dashboard alert, warning beep, 19°C external ventilation (direct airflow), Pop genre (60% vol), Seat ventilation level 2 |
| **Drowsiness (Danger)** | 🚨 DANGEROUS! Drowsiness Detected | Flashes red dashboard alerts, continuous warning beeps, forces A/C ON at 17°C (max fan speed), external ventilation, direct airflow, Dance genre (80% vol), Seat ventilation level 3, Window tilting open, Haptic vibration ON |
| **Sunlight Glare (with Stress)** | ☀ Sunlight Glare Detected | Display dark mode (40% brightness), Amber ambient light, indirect airflow |
| **Fear / Sadness (Low Engagement)** | 😶 Low Engagement Detected | Green ambient light, 24°C external ventilation (indirect airflow), Classic genre (25% vol), Seat heater level 1 |

---

## 💡 Additional Notes
* **Camera Selection:** You can switch between active webcams on the fly using the dropdown menu under the driver monitoring screen.
* **Audio Alerts:** The sound alert toggle state in the header bar is persistently saved. The preference is maintained across application restarts.
