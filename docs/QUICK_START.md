# Quick Start - Disha LMS

Get up and running in 5 minutes!

---

## ✅ What's Already Done

- ✅ Django project structure created
- ✅ Python dependencies defined (requirements.txt)
- ✅ Node.js dependencies installed (npm install - DONE)
- ✅ Core app with event sourcing (TimeStampedModel, AuditLog)
- ✅ Accounts app with custom User model and RBAC
- ✅ API app with token authentication
- ✅ Beautiful UI with Tailwind CSS + DaisyUI
- ✅ Redis made optional for development

---

## 🚀 Steps to Run (First Time)

### 1. Build Tailwind CSS
```bash
npm run build:css
```

### 2. Create Database & Migrations
```bash
./setup_migrations.sh
```

Or manually:
```bash
python manage.py makemigrations accounts
python manage.py makemigrations core
python manage.py migrate
```

### 3. Create Superuser
```bash
python manage.py createsuperuser
```

Example:
- Email: `admin@example.com`
- First name: `Admin`
- Last name: `User`
- Role: `master` (important!)
- Password: (your secure password)

### 4. Run the Server
```bash
python manage.py runserver
```

---

## 🌐 Access the Application

Open your browser and visit:

### Main Pages
- **Home**: http://127.0.0.1:8000/
- **Login**: http://127.0.0.1:8000/accounts/login/
- **Profile**: http://127.0.0.1:8000/accounts/profile/
- **Admin Panel**: http://127.0.0.1:8000/admin/

### API Documentation
- **Swagger UI**: http://127.0.0.1:8000/api/docs/
- **ReDoc**: http://127.0.0.1:8000/api/redoc/
- **OpenAPI Schema**: http://127.0.0.1:8000/api/schema/

---

## 🧪 Test the Setup

### 1. Test Web Login
1. Go to http://127.0.0.1:8000/accounts/login/
2. Enter your superuser credentials
3. You should be redirected to your profile page
4. Click "Admin Panel" to access Django admin

### 2. Test API Login
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "admin@example.com",
    "password": "yourpassword"
  }'
```

Expected response:
```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "email": "admin@example.com",
    "role": "master"
  }
}
```

### 3. Test Authenticated API
```bash
curl -X GET http://127.0.0.1:8000/api/v1/auth/me/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"
```

---

## 🎯 What You Can Do Now

✅ **Login** - Web and API authentication working  
✅ **Profile Management** - Update your profile  
✅ **Admin Panel** - Manage users, view audit logs  
✅ **API Documentation** - Explore API endpoints  
✅ **User Management** - Create users with different roles  

---

## 📋 User Roles

The system has 3 roles:

1. **Master Account** (`master`)
   - Can manage multiple centers
   - Full system access
   - Cross-center reporting

2. **Center Head** (`center_head`)
   - Manages one center
   - Can create students, faculty, subjects
   - Center-level reporting

3. **Faculty** (`faculty`)
   - Marks student attendance
   - Tracks topics taught
   - Views attendance history

---

## 🛠️ Development Workflow

### Watch CSS Changes (Recommended)
In a separate terminal:
```bash
npm run watch:css
```

### Create New Users
Via admin panel: http://127.0.0.1:8000/admin/users/user/

Or via Django shell:
```bash
python manage.py shell
```

```python
from apps.accounts.models import User

# Create a center head
user = User.objects.create_user(
    email='centerhead@example.com',
    password='password123',
    first_name='Center',
    last_name='Head',
    role='center_head'
)

# Create a faculty member
user = User.objects.create_user(
    email='faculty@example.com',
    password='password123',
    first_name='Faculty',
    last_name='Member',
    role='faculty'
)
```

---

## 🐛 Common Issues

### Redis Connection Error
**Fixed!** Redis is now optional for development. Just restart the server.

### NoReverseMatch Error
**Fixed!** Login now redirects to profile page instead of non-existent dashboards.

### Static Files Not Loading
Run: `npm run build:css`

### Migration Errors
Run: `./setup_migrations.sh`

For more issues, see **TROUBLESHOOTING.md**

---

## 📚 Documentation

- **SETUP_GUIDE.md** - Detailed setup instructions
- **PHASE2_COMPLETE.md** - What was implemented in Phase 2
- **TROUBLESHOOTING.md** - Common issues and solutions
- **README.md** - Project overview

---

## 🚀 Next Steps

**Phase 2 is COMPLETE!** ✅

You can now:
1. **Explore the application** - Login, check admin panel, test API
2. **Create test users** - Different roles to see RBAC in action
3. **Start Phase 3** - Implement Faculty Attendance Tracking (29 tasks)

---

## 💡 Quick Tips

- **Admin Panel**: Best place to manage users and view audit logs
- **API Docs**: Interactive Swagger UI to test API endpoints
- **Profile Page**: Update your name and phone number
- **Audit Logs**: Every action is logged (check admin panel)
- **Soft Delete**: Records are never hard-deleted (audit trail preserved)

---

**Status**: Phase 1 ✅ | Phase 2 ✅ | Ready for Phase 3! 🎉

**Happy Coding!** 🚀
