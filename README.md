# Privemail

**A private, local-first AI email assistant.**

Privemail runs entirely on your machine. It connects to Gmail, downloads your messages to a local encrypted database, and uses local AI models to draft replies, analyze tone, and prioritize your inbox—keeping your data 100% private.

**Now Universal:** Works with **Ollama**, **LM Studio**, **LocalAI**, or any OpenAI-compatible local server.

---

### 📥 Download & Support
**Not a developer?** You can support the project by purchasing the pre-compiled installer. It includes everything pre-configured (no Python or terminal required).

[ **Download Installer for Windows ($10)** ](https://safhacster.gumroad.com/l/bnnpg)

[ **Download Installer for Mac ($10)** ](https://safhacster.gumroad.com/l/kxwfcv)

*Building from source is free (see below).*

---

## 🚀 Features

* **Universal AI Backend**: Connect to **Ollama** (native), **LM Studio**, **vLLM**, or any OpenAI-compatible API.
* **Zero Data Leakage**: Your email data never leaves your machine.
* **Smart Prioritization**: AI analyzes email tone and urgency to score your inbox locally.
* **Draft & Edit**: The AI proposes drafts based on your goals; you refine them before sending.
* **Google Sync**: Connects securely to Gmail via OAuth.

## 📂 Project Structure

This project uses a standard `src` layout:

* `src/`: Application source code (`routes`, `database`, `core` logic).
* `src/app_data/`: Stores your local database (`app.db`) and secrets.
* `src/clients/`: AI Engine adapters.

## 🛠️ Prerequisites

1.  **Python 3.10+**
2.  **Local AI Provider** (Choose one):
    * **[Ollama](https://ollama.com/)** (Easiest): Install and run `ollama serve`.
    * **[LM Studio](https://lmstudio.ai/)**: Start the "Local Server" on port 1234.
    * **Any OpenAI-Compatible API**: Any local server that speaks the `/v1/chat/completions` protocol.

    *Recommended Model:* `qwen2.5:3b` (Fast) or `mistral-nemo` (Smart).

## 📦 Installation (Source)

1.  **Install uv** (An extremely fast Python package manager)
    * Mac/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
    * Windows: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"`

2.  **Run the App**
    ```bash
    uv run src/launcher.py
    ```
    *(This command will automatically create the virtual environment, install all dependencies, and launch the app in one step.)*

## 🔑 Google OAuth Setup

Privemail connects to Gmail using a Google Cloud OAuth credential file. You need to create this file once.

### Step 1 — Create credentials.json

1. Go to the [Google Cloud Console](https://console.cloud.google.com/) and sign in.
2. Create a new project (or select an existing one).
3. Enable two APIs: **Gmail API** and **People API** (search for each under *APIs & Services → Library*).
4. Go to *APIs & Services → OAuth Consent Screen*. Set it to **External**, fill in the app name.
5. Go to *APIs & Services → Credentials → Create Credentials → OAuth Client ID*.
6. Choose **Desktop App** as the application type.
7. Click **Download JSON**. Rename the downloaded file to `credentials.json`.

### Step 2 — Place credentials.json in the right folder

Where you put the file depends on how you are running Privemail:

| How you run Privemail | Where to put `credentials.json` |
|---|---|
| **Windows installer** (downloaded from Gumroad) | `C:\Users\YOUR_NAME\AppData\Roaming\Privemail\` |
| **Mac installer** (downloaded from Gumroad) | `~/Library/Application Support/Privemail/` |
| **Running from source** (developers) | `src/app_data/` inside the project folder |

> **Windows tip:** Press `Win + R`, type `%APPDATA%\Privemail` and press Enter to open the folder directly. If the folder does not exist yet, run the app once and it will be created automatically.

After placing the file, restart the app. The setup wizard will guide you through the Google sign-in.

---

## ▶️ Usage

1.  Run `uv run src/launcher.py` (source) or launch the installed app.
2.  The browser will open automatically to the setup wizard.
3.  Follow the wizard: set a password → authorize Google → select an AI model.
4.  On subsequent launches, the app opens directly to your inbox.