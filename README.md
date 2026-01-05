# HingeGenie 🧞‍♂️

Smart, human-like auto-messaging bot for Hinge using UI XML extraction + GPT-4.

## 🧠 Features

- Auto-detects bio and profile data from Android UI hierarchy (XML)
- Sends flirty, friendly messages via ADB or emulator
- Supports GPT-4 message generation
- Human-like typing with delays, cursor movement
- Fully configurable via `config.yaml`

## 📜 Implementation History

**Current Method (Recommended): UI XML Extraction**
- Uses `adb shell uiautomator dump` to get the UI hierarchy as XML
- Directly parses text content from UI elements
- More reliable, faster, and doesn't require Tesseract OCR
- No dependency on screen resolution or image quality

**Legacy Method: OCR-based Extraction**
- Previously used screenshot + Tesseract OCR to extract text
- Required additional system dependencies (Tesseract)
- Prone to OCR accuracy issues with different fonts/backgrounds
- See "Legacy OCR Setup" section below if you prefer this method

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

4. (Optional) Install Tesseract OCR if using legacy OCR method:
   - Windows: Download installer from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)
   - Linux: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`
   - **Note**: Not required for the default XML-based extraction method

### Running Locally

1. Ensure your Android device is connected and ADB is working
2. Run the main script:
   ```bash
   python main.py
   ```

## 📋 Logs and History

The bot automatically creates and manages several directories to track its activity:

### Directory Structure

```
history/
├── dumps/               # UI XML dumps with timestamps
├── new_matches/         # UI dumps of new matches
├── profiles/            # Profile images (if saved)
├── messages/            # Sent messages (if saved)
├── prompt-response/     # GPT prompts and generated responses
├── tmp/                 # Temporary UI dumps during scrolling
├── interactions.log     # Log of all profile interactions
└── allPromts.txt        # Extracted profile prompts
```

### Files Created During Runtime

**Console Logs:**
- Real-time logging output to console with timestamps
- Format: `[YYYY-MM-DD HH:MM:SS] LEVEL: message`
- Logs all bot actions: scrolling, tapping, message generation, etc.

**UI Dumps (`history/dumps/`):**
- Timestamped XML snapshots: `dump_YYYYMMDD_HHMMSS.xml`
- Contains the complete Android UI hierarchy at time of capture
- Used for debugging and understanding app state

**Temporary Dumps (`history/tmp/`):**
- Sequential dumps during profile scrolling: `dump_1.xml`, `dump_2.xml`, etc.
- Cleared and regenerated each session
- Used to extract all profile prompts from multiple screens

**Prompt-Response Pairs (`history/prompt-response/`):**
- Timestamped files: `prompt_response_YYYYMMDD_HHMMSS.txt`
- Contains the extracted profile prompts and GPT-generated message
- Useful for reviewing bot performance and message quality

**Interaction Log (`history/interactions.log`):**
- Simple text file tracking which profiles have been contacted
- Prevents duplicate messages to the same profile
- One profile name per line

**Root Directory:**
- `ui.xml` - Latest UI hierarchy dump (overwritten each time)
- `ui_dump.xml` - Working copy of UI dump for parsing

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
    apt-get install -y adb && \
    pip install -r requirements.txt

# Note: tesseract-ocr not required for XML-based extraction
# Add 'tesseract-ocr' to apt-get if using legacy OCR method

CMD ["python", "main.py"]
```

## 📁 Config

Edit `config.yaml` to change your GPT style or fallback rules.

## 🔄 Legacy OCR Setup (Optional)

If you prefer using the original OCR-based method instead of XML extraction:

1. Install Tesseract OCR (see prerequisites above)
2. Modify your code to use screenshot + OCR instead of XML parsing
3. The OCR method captures a screenshot and uses pytesseract to extract text

**Why XML is better:**
- ✅ Faster extraction (no image processing needed)
- ✅ 100% accuracy (reads actual UI text, not interpreted from pixels)
- ✅ No additional dependencies (uses built-in Android uiautomator)
- ✅ Works in all lighting conditions and with any font/theme

**When to use OCR:**
- If you need to extract text from images or non-standard UI elements
- If the app obfuscates its UI hierarchy
- For compatibility with older Android versions that don't support uiautomator

## ⚠️ Ethical Note

This tool is for educational/personal automation. Don't use to spam or break Hinge TOS.
