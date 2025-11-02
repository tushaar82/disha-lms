# Complete REST API Endpoints - Disha LMS

Full list of all REST API endpoints available in Disha LMS for Next.js frontend development.

## 🔐 Authentication

### Auth Endpoints
```
POST   /api/v1/auth/login/          - Login and get token
POST   /api/v1/auth/logout/         - Logout and delete token
GET    /api/v1/auth/me/             - Get current user profile
```

---

## 👥 User Management

### Students
```
GET    /api/v1/students/                    - List all students
POST   /api/v1/students/                    - Create student
GET    /api/v1/students/{id}/               - Get student details
PUT    /api/v1/students/{id}/               - Update student
PATCH  /api/v1/students/{id}/               - Partial update
DELETE /api/v1/students/{id}/               - Delete student
GET    /api/v1/students/{id}/assignments/   - Get student assignments
GET    /api/v1/students/{id}/attendance/    - Get student attendance
```

### Faculty
```
GET    /api/v1/faculty/                     - List all faculty
POST   /api/v1/faculty/                     - Create faculty
GET    /api/v1/faculty/{id}/                - Get faculty details
PUT    /api/v1/faculty/{id}/                - Update faculty
PATCH  /api/v1/faculty/{id}/                - Partial update
DELETE /api/v1/faculty/{id}/                - Delete faculty
```

### Subjects
```
GET    /api/v1/subjects/                    - List all subjects
POST   /api/v1/subjects/                    - Create subject
GET    /api/v1/subjects/{id}/               - Get subject details
PUT    /api/v1/subjects/{id}/               - Update subject
PATCH  /api/v1/subjects/{id}/               - Partial update
DELETE /api/v1/subjects/{id}/               - Delete subject
```

### Assignments
```
GET    /api/v1/assignments/                 - List all assignments
POST   /api/v1/assignments/                 - Create assignment
GET    /api/v1/assignments/{id}/            - Get assignment details
PUT    /api/v1/assignments/{id}/            - Update assignment
PATCH  /api/v1/assignments/{id}/            - Partial update
DELETE /api/v1/assignments/{id}/            - Delete assignment
```

---

## 🏢 Center Management

### Centers
```
GET    /api/v1/centers/                     - List all centers
POST   /api/v1/centers/                     - Create center
GET    /api/v1/centers/{id}/                - Get center details
PUT    /api/v1/centers/{id}/                - Update center
PATCH  /api/v1/centers/{id}/                - Partial update
DELETE /api/v1/centers/{id}/                - Delete center
```

### Center Heads
```
GET    /api/v1/center-heads/                - List all center heads
POST   /api/v1/center-heads/                - Create center head
GET    /api/v1/center-heads/{id}/           - Get center head details
PUT    /api/v1/center-heads/{id}/           - Update center head
PATCH  /api/v1/center-heads/{id}/           - Partial update
DELETE /api/v1/center-heads/{id}/           - Delete center head
```

---

## 📅 Attendance

### Attendance Records
```
GET    /api/v1/attendance/                  - List attendance records
POST   /api/v1/attendance/                  - Mark attendance
GET    /api/v1/attendance/today/            - Get today's attendance
POST   /api/v1/attendance/bulk/             - Bulk attendance marking
```

---

## 📊 Reports & Analytics

### Center Reports
```
GET    /api/v1/reports/center/{center_id}/  - Get center report
  Query params: ?days=30
```

### Student Reports
```
GET    /api/v1/reports/student/{student_id}/ - Get student report
  Query params: ?days=30
```

### Faculty Reports
```
GET    /api/v1/reports/faculty/{faculty_id}/ - Get faculty report
  Query params: ?days=30
```

### Insights
```
GET    /api/v1/reports/insights/             - Get all insights (master)
GET    /api/v1/reports/insights/{center_id}/ - Get center insights
  Query params: 
    ?days_threshold=7
    ?months_threshold=6
    ?completion_threshold=80
```

---

## 📋 Feedback & Surveys

### Survey Management
```
GET    /api/v1/surveys/                     - List all surveys
  Query params: ?status=published&search=term
POST   /api/v1/surveys/                     - Create survey
GET    /api/v1/surveys/{id}/                - Get survey details
PUT    /api/v1/surveys/{id}/                - Update survey
PATCH  /api/v1/surveys/{id}/                - Partial update
DELETE /api/v1/surveys/{id}/                - Delete survey (soft)
POST   /api/v1/surveys/{id}/publish/        - Publish survey
POST   /api/v1/surveys/{id}/unpublish/      - Unpublish survey
GET    /api/v1/surveys/{id}/students/       - Get students list for survey
```

### Send Surveys
```
POST   /api/v1/surveys/{id}/send/           - Send survey to students
  Body: {"student_ids": [1, 2, 3]}
```

### Survey Submission (Public - No Auth)
```
GET    /api/v1/surveys/submit/{token}/      - Get survey by token
POST   /api/v1/surveys/submit/{token}/      - Submit survey response
  Body: {
    "answers": {"q1": "answer"},
    "satisfaction_score": 5
  }
```

