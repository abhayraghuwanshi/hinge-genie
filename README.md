# HingeGenie 🧞‍♂️

Smart, human-like auto-messaging bot for Hinge using screen scraping + GPT-4.

## 🧠 Features

- Auto-detects bio from screen using OCR
- Sends flirty, friendly messages via ADB or emulator
- Supports GPT-4 message generation
- Human-like typing with delays, cursor movement
- Fully configurable via `config.yaml`

## 🛠️ Local Development Setup

### Prerequisites

1. Python 3.10 or higher
2. ADB (Android Debug Bridge) installed and configured
   - For Windows: Download from [Android Platform Tools](https://developer.android.com/studio/releases/platform-tools)
   - For Linux: `sudo apt-get install adb`
   - For macOS: `brew install android-platform-tools`

### ADB Setup

1. Enable Developer Options on your Android device:
   - Go to Settings > About Phone
   - Tap "Build Number" 7 times to enable Developer Options
2. Enable USB Debugging in Developer Options
3. Connect your device via USB and run:
   ```bash
   adb devices
   ```
   You should see your device listed

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hinge-genie.git
   cd hinge-genie
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   .\venv\Scripts\activate
   # On Linux/macOS
   source venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install system dependencies:
   - Tesseract OCR:
     - Windows: Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
     - Linux: `sudo apt-get install tesseract-ocr`
     - macOS: `brew install tesseract`

### Running Locally

1. Ensure your Android device is connected and ADB is working
2. Run the main script:
   ```bash
   python main.py
   ```

## 🚀 Deployment with Docker

### Step 1: Build the Docker image

```bash
docker build -t hingegenie .
```

### Step 2: Run the container

```bash
docker run -it --rm \
  --device=/dev/kvm \
  --privileged \
  -v $PWD:/app \
  hingegenie
```

> Note: You must run this on a system with ADB access or emulator. Docker container must have access to host ADB or device via port binding or volume mounting.

## 📦 Dockerfile (minimal)

```Dockerfile
FROM python:3.10

WORKDIR /app

COPY . .

RUN apt-get update && \
    apt-get install -y tesseract-ocr adb && \
    pip install pytesseract pyautogui openai pyyaml Pillow

CMD ["python", "main.py"]
```

## 📁 Config

Edit `config.yaml` to change your GPT style or fallback rules.

## ⚠️ Ethical Note

This tool is for educational/personal automation. Don't use to spam or break Hinge TOS.
