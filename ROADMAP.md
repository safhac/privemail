# 🗺️ Privemail Roadmap

This document outlines the current status and future plans for Privemail. Our goal is to build the fastest, most private local-first email client.

**Legend:**
- ✅ **Completed**: Live in the current build.
- 🚧 **In Progress**: Currently being worked on.
- 🔮 **Planned**: Scheduled for future releases.

---

## 🚀 Phase 1: Core Stability & Architecture (Current)
*Focus: Establishing the local-first database and basic email operations.*

- ✅ **Local-First Architecture**: Complete SQLite database integration for offline access & persistence.
- ✅ **Basic Email Ingestion**: Gmail API syncing and storage.
- ✅ **Secure Storage**: Database encryption at rest for user privacy.
- ✅ **Contact & Group Management**: Organize contacts locally.
- ✅ **Inbox View**: Navigation and thread viewing.
- 🚧 **Sending Capability**: UI fully implemented; backend transmission in testing (currently mock).
- 🚧 **System Status**: Visual indicators for sync state and loading background tasks.

## 🧠 Phase 2: AI & Intelligence
*Focus: On-device model optimization and smart context.*

- ✅ **AI Analysis Pipeline**: Integrated Ollama for local inference.
- ✅ **Model Selection**: Support switching between qwen3, llama3, or others for performance/quality balance.
- ✅ **Prompt Engineering**: "Goal" templates refined for specific industries (Legal, Tech, Sales).
- 🔮 **Context Awareness**: Allow AI to read full conversation history for better reply context.
- 🔮 **Smart Priority Scoring**: Algorithm to rank emails by importance locally.

## 🛠️ Phase 3: User Experience & Reliability
*Focus: Smoothing out the edges for daily use.*

- 🔮 **Help & Tutorials**: "Read the Docs" section with examples for Goal/Tone settings.
- 🔮 **Error Logging**: Rolling 3-day log retention for easier debugging.
- 🔮 **Tracker Blocking**: Automatically strip pixel trackers from incoming emails.

## 📦 Phase 4: Production & Distribution
*Focus: Preparing for public release and monetization.*

- 🚧 **Packaging**: Bundle application as a standalone Windows executable (`.exe`).
- 🔮 **License Server**: Implement JWT-based offline activation for paid users.
- 🔮 **Auto-Update**: Mechanism to fetch and apply updates securely.

---

## 🤝 How to Contribute
We welcome contributions!
1.  Check the [Issues](https://github.com/YOUR_USERNAME/privemail/issues) tab.
2.  Fork the repository.
3.  Submit a Pull Request targeting the `main` branch.