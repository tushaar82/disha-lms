# Quickstart Guide: Multi-Center LMS

**Feature**: Multi-Center Student Learning & Satisfaction Management System  
**Branch**: 001-multi-center-lms  
**Date**: 2025-11-01

## Overview

This guide helps developers set up the Disha LMS development environment and start contributing to the multi-center learning management system.

---

## Prerequisites

- **Python**: 3.11 or higher
- **pip**: Latest version
- **Git**: For version control
- **Node.js**: 18+ (for Tailwind CSS compilation)
- **Code Editor**: VS Code, PyCharm, or similar

---

## Quick Setup (5 minutes)

### 1. Clone Repository

```bash
git clone <repository-url>
cd disha-lms
git checkout 001-multi-center-lms
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Node.js dependencies (for Tailwind CSS)
npm install
```

### 4. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your settings
# For development, defaults should work fine
```

### 5. Initialize Database

```bash
# Run migrations
python manage.py migrate

# Create superuser (Master Account)
python manage.py createsuperuser
# Email: admin@example.com
# Password: (choose a strong password)
# Role: master

# Load sample data (optional)
python manage.py loaddata initial_data.json
```

### 6. Compile Static Assets

```bash
# Compile Tailwind CSS
npm run build:css

# Or watch for changes during development
npm run watch:css
```

### 7. Run Development Server

```bash
# Start Django development server
python manage.py runserver

# Server will be available at: http://127.0.0.1:8000/
```

### 8. Access the Application

- **Web Interface**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **API Documentation**: http://127.0.0.1:8000/api/docs/
- **Login**: Use the superuser credentials created in step 5

---

## Project Structure

```
disha_lms/
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── package.json                # Node.js dependencies (Tailwind)
├── tailwind.config.js          # Tailwind CSS configuration
├── pytest.ini                  # Pytest configuration
├── .env                        # Environment variables (gitignored)
├── .env.example                # Environment template
├── config/                     # Django settings
│   ├── settings/
│   │   ├── base.py             # Base settings
│   │   ├── development.py      # Development settings (SQLite)
│   │   └── production.py       # Production settings (PostgreSQL)
│   ├── urls.py                 # Root URL configuration
│   └── wsgi.py                 # WSGI application
├── apps/                       # Django applications
│   ├── accounts/               # Authentication & authorization
│   ├── centers/                # Center management
│   ├── students/               # Student management
│   ├── faculty/                # Faculty management
│   ├── subjects/               # Subject & topic management
│   ├── attendance/             # Attendance tracking (core)
│   ├── reports/                # Reporting & analytics
│   ├── feedback/               # Student feedback
│   ├── api/                    # REST API
│   └── core/                   # Shared utilities
├── templates/                  # Django templates
│   ├── base.html               # Base template
│   └── components/             # Reusable components
├── static/                     # Static files
│   ├── css/                    # Compiled CSS
│   ├── js/                     # JavaScript
│   └── images/                 # Images
└── tests/                      # Tests
    ├── integration/            # Integration tests
    └── e2e/                    # End-to-end tests
```

---

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Edit code in `apps/` directory. Each app follows Django's standard structure:
- `models.py` - Database models
- `views.py` - View logic
- `forms.py` - Form definitions
- `urls.py` - URL routing
- `templates/` - HTML templates
- `tests/` - Unit tests

### 3. Run Tests

```bash
# Run all tests
pytest

# Run specific app tests
pytest apps/attendance/tests/

# Run with coverage
pytest --cov=apps --cov-report=html

# View coverage report
open htmlcov/index.html
```

### 4. Check Code Quality

```bash
# Run linter
flake8 apps/

# Run type checker
mypy apps/

# Run security checks
bandit -r apps/

# Check for dependency vulnerabilities
safety check
```

### 5. Format Code

```bash
# Format with Black
black apps/

# Sort imports
isort apps/
```

### 6. Create Migrations

```bash
# After modifying models
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### 7. Commit Changes

```bash
git add .
git commit -m "feat: add attendance marking feature"
git push origin feature/your-feature-name
```

---

## Common Development Tasks

### Create a New Django App

```bash
# Create app in apps/ directory
python manage.py startapp myapp apps/myapp

# Add to INSTALLED_APPS in config/settings/base.py
INSTALLED_APPS = [
    ...
    'apps.myapp',
]
```

### Create a New Model

```python
# apps/myapp/models.py
from apps.core.models import TimeStampedModel, SoftDeleteModel

class MyModel(TimeStampedModel, SoftDeleteModel):
    name = models.CharField(max_length=200)
    description = models.TextField()
    
    class Meta:
        db_table = 'my_models'
        verbose_name = 'My Model'
        verbose_name_plural = 'My Models'
    
    def __str__(self):
        return self.name
```

### Create API Endpoint

```python
# apps/api/v1/views.py
from rest_framework import viewsets
from apps.myapp.models import MyModel
from .serializers import MyModelSerializer

class MyModelViewSet(viewsets.ModelViewSet):
    queryset = MyModel.objects.all()
    serializer_class = MyModelSerializer
    permission_classes = [IsAuthenticated]

# apps/api/v1/urls.py
router.register(r'mymodels', MyModelViewSet)
```

