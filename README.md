<div align="center">

# 🎓 Menouf Bot

### Advanced Telegram Bot for University Services

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-0088CC.svg)](https://telegram.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B.svg)](https://streamlit.io/)
[![Firebase](https://img.shields.io/badge/Firebase-Ready-FFCA28.svg)](https://firebase.google.com/)

**Subject Search • Program Selection • Interactive Dashboard**

[Features](#-features) • [Installation](#-installation) • [Usage](#-usage) • [Contributing](#-contributing)

[العربية](README-ar.md) | [English](#-menouf-bot)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [Technologies Used](#-technologies-used)
- [Contributing](#-contributing)

---

## 🎯 Overview

**Menouf Bot** is an advanced Telegram bot for Menoufia University services with subject search features, program selection, and intuitive navigation. Includes an interactive Streamlit dashboard and Firebase data management.

### ✨ Why Menouf Bot?

- 🔍 **Fast Search** - Instant search for academic subjects
- 📚 **Browse Programs** - Easily browse and select academic programs
- 📊 **Dashboard** - Manage data from an interactive interface
- 🔥 **Cloud Storage** - Secure data in Firebase

---

## 🌟 Features

### 🚀 Main Features

| Feature | Description |
|---------|-------------|
| 🔍 **Subject Search** | Fast search for academic subjects |
| 📚 **Program Selection** | Browse and select different academic programs |
| 🎯 **Intuitive Navigation** | Easy and comfortable user interface |
| 📊 **Streamlit Dashboard** | Interactive dashboard for data management |
| 🔥 **Firebase Support** | Data storage in Firebase |
| 🤖 **Telegram Bot** | Fast and easy-to-use bot interface |

### 📱 Additional Features

- ✅ SQLite support as local alternative
- ✅ Advanced management interface
- ✅ Data export
- ✅ Detailed statistics

---

## 📦 Requirements

Before starting, make sure you have installed:

- **Python** 3.8 or higher
- **Telegram Bot Token** (from [@BotFather](https://t.me/BotFather))
- **Firebase** account (optional)
- **Git**

---

## 🚀 Installation

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/3bkader-gpt/menouf_bot.git
cd menouf_bot

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install requirements
pip install -r requirements.txt

# 4. Set up environment variables
export BOT_TOKEN="your_telegram_bot_token"
export FIREBASE_CREDENTIALS="path/to/credentials.json"  # Optional
```

### Firebase Setup (Optional)

```bash
# 1. Create a new Firebase project
# 2. Get credentials file
# 3. Add path in environment variables
export FIREBASE_CREDENTIALS="path/to/credentials.json"

# Or use SQLite as local alternative
```

---

## ⚙️ Configuration

### Telegram Bot Setup

1. Talk to [@BotFather](https://t.me/BotFather)
2. Create a new bot using `/newbot`
3. Get the Token
4. Add Token in environment variables:
   ```bash
   export BOT_TOKEN="123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
   ```

### Firebase Setup

1. Create a new Firebase project from [Console](https://console.firebase.google.com)
2. Get credentials file (JSON)
3. Add path in environment variables

### Streamlit Setup

Copy `streamlit_secrets_template.toml` and add your data:

```toml
[BOT_TOKEN]
token = "your_bot_token"

[FIREBASE]
credentials_path = "path/to/credentials.json"
```

---

## 📖 Usage

### Running the Bot

```bash
python bot.py
```

### Running the Dashboard

```bash
streamlit run dashboard.py
```

Then open browser at `http://localhost:8501`

### Available Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start using the bot |
| `/search` | Search for an academic subject |
| `/programs` | Show available programs |
| `/help` | Show help |
| `/about` | Bot information |

### Using the Dashboard

- 📊 **View Data** - View all subjects and programs
- 🔍 **Search & Filter** - Advanced search and filtering
- ✏️ **Edit Data** - Add/edit/delete data
- 📈 **Statistics** - Detailed statistics

---

## 📁 Project Structure

```
menouf_bot/
├── 📂 .devcontainer/        # Dev Container settings
├── 📂 .github/               # GitHub settings
├── 📄 bot.py                 # Main bot code
├── 📄 dashboard.py           # Streamlit dashboard
├── 📄 db.py                  # Database management
├── 📄 strings.py             # Texts and messages
├── 📄 check_firebase.py      # Firebase connection check
├── 📄 migrate_firebase.py    # Data migration to Firebase
├── 📄 test_db.py             # Database tests
├── 📄 requirements.txt       # Requirements
└── 📄 streamlit_secrets_template.toml  # Streamlit settings template
```

---

## 🛠️ Technologies Used

<div align="center">

| Technology | Description |
|------------|-------------|
| ![Python](https://img.shields.io/badge/Python-3.8+-3776AB?logo=python&logoColor=white) | Main programming language |
| ![Telegram](https://img.shields.io/badge/Telegram-Bot-0088CC?logo=telegram&logoColor=white) | Telegram bot |
| ![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit&logoColor=white) | Dashboard |
| ![Firebase](https://img.shields.io/badge/Firebase-Ready-FFCA28?logo=firebase&logoColor=white) | Cloud database |
| ![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white) | Local database |

</div>

---

## 🚀 Deployment

### Render.com

See `DEPLOY_RENDER.md` for deployment instructions on Render.com.

### Required Environment Variables

See `RENDER_ENV_VARS.md` for list of required environment variables.

---

## 🤝 Contributing

Contributions are welcome! 🎉

1. 🍴 Fork the project
2. 🌿 Create a branch (`git checkout -b feature/AmazingFeature`)
3. 💾 Commit (`git commit -m 'Add some AmazingFeature'`)
4. 📤 Push (`git push origin feature/AmazingFeature`)
5. 🔄 Open a Pull Request

---

## 📄 License

This project is open source and available for free use.

---

## 📞 Contact & Support

- 🐛 **Report Issues**: [Open an Issue](https://github.com/3bkader-gpt/menouf_bot/issues)
- 💡 **Suggest Features**: [Open an Issue](https://github.com/3bkader-gpt/menouf_bot/issues)
- 📧 **Email**: medo.omar.salama@gmail.com

---

<div align="center">

**Made with ❤️ by [Mohamed Omar](https://github.com/3bkader-gpt)**

⭐ If you like this project, don't forget to give it a star!

[⬆ Back to Top](#-menouf-bot)

</div>