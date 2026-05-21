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

* **❄️ Smart HVAC & Cockpit Control Interlock**
  - When **AI Auto Mode** is activated, the system dynamically adjusts the cabin temperature, Air Conditioner (A/C) power, and fan speed based on drowsiness or sudden emotion changes.
  - Example: **Upon detecting drowsiness**, it forces the HVAC power ON, activates A/C cooling, and boosts the fan speed to the maximum to wake the driver up.

* **📊 Premium Dark-Themed Cockpit GUI**
  - Built with **CustomTkinter** for a sleek, modern, and high-tech dark-themed cockpit design.
  - **Live Video Feed**: Displays the real-time camera stream rendered with bounding boxes and landmark points.
  - **System Logs & Safety Alerts**: Provides chronological logging and color-coded interactive safety banner alerts.
  - **Air Vent Animation**: Displays interactive airflow motion graphics and spinning fan animations reacting to the current fan speed and cooling status.

---

## 🛠️ Tech Stack

* **Language:** `Python 3.10+`
* **UI Framework:** `CustomTkinter`, `Pillow`
* **AI & Computer Vision:** `OpenCV (opencv-python)`, `MediaPipe`, `ONNX Runtime`
* **Protocols & Utilities:** `paho-mqtt` (for simulation telemetry), `pygrabber` (for automated camera device list querying)

---

## 📂 Project Folder Structure

```text
OpenCV_CarManage/
│
├── requirements.txt      # Project library dependencies
├── run.bat              # One-click virtualenv builder & run script
├── plan.txt             # Development architecture & plan draft
│
└── src/
    ├── main.py          # Application entry point (Initializes UI and main loop)
    │
    ├── core/            # Core business logic and states
    │   ├── config_manager.py  # Handles system preferences (saving/loading config)
    │   ├── safety_system.py   # Analyzes drowsiness and flags critical hazard warnings
    │   └── vehicle_env.py     # Models virtual cabin physical environments (temp, AC states)
    │
    ├── vision/          # Computer vision and AI pipelines
    │   ├── camera.py          # Multi-threaded camera device frames capture
    │   ├── detectors.py       # Implements MediaPipe Face Mesh & ONNX Emotion Detector
    │   ├── visualizer.py      # Vision rendering helpers (drawing face box & mesh landmarks)
    │   ├── face_landmarker.task  # MediaPipe landmark model file
    │   └── emotion_ferplus.onnx  # Deep learning emotion recognition model weights
    │
    ├── simulation/      # Virtual environment simulation
    │   └── simulation_manager.py # Syncs AI outputs and feeds telemetry data back to cabin
    │
    └── ui/              # CustomTkinter dashboard elements
        ├── header.py          # Top navigation (Auto Mode toggle, Audio toggle)
        ├── driver_seat.py     # Camera viewport and driver status monitoring panel
        ├── center_display.py  # Logs screen, detail charts, and safety banners
        └── ac_panel.py        # Interactive HVAC system controls & air motion graphics
```

---

## 🚀 How to Run

This project provides a one-click batch script (`run.bat`) for Windows users to automatically prepare the virtual environment and launch the dashboard.

### 1. Prerequisites
* A PC with a connected webcam.
* Python 3.10 or higher installed (Make sure Python is added to your PATH env).

### 2. Execution
Run **`run.bat`** in the project root folder (Double-click or run from CLI):
```bash
# Double-click run.bat, or run via PowerShell/CMD
./run.bat
```
* **What it does:**
  1. Detects and builds a Python virtual environment (`venv`) if not present.
  2. Activates the virtual environment and installs required libraries silently.
  3. Launches the application by executing `src/main.py`.

---

## 🛡️ Multi-Hazard Safety Responses

The system continuously evaluates telemetric and behavioral data in the background to apply preventive safety actions.

| Driver State | Safety Evaluation | Vehicle Action |
| :--- | :--- | :--- |
| **Normal (Neutral / Happy)** | Safe Driving Condition | Maintained current HVAC settings |
| **Anger Detected (Angry)** | Caution Advised | Warning banner displayed; recommends relaxing environments |
| **Drowsiness (Drowsy, EAR Drop)** | **⚠️ DANGEROUS! Drowsiness Detected** | Flashes yellow dashboard alerts, plays beep sound, forces A/C ON, sets temperature low, and raises fan speed to maximum. |
| **Face Not Detected** | **⚠️ Driver Missing / Out of View** | Triggers visual alert banner prompting safety inspection |

---

## 💡 Additional Notes
* **Camera Selection:** You can switch between active webcams on the fly using the dropdown menu under the driver monitoring screen.
* **Audio Alerts:** The sound alert toggle state in the header bar is persistently saved. The preference is maintained across application restarts.
