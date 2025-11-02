# Implementation Plan: Multi-Center Student Learning & Satisfaction Management System

**Branch**: `001-multi-center-lms` | **Date**: 2025-11-01 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/001-multi-center-lms/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build a multi-center student learning and satisfaction management system focused on individual/personal teaching. The system enables faculty to mark daily attendance with in/out times and topics taught, admins to manage students and faculty assignments, and master accounts to oversee multiple centers with consolidated reporting. Core features include event-sourced attendance tracking, comprehensive analytics with Gantt charts and timelines, automated insights (students absent 3+ days, extended enrollments), and student feedback surveys. The system prioritizes student learning outcomes, maintains complete audit trails, and delivers a delightful mobile-first experience with offline capabilities.

**Technical Approach**: Django web application with SQLite for development (PostgreSQL migration path for production), server-side rendered templates with Tailwind CSS and DaisyUI components for rapid UI development, Google Charts for data visualizations, and Django's built-in authentication extended with role-based access control. Event sourcing implemented via Django models with immutable audit logs. Progressive Web App (PWA) capabilities with service workers for offline attendance marking.

## Technical Context

**Language/Version**: Python 3.11+  
**Primary Dependencies**: Django 5.0+, Tailwind CSS 3.4+, DaisyUI 4.0+, Google Charts (via CDN)  
**Storage**: SQLite 3.x (development), PostgreSQL 14+ (production migration path)  
**Testing**: pytest 8.0+, pytest-django, Django TestCase, Selenium for integration tests  
**Target Platform**: Linux/Windows/macOS server, modern browsers (Chrome 90+, Firefox 88+, Safari 14+, Edge 90+)  
**Project Type**: Web application (Django monolith with server-side rendering)  
**Performance Goals**: 100 concurrent users, <2s page load on 3G (1.6 Mbps), P95 response time <2.5s  
**Constraints**: Offline-capable attendance marking, WCAG 2.2 AA compliance, mobile-first responsive design (320px+), <200KB JS bundle, <50KB CSS bundle  
**Scale/Scope**: 10+ centers, 1000+ students, 100+ faculty, 50+ admin screens, event-sourced audit trail with temporal queries

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### ✅ Principle I: Student-First Design
- **Compliance**: Attendance tracking captures learning progress daily; student reports show complete learning history; feedback surveys give students a voice
- **Validation**: Faculty can mark attendance in <60 seconds; student data is portable via export features; learning progress visibility increased by 80%

### ✅ Principle II: Evidence-Based & Event-Sourced Architecture
- **Compliance**: All attendance records stored as immutable events; Django models include `created_at`, `created_by`, `modified_at`, `modified_by` fields; soft-delete only
- **Implementation**: Custom Django model base class for event sourcing; audit log table captures all state changes; temporal queries via Django ORM filters on timestamps
- **Validation**: Event replay capability to reconstruct student learning history at any point in time

### ✅ Principle III: Explainability & Transparency
- **Compliance**: Audit trails show "Who marked what, when, and why"; attendance corrections include reason field; reports explain calculations (e.g., "Attendance rate = present days / total days")
- **Implementation**: Audit log includes `action`, `reason`, `user`, `timestamp` fields; UI displays audit history for all records

### ✅ Principle IV: Privacy & Data Protection
- **Compliance**: Django's built-in password hashing (PBKDF2); HTTPS enforced in production; minimal data collection (name, email, phone only)
- **Implementation**: Django settings: `SESSION_COOKIE_SECURE=True`, `CSRF_COOKIE_SECURE=True`, `SECURE_SSL_REDIRECT=True`; data export API for student data portability
- **Gap**: AES-256 encryption at rest requires additional library (django-encrypted-model-fields or database-level encryption)

### ✅ Principle V: Accessibility & Inclusion
- **Compliance**: Tailwind CSS with DaisyUI provides accessible components; semantic HTML5; ARIA labels; keyboard navigation
- **Implementation**: Service worker for offline mode; responsive design with Tailwind breakpoints; Google Charts accessibility features enabled
- **Validation**: Automated WCAG checks with axe-core; manual screen reader testing with NVDA/JAWS

