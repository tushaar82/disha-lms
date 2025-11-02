# Research: Multi-Center LMS Technology Stack & Best Practices

**Feature**: Multi-Center Student Learning & Satisfaction Management System  
**Branch**: 001-multi-center-lms  
**Date**: 2025-11-01

## Overview

This document consolidates research findings for technology choices, best practices, and implementation patterns for the multi-center LMS. All decisions align with the Disha LMS constitution principles.

---

## 1. Django Framework Selection

### Decision
**Django 5.0+** as the web framework

### Rationale
- **Batteries-included**: Built-in admin, ORM, authentication, CSRF protection, template engine
- **Security**: Automatic protection against SQL injection, XSS, CSRF, clickjacking
- **Mature ecosystem**: 18+ years of development, extensive third-party packages
- **Event sourcing support**: Django ORM supports audit logging patterns via signals and custom managers
- **RBAC built-in**: Django's Groups and Permissions system provides role-based access control
- **Performance**: Supports caching (Redis), database connection pooling, query optimization
- **Testing**: Excellent test framework with TestCase, fixtures, and test client
- **Documentation**: Comprehensive official documentation and large community

### Alternatives Considered
- **FastAPI**: Rejected - async not required for MVP; Django's maturity and admin interface more valuable
- **Flask**: Rejected - too minimal; would require assembling many components Django provides out-of-box
- **Ruby on Rails**: Rejected - team familiarity with Python; Django's security features superior

### Best Practices
- Use Django 5.0+ for latest security patches and async view support (future)
- Split settings by environment (`settings/base.py`, `settings/development.py`, `settings/production.py`)
- Use Django's `select_related()` and `prefetch_related()` to avoid N+1 queries
- Implement custom User model extending `AbstractBaseUser` for flexibility
- Use Django signals for event sourcing (post_save, post_delete)
- Enable Django Debug Toolbar in development for query optimization

---

## 2. Database Strategy: SQLite → PostgreSQL Migration Path

### Decision
**SQLite 3.x** for development, **PostgreSQL 14+** for production

### Rationale
- **Development simplicity**: SQLite requires zero configuration, perfect for local development
- **Production scalability**: PostgreSQL handles concurrent writes, complex queries, and large datasets
- **Django compatibility**: Django ORM abstracts database differences; most code works unchanged
- **Migration path**: Django migrations work across both databases
- **Cost-effective**: SQLite free for development; PostgreSQL free and open-source for production
- **Event sourcing**: PostgreSQL's JSONB type excellent for storing event payloads

### Implementation Strategy
1. **Development**: Use SQLite with `settings/development.py`
2. **Testing**: Use SQLite for fast test execution
3. **Production**: Switch to PostgreSQL via `settings/production.py`
4. **Migration script**: Create `scripts/migrate_to_postgres.py` using `dumpdata`/`loaddata`

### Database Differences to Handle
- **Date/Time**: Use Django's timezone-aware datetimes (`USE_TZ=True`)
- **JSON fields**: Use Django's `JSONField` (works on both SQLite 3.9+ and PostgreSQL)
- **Full-text search**: Implement basic search in SQLite, upgrade to PostgreSQL's full-text search in production
- **Concurrent writes**: SQLite locks entire database; PostgreSQL row-level locking (acceptable trade-off for dev)

### Best Practices
- Use Django's `JSONField` for flexible schema (event payloads, survey responses)
- Add database indexes on foreign keys and frequently queried fields
- Use `db_index=True` in model fields for automatic index creation
- Implement database connection pooling in production (django-db-pool or pgbouncer)
- Use PostgreSQL's `EXPLAIN ANALYZE` for query optimization in production

---

## 3. Frontend: Tailwind CSS + DaisyUI

### Decision
**Tailwind CSS 3.4+** with **DaisyUI 4.0+** components

### Rationale
- **Utility-first**: Rapid UI development without writing custom CSS
- **Mobile-first**: Built-in responsive design with breakpoints (sm, md, lg, xl)
- **Performance**: PurgeCSS removes unused styles; production bundle <50KB
- **DaisyUI components**: Pre-built accessible components (buttons, cards, modals, forms)
- **Customization**: Easy theming via Tailwind config; DaisyUI provides multiple themes
- **Accessibility**: DaisyUI components follow WCAG guidelines
- **Django integration**: Works with Django templates; no build complexity

### Implementation Strategy
1. **Install Tailwind**: Use Tailwind CLI or django-tailwind package
2. **Configure PurgeCSS**: Scan Django templates for used classes
3. **DaisyUI setup**: Add DaisyUI plugin to `tailwind.config.js`
4. **Base template**: Create `templates/base.html` with Tailwind CDN (dev) or compiled CSS (prod)
5. **Component library**: Build reusable components in `templates/components/`

