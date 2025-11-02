# API Endpoints: Multi-Center LMS

**Feature**: Multi-Center Student Learning & Satisfaction Management System  
**Branch**: 001-multi-center-lms  
**API Version**: v1  
**Base URL**: `/api/v1/`

## Authentication
- **Method**: Token-based (Django REST Framework)
- **Header**: `Authorization: Token <token>`

## Endpoint Summary

### 1. Authentication
- `POST /api/v1/auth/login/` - Login and get token
- `POST /api/v1/auth/logout/` - Logout
- `GET /api/v1/auth/me/` - Get current user profile

### 2. Centers
- `GET /api/v1/centers/` - List centers
- `POST /api/v1/centers/` - Create center (Master Account)
- `GET /api/v1/centers/{id}/` - Get center details
- `PATCH /api/v1/centers/{id}/` - Update center
- `DELETE /api/v1/centers/{id}/` - Delete center
- `POST /api/v1/centers/{id}/access/` - Master Account access center dashboard

### 3. Students
- `GET /api/v1/students/` - List students
- `POST /api/v1/students/` - Create student (Center Head)
- `GET /api/v1/students/{id}/` - Get student details
- `PATCH /api/v1/students/{id}/` - Update student
- `DELETE /api/v1/students/{id}/` - Delete student

### 4. Faculty
- `GET /api/v1/faculty/` - List faculty
- `POST /api/v1/faculty/` - Create faculty profile
- `GET /api/v1/faculty/{id}/` - Get faculty details
- `PATCH /api/v1/faculty/{id}/` - Update faculty

### 5. Subjects & Topics
- `GET /api/v1/subjects/` - List subjects
- `POST /api/v1/subjects/` - Create subject
- `GET /api/v1/subjects/{id}/topics/` - List topics
- `POST /api/v1/subjects/{id}/topics/` - Add topic

### 6. Assignments
- `GET /api/v1/assignments/` - List assignments
- `POST /api/v1/assignments/` - Create assignment
- `PATCH /api/v1/assignments/{id}/` - Update assignment (transfer student)

### 7. Attendance
- `GET /api/v1/attendance/` - List attendance records
- `POST /api/v1/attendance/` - Mark attendance
- `POST /api/v1/attendance/bulk/` - Bulk mark attendance
- `GET /api/v1/attendance/today/` - Get today's attendance

### 8. Reports
- `GET /api/v1/reports/center/` - Overall center report
- `GET /api/v1/reports/student/{id}/` - Student report
- `GET /api/v1/reports/faculty/{id}/` - Faculty report
- `GET /api/v1/reports/insights/` - Automated insights

### 9. Feedback
- `GET /api/v1/feedback/surveys/` - List surveys
- `POST /api/v1/feedback/surveys/` - Create survey
- `POST /api/v1/feedback/surveys/{id}/send/` - Send survey emails
- `GET /api/v1/feedback/surveys/{id}/responses/` - Get responses
- `POST /api/v1/feedback/submit/{token}/` - Submit response (public)

### 10. Audit Logs
- `GET /api/v1/audit-logs/` - Get audit logs for compliance

## Response Format
```json
{
  "success": true,
  "data": {...},
  "message": "Success message"
}
```

## Rate Limiting
- Auth endpoints: 5 req/min
- Read endpoints: 100 req/min
- Write endpoints: 30 req/min

## Pagination
- Default: 20 items per page
- Max: 100 items per page
- Parameters: `page`, `page_size`

See OpenAPI spec (`api-spec.yaml`) for detailed schemas and examples.
