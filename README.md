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

## 🔑 Configuration (Google OAuth)

To access your Gmail, you need a `credentials.json` file from Google Cloud.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a project and enable the **Gmail API** and **People API**.
3.  Configure the OAuth Consent Screen (Add `http://localhost:8080/` as a Redirect URI).
4.  Create Credentials (**OAuth Client ID** -> **Desktop App**).
5.  Download the JSON file, rename it to `credentials.json`, and place it in the **`src/`** folder.

## ▶️ Usage

1.  Run `uv run src/launcher.py`.
2.  The browser will open automatically.
3.  Go to **Settings** to configure your AI Provider (Ollama is default).
4.  On first run, you will be prompted to log in to Google to sync emails.