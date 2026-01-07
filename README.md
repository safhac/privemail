# Privemail

**A private, local-first AI email assistant.**

Privemail runs entirely on your machine. It connects to Gmail, downloads your messages to a local encrypted database, and uses local LLMs (via Ollama) to draft replies, analyze tone, and prioritize your inbox—keeping your data 100% private.

---

### 📥 Download & Support
**Not a developer?** You can support the project by purchasing the pre-compiled installer. It includes everything pre-configured (no Python or terminal required).

[ **Download Installer for Windows/Mac ($10)** ](https://your-website-link-here)

*Building from source is free (see below).*

---

## 🚀 Features

* **Zero Data Leakage**: Uses local AI models (Ollama). No data is sent to OpenAI or third parties.
* **Smart Prioritization**: AI analyzes email tone and urgency to score your inbox locally.
* **Draft & Edit**: The AI proposes drafts based on your goals; you refine them before sending.
* **Google Sync**: Connects securely to Gmail via OAuth.

## 📂 Project Structure

This project uses a standard `src` layout:

* `src/`: Application source code (`routes`, `database`, `core` logic).
* `app_data/`: Stores your local database (`app.db`) and secrets.
* `scripts/`: Maintenance and build scripts.

## 🛠️ Prerequisites

1.  **Python 3.10+**
2.  **[Ollama](https://ollama.com/)**: Required for AI features.
    * Install Ollama and run `ollama serve` in a terminal.
    * Pull the default model:
        ```bash
        ollama pull qwen2.5:3b
        ```

## 📦 Installation (Build from Source)

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/yourusername/privemail.git](https://github.com/yourusername/privemail.git)
    cd privemail
    ```

2.  **Create a Virtual Environment**
    ```bash
    python -m venv venv
    # Windows:
    .\venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

## 🔑 Configuration (Google OAuth)

To access your Gmail, you need a `credentials.json` file from Google Cloud.

1.  Go to the [Google Cloud Console](https://console.cloud.google.com/).
2.  Create a project and enable the **Gmail API** and **People API**.
3.  Configure the OAuth Consent Screen (Add `http://localhost:8080/` as a Redirect URI).
4.  Create Credentials (**OAuth Client ID** -> **Desktop App**).
5.  Download the JSON file, rename it to `credentials.json`, and place it in the **project root** folder.

## ▶️ Running the App

Once setup is complete, run the launcher script from the root directory:

```bash
python src/launcher.py