# Disha LMS - Complete Setup Guide

This guide will help you set up the Disha LMS project from scratch.

---

## ✅ Prerequisites

- Python 3.11+ installed
- Node.js 18+ and npm installed
- Virtual environment activated (you should see `(venv)` in your terminal)

---

## 🚀 Step-by-Step Setup

### Step 1: Install Python Dependencies

```bash
pip install -r requirements.txt
```

**What this does**: Installs Django, DRF, PostgreSQL drivers, and all backend dependencies.

---

### Step 2: Install Node.js Dependencies

```bash
npm install
```

**What this does**: Installs Tailwind CSS, DaisyUI, and frontend build tools.

✅ **Status**: COMPLETE (119 packages installed)

---

### Step 3: Build Tailwind CSS

```bash
npm run build:css
```

**What this does**: Compiles `static/css/input.css` → `static/css/output.css` with Tailwind and DaisyUI styles.

**Alternative** (for development with auto-rebuild):
```bash
npm run watch:css
```

---

### Step 4: Create Database Migrations

Run the migrations in the correct order to avoid dependency errors:

```bash
# Option A: Use the setup script
./setup_migrations.sh

# Option B: Run manually
python manage.py makemigrations accounts
python manage.py makemigrations core
python manage.py makemigrations api
python manage.py migrate
```

**What this does**: 
- Creates migration files for the database schema
- Applies migrations to create tables in SQLite database

---

### Step 5: Create a Superuser

```bash
python manage.py createsuperuser
```

**Example**:
```
Email: admin@example.com
First name: Admin
Last name: User
Role: master
Password: (your secure password)
```

**Important**: Choose `master` as the role to get Master Account permissions.

---

### Step 6: Run the Development Server

```bash
python manage.py runserver
```

The server will start at: http://127.0.0.1:8000/

---

## 🌐 Access Points

Once the server is running, you can access:

### Web Interface
- **Login Page**: http://127.0.0.1:8000/accounts/login/
- **Admin Panel**: http://127.0.0.1:8000/admin/
- **Profile**: http://127.0.0.1:8000/accounts/profile/

### API Documentation
- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **ReDoc**: http://127.0.0.1:8000/api/redoc/
- **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/

### API Endpoints
- **Login**: POST http://127.0.0.1:8000/api/v1/auth/login/
- **Logout**: POST http://127.0.0.1:8000/api/v1/auth/logout/
- **Current User**: GET http://127.0.0.1:8000/api/v1/auth/me/

---

## 🧪 Testing the Setup

### 1. Test Web Login

1. Go to http://127.0.0.1:8000/accounts/login/
2. Enter your superuser credentials
3. You should be redirected based on your role:
   - **Master Account** → Centers list
   - **Center Head** → Dashboard
   - **Faculty** → Mark Attendance

### 2. Test API Login

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "yourpassword"
  }'
```

**Expected Response**:
```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "first_name": "Admin",
    "last_name": "User",
    "role": "master",
    "role_display": "Master Account"
  }
}
```

### 3. Test Authenticated API Request

```bash
# Use the token from login response
curl -X GET http://127.0.0.1:8000/api/v1/auth/me/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

---

## 🛠️ Development Workflow

### Watch Tailwind CSS Changes (Recommended for Development)

In a separate terminal:
```bash
npm run watch:css
```

This will automatically rebuild CSS when you modify `static/css/input.css` or templates.

### Create New Migrations (After Model Changes)

```bash
python manage.py makemigrations
python manage.py migrate
```

### Run Tests

```bash
pytest
```

### Code Quality Checks

```bash
# Format code
black apps/
isort apps/

# Lint
flake8 apps/

# Security scan
bandit -r apps/
```

---

## 📁 Project Structure

```
disha-lms/
├── apps/
│   ├── core/           # Base models (TimeStampedModel, AuditLog)
│   ├── accounts/       # User model, authentication
│   └── api/            # REST API endpoints
├── config/
│   ├── settings/       # Django settings (base, development, production)
│   ├── urls.py         # URL routing
│   ├── wsgi.py         # WSGI application
│   └── asgi.py         # ASGI application
├── templates/          # HTML templates
│   ├── base.html       # Base template
│   ├── components/     # Reusable components
│   └── accounts/       # Account templates
├── static/
│   ├── css/            # Tailwind CSS
│   └── js/             # JavaScript
├── manage.py           # Django management script
├── requirements.txt    # Python dependencies
├── package.json        # Node.js dependencies
└── README.md           # Project documentation
```

---

## 🔧 Troubleshooting

### Issue: "Dependency on app with no migrations: accounts"

**Solution**: Run migrations in order:
```bash
./setup_migrations.sh
```

### Issue: "npm error could not determine executable to run"

**Solution**: Install npm packages first:
```bash
npm install
```

### Issue: "Couldn't import Django"

**Solution**: 
1. Activate virtual environment: `source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`

### Issue: Static files not loading

**Solution**: 
1. Build CSS: `npm run build:css`
2. Collect static files: `python manage.py collectstatic`

---

## 📊 What's Implemented (Phase 2 Complete)

✅ **Core App**
- TimeStampedModel (automatic audit tracking)
- SoftDeleteModel (soft-delete with history)
- AuditLog (immutable event store)
- 8 view mixins for RBAC and audit logging
- 12 utility functions
- Custom middleware and template tags

✅ **Accounts App**
- Custom User model with email authentication
- 3 roles: Master Account, Center Head, Faculty
- 5 permission classes for RBAC
- Login/logout/profile views
- Beautiful DaisyUI-styled templates

✅ **API App**
- Token-based authentication
- Login/logout/me endpoints
- OpenAPI 3.0+ documentation
- Rate limiting (100/hour anon, 1000/hour auth)

---

## 🚀 Next Steps

After setup is complete, you can:

1. **Explore the Admin Panel**: http://127.0.0.1:8000/admin/
2. **Check API Documentation**: http://127.0.0.1:8000/api/docs/
3. **Start Phase 3 Development**: Faculty Attendance Tracking (29 tasks)

---

## 📞 Need Help?

- Check `PHASE2_COMPLETE.md` for detailed implementation notes
- Review `README.md` for project overview
- See `specs/001-multi-center-lms/` for feature specifications

---

**Setup Status**: Phase 1 ✅ | Phase 2 ✅ | Ready for Phase 3! 🎉
