# HingeGenie

Smart, human-like auto-messaging bot for Hinge using UI XML extraction + Gemini AI.

## Features

- **UI XML Extraction**: Extracts profile data directly from Android UI hierarchy - no OCR needed
- **AI-Powered Responses**: Generates witty, personalized messages using Google Gemini 2.0 Flash
- **Human-Like Behavior**: Realistic typing delays, natural scrolling, and randomized timing
- **History Tracking**: Logs all interactions to prevent duplicate messages
- **Fully Configurable**: Customize tone, delays, and response style via `config.yaml`

## How It Works

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Android Device │────▶│   UI XML Dump    │────▶│ Parse Profiles  │
│  (via ADB)      │     │  (uiautomator)   │     │  & Prompts      │
└─────────────────┘     └──────────────────┘     └────────┬────────┘
                                                          │
┌─────────────────┐     ┌──────────────────┐     ┌────────▼────────┐
│  Send Message   │◀────│  Type with       │◀────│  Gemini AI      │
│  & Log          │     │  Human Delays    │     │  Response Gen   │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

1. **Capture**: Scrolls through Hinge and dumps UI hierarchy as XML
2. **Extract**: Parses XML to find profile prompts and answers
3. **Generate**: Sends context to Gemini AI for a personalized response
4. **Deliver**: Types and sends the message with human-like behavior
5. **Track**: Logs the interaction to prevent duplicates

## Prerequisites

- Python 3.10+
- ADB (Android Debug Bridge)
- Google Gemini API key

### Installing ADB

| Platform | Command |
|----------|---------|
| Windows  | Download from [Android Platform Tools](https://developer.android.com/studio/releases/platform-tools) |
| Linux    | `sudo apt-get install adb` |
| macOS    | `brew install android-platform-tools` |

### Setting Up Your Android Device

1. Go to **Settings > About Phone**
2. Tap **Build Number** 7 times to enable Developer Options
3. Go to **Developer Options** and enable **USB Debugging**
4. Connect your device via USB
5. Verify connection:
   ```bash
   adb devices
   ```

## Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/abhayraghuwanshi/hinge-genie.git
   cd hinge-genie
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv

   # Windows
   .\venv\Scripts\activate

   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**

   Create a `.env` file in the project root:
   ```
   GEMINI_API_KEY=your_api_key_here
   ```

## Usage

1. Connect your Android device with Hinge open
2. Run the bot:
   ```bash
   python main.py
   ```

The bot will continuously:
- Scroll through profiles
- Extract prompt-answer pairs
- Generate personalized responses
- Send messages with natural timing

Press `Ctrl+C` to stop.

## Configuration

Edit `config.yaml` to customize behavior:

```yaml
gpt:
  enabled: true
  target_age: 23-26
  target_relationship: "Short to long"
  style: "playful and flirty"
  personality: "witty and charming"
  temperature: 0.3

delays:
  min_typing_delay: 0.08      # Seconds between keystrokes
  max_typing_delay: 0.20
  min_message_wait: 3         # Seconds before sending
  max_message_wait: 7

max_retries: 3
```

## Project Structure

```
hinge-genie/
├── main.py                 # Entry point - main bot loop
├── config.yaml             # Bot configuration
├── requirements.txt        # Python dependencies
├── .env                    # API keys (create this)
├── utils/
│   ├── actions.py          # ADB interactions (tap, scroll, UI dumps)
│   ├── llm.py              # Gemini AI integration
│   ├── prompt_extractor.py # Extract prompts from UI XML
│   ├── interaction_manager.py  # History and file management
│   └── message_sender.py   # Message typing and sending
└── history/
    ├── dumps/              # UI XML snapshots
    ├── tmp/                # Temporary dumps during scrolling
    ├── prompt-response/    # Generated prompts and responses
    └── interactions.log    # Interaction history
```

## Logs & History

The bot creates several files to track activity:

| Location | Purpose |
|----------|---------|
| `history/dumps/` | Timestamped UI XML snapshots |
| `history/prompt-response/` | AI prompts and generated responses |
| `history/interactions.log` | Profiles already contacted |
| `ui.xml` | Latest UI hierarchy dump |

## Technical Details

### Why XML over OCR?

| Feature | XML Extraction | OCR |
|---------|---------------|-----|
| Accuracy | 100% | Variable |
| Speed | Fast | Slow |
| Dependencies | None | Tesseract |
| Font/Theme | Any | Limited |
| Reliability | High | Medium |

### AI Response Guidelines

The bot instructs Gemini to:
- Keep responses under 140 characters
- Use simple, conversational English
- End with an open-ended question
- Avoid emojis
- Match a playful, flirty tone

## Troubleshooting

**Device not detected**
```bash
adb kill-server
adb start-server
adb devices
```

**Permission denied**
- Ensure USB debugging is enabled
- Accept the debugging prompt on your device

**API errors**
- Verify your Gemini API key in `.env`
- Check your API quota

## Disclaimer

This tool is for educational and personal use only. Use responsibly and in accordance with Hinge's Terms of Service. Do not use for spam or automated mass messaging.

## License

MIT
