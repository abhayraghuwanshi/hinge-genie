# HingeGenie 🧞‍♂️

Smart, human-like auto-messaging bot for Hinge using screen scraping + GPT-4.

## 🧠 Features

- Auto-detects bio from screen using OCR
- Sends flirty, friendly messages via ADB or emulator
- Supports GPT-4 message generation
- Human-like typing with delays, cursor movement
- Fully configurable via `config.yaml`

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

This tool is for educational/personal automation. Don’t use to spam or break Hinge TOS.
