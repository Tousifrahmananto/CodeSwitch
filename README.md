<div align="center">

# 🔀 CodeSwitch

### Translate code between Python, C, and Java — instantly.

[![Django](https://img.shields.io/badge/Django-4.x-092E20?style=flat&logo=django&logoColor=white)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![JWT](https://img.shields.io/badge/Auth-JWT-000000?style=flat&logo=jsonwebtokens&logoColor=white)](https://jwt.io)
[![Monaco](https://img.shields.io/badge/Editor-Monaco-0078D4?style=flat&logo=visualstudiocode&logoColor=white)](https://microsoft.github.io/monaco-editor/)

</div>

---

## ✨ What is CodeSwitch?

**CodeSwitch** is a full-stack web application that converts source code between programming languages using both AI-powered and rule-based engines. It also includes an interactive learning platform, a personal file manager, and a user dashboard — all in a clean, dark-themed interface.

---

## 🚀 Features

| Feature | Description |
|---|---|
| **Code Converter** | Convert between Python, C, and Java with AI or rule-based engine |
| **5 Editor Themes** | Dark, Light, High Contrast, Monokai, Dracula |
| **Learning Modules** | 8+ modules from beginner to university-level algorithms |
| **Interactive Sandbox** | Live Try-It editor inside every lesson |
| **File Manager** | Save, edit, and manage your code files in the cloud |
| **Dashboard** | Conversion history, learning progress, file stats |
| **JWT Auth** | Secure login with email or username, strong password rules |
| **Admin Panel** | Manage users, modules, and conversions |

---

## 🛠️ Tech Stack

**Backend**
- Python 3.11 + Django 4 + Django REST Framework
- SimpleJWT for authentication (access + refresh tokens, blacklist on logout)
- AI integration: Groq / OpenAI / Google Gemini (configurable)
- SQLite (dev) / PostgreSQL (prod)

**Frontend**
- React 18 (no router — state-based navigation)
- Monaco Editor (`@monaco-editor/react`) with custom themes
- Axios with automatic JWT refresh interceptor
- Ubuntu font via Google Fonts

---

## 📦 Project Structure

```
codeswitch_project/
├── codeswitch/                  # Django project root
│   ├── codeswitch/              # Settings, URLs, WSGI
│   ├── users/                   # Auth: register, login, profile
│   ├── converter/               # Code conversion API + AI service
│   ├── files/                   # User file storage API
│   ├── learning/                # Modules, lessons, progress tracking
│   │   └── management/commands/ # Seed scripts for learning content
│   ├── frontend/                # React app
│   │   └── src/
│   │       ├── pages/           # Dashboard, Editor, FileManager, Learning, Login
│   │       ├── components/      # CodeEditor, LanguageSelector
│   │       └── api/client.js    # Axios instance with interceptors
│   ├── .env.example             # Environment variable template
│   ├── requirements.txt
│   └── manage.py
└── venv/                        # Not committed
```

---

## ⚙️ Setup & Installation

### Prerequisites
- Python 3.11+
- Node.js 18+
- (Optional) PostgreSQL for production

### 1. Clone the repository

```bash
git clone https://github.com/your-username/codeswitch.git
cd codeswitch
```

### 2. Create and activate virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
cd codeswitch
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
```

Edit `.env` and fill in your values:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Leave DB_ENGINE blank to use SQLite (recommended for dev)
DB_ENGINE=
DB_PASSWORD=

# AI conversion (optional — falls back to rule-based engine if blank)
AI_PROVIDER=groq        # groq | openai | gemini
AI_API_KEY=your-api-key
AI_MODEL=llama3-70b-8192
```

### 5. Run database migrations & seed learning content

```bash
python manage.py migrate
python manage.py seed_learning
python manage.py seed_modules
python manage.py seed_advanced_modules
```

### 6. Create an admin account

```bash
python manage.py createsuperuser
```

### 7. Start the backend

```bash
python manage.py runserver
```

### 8. Install frontend dependencies & start React

```bash
cd frontend
npm install
npm start
```

The app will be available at **http://localhost:3000**
The API runs at **http://localhost:8000**
The Django admin is at **http://localhost:8000/admin**

---

## 🔑 Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | — |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated hostnames | `localhost,127.0.0.1` |
| `DB_ENGINE` | Database engine (blank = SQLite) | `` |
| `DB_NAME` | PostgreSQL database name | `codeswitch_db` |
| `DB_USER` | PostgreSQL user | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | — |
| `DB_HOST` | Database host | `localhost` |
| `AI_PROVIDER` | AI provider (`groq`/`openai`/`gemini`) | `groq` |
| `AI_API_KEY` | Primary AI API key | — |
| `AI_API_KEY_2` | Fallback API key | — |
| `AI_API_KEY_3` | Second fallback API key | — |
| `AI_MODEL` | Model name | `llama3-70b-8192` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Access token lifetime | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Refresh token lifetime | `7` |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | `http://localhost:3000` |

---

## 📡 API Overview

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/register` | Create account | No |
| `POST` | `/api/login` | Login (username or email) | No |
| `POST` | `/api/logout` | Logout + blacklist token | No |
| `GET/PUT` | `/api/profile` | Get / update profile | Yes |
| `POST` | `/api/convert` | Convert code | Yes |
| `GET` | `/api/convert/history` | Conversion history | Yes |
| `GET/POST` | `/api/files` | List / create files | Yes |
| `GET/PUT/DELETE` | `/api/files/:id` | Manage a file | Yes |
| `GET` | `/api/modules` | List learning modules | Yes |
| `GET` | `/api/modules/:id` | Get module + lessons | Yes |
| `POST` | `/api/progress/update` | Mark lesson complete | Yes |
| `GET` | `/api/progress` | Get all progress | Yes |

---

## 🎓 Learning Modules

| Module | Level |
|---|---|
| CodeSwitch Learning Module | Beginner |
| Working with Strings | Beginner |
| Data Structures | Intermediate |
| Object-Oriented Programming | Intermediate |
| Error Handling and File I/O | Advanced |
| Algorithms and Recursion | Advanced |
| Advanced Sorting Algorithms | Intermediate |
| Dynamic Programming | Advanced |
| Graph Algorithms | Advanced |

---

## 🔒 Security

- Passwords require: 8+ characters, uppercase, lowercase, digit, and special character
- JWT tokens are rotated and blacklisted on logout
- API throttling: 300 req/min (authenticated), 30 req/min (anonymous)
- All secrets loaded from `.env` — never hardcoded
- Email uniqueness enforced at registration

---

## 📄 License

This project is for educational purposes.

---

<div align="center">
Built with ❤️ using Django + React
</div>
