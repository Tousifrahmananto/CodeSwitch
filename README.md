<div align="center">

# CodeSwitch

### Translate code between Python, C, C++, Java, and JavaScript — instantly.

[![Django](https://img.shields.io/badge/Django-4.x-092E20?style=flat&logo=django&logoColor=white)](https://djangoproject.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?style=flat&logo=react&logoColor=black)](https://reactjs.org)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?style=flat&logo=typescript&logoColor=white)](https://www.typescriptlang.org)
[![JWT](https://img.shields.io/badge/Auth-JWT%20httpOnly-000000?style=flat&logo=jsonwebtokens&logoColor=white)](https://jwt.io)
[![Monaco](https://img.shields.io/badge/Editor-Monaco-0078D4?style=flat&logo=visualstudiocode&logoColor=white)](https://microsoft.github.io/monaco-editor/)
[![Railway](https://img.shields.io/badge/Backend-Railway-0B0D0E?style=flat&logo=railway&logoColor=white)](https://railway.app)
[![Vercel](https://img.shields.io/badge/Frontend-Vercel-000000?style=flat&logo=vercel&logoColor=white)](https://vercel.com)

</div>

---

## What is CodeSwitch?

**CodeSwitch** is a full-stack web application that converts source code between five programming languages using a dual-engine approach: an AI-powered backend (Groq / OpenAI / Google Gemini) with automatic key rotation and a pure rule-based fallback engine. It also includes a live code execution sandbox, shareable conversion snippets, an interactive learning platform, a personal file manager, and a full admin panel — all behind a strict security stack with httpOnly cookie auth, CSP, and brute-force lockout.

---

## Features

| Feature | Description |
|---|---|
| **Code Converter** | Convert between Python, C, C++, Java, and JavaScript |
| **Dual Engine** | AI-first (Groq/OpenAI/Gemini) with auto key rotation; regex rule-based fallback |
| **Live Code Execution** | Run converted code instantly via Wandbox sandbox |
| **AI Code Explanation** | Plain-English explanation of what changed between source and output |
| **Shareable Snippets** | Share any conversion as a permanent public UUID-slug URL |
| **5 Editor Themes** | Dark, Light, High Contrast, Monokai, Dracula (Monaco Editor) |
| **9 Learning Modules** | Beginner → Advanced topics with quizzes and in-lesson Monaco sandbox |
| **Progress Tracking** | Track completed lessons and quiz attempts per user |
| **File Manager** | Save, edit, and organize code files in the cloud per language |
| **Dashboard** | Conversion history, learning progress, and file stats in one view |
| **Public Profiles** | Public per-user page showing conversion count, lessons, and languages used |
| **Admin Panel** | Staff-only dashboard: user management, module/lesson CRUD, site stats |
| **httpOnly JWT Auth** | Tokens stored in httpOnly cookies — never accessible to JavaScript |

---

## Tech Stack

### Backend
- Python 3.11 + Django 4 + Django REST Framework
- SimpleJWT — httpOnly cookie-based auth with token rotation and blacklist
- Custom `JWTCookieAuthentication` backend (tokens never exposed to JS)
- AI integration: Groq, OpenAI, or Google Gemini — configurable provider with 3-key failover
- Rule-based conversion engine (`converter/services.py`) as offline fallback
- Code execution proxied to [Wandbox](https://wandbox.org) (sandboxed, no server eval)
- `django-axes` — brute-force login lockout (5 attempts → 1-hour cooldown)
- `django-csp` — strict Content Security Policy middleware
- SQLite (dev) / PostgreSQL via `DATABASE_URL` (prod, Railway / Neon)
- Gunicorn + Railway deployment; Procfile handles migrate + seed + collectstatic on every deploy

### Frontend
- React 18 + TypeScript, built with Vite
- Monaco Editor (`@monaco-editor/react`) — 5 themes, lazy-loaded to cut initial bundle size
- `React.lazy` + `Suspense` code splitting (defers Monaco-heavy pages)
- `ErrorBoundary` class component — catches render errors with a "Try Again" fallback
- Axios with automatic JWT refresh interceptor and CSRF header injection
- TailwindCSS for styling
- Deployed on Vercel

---

## Project Structure

```
codeswitch_project/
├── codeswitch/                    # Django project root
│   ├── codeswitch/                # Settings, URLs, WSGI
│   │   ├── settings.py            # All security, JWT, throttle, CSP config
│   │   ├── urls.py                # Root url routing
│   │   └── admin_views.py         # Staff-only admin API views
│   ├── users/                     # Auth: register, login, logout, profile
│   │   └── authentication.py      # Custom httpOnly cookie JWT backend
│   ├── converter/                 # Code conversion API + AI service
│   │   ├── ai_service.py          # Multi-provider AI client with key rotation
│   │   ├── services.py            # Rule-based regex conversion engine (~46 KB)
│   │   ├── throttles.py           # Per-user AI burst/sustained + anon run throttles
│   │   └── views.py               # Convert, history, run, explain, snippet endpoints
│   ├── files/                     # User file storage API
│   ├── learning/                  # Modules, lessons, quizzes, progress tracking
│   │   └── management/commands/   # Seed scripts (auto-run on deploy if DB is empty)
│   ├── frontend/                  # React + TypeScript app (Vite)
│   │   └── src/
│   │       ├── pages/             # Converter, FileManager, Learning, Dashboard, Admin
│   │       ├── components/        # CodeEditor, LanguageSelector, etc.
│   │       └── api/client.ts      # Axios instance with refresh interceptor + CSRF
│   ├── .env.example               # Environment variable template
│   ├── requirements.txt
│   ├── Procfile                   # Railway: migrate → seed → collectstatic → gunicorn
│   └── manage.py
└── venv/                          # Not committed
```

---

## Setup & Installation

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
SECRET_KEY=your-django-secret-key-min-50-chars
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
CSRF_TRUSTED_ORIGINS=http://localhost:5173

# Leave DATABASE_URL blank to use SQLite (recommended for dev)
DATABASE_URL=

# AI conversion — falls back to rule-based engine if all keys are blank
AI_PROVIDER=groq       # groq | openai | gemini
AI_API_KEY=your-api-key
AI_API_KEY_2=          # optional failover key
AI_API_KEY_3=          # optional failover key
AI_MODEL=llama3-70b-8192
```

### 5. Run migrations and seed learning content

```bash
python manage.py migrate
python manage.py seed_all_if_empty   # seeds all modules, lessons, and quizzes if DB is empty
```

Or individually:

```bash
python manage.py seed_learning
python manage.py seed_modules
python manage.py seed_advanced_modules
python manage.py seed_new_modules
python manage.py seed_quizzes
```

### 6. Create an admin account

```bash
python manage.py createsuperuser
```

### 7. Start the backend

```bash
python manage.py runserver
```

### 8. Install frontend dependencies and start Vite dev server

```bash
cd frontend
npm install
npm run dev
```

The frontend runs at **http://localhost:5173**
The API runs at **http://localhost:8000**
The Django admin is at **http://localhost:8000/admin**

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key (50+ chars recommended) | — |
| `DEBUG` | Debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames | `localhost,127.0.0.1` |
| `DATABASE_URL` | Full DB URL (blank = SQLite) | `` |
| `DB_NAME` | PostgreSQL DB name (fallback if no DATABASE_URL) | `codeswitch_db` |
| `DB_USER` | PostgreSQL user | `postgres` |
| `DB_PASSWORD` | PostgreSQL password | — |
| `DB_HOST` | Database host | `localhost` |
| `CORS_ALLOWED_ORIGINS` | Allowed CORS origins | `http://localhost:5173` |
| `CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF | `http://localhost:5173` |
| `AI_PROVIDER` | AI provider (`groq`/`openai`/`gemini`) | `groq` |
| `AI_API_KEY` | Primary AI API key | — |
| `AI_API_KEY_2` | First failover AI key | — |
| `AI_API_KEY_3` | Second failover AI key | — |
| `AI_MODEL` | Model name | `llama3-70b-8192` |
| `JWT_ACCESS_TOKEN_LIFETIME_MINUTES` | Access token TTL | `60` |
| `JWT_REFRESH_TOKEN_LIFETIME_DAYS` | Refresh token TTL | `7` |

---

## API Overview

### Auth

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/register/` | Create account | No |
| `POST` | `/api/login/` | Login (username or email) | No |
| `POST` | `/api/logout/` | Logout + blacklist refresh token + clear cookies | Yes |
| `POST` | `/api/token/refresh/` | Rotate access token using refresh cookie | No |
| `GET` | `/api/me/` | Current authenticated user | Yes |
| `GET/PUT` | `/api/profile/` | Get / update profile (bio, avatar) | Yes |
| `GET` | `/api/users/<username>/` | Public profile — stats, languages, progress | No |

### Code Conversion

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/api/convert/` | Convert code (AI + rule-based fallback) | Yes |
| `GET` | `/api/convert/history/` | Last 50 conversions for the current user | Yes |
| `POST` | `/api/run/` | Execute code via Wandbox sandbox | No |
| `POST` | `/api/explain/` | AI explanation of conversion differences | Yes |
| `POST` | `/api/snippets/` | Create a shareable snippet | Yes |
| `GET` | `/api/snippets/<slug>/` | Read a shared snippet (public) | No |

### Files

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET/POST` | `/api/files/` | List / create files | Yes |
| `GET/PUT/DELETE` | `/api/files/<id>/` | Retrieve, update, or delete a file | Yes |

### Learning

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `GET` | `/api/modules/` | List all learning modules | Yes |
| `GET` | `/api/modules/<id>/` | Module detail + lessons | Yes |
| `GET` | `/api/lessons/<id>/` | Single lesson detail | Yes |
| `POST` | `/api/progress/update/` | Mark a lesson as complete | Yes |
| `GET` | `/api/progress/` | All progress for current user | Yes |
| `GET` | `/api/quizzes/<lesson_id>/` | Quiz for a lesson | Yes |
| `POST` | `/api/quizzes/<lesson_id>/attempt/` | Submit quiz answers | Yes |

### Admin (staff only)

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/admin/stats/` | Site-wide counts + week-over-week stats |
| `GET/POST` | `/api/admin/users/` | List users |
| `GET/PUT/DELETE` | `/api/admin/users/<id>/` | Toggle staff/active, delete user |
| `GET` | `/api/admin/conversions/` | Last 100 conversions across all users |
| `GET/POST` | `/api/admin/modules/` | List / create learning modules |
| `GET/PUT/DELETE` | `/api/admin/modules/<id>/` | Edit or delete a module |
| `GET` | `/api/admin/modules/<id>/lessons/` | All lessons for a module |
| `GET/PUT/DELETE` | `/api/admin/lessons/<id>/` | Edit or delete a lesson |

---

## Learning Modules

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

Each module contains structured lessons with a built-in Monaco sandbox for live experimentation, followed by a quiz. Progress is tracked per user and visible on the dashboard and public profile.

---

## Security

### Authentication
- **httpOnly cookie JWT** — Access and refresh tokens are set as `httpOnly; Secure; SameSite=None` cookies. JavaScript on the page can never read them, eliminating XSS-based token theft.
- **Custom `JWTCookieAuthentication`** — Django reads tokens from the cookie header, not from `Authorization`, so the frontend never handles raw tokens.
- **Token rotation + blacklist** — Every token refresh rotates the refresh token and the old token is blacklisted. Logout explicitly blacklists the current refresh token and clears both cookies.
- **Access token TTL: 60 min. Refresh token TTL: 7 days.**

### Password Policy
- Minimum 8 characters
- Must contain at least one uppercase letter, one lowercase letter, one digit, and one special character
- Enforced by `RegisterSerializer._check_password_strength()` before any database write

### Brute-Force Protection
- `django-axes` locks an account after **5 consecutive failed login attempts**
- Lockout duration: **1 hour**
- Locks on the combination of username + IP address
- Resets automatically on successful login

### Rate Limiting
| Scope | Limit |
|---|---|
| Authenticated users (global) | 300 requests/minute |
| Anonymous users (global) | 30 requests/minute |
| AI conversion — burst | 5 requests/minute per user |
| AI conversion — sustained | 30 requests/hour per user |
| Anonymous code execution | 10 requests/minute |

### Input Validation
- Language allowlist — only `python`, `c`, `cpp`, `java`, `javascript` accepted
- Code body capped at **50,000 characters**
- Null bytes stripped from code input before processing
- All serializer fields validated by DRF before hitting any service logic

### CORS and CSRF
- `CORS_ALLOWED_ORIGINS` is loaded from `.env` — no wildcard origins allowed when credentials are enabled
- `CORS_ALLOW_CREDENTIALS = True` — required for cross-origin cookie delivery (Vercel → Railway)
- `X-CSRFToken` header injected automatically by the Axios client on every state-changing request
- `CSRF_TRUSTED_ORIGINS` loaded from `.env`

### Security Headers
| Header | Value |
|---|---|
| `X-Frame-Options` | `DENY` |
| `X-Content-Type-Options` | `nosniff` |
| `X-XSS-Protection` | `1; mode=block` |
| `Strict-Transport-Security` | 1 year, includeSubDomains, preload (production only) |
| `Content-Security-Policy` | `default-src 'none'`; script-src `'self' 'unsafe-eval'`; frame-ancestors `'none'` |

### Content Security Policy
`django-csp` enforces a strict policy:
- `default-src 'none'`
- `script-src 'self' 'unsafe-eval'` — `unsafe-eval` required by Monaco Editor's worker model
- `font-src fonts.gstatic.com`
- `connect-src 'self' wandbox.org` — allows proxied code execution calls
- `frame-ancestors 'none'` — prevents clickjacking

### Code Execution Isolation
- Code is never executed on the CodeSwitch server
- All run requests are proxied to [Wandbox](https://wandbox.org), an isolated third-party sandbox
- The `RunCodeView` automatically selects the best available Wandbox compiler for the target language

### Environment Secrets
- All secrets (`SECRET_KEY`, API keys, DB credentials) are loaded exclusively from `.env` — never hardcoded
- `.env` and `.env.local` are listed in `.gitignore`

---

## Deployment

### Backend — Railway
The `Procfile` runs the following on every deploy:
```
web: python manage.py migrate && python manage.py seed_all_if_empty && python manage.py collectstatic --noinput && gunicorn codeswitch.wsgi
```

Set these Railway environment variables: `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `AI_PROVIDER`, `AI_API_KEY`, `AI_API_KEY_2`, `AI_API_KEY_3`, `AI_MODEL`, `DEBUG=False`.

### Frontend — Vercel
Build command: `npm run build`
Output directory: `dist`
Set `VITE_API_URL` to your Railway backend URL.

---

## License

This project is for educational purposes.

---

<div align="center">
Built with Django + React
</div>
