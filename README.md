# Privemail

**Privemail** is an open-source, local-first email client designed for privacy and speed.

## 📥 Download Installer
Support the development of Privemail by purchasing the official Windows Installer. It comes pre-compiled, signed, and ready to use.

[**👉 Buy Privemail for Windows**](LINK_TO_YOUR_GUMROAD_OR_WEBSITE)

---

## 🛠️ Building from Source (Free)
If you are a developer, you can build Privemail yourself for free.

### Prerequisites
* Python 3.12+
* Your own Google Cloud Credentials (`credentials.json`)

### Installation
1.  Clone the repo:
    ```bash
    git clone [https://github.com/YOUR_USER/privemail.git](https://github.com/YOUR_USER/privemail.git)
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

## 📄 License
This project is licensed under the **GNU General Public License v3.0**.