### Alternatives Considered
- **Bootstrap**: Rejected - heavier bundle size; less modern design aesthetic
- **Material UI**: Rejected - requires React; not suitable for Django templates
- **Custom CSS**: Rejected - slower development; harder to maintain consistency

### Best Practices
- Use Tailwind's `@apply` directive sparingly (prefer utility classes in HTML)
- Configure dark mode support via DaisyUI themes
- Use Tailwind's `prose` class for rich text content
- Implement responsive images with Tailwind's `aspect-ratio` utilities
- Use DaisyUI's semantic color classes (primary, secondary, accent, neutral)

---

## 4. Data Visualization: Google Charts

### Decision
**Google Charts** (via CDN)

### Rationale
- **Zero installation**: Load via CDN; no npm dependencies
- **Rich chart types**: Line, bar, pie, Gantt, timeline, scatter, geo charts
- **Interactive**: Hover tooltips, zoom, pan, drill-down
- **Accessibility**: Built-in ARIA labels and keyboard navigation
- **Performance**: Client-side rendering; reduces server load
- **Free**: No licensing costs; unlimited usage
- **Documentation**: Comprehensive examples and API reference

### Chart Types for LMS
- **Gantt charts**: Student learning progress timeline (topics over time)
- **Timeline charts**: Attendance history visualization
- **Column charts**: Attendance rates by center/faculty/student
- **Pie charts**: Attendance status distribution (present/absent/leave)
- **Line charts**: Trends over time (attendance rate, completion rate)
- **Table charts**: Sortable, filterable data tables with charts

### Implementation Strategy
1. **Load library**: Include Google Charts loader in base template
2. **Data preparation**: Django views prepare JSON data for charts
3. **Chart rendering**: JavaScript in templates renders charts client-side
4. **Responsive**: Use Google Charts' responsive options
5. **Theming**: Match chart colors to Tailwind/DaisyUI theme

### Alternatives Considered
- **Chart.js**: Rejected - requires npm build; Google Charts more feature-rich
- **D3.js**: Rejected - steep learning curve; overkill for standard charts
- **Plotly**: Rejected - larger bundle size; Google Charts sufficient

### Best Practices
- Prepare chart data in Django views (Python) not templates (JavaScript)
- Use Google Charts' `DataTable` for structured data
- Implement loading states while charts render
- Add fallback text for screen readers
- Cache chart data in Redis for expensive calculations

---

## 5. Event Sourcing Implementation in Django

### Decision
**Custom Django models** with audit logging and immutable records

### Rationale
- **No external dependencies**: Use Django ORM's capabilities
- **Simplicity**: Event sourcing via append-only tables with soft-delete
- **Performance**: Django ORM optimized for relational databases
- **Flexibility**: Can migrate to dedicated event store (EventStoreDB) later if needed

### Implementation Pattern
```python
# Base model for event sourcing
class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    modified_at = models.DateTimeField(auto_now=True)
    modified_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='+')
    
    class Meta:
        abstract = True

# Soft-delete model
class SoftDeleteModel(models.Model):
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='+')
    
    class Meta:
        abstract = True

# Audit log for all changes
class AuditLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    action = models.CharField(max_length=50)  # CREATE, UPDATE, DELETE
    model_name = models.CharField(max_length=100)
    object_id = models.IntegerField()
    changes = models.JSONField()  # Before/after state
    reason = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True)
```

### Best Practices
- Use Django signals (`post_save`, `post_delete`) to automatically create audit logs
- Store full object state in `changes` JSON field for event replay
- Never hard-delete records; use `is_deleted` flag
- Add database indexes on `timestamp`, `user`, `model_name` for fast queries
- Implement custom manager to filter out deleted records by default

---

## 6. Offline Support: Progressive Web App (PWA)

### Decision
**Service Worker** with **IndexedDB** for offline attendance marking

### Rationale
- **No app store**: PWA installable from browser
- **Offline-first**: Service worker caches assets and data
- **Background sync**: Queues offline actions, syncs when online
- **Native-like**: Add to home screen, push notifications (future)
- **Cross-platform**: Works on Android, iOS (limited), desktop

