# Changelog

All notable changes to Privemail are documented here.

---

## [1.2.1] – 2026-02-27

### Summary

This patch release fixes a security issue where the Google OAuth credentials file
was being bundled into the installer executable, and corrects the path where the
file must be placed. The setup wizard now shows clear instructions for obtaining
and placing the credentials file, and shows a helpful error message if it is missing.

---

### For installer users (Windows / Mac)

**Action required if upgrading from 1.2.0:**

If you previously placed `credentials.json` next to the Privemail executable
(e.g. inside `C:\Program Files\Privemail\`), please move it to the new location:

| Platform | New location for `credentials.json` |
|---|---|
| Windows | `C:\Users\YOUR_NAME\AppData\Roaming\Privemail\` |
| Mac | `~/Library/Application Support/Privemail/` |

**Windows tip:** Press `Win + R`, type `%APPDATA%\Privemail`, press Enter.

If you have not set up credentials yet, the setup wizard now walks you through
the process step by step.

---

### Changes

#### Security
- **Removed `credentials.json` from the PyInstaller bundle.** The file contains
  Google OAuth client secrets and must never be shipped inside the executable.
  The build no longer fails when the file is absent; instead the app shows a
  clear error message at runtime.

#### Bug fixes
- **Correct path for `credentials.json`.** The file is now read from the
  platform-specific user data directory (`%APPDATA%\Roaming\Privemail\` on
  Windows, `~/Library/Application Support/Privemail/` on Mac) instead of the
  executable directory, which may not be writable without administrator rights.
- **Setup wizard now shows when Google is not yet authorized.** Previously, if
  `credentials.json` or `token.json` was missing after a reinstall or on a fresh
  machine, the app would skip the setup wizard and open the main inbox (which
  would be empty or broken). The app now always shows the setup wizard until
  Google authorization is complete.

#### UX improvements
- **Setup wizard step 3** now includes a step-by-step guide explaining how to
  obtain `credentials.json` from the Google Cloud Console and where to place it,
  with platform-specific folder paths shown inline.
- **Clear error messages in the wizard.** If `credentials.json` is missing when
  you click "Authorize Google", the wizard now shows the exact file path where
  the file must be placed, instead of hanging silently.
- **Timeout feedback.** If the Google sign-in browser window is not completed
  within two minutes, the wizard shows a "Timed out" message and re-enables the
  Retry button.

#### Documentation
- **README** Google OAuth section rewritten with a table of correct data-folder
  paths for Windows installer, Mac installer, and source builds.

---

## [1.2.0] – (previous release)

- Universal AI backend: support for Ollama, LM Studio, LocalAI, and any
  OpenAI-compatible local server.
- Improved Windows installer.
- Mac build via GitHub Actions.