### Survey Analytics
```
GET    /api/v1/surveys/{id}/responses/      - Get survey responses
  Query params: ?limit=50&include_pending=false
```

### Feedback Analytics
```
GET    /api/v1/feedback/trends/             - Get satisfaction trends
  Query params: ?center_id=1&months=6

GET    /api/v1/feedback/faculty-breakdown/  - Get faculty breakdown
  Query params: ?center_id=1
```

---

## 📈 Complete Endpoint Count

| Category | Endpoints | Auth Required |
|----------|-----------|---------------|
| Authentication | 3 | Partial |
| Students | 8 | Yes |
| Faculty | 6 | Yes |
| Subjects | 6 | Yes |
| Assignments | 6 | Yes |
| Centers | 6 | Yes |
| Center Heads | 6 | Yes |
| Attendance | 4 | Yes |
| Reports | 5 | Yes |
| Surveys | 12 | Partial |
| Feedback Analytics | 2 | Yes |
| **TOTAL** | **64** | - |

---

## 🎯 Role-Based Access

### Master Account
- Full access to all endpoints
- Can view/manage all centers
- Can access all reports and analytics

### Center Head
- Access to their center's data only
- Can manage students, faculty, subjects
- Can create and send surveys
- Can view center-specific reports

### Faculty
- Can mark attendance
- Can view student reports
- Limited access to analytics

### Public (No Auth)
- Survey submission via token
- Get survey details via token

---

## 📦 Response Format

All API responses follow this format:

### Success Response
```json
{
  "id": 1,
  "field1": "value1",
  "field2": "value2",
  ...
}
```

### List Response (Paginated)
```json
{
  "count": 100,
  "next": "http://api.example.com/endpoint/?page=2",
  "previous": null,
  "results": [...]
}
```

### Error Response
```json
{
  "error": "Error message",
  "details": {...}
}
```

---

## 🔑 Authentication Header

All authenticated endpoints require:
```
Authorization: Token <your-token-here>
```

Get token from login endpoint:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

Response:
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "center_head"
  }
}
```

---

## 🌐 CORS Configuration

For Next.js frontend, ensure CORS is configured in Django settings:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

---

## 📚 Interactive Documentation

- **Swagger UI:** http://localhost:8000/api/docs/
- **ReDoc:** http://localhost:8000/api/redoc/

---

## 🚀 Next.js Integration Example

```typescript
// lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const api = {
  // Auth
  login: (email: string, password: string) =>
    fetch(`${API_BASE}/auth/login/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password }),
    }).then(res => res.json()),

  // Surveys
  getSurveys: (token: string, params?: URLSearchParams) =>
    fetch(`${API_BASE}/surveys/?${params}`, {
      headers: { 'Authorization': `Token ${token}` },
    }).then(res => res.json()),

  createSurvey: (token: string, data: any) =>
    fetch(`${API_BASE}/surveys/`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    }).then(res => res.json()),

  sendSurvey: (token: string, surveyId: number, studentIds: number[]) =>
    fetch(`${API_BASE}/surveys/${surveyId}/send/`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ student_ids: studentIds }),
    }).then(res => res.json()),

  // Public survey submission
  getSurveyByToken: (token: string) =>
    fetch(`${API_BASE}/surveys/submit/${token}/`)
      .then(res => res.json()),

  submitSurvey: (token: string, answers: any, score: number) =>
    fetch(`${API_BASE}/surveys/submit/${token}/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        answers,
        satisfaction_score: score,
      }),
    }).then(res => res.json()),

  // Analytics
  getSurveyResponses: (token: string, surveyId: number) =>
    fetch(`${API_BASE}/surveys/${surveyId}/responses/`, {
      headers: { 'Authorization': `Token ${token}` },
    }).then(res => res.json()),

  getSatisfactionTrends: (token: string, months: number = 6) =>
    fetch(`${API_BASE}/feedback/trends/?months=${months}`, {
      headers: { 'Authorization': `Token ${token}` },
    }).then(res => res.json()),
};
```

---

## 📝 Notes for Frontend Development

1. **Token Storage:** Store auth token in httpOnly cookie or secure localStorage
2. **Error Handling:** Implement global error handler for 401/403/500 errors
3. **Loading States:** Show loading indicators during API calls
4. **Pagination:** Handle paginated responses properly
5. **Caching:** Use React Query or SWR for data caching
6. **Type Safety:** Generate TypeScript types from API schema
7. **Environment Variables:** Use `.env.local` for API URL
8. **CORS:** Ensure CORS is properly configured on backend

---

## 🔗 Related Documentation

- [Feedback API Documentation](./API_FEEDBACK_DOCUMENTATION.md)
- [Reports API Documentation](./API_REPORTS_USAGE.md)
- [Setup Guide](../SETUP_GUIDE.md)
- [Quick Start](../QUICK_START.md)

---

**Last Updated:** 2024-11-02
**API Version:** v1
**Django Version:** 5.0+
**DRF Version:** 3.14+