### Implementation Strategy
1. **Service worker**: Cache static assets (CSS, JS, images)
2. **IndexedDB**: Store attendance records offline
3. **Background sync**: Use Background Sync API to upload when online
4. **Manifest**: Create `manifest.json` for PWA metadata
5. **HTTPS**: Required for service workers (use Let's Encrypt in production)

### Offline Capabilities
- **Mark attendance**: Store in IndexedDB, sync later
- **View student list**: Cache student data
- **View today's attendance**: Show cached records
- **Conflict resolution**: Last-write-wins or manual resolution

### Best Practices
- Use Workbox library for service worker generation
- Implement cache-first strategy for static assets
- Use network-first strategy for dynamic data
- Show offline indicator in UI
- Display sync status (pending, syncing, synced)

---

## 7. Authentication & Authorization

### Decision
**Django's built-in auth** with custom permissions

### Rationale
- **Proven security**: Django's auth system battle-tested
- **RBAC support**: Groups and Permissions built-in
- **Session management**: Secure session handling
- **Password hashing**: PBKDF2 by default (configurable to Argon2)
- **Extensible**: Custom User model, custom permissions

### Role-Based Access Control (RBAC)
```python
# Three primary roles
ROLES = {
    'MASTER_ACCOUNT': {
        'permissions': ['view_all_centers', 'create_center', 'assign_center_head', 'access_any_center']
    },
    'CENTER_HEAD': {
        'permissions': ['manage_students', 'manage_faculty', 'manage_subjects', 'view_center_reports', 'mark_backdated_attendance']
    },
    'FACULTY': {
        'permissions': ['mark_attendance', 'view_assigned_students', 'add_topics']
    }
}
```

### Implementation Strategy
1. **Custom User model**: Extend `AbstractBaseUser` with `role` field
2. **Permission classes**: Create `IsMasterAccount`, `IsCenterHead`, `IsFaculty`
3. **View decorators**: Use `@login_required` and `@permission_required`
4. **Template tags**: Check permissions in templates (`{% if perms.attendance.mark_attendance %}`)
5. **API permissions**: DRF permission classes for API endpoints

### Best Practices
- Use Django's `@login_required` decorator on all views
- Implement `@permission_required` for role-specific actions
- Use Django's `PermissionRequiredMixin` for class-based views
- Store role in User model, not separate table (simpler queries)
- Implement "switch center" functionality for Master Account via session variable

---

## 8. Testing Strategy

### Decision
**pytest** with **pytest-django** and **Selenium** for E2E tests

### Rationale
- **pytest advantages**: Fixtures, parametrize, better assertions than unittest
- **pytest-django**: Django-specific fixtures and helpers
- **Selenium**: Browser automation for E2E tests
- **Coverage**: pytest-cov for code coverage reports
- **Fast**: pytest runs tests in parallel with pytest-xdist

### Test Types
1. **Unit tests**: Test models, forms, services in isolation
2. **Integration tests**: Test views with database
3. **API tests**: Test REST API endpoints with DRF's APIClient
4. **E2E tests**: Test complete user journeys with Selenium

### Test Structure
```
tests/
├── unit/
│   ├── test_models.py
│   ├── test_forms.py
│   └── test_services.py
├── integration/
│   ├── test_attendance_views.py
│   ├── test_reports_views.py
│   └── test_api.py
└── e2e/
    ├── test_faculty_attendance_flow.py
    ├── test_admin_student_management.py
    └── test_master_account_center_access.py
```

### Best Practices
- Use pytest fixtures for test data setup
- Use `@pytest.mark.django_db` for tests requiring database
- Use factory_boy for creating test objects
- Mock external services (email, SMS) in tests
- Aim for >80% code coverage
- Run tests in CI/CD pipeline before deployment

---

## 9. Performance Optimization

### Decision
**Redis caching** + **Database optimization** + **CDN for static assets**

### Rationale
- **Redis**: Fast in-memory cache for reports and session data
- **Database indexes**: Speed up queries on foreign keys and filters
- **Query optimization**: Use `select_related` and `prefetch_related`
- **CDN**: Serve static assets (CSS, JS, images) from CDN in production
- **Lazy loading**: Load images and charts on-demand

### Caching Strategy
- **View caching**: Cache entire views for anonymous users
- **Template fragment caching**: Cache expensive template sections
- **Query caching**: Cache database query results for reports
- **Session caching**: Store sessions in Redis instead of database

### Database Optimization
- Add indexes on: `created_at`, `user_id`, `center_id`, `student_id`, `faculty_id`
- Use `select_related()` for foreign keys (one-to-one, many-to-one)
- Use `prefetch_related()` for reverse foreign keys (one-to-many, many-to-many)
- Use `only()` and `defer()` to load specific fields
- Use database connection pooling (pgbouncer or django-db-pool)

### Best Practices
- Profile with Django Debug Toolbar to identify slow queries
- Use `django-silk` for request profiling in production
- Implement pagination for large datasets (Django's `Paginator`)
- Use lazy loading for images (`loading="lazy"` attribute)
- Compress responses with GZip middleware

---

## 10. Security Best Practices

### Decision
**Defense-in-depth** with multiple security layers

### Security Measures
1. **HTTPS**: Enforce SSL/TLS in production
2. **CSRF protection**: Django's CSRF middleware enabled
3. **XSS protection**: Template auto-escaping enabled
4. **SQL injection**: Use Django ORM (never raw SQL with user input)
5. **Clickjacking**: X-Frame-Options header set to DENY
6. **Content Security Policy**: Restrict resource loading
7. **Rate limiting**: django-ratelimit for API endpoints
8. **Password policy**: Minimum 8 characters, complexity requirements
9. **Session security**: Secure cookies, HTTP-only, SameSite=Strict
10. **Dependency scanning**: Use Safety to check for vulnerable packages

### Django Security Settings
```python
# Production settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
```

### Best Practices
- Run `python manage.py check --deploy` before production deployment
- Use environment variables for secrets (never commit to git)
- Implement rate limiting on login endpoints (prevent brute force)
- Log all authentication attempts and authorization failures
- Use Django's `django-axes` for automatic account lockout after failed logins
- Regularly update dependencies with `pip-audit` or `safety`

---

## 11. Deployment & DevOps

### Decision
**Docker** + **Gunicorn** + **Nginx** + **PostgreSQL**

### Rationale
- **Docker**: Consistent environment across dev/staging/prod
- **Gunicorn**: Production-ready WSGI server
- **Nginx**: Reverse proxy, static file serving, SSL termination
- **PostgreSQL**: Production database
- **Docker Compose**: Orchestrate multi-container setup

### Deployment Architecture
```
[Internet] → [Nginx] → [Gunicorn] → [Django App]
                ↓           ↓
            [Static]    [PostgreSQL]
            [Files]     [Redis]
```

### Best Practices
- Use multi-stage Docker builds to reduce image size
- Run Django with Gunicorn (4 workers = 2 * CPU cores + 1)
- Serve static files with Nginx (not Django)
- Use Docker volumes for persistent data (database, media files)
- Implement health checks in Docker Compose
- Use environment-specific `.env` files
- Implement CI/CD pipeline (GitHub Actions, GitLab CI, or Jenkins)

---

## 12. Email & Background Tasks

### Decision
**Django's email backend** + **Celery** for async tasks

### Rationale
- **Django email**: Built-in support for SMTP, SendGrid, AWS SES
- **Celery**: Distributed task queue for async processing
- **Redis**: Message broker for Celery
- **Celery Beat**: Scheduled tasks (daily reports, reminders)

### Use Cases
- Send feedback survey emails (async)
- Generate large reports (background task)
- Send daily/weekly attendance summaries
- Process bulk attendance imports
- Send reminders for incomplete surveys

### Best Practices
- Use Celery for tasks taking >2 seconds
- Implement retry logic for failed tasks
- Monitor Celery with Flower (web-based monitoring tool)
- Use Celery Beat for scheduled tasks
- Store task results in Redis or database

---

## Summary of Technology Decisions

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend Framework** | Django 5.0+ | Batteries-included, secure, mature |
| **Database (Dev)** | SQLite 3.x | Zero config, fast for development |
| **Database (Prod)** | PostgreSQL 14+ | Scalable, concurrent writes, JSONB |
| **Frontend CSS** | Tailwind CSS 3.4+ | Utility-first, mobile-first, small bundle |
| **UI Components** | DaisyUI 4.0+ | Accessible, pre-built components |
| **Charts** | Google Charts | Free, rich chart types, accessible |
| **API** | Django REST Framework | Standard, well-documented, DRF |
| **Authentication** | Django Auth + RBAC | Built-in, secure, extensible |
| **Testing** | pytest + Selenium | Modern, powerful, E2E capable |
| **Caching** | Redis | Fast, in-memory, session storage |
| **Task Queue** | Celery | Async tasks, scheduled jobs |
| **Web Server** | Gunicorn + Nginx | Production-ready, performant |
| **Containerization** | Docker | Consistent environments |
| **Offline Support** | Service Worker + IndexedDB | PWA, offline-first |

---

## Next Steps

1. **Phase 1**: Create `data-model.md` with Django models
2. **Phase 1**: Generate API contracts in `contracts/`
3. **Phase 1**: Create `quickstart.md` for development setup
4. **Phase 2**: Generate `tasks.md` with implementation tasks

All technology choices align with the Disha LMS constitution principles and support the 5 prioritized user stories (P1-P5).