### ✅ Principle VI: Interoperability Standards
- **Compliance**: REST API for all features (Django REST Framework); OpenAPI 3.0 documentation via drf-spectacular
- **Future**: OneRoster/LTI/QTI integration planned for Phase 2+ (not in MVP)
- **Implementation**: API versioning via URL path (`/api/v1/`); JSON responses; standard HTTP methods

### ✅ Principle VII: Reliability & Performance
- **Compliance**: Django's robust error handling; database connection pooling; query optimization with `select_related`/`prefetch_related`
- **Implementation**: Redis caching for reports; database indexes on foreign keys and frequently queried fields; pagination for large datasets
- **Validation**: Load testing with Locust (100 concurrent users); performance monitoring with Django Debug Toolbar (dev) and APM tools (prod)

### ✅ Principle VIII: Security & Least Privilege
- **Compliance**: Django's RBAC via Groups and Permissions; CSRF protection; SQL injection prevention via ORM; XSS protection via template auto-escaping
- **Implementation**: Custom permission classes: `IsMasterAccount`, `IsCenterHead`, `IsFaculty`; Django's `@login_required` and `@permission_required` decorators
- **Validation**: Security scan with Bandit; dependency vulnerability checks with Safety

### ✅ Principle IX: Open API-Driven Architecture
- **Compliance**: Django REST Framework for all CRUD operations; API-first design; same APIs used by internal views and external consumers
- **Implementation**: ViewSets for consistent API patterns; token authentication for API access; rate limiting with django-ratelimit
- **Documentation**: drf-spectacular generates OpenAPI 3.0 schema; Swagger UI for interactive API docs

### ⚠️ Principle X: Ethical AI with Human Oversight
- **Status**: No AI/ML features in MVP; future automated insights (absent 3+ days) are rule-based, not ML
- **Compliance**: When AI is added, all recommendations will be advisory with human override; explainability required

### ✅ Principle XI: Delightful User Experience
- **Compliance**: Tailwind CSS + DaisyUI for modern, clean UI; Google Charts for impressive visualizations; max 3 clicks to common tasks
- **Implementation**: Optimistic UI updates with HTMX or Alpine.js; toast notifications for feedback; loading states; mobile-first responsive design
- **Validation**: User testing with faculty and admins; page load <2s on 3G; Lighthouse performance score >90

### 🔍 Constitution Check Summary

**Passes**: 10/11 principles (AI principle N/A for MVP)  
**Gaps Identified**:
1. AES-256 encryption at rest requires additional implementation (django-encrypted-model-fields)
2. Interoperability standards (OneRoster/LTI/QTI) deferred to post-MVP

**Justification**: Both gaps are acceptable for MVP. Encryption at rest can be added via library or database-level encryption before production. Interoperability standards are future enhancements not required for core functionality.

## Project Structure

### Documentation (this feature)

