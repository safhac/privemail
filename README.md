# Privemail

**Privemail** is an open-source, local-first email client designed for privacy and speed.

## 📥 Download Installer
Support the development of Privemail by purchasing the official Windows Installer. It comes pre-compiled, signed, and ready to use.

[**👉 Buy Privemail for Windows**](https://safhacster.gumroad.com/l/bnnpg)

---

## 🛠️ Building from Source (Free)
If you are a developer, you can build Privemail yourself for free.

### Prerequisites
* Python 3.12+
* Your own Google Cloud Credentials (`credentials.json`)

### Installation
1.  Clone the repo:
    ```bash
    git clone https://github.com/safhac/privemail
    cd privemail
    ```
2.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
3.  Add your `credentials.json` to `apps/privemail/`.
4.  Run the app:
    ```bash
    python -m apps.privemail.main
    ```

## 📥 Installation

### Windows Installer (Paid)
Support the project by buying the compiled installer.
[**👉 Buy on Gumroad**](https://safhacster.gumroad.com/l/bnnpg)

**Note on Windows SmartScreen:**
Because Privemail is an independent open-source project, we do not have a corporate signing certificate from Microsoft.
* Windows may flag the installer as an "Unrecognized App".
* This is normal. Click **"More Info"** $\rightarrow$ **"Run Anyway"** to install.
* You can verify the safety of the installer by checking the [Source Code](https://github.com/safhac/privemail) or comparing the SHA-256 hash below.

**SHA-256 Checksum:**
`[PASTE_YOUR_HASH_HERE]`


## 🔐 Zero-Trust & BYOK (Bring Your Own Key)
Privemail is built on a **Zero-Trust** architecture. Unlike other email clients that route your data through their servers, Privemail connects directly from your machine to Gmail.

To ensure total privacy, **we do not bundle shared API keys**.
* You must provide your own Google Cloud "Client ID" and "Secret".
* This ensures **we can never access your account**, even if we wanted to.
* It takes about 2 minutes to set up. [**👉 Read the Setup Guide**](LINK_TO_SETUP_GUIDE)


## 📄 License
This project is licensed under the **GNU General Public License v3.0**.