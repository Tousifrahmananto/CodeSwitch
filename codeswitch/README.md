# CodeSwitch – Multi-Language Code Conversion & Learning Platform

## Project Overview
A Django + React web application that allows users to convert code between Python, C, and Java, and learn programming through structured modules.

---

## Tech Stack
| Layer | Technology |
|-------|-----------|
| Backend | Django 4.x + Django REST Framework |
| Frontend | React.js |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Auth | JWT (djangorestframework-simplejwt) |
| Code Editor | Monaco Editor |
| Deployment | Nginx + Gunicorn |

---

## Project Structure
```
codeswitch/
├── manage.py
├── requirements.txt
├── .env.example
├── README.md
│
├── codeswitch/              # Django project config
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── users/                   # Auth & user profiles
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── converter/               # Code conversion engine
│   ├── models.py
│   ├── services.py          # Conversion logic lives here
│   ├── views.py
│   └── urls.py
│
├── files/                   # User file management
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
├── learning/                # Modules, lessons, progress
│   ├── models.py
│   ├── views.py
│   └── urls.py
│
└── frontend/                # React app
    ├── public/
    └── src/
        ├── App.jsx
        ├── pages/
        │   ├── Login.jsx
        │   ├── Dashboard.jsx
        │   ├── Editor.jsx
        │   ├── FileManager.jsx
        │   └── Learning.jsx
        ├── components/
        │   ├── CodeEditor.jsx
        │   ├── LanguageSelector.jsx
        │   └── ProgressTracker.jsx
        └── api/
            └── client.js
```

---

## Quick Setup

### 1. Clone & Install Backend
```bash
git clone <repo-url>
cd codeswitch
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Environment Variables
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Database Setup
```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

### 4. Run Backend
```bash
python manage.py runserver
# API available at http://localhost:8000/api/
```

### 5. Run Frontend
```bash
cd frontend
npm install
npm start
# App available at http://localhost:3000
```

---

## API Endpoints Summary

### Auth
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/register | Register new user |
| POST | /api/login | Login, returns JWT token |
| POST | /api/logout | Logout |
| GET | /api/profile | Get user profile |

### Code Conversion
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/convert | Convert code between languages |

### File Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/files | List user's files |
| POST | /api/files/create | Create new file |
| GET | /api/files/{id} | Get file by ID |
| PUT | /api/files/{id} | Update file |
| DELETE | /api/files/{id} | Delete file |

### Learning
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/modules | List all modules |
| GET | /api/modules/{id} | Get module detail |
| GET | /api/modules/{id}/lessons | Get lessons in a module |
| POST | /api/progress/update | Mark lesson complete |
| GET | /api/progress | Get user's progress |

---

## Functional Requirements Checklist
- [x] FR1–FR4: Code conversion (input, source lang, target lang, output)
- [x] FR5–FR6: Syntax-highlighted online editor
- [x] FR7–FR10: File create, save, delete, organize
- [x] FR11–FR14: Learning modules with exercises and progress tracking
- [x] FR15–FR17: User signup, login, secure profiles
- [x] FR18–FR20: Lesson completion, saved files, conversion history

---

## Database Models Summary

### User
- id, username, email, password, date_joined

### CodeFile
- id, user_id, filename, language, code_content, created_at, updated_at

### ConversionHistory
- id, user_id, source_language, target_language, input_code, output_code, timestamp

### LearningModule
- id, title, description, difficulty, language

### Lesson
- id, module_id, title, content, example_code, order

### UserProgress
- id, user_id, module_id, lesson_id, completed, completion_date

---

## Supported Languages (v1)
- Python
- C
- Java

## Future Enhancements
- JavaScript, Go, Rust, C++ support
- AI-based code explanation (AST parsing)
- Real-time code execution
- Collaborative workspace
- Gamified learning modules
- Instructor dashboards
