# Troubleshooting Guide - Disha LMS

Common issues and their solutions.

---

## ✅ FIXED: Redis Connection Error

### Issue
```
ConnectionError: Error 111 connecting to localhost:6379. Connection refused.
```

### Cause
Django was configured to use Redis for caching and sessions, but Redis wasn't running.

### Solution
**For Development**: Redis is now optional! The development settings have been updated to use:
- **In-memory cache** instead of Redis cache
- **Database-backed sessions** instead of Redis sessions

**No action needed** - just restart your Django server:
```bash
python manage.py runserver
```

### For Production
If you want to use Redis in production (recommended for performance):

1. **Install Redis**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install redis-server
   
   # macOS
   brew install redis
   ```

2. **Start Redis**:
   ```bash
   # Ubuntu/Debian
   sudo systemctl start redis
   
   # macOS
   brew services start redis
   ```

3. **Verify Redis is running**:
   ```bash
   redis-cli ping
   # Should return: PONG
   ```

---

## Migration Dependency Error

### Issue
```
ValueError: Dependency on app with no migrations: accounts
```

### Solution
Create migrations in the correct order:

```bash
./setup_migrations.sh
```

Or manually:
```bash
python manage.py makemigrations accounts
python manage.py makemigrations core
python manage.py makemigrations api
python manage.py migrate
```

**Why?** The `core` app's `AuditLog` model has a ForeignKey to `User`, so `accounts` migrations must be created first.

---

## Tailwind CSS Build Error

### Issue
```
npm error could not determine executable to run
```

### Solution
Install npm packages first:
```bash
npm install
npm run build:css
```

---

## Django Import Error

### Issue
```
ModuleNotFoundError: No module named 'django'
```

### Solution
1. Activate virtual environment:
   ```bash
   source venv/bin/activate  # Linux/macOS
   venv\Scripts\activate     # Windows
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Static Files Not Loading

### Issue
CSS/JS files return 404 errors.

### Solution
1. **Build Tailwind CSS**:
   ```bash
   npm run build:css
   ```

2. **Collect static files** (for production):
   ```bash
   python manage.py collectstatic
   ```

3. **Check DEBUG setting**:
   - In development, `DEBUG=True` serves static files automatically
   - In production, use a web server (Nginx) to serve static files

---

## Login Redirects to Wrong Page

### Issue
After login, redirected to unexpected page or 404.

### Cause
The redirect logic is based on user role, but the target URLs don't exist yet.

### Solution
**Temporary**: Comment out role-based redirects in `apps/accounts/views.py`:

```python
# In LoginView.post()
# Redirect to a page that exists
return redirect('/admin/')  # or '/' for home
```

**Permanent**: Implement the missing views for each role (Phase 3+).

---

## CSRF Token Missing

### Issue
```
CSRF verification failed. Request aborted.
```

### Solution
1. **In templates**: Ensure `{% csrf_token %}` is inside `<form>` tags
2. **In API**: Use token authentication instead of session auth
3. **For testing**: Temporarily disable CSRF in development settings (not recommended)

---

## Database Locked Error (SQLite)

### Issue
```
OperationalError: database is locked
```

### Cause
SQLite doesn't handle concurrent writes well.

### Solution
**For Development**: 
- Only one process should write to the database
- Close any other Django shells or processes

**For Production**: 
- Use PostgreSQL instead of SQLite
- Update `DATABASE_URL` in `.env`

---

## Port Already in Use

### Issue
```
Error: That port is already in use.
```

### Solution
1. **Find the process**:
   ```bash
   lsof -i :8000  # Linux/macOS
   ```

2. **Kill the process**:
   ```bash
   kill -9 <PID>
   ```

3. **Or use a different port**:
   ```bash
   python manage.py runserver 8001
   ```

---

## Permission Denied Errors

### Issue
```
PermissionError: [Errno 13] Permission denied
```

### Solution
1. **For scripts**:
   ```bash
   chmod +x setup_migrations.sh
   ```

2. **For directories**:
   ```bash
   sudo chown -R $USER:$USER .
   ```

---

## Module Import Errors

### Issue
```
ModuleNotFoundError: No module named 'apps.core'
```

### Solution
1. **Check INSTALLED_APPS** in settings:
   ```python
   INSTALLED_APPS = [
       'apps.core',
       'apps.accounts',
       'apps.api',
   ]
   ```

2. **Verify app structure**:
   ```
   apps/
   ├── __init__.py
   ├── core/
   │   ├── __init__.py
   │   └── apps.py
   ```

3. **Restart Django server** after adding new apps

---

## Environment Variables Not Loading

### Issue
Settings using `config('VARIABLE')` return default values.

### Solution
1. **Create .env file**:
   ```bash
   cp .env.example .env
   ```

2. **Edit .env** with your values:
   ```
   DEBUG=True
   SECRET_KEY=your-secret-key
   ```

3. **Restart Django server**

---

## API Authentication Fails

### Issue
```
{"detail": "Authentication credentials were not provided."}
```

### Solution
Include the token in the Authorization header:

```bash
curl -H "Authorization: Token YOUR_TOKEN_HERE" \
  http://127.0.0.1:8000/api/v1/auth/me/
```

Get your token from:
```bash
python manage.py drf_create_token <email>
```

Or login via API:
```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@example.com", "password": "yourpassword"}'
```

---

## Need More Help?

1. Check the **SETUP_GUIDE.md** for detailed setup instructions
2. Review **PHASE2_COMPLETE.md** for implementation details
3. Check Django logs for specific error messages
4. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

---

**Last Updated**: 2025-11-01  
**Phase**: 2 (Foundational Infrastructure Complete)
