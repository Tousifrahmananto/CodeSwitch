# CodeSwitch – Backend

Django REST API for the CodeSwitch multi-language code conversion and learning platform.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Django 4.x + Django REST Framework |
| Auth | SimpleJWT — httpOnly cookie-based (custom `JWTCookieAuthentication`) |
| Database | PostgreSQL (prod) / SQLite (dev) |
| AI | Groq / OpenAI / Gemini with 3-key automatic failover rotation |
| Brute-Force | `django-axes` (5 failed logins → 1-hour lockout) |
| CSP | `django-csp` strict Content Security Policy headers |
| Deployment | Gunicorn on Railway |

---

## Supported Languages

Python, C, C++, Java, JavaScript

---

## Project Structure

```
codeswitch/
├── manage.py
├── requirements.txt
├── Procfile                    # Railway: migrate → seed → collectstatic → gunicorn
├── .env.example
│
├── codeswitch/                 # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── admin_views.py          # Staff-only admin API views
│   └── wsgi.py
│
├── users/                      # Auth & user profiles
│   ├── authentication.py       # Custom httpOnly cookie JWT backend
│   ├── models.py               # Extended AbstractUser (bio, avatar)
│   ├── serializers.py
│   └── views.py
│
├── converter/                  # Code conversion engine
│   ├── ai_service.py           # Multi-provider AI client with key rotation
│   ├── services.py             # Rule-based regex conversion engine (fallback)
│   ├── throttles.py            # Per-user AI burst/sustained + anon run throttles
│   ├── models.py               # ConversionHistory, SharedSnippet
│   └── views.py
│
├── files/                      # User file workspace
│   ├── models.py               # CodeFile
│   └── views.py
│
└── learning/                   # Modules, lessons, quizzes, progress
    ├── models.py               # LearningModule, Lesson, UserProgress, Quiz, QuizAttempt
    ├── views.py
    └── management/commands/    # Seed scripts (auto-run on deploy if DB is empty)
        ├── seed_all_if_empty.py
        ├── seed_learning.py
        ├── seed_modules.py
        ├── seed_advanced_modules.py
        ├── seed_new_modules.py
        ├── seed_quizzes.py
        ├── seed_remaining_quizzes.py
        └── seed_new_quizzes.py
```

---

## Quick Setup

### 1. Install dependencies

```bash
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with SECRET_KEY, AI keys, database config
```

### 3. Migrate and seed

```bash
python manage.py migrate
python manage.py seed_all_if_empty
python manage.py createsuperuser
```

### 4. Run

```bash
python manage.py runserver
# API: http://localhost:8000/api/
# Django admin: http://localhost:8000/admin/
```

---

## API Endpoints

### Auth
| Method | Endpoint | Auth |
|---|---|---|
| POST | `/api/register/` | No |
| POST | `/api/login/` | No |
| POST | `/api/logout/` | Yes |
| POST | `/api/token/refresh/` | No |
| GET | `/api/me/` | Yes |
| GET/PUT | `/api/profile/` | Yes |
| GET | `/api/users/<username>/` | No |

### Conversion
| Method | Endpoint | Auth |
|---|---|---|
| POST | `/api/convert/` | Yes |
| GET | `/api/convert/history/` | Yes |
| POST | `/api/run/` | No |
| POST | `/api/explain/` | Yes |
| POST | `/api/snippets/` | Yes |
| GET | `/api/snippets/<slug>/` | No |

### Files
| Method | Endpoint | Auth |
|---|---|---|
| GET/POST | `/api/files/` | Yes |
| GET/PUT/DELETE | `/api/files/<id>/` | Yes |

### Learning
| Method | Endpoint | Auth |
|---|---|---|
| GET | `/api/modules/` | Yes |
| GET | `/api/modules/<id>/` | Yes |
| GET | `/api/lessons/<id>/` | Yes |
| POST | `/api/progress/update/` | Yes |
| GET | `/api/progress/` | Yes |
| GET | `/api/lessons/<id>/quiz/` | Yes |
| POST | `/api/quizzes/<id>/submit/` | Yes |

### Admin (staff only)
| Method | Endpoint |
|---|---|
| GET | `/api/admin/stats/` |
| GET/POST | `/api/admin/users/` |
| PATCH/DELETE | `/api/admin/users/<id>/` |
| GET | `/api/admin/conversions/` |
| GET/POST | `/api/admin/modules/` |
| PUT/DELETE | `/api/admin/modules/<id>/` |
| GET/PUT/DELETE | `/api/admin/lessons/<id>/` |

---

## Learning Modules (13 total)

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
| Pointers & Memory Management | Advanced |
| Linked Lists | Intermediate |
| Stacks & Queues | Intermediate |
| Hash Tables & Dictionaries | Intermediate |

---

## Deployment (Railway)

The `Procfile` runs on every deploy:

```
web: python manage.py migrate && python manage.py seed_all_if_empty && python manage.py collectstatic --noinput && gunicorn codeswitch.wsgi --bind 0.0.0.0:$PORT
```

Required Railway env vars: `DATABASE_URL`, `SECRET_KEY`, `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS`, `CSRF_TRUSTED_ORIGINS`, `AI_PROVIDER`, `AI_API_KEY`, `AI_API_KEY_2`, `AI_API_KEY_3`, `AI_MODEL`, `DEBUG=False`.

---

## Functional Requirements

- [x] Code conversion: input, source lang, target lang, output (Python, C, C++, Java, JavaScript)
- [x] AI conversion with Groq/OpenAI/Gemini + rule-based fallback
- [x] Live code execution via Wandbox sandbox
- [x] AI explanation of conversion differences
- [x] Shareable snippet links (UUID slugs)
- [x] File workspace: create, save, update, delete
- [x] 13 learning modules with quizzes and progress tracking
- [x] User registration, login, secure httpOnly JWT auth
- [x] Public user profiles with stats
- [x] Staff admin panel (user management, content CRUD, site stats)
- [x] Brute-force lockout, rate limiting, CSP headers