### Add a Template

```html
<!-- templates/myapp/mytemplate.html -->
{% extends "base.html" %}

{% block title %}My Page{% endblock %}

{% block content %}
<div class="container mx-auto p-4">
    <h1 class="text-2xl font-bold">My Page</h1>
    <!-- Your content here -->
</div>
{% endblock %}
```

### Add Tailwind CSS Classes

```html
<!-- Use DaisyUI components -->
<button class="btn btn-primary">Click Me</button>
<div class="card bg-base-100 shadow-xl">
    <div class="card-body">
        <h2 class="card-title">Card Title</h2>
        <p>Card content</p>
    </div>
</div>
```

### Create a Management Command

```python
# apps/myapp/management/commands/mycommand.py
from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Description of your command'
    
    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Command executed'))
```

Run with: `python manage.py mycommand`

---

## Testing

### Run Specific Tests

```bash
# Run unit tests for attendance app
pytest apps/attendance/tests/test_models.py

# Run integration tests
pytest tests/integration/

# Run E2E tests (requires Selenium)
pytest tests/e2e/

# Run with verbose output
pytest -v

# Run with print statements
pytest -s
```

### Write a Test

```python
# apps/attendance/tests/test_models.py
import pytest
from django.utils import timezone
from apps.attendance.models import AttendanceRecord
from apps.students.models import Student

@pytest.mark.django_db
class TestAttendanceRecord:
    def test_create_attendance_record(self, student, faculty, assignment):
        """Test creating an attendance record."""
        record = AttendanceRecord.objects.create(
            assignment=assignment,
            student=student,
            faculty=faculty,
            date=timezone.now().date(),
            status='present',
            in_time='09:00:00',
            out_time='10:30:00',
            created_by=faculty.user
        )
        
        assert record.status == 'present'
        assert record.session_duration_minutes == 90
```

---

## Database Management

### Reset Database

```bash
# Delete database file
rm db.sqlite3

# Run migrations again
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Backup Database

```bash
# Export data
python manage.py dumpdata > backup.json

# Import data
python manage.py loaddata backup.json
```

### View Database

```bash
# Open Django shell
python manage.py shell

# Query models
from apps.students.models import Student
students = Student.objects.all()
for student in students:
    print(student.full_name)
```

---

## Debugging

### Django Debug Toolbar

Already installed in development. Access at: http://127.0.0.1:8000/__debug__/

Shows:
- SQL queries
- Template rendering time
- Cache hits/misses
- Signal calls

### Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint() in Python 3.7+
breakpoint()
```

### View Logs

```bash
# Django logs to console by default in development
# Check terminal where runserver is running
```

---

## Environment Variables

Edit `.env` file:

```bash
# Django settings
DJANGO_SETTINGS_MODULE=config.settings.development
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Email (console backend for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Redis (optional, for caching)
REDIS_URL=redis://localhost:6379/0

# Celery (optional, for background tasks)
CELERY_BROKER_URL=redis://localhost:6379/0
```

---

## API Development

### Test API with cURL

```bash
# Login
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "yourpassword"}'

# Get token from response, then:
TOKEN="your-token-here"

# List students
curl http://127.0.0.1:8000/api/v1/students/ \
  -H "Authorization: Token $TOKEN"

# Create student
curl -X POST http://127.0.0.1:8000/api/v1/students/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "John", "last_name": "Doe", ...}'
```

### API Documentation

- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **ReDoc**: http://127.0.0.1:8000/api/redoc/
- **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/

---

## Troubleshooting

### Port Already in Use

```bash
# Kill process on port 8000
# Linux/Mac:
lsof -ti:8000 | xargs kill -9

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Migration Conflicts

```bash
# Reset migrations (development only!)
python manage.py migrate --fake <app_name> zero
python manage.py migrate <app_name>
```

### Static Files Not Loading

```bash
# Collect static files
python manage.py collectstatic --noinput

# Rebuild Tailwind CSS
npm run build:css
```

### Import Errors

```bash
# Ensure virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall dependencies
pip install -r requirements.txt
```

---

## Production Deployment

See `docs/deployment.md` for production deployment guide with:
- PostgreSQL setup
- Gunicorn + Nginx configuration
- Docker deployment
- Environment variables for production
- SSL/TLS setup
- Monitoring and logging

---

## Additional Resources

- **Django Documentation**: https://docs.djangoproject.com/
- **Django REST Framework**: https://www.django-rest-framework.org/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **DaisyUI**: https://daisyui.com/components/
- **pytest-django**: https://pytest-django.readthedocs.io/

---

## Getting Help

- **Project Documentation**: `docs/` directory
- **API Contracts**: `specs/001-multi-center-lms/contracts/`
- **Data Model**: `specs/001-multi-center-lms/data-model.md`
- **Research**: `specs/001-multi-center-lms/research.md`

---

## Next Steps

1. ✅ Complete quickstart setup
2. 📖 Read `data-model.md` to understand database structure
3. 🔍 Explore `contracts/endpoints.md` for API reference
4. 🧪 Run tests to ensure everything works
5. 💻 Start implementing user stories from `tasks.md` (coming next)

Happy coding! 🚀
