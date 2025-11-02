# Disha LMS - Multi-Center Student Learning & Satisfaction Management System

A comprehensive Learning Management System designed for individual/personal teaching across multiple learning centers.

## Features

- **Faculty Attendance Tracking**: Mark student attendance with in/out times and topics taught
- **Multi-Center Management**: Manage multiple learning centers from a single master account
- **Student Management**: Track student progress, assignments, and learning outcomes
- **Comprehensive Reporting**: Gantt charts, timelines, and automated insights
- **Feedback System**: Collect and analyze student satisfaction data
- **Event-Sourced Architecture**: Complete audit trail for all actions
- **Offline Support**: Mark attendance offline with automatic sync
- **Mobile-First Design**: Responsive interface with WCAG 2.2 AA compliance

## Technology Stack

- **Backend**: Django 5.0+ with Python 3.11+
- **Database**: SQLite (development) → PostgreSQL 14+ (production)
- **Frontend**: Tailwind CSS 3.4+ with DaisyUI 4.0+
- **Charts**: Google Charts
- **API**: Django REST Framework with OpenAPI 3.0+ documentation
- **Testing**: pytest with pytest-django
- **Caching**: Redis
- **Task Queue**: Celery

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Redis (optional - only needed for production caching and Celery)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd disha-lms
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

4. **Install Node.js dependencies**
   ```bash
   npm install
   ```

5. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Run migrations**
   ```bash
   python manage.py migrate
   ```

7. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

8. **Compile Tailwind CSS**
   ```bash
   npm run build:css
   ```

9. **Run development server**
   ```bash
   python manage.py runserver
   ```

10. **Access the application**
    - Web: http://127.0.0.1:8000/
    - Admin: http://127.0.0.1:8000/admin/
    - API Docs: http://127.0.0.1:8000/api/docs/

## Development

### Run tests
```bash
pytest
```

### Watch Tailwind CSS changes
```bash
npm run watch:css
```

### Code formatting
```bash
black apps/
isort apps/
```

### Run linter
```bash
flake8 apps/
```

### Security checks
```bash
bandit -r apps/
safety check
```

## Project Structure

```
disha_lms/
├── apps/                   # Django applications
│   ├── accounts/          # Authentication & authorization
│   ├── centers/           # Center management
│   ├── students/          # Student management
│   ├── faculty/           # Faculty management
│   ├── subjects/          # Subject & topic management
│   ├── attendance/        # Attendance tracking
│   ├── reports/           # Reporting & analytics
│   ├── feedback/          # Student feedback
│   ├── api/               # REST API
│   └── core/              # Shared utilities
├── config/                # Django settings
├── templates/             # HTML templates
├── static/                # Static files (CSS, JS, images)
├── tests/                 # Tests
└── specs/                 # Feature specifications
```

## Documentation

- [Feature Specification](specs/001-multi-center-lms/spec.md)
- [Implementation Plan](specs/001-multi-center-lms/plan.md)
- [Data Model](specs/001-multi-center-lms/data-model.md)
- [API Documentation](specs/001-multi-center-lms/contracts/endpoints.md)
- [Quickstart Guide](specs/001-multi-center-lms/quickstart.md)

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, email support@dishalms.com or open an issue in the repository.