```text
specs/001-multi-center-lms/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
│   ├── api-spec.yaml    # OpenAPI 3.0 specification
│   └── endpoints.md     # Endpoint documentation
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
disha_lms/                      # Django project root
├── manage.py                   # Django management script
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── pytest.ini                  # Pytest configuration
├── .env.example                # Environment variables template
├── static/                     # Static files (collected)
│   ├── css/                    # Compiled Tailwind CSS
│   ├── js/                     # JavaScript files
│   └── images/                 # Static images
├── media/                      # User-uploaded files
├── templates/                  # Global Django templates
│   ├── base.html               # Base template with Tailwind/DaisyUI
│   ├── components/             # Reusable template components
│   └── errors/                 # Error pages (404, 500)
├── staticfiles/                # Production static files (gitignored)
├── config/                     # Django project settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py             # Base settings
│   │   ├── development.py      # Development settings (SQLite)
│   │   └── production.py       # Production settings (PostgreSQL)
│   ├── urls.py                 # Root URL configuration
│   ├── wsgi.py                 # WSGI application
│   └── asgi.py                 # ASGI application (future WebSocket support)
├── apps/                       # Django applications
│   ├── accounts/               # User authentication & authorization
│   │   ├── models.py           # User, Role models
│   │   ├── views.py            # Login, logout, profile views
│   │   ├── forms.py            # Authentication forms
│   │   ├── permissions.py      # Custom permission classes
│   │   ├── urls.py             # Account URLs
│   │   ├── templates/accounts/ # Account templates
│   │   └── tests/              # Account tests
│   ├── centers/                # Center management
│   │   ├── models.py           # Center, CenterHead models
│   │   ├── views.py            # Center CRUD views
│   │   ├── forms.py            # Center forms
│   │   ├── urls.py             # Center URLs
│   │   ├── templates/centers/  # Center templates
│   │   └── tests/              # Center tests
│   ├── students/               # Student management
│   │   ├── models.py           # Student, Assignment models
│   │   ├── views.py            # Student CRUD, assignment views
│   │   ├── forms.py            # Student forms
│   │   ├── urls.py             # Student URLs
│   │   ├── templates/students/ # Student templates
│   │   └── tests/              # Student tests
│   ├── faculty/                # Faculty management
│   │   ├── models.py           # Faculty model
│   │   ├── views.py            # Faculty CRUD views
│   │   ├── forms.py            # Faculty forms
│   │   ├── urls.py             # Faculty URLs
│   │   ├── templates/faculty/  # Faculty templates
│   │   └── tests/              # Faculty tests
│   ├── subjects/               # Subject & topic management
│   │   ├── models.py           # Subject, Topic models
│   │   ├── views.py            # Subject/topic CRUD views
│   │   ├── forms.py            # Subject forms
│   │   ├── urls.py             # Subject URLs
│   │   ├── templates/subjects/ # Subject templates
│   │   └── tests/              # Subject tests
│   ├── attendance/             # Attendance tracking (core feature)
│   │   ├── models.py           # AttendanceRecord, AuditLog models
│   │   ├── views.py            # Attendance marking, history views
│   │   ├── forms.py            # Attendance forms
│   │   ├── services.py         # Business logic for attendance
│   │   ├── urls.py             # Attendance URLs
│   │   ├── templates/attendance/ # Attendance templates
│   │   └── tests/              # Attendance tests
│   ├── reports/                # Reporting & analytics
│   │   ├── views.py            # Report generation views
│   │   ├── services.py         # Report calculation logic
│   │   ├── charts.py           # Google Charts data preparation
│   │   ├── urls.py             # Report URLs
│   │   ├── templates/reports/  # Report templates with charts
│   │   └── tests/              # Report tests
│   ├── feedback/               # Student feedback & surveys
│   │   ├── models.py           # Survey, Response models
│   │   ├── views.py            # Survey CRUD, response views
│   │   ├── forms.py            # Survey forms
│   │   ├── tasks.py            # Email sending tasks (Celery)
│   │   ├── urls.py             # Feedback URLs
│   │   ├── templates/feedback/ # Feedback templates
│   │   └── tests/              # Feedback tests
│   ├── api/                    # REST API (Django REST Framework)
│   │   ├── v1/                 # API version 1
│   │   │   ├── serializers.py  # DRF serializers
│   │   │   ├── views.py        # API ViewSets
│   │   │   ├── permissions.py  # API permissions
│   │   │   └── urls.py         # API URLs
│   │   └── tests/              # API tests
│   └── core/                   # Shared utilities
│       ├── models.py           # Base models (TimeStampedModel, SoftDeleteModel)
│       ├── mixins.py           # View mixins
│       ├── utils.py            # Helper functions
│       ├── middleware.py       # Custom middleware
│       └── templatetags/       # Custom template tags
├── tests/                      # Integration & E2E tests
│   ├── integration/            # Integration tests
│   ├── e2e/                    # Selenium E2E tests
│   └── fixtures/               # Test fixtures
├── scripts/                    # Utility scripts
│   ├── setup_dev.sh            # Development setup script
│   └── migrate_to_postgres.py # SQLite to PostgreSQL migration
└── docs/                       # Additional documentation
    ├── architecture.md         # Architecture overview
    ├── deployment.md           # Deployment guide
    └── api.md                  # API documentation
```

**Structure Decision**: Django monolith with app-based organization. Each Django app represents a bounded context (accounts, centers, students, faculty, subjects, attendance, reports, feedback, api). This structure supports:
- Clear separation of concerns
- Independent testing per app
- Reusable components via core app
- API-first design with dedicated api app
- Easy migration to microservices if needed (each app can become a service)

The structure follows Django best practices with settings split by environment (development/production) to support SQLite → PostgreSQL migration path.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

No violations requiring justification. All constitution principles are met or have acceptable gaps documented in Constitution Check section.
