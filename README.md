# Loopi-AI (Uppi) 🤖🎙️

> *"A high-fidelity, autonomous local AI assistant modeled after Tony Stark's JARVIS, custom built for macOS."*

**Loopi** is a unified, stateful voice-and-tool agent that runs locally on your Mac. It integrates physical wake triggers, a stateful Gemini-powered brain, and native macOS system controls to act not just as a chatbot, but as an active, agentic doer.

---

## 🌟 Key Features

### 🎙️ 1. Physical Wake Triggers
Loopi supports two background listening states to conserve API quota and sit unobtrusively in your menu bar or terminal:
*   **Wake Word**: Responds instantly to `"Hey Loopi"`, `"Da Loopi"`, `"Loopi"`, and vocal variations.
*   **Clap Detection**: Wakes up immediately upon a physical clap (detects transient audio amplitude spikes via numpy analysis).

### 🗣️ 2. Expressive Speech Engine
Rather than using static text-to-speech engines, Loopi speaks with real human emotion:
*   Powered by the **Gemini Live API (`gemini-3.1-flash-live-preview`)**.
*   Utilizes the premium, highly natural voice model `"Aoede"` to stream real-time expressive audio.
*   Pipes raw **24kHz Mono 16-bit PCM** audio streams directly to your Mac's hardware speakers using PyAudio.

### 🧠 3. Stateful Agentic Brain
Loopi is built on top of the `gemini-3.1-flash-lite` stateful chat API:
*   Maintains a persistent, conversational memory during your active sessions.
*   Natively binds system tools, executing them autonomously or chain-calling them on the fly.
*   Capable of writing and running temporary python/bash scripts locally to solve problems if a direct tool isn't available.

### 💻 4. Deep macOS Integration (Local Tools)
Loopi has full access to control your Mac through a custom suite of Python and AppleScript tools:
*   ⚡ **Terminal Action** (`run_command`): Safely executes bash commands on your macOS system.
*   📂 **File Manager** (`read_file`, `write_file`, `list_directory`): Directly reads, writes, and lists local directories.
*   📸 **System Actions** (`take_screenshot`, `set_volume`): Sets system volume via AppleScript and captures screenshots directly to your Desktop.
*   📱 **App Launcher** (`open_application`): Opens any macOS app (e.g., *Safari*, *Spotify*) by name.
*   🔍 **Yahoo Web Search** (`web_search`): Real-time scraping and HTML parsing via BeautifulSoup4 for live up-to-date facts.
*   📞 **Smart Contact Book** (`search_contact`, `add_contact`): Manages a local secure [contacts.json](file:///Users/mac/Desktop/Uppi/contacts.json).
*   ⌨️ **Keyboard Fallback** (`prompt_user_input`): Prompts you in the terminal for text that is hard to dictate verbally (like emails or passwords).
*   ✉️ **Active Gmail Compose** (`write_to_active_email`): Copies text to clipboard and runs a highly-focused AppleScript to paste text directly into your currently active Gmail tab in Google Chrome, avoiding opening messy new tabs.

---

## ⚙️ System Architecture

```
                                      ┌──────────────────────────────────────┐
                                      │              User's Mac              │
                                      └──────────────────┬───────────────────┘
                                                         │
                                               [PyAudio Mic Stream]
                                                         │
                                                         ▼
                                       ┌───────────────────────────────────┐
                       ┌──────────────►│    Background Wake Detector       │
                       │               └─────────────────┬─────────────────┘
                       │                                 │
                 [No Wake Triggered]          [Wake Word / Loud Clap]
                       │                                 │
                       └─────────────────────────────────┼─────────────────┐
                                                         ▼                 ▼
                                               ┌──────────────────┐  ┌──────────────┐
                                               │ Google Speech to │  │ PyAudio Live │
                                               │    Text (STT)    │  │  PCM Stream  │
                                               └─────────┬────────┘  └──────▲───────┘
                                                         │                  │
                                                   [Parsed Text]     [Expressive 24kHz]
                                                         │              [PCM Bytes]
                                                         ▼                  │
                                               ┌──────────────────┐         │
                                               │   Gemini Lite    │         │
                                               │ Stateful Chat    │         │
                                               └─────────┬────────┘         │
                                                         │                  │
                                                [Tool Call / Response]      │
                                                         │                  │
                                                         ▼                  │
                                               ┌──────────────────┐  ┌──────┴───────┐
                                               │ Loopi MCP Tools  │  │ Gemini Live  │
                                               │ (Mac System APIs)│  │ Voice Model  │
                                               └──────────────────┘  └──────────────┘
```

---

## ⚡ Quick Start

### 1. Prerequisites
Ensure you are running macOS and have the following installed:
*   **Python ≥ 3.11**
*   **PortAudio** (required for `PyAudio` voice capture). Install it via Homebrew:
    ```bash
    brew install portaudio
    ```
*   **`uv` Package Manager** (highly recommended for fast dependency resolution):
    ```bash
    curl -Lsf https://astral.sh/uv/install.sh | sh
    ```

### 2. Setup & Installation
Clone the repository and sync dependencies:
```bash
git clone https://github.com/Revu1309/Loopi-AI.git
cd Loopi-AI

# Create virtual environment and install dependencies in seconds using uv
uv sync
```

### 3. Environment Variables
Create a local `.env` configuration file from the provided example:
```bash
cp .env.example .env
```
Open [.env](file:///Users/mac/Desktop/Uppi/.env) and paste in your Gemini API Key:
```env
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. Running Loopi
You can start the unified assistant using `uv`:
```bash
uv run loopi.py
```
*   Upon launch, Loopi will ask you to remain quiet for **2 seconds** to calibrate its microphone for your room's ambient noise.
*   Once calibrated, she will enter **Sleeping Mode**. You can wake her up by saying `"Hey Loopi"` or simply by **clapping your hands**.

---

## 💬 Conversational Guardrails
To keep interactions quick, snappy, and premium:
*   Loopi speaks in highly conversational, punchy responses (**under 25 words / 2 sentences max**).
*   If you ask her for something long (e.g., a codebase explanation, a massive recipe, or directory logs), she will not read it out loud. Instead, she will dynamically compile it into a beautifully formatted text file, save it to your **Desktop**, and open it for you automatically, followed by a quick verbal summary.

---

## 📄 License
This project is licensed under the MIT License.
