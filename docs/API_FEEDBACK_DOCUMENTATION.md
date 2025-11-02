# Feedback & Satisfaction API Documentation

Complete REST API documentation for the Feedback & Satisfaction system in Disha LMS.

## Base URL
```
http://localhost:8000/api/v1/
```

## Authentication
All endpoints (except public survey submission) require authentication via Token:
```
Authorization: Token <your-token-here>
```

---

## 📋 Survey Management

### 1. List Surveys
Get all surveys (filtered by role).

**Endpoint:** `GET /surveys/`

**Query Parameters:**
- `status` (optional): Filter by status (`active`, `published`, `draft`)
- `search` (optional): Search in title and description
- `page` (optional): Page number for pagination

**Response:**
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Student Satisfaction Survey Q1 2024",
      "description": "Quarterly satisfaction survey",
      "center": 1,
      "center_name": "Mumbai Center",
      "valid_from": "2024-01-01",
      "valid_until": "2024-03-31",
      "is_active": true,
      "is_published": true,
      "response_count": 45,
      "completed_count": 38,
      "avg_satisfaction": 4.2,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ]
}
```

**Permissions:** Center Head, Master Account

---

### 2. Create Survey
Create a new survey.

**Endpoint:** `POST /surveys/`

**Request Body:**
```json
{
  "title": "Student Satisfaction Survey Q2 2024",
  "description": "Quarterly satisfaction survey for Q2",
  "questions": [
    {
      "id": "q1",
      "text": "How satisfied are you with the teaching quality?",
      "type": "rating",
      "required": true
    },
    {
      "id": "q2",
      "text": "What can we improve?",
      "type": "textarea",
      "required": false
    }
  ],
  "valid_from": "2024-04-01",
  "valid_until": "2024-06-30",
  "is_active": true,
  "is_published": false
}
```

**Response:** `201 Created`
```json
{
  "id": 2,
  "title": "Student Satisfaction Survey Q2 2024",
  "description": "Quarterly satisfaction survey for Q2",
  "questions": [...],
  "center": 1,
  "center_name": "Mumbai Center",
  "valid_from": "2024-04-01",
  "valid_until": "2024-06-30",
  "is_active": true,
  "is_published": false,
  "is_valid": true,
  "response_count": 0,
  "created_at": "2024-04-01T00:00:00Z",
  "updated_at": "2024-04-01T00:00:00Z"
}
```

**Permissions:** Center Head, Master Account

---

### 3. Get Survey Details
Get detailed information about a specific survey.

**Endpoint:** `GET /surveys/{id}/`

**Response:** `200 OK`
```json
{
  "id": 1,
  "title": "Student Satisfaction Survey Q1 2024",
  "description": "Quarterly satisfaction survey",
  "questions": [
    {
      "id": "q1",
      "text": "How satisfied are you with the teaching quality?",
      "type": "rating",
      "required": true,
      "options": null
    }
  ],
  "center": 1,
  "center_name": "Mumbai Center",
  "valid_from": "2024-01-01",
  "valid_until": "2024-03-31",
  "is_active": true,
  "is_published": true,
  "is_valid": false,
  "response_count": 45,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-15T00:00:00Z"
}
```

**Permissions:** Center Head, Master Account

---

### 4. Update Survey
Update an existing survey.

**Endpoint:** `PUT /surveys/{id}/` or `PATCH /surveys/{id}/`

**Request Body:** (same as create, all fields for PUT, partial for PATCH)

**Response:** `200 OK`

**Permissions:** Center Head, Master Account

---

### 5. Delete Survey
Soft delete a survey.

**Endpoint:** `DELETE /surveys/{id}/`

**Response:** `204 No Content`

**Permissions:** Center Head, Master Account

---

### 6. Publish Survey
Publish a draft survey.

**Endpoint:** `POST /surveys/{id}/publish/`

**Response:** `200 OK`
```json
{
  "id": 2,
  "is_published": true,
  ...
}
```

**Permissions:** Center Head, Master Account

---

### 7. Unpublish Survey
Unpublish a survey.

**Endpoint:** `POST /surveys/{id}/unpublish/`

**Response:** `200 OK`

**Permissions:** Center Head, Master Account

---

### 8. Get Students for Survey
Get list of students to send survey to.

**Endpoint:** `GET /surveys/{id}/students/`

**Response:** `200 OK`
```json
{
  "students": [
    {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "email": "john.doe@example.com",
      "phone": "+91-9876543210",
      "center": 1,
      "status": "active"
    }
  ],
  "existing_response_ids": [1, 5, 10]
}
```

**Permissions:** Center Head, Master Account

---

## 📧 Send Survey

### 9. Send Survey Emails
Send survey emails to selected students.

**Endpoint:** `POST /surveys/{id}/send/`

**Request Body:**
```json
{
  "student_ids": [1, 2, 3, 4, 5]
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Survey emails are being sent to 5 student(s).",
  "survey_id": 1,
  "student_count": 5
}
```

**Permissions:** Center Head, Master Account

---

## 📝 Survey Submission (Public)

### 10. Get Survey by Token
Get survey details using unique token (for students).

**Endpoint:** `GET /surveys/submit/{token}/`

**Authentication:** None required

**Response:** `200 OK`
```json
{
  "survey": {
    "id": 1,
    "title": "Student Satisfaction Survey Q1 2024",
    "description": "Quarterly satisfaction survey",
    "questions": [...]
  },
  "response_id": 10,
  "student_name": "John Doe",
  "student_email": "john.doe@example.com",
  "is_completed": false,
  "email_sent_at": "2024-01-15T10:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Survey expired or already completed

---

### 11. Submit Survey Response
Submit survey answers (for students).

**Endpoint:** `POST /surveys/submit/{token}/`

**Authentication:** None required

**Request Body:**
```json
{
  "answers": {
    "q1": "5",
    "q2": "The teaching quality is excellent. I would like more practical sessions."
  },
  "satisfaction_score": 5
}
```

**Response:** `200 OK`
```json
{
  "status": "success",
  "message": "Survey submitted successfully.",
  "response_id": 10,
  "submitted_at": "2024-01-20T15:30:00Z",
  "satisfaction_score": 5
}
```

**Error Responses:**
- `400 Bad Request` - Invalid data, expired survey, or already completed

---

## 📊 Survey Analytics

### 12. Get Survey Responses
Get responses and analytics for a survey.

**Endpoint:** `GET /surveys/{id}/responses/`

**Query Parameters:**
- `limit` (optional, default: 50): Number of responses to return
- `include_pending` (optional, default: false): Include pending responses

**Response:** `200 OK`
```json
{
  "survey_id": 1,
  "survey_title": "Student Satisfaction Survey Q1 2024",
  "total_responses": 50,
  "completed_responses": 45,
  "pending_responses": 5,
  "completion_rate": 90.0,
  "avg_satisfaction": 4.2,
  "rating_distribution": {
    "1": 2,
    "2": 3,
    "3": 8,
    "4": 15,
    "5": 17
  },
  "responses": [
    {
      "id": 10,
      "survey_id": 1,
      "survey_title": "Student Satisfaction Survey Q1 2024",
      "student_id": 1,
      "student_name": "John Doe",
      "student": {...},
      "token": "abc123...",
      "answers": {...},
      "satisfaction_score": 5,
      "submitted_at": "2024-01-20T15:30:00Z",
      "is_completed": true,
      "email_sent_at": "2024-01-15T10:00:00Z",
      "email_opened_at": "2024-01-15T14:00:00Z",
      "created_at": "2024-01-15T10:00:00Z"
    }
  ]
}
```

**Permissions:** Center Head, Master Account

---

### 13. Get Satisfaction Trends
Get satisfaction trends over time.

**Endpoint:** `GET /feedback/trends/`

**Query Parameters:**
- `center_id` (optional for master): Filter by center
- `months` (optional, default: 6): Number of months

**Response:** `200 OK`
```json
{
  "center_id": 1,
  "center_name": "Mumbai Center",
  "months": 6,
  "overall_avg": 4.15,
  "total_responses": 250,
  "monthly_trends": [
    {
      "month": "Jan 2024",
      "avg_satisfaction": 4.2,
      "response_count": 45
    },
    {
      "month": "Feb 2024",
      "avg_satisfaction": 4.1,
      "response_count": 42
    }
  ]
}
```

**Permissions:** Center Head, Master Account

---

### 14. Get Faculty Satisfaction Breakdown
Get satisfaction breakdown by faculty.

**Endpoint:** `GET /feedback/faculty-breakdown/`

**Query Parameters:**
- `center_id` (required for master): Filter by center

**Response:** `200 OK`
```json
{
  "center_id": 1,
  "center_name": "Mumbai Center",
  "faculty_count": 5,
  "breakdown": [
    {
      "faculty_id": 1,
      "faculty_name": "Dr. Smith",
      "response_count": 30,
      "avg_satisfaction": 4.5
    },
    {
      "faculty_id": 2,
      "faculty_name": "Prof. Johnson",
      "response_count": 28,
      "avg_satisfaction": 4.3
    }
  ]
}
```

**Permissions:** Center Head, Master Account

---

## 🔐 Access Control Summary

| Endpoint | Master Account | Center Head | Faculty | Public |
|----------|---------------|-------------|---------|--------|
| List Surveys | ✅ All | ✅ Center only | ❌ | ❌ |
| Create Survey | ✅ | ✅ | ❌ | ❌ |
| Update Survey | ✅ | ✅ Own center | ❌ | ❌ |
| Delete Survey | ✅ | ✅ Own center | ❌ | ❌ |
| Publish/Unpublish | ✅ | ✅ Own center | ❌ | ❌ |
| Get Students | ✅ | ✅ Own center | ❌ | ❌ |
| Send Survey | ✅ | ✅ Own center | ❌ | ❌ |
| Get Survey (Token) | ❌ | ❌ | ❌ | ✅ |
| Submit Survey | ❌ | ❌ | ❌ | ✅ |
| Get Responses | ✅ All | ✅ Center only | ❌ | ❌ |
| Get Trends | ✅ All centers | ✅ Center only | ❌ | ❌ |
| Faculty Breakdown | ✅ All centers | ✅ Center only | ❌ | ❌ |

---

## 📖 Usage Examples

### Next.js/React Example

```typescript
// API Client Setup
const API_BASE_URL = 'http://localhost:8000/api/v1';

const apiClient = {
  get: async (endpoint: string, token: string) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json',
      },
    });
    return response.json();
  },
  
  post: async (endpoint: string, data: any, token: string) => {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Authorization': `Token ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    return response.json();
  },
};

// List Surveys
const surveys = await apiClient.get('/surveys/?status=published', token);

// Create Survey
const newSurvey = await apiClient.post('/surveys/', {
  title: 'New Survey',
  description: 'Description',
  questions: [...],
  valid_from: '2024-01-01',
  valid_until: '2024-12-31',
  is_active: true,
  is_published: false,
}, token);

// Send Survey
const result = await apiClient.post(`/surveys/${surveyId}/send/`, {
  student_ids: [1, 2, 3],
}, token);

// Get Survey by Token (Public - No Auth)
const surveyData = await fetch(`${API_BASE_URL}/surveys/submit/${token}/`)
  .then(res => res.json());

// Submit Survey (Public - No Auth)
const submitResult = await fetch(`${API_BASE_URL}/surveys/submit/${token}/`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    answers: { q1: '5', q2: 'Great!' },
    satisfaction_score: 5,
  }),
}).then(res => res.json());

// Get Analytics
const analytics = await apiClient.get(`/surveys/${surveyId}/responses/`, token);
const trends = await apiClient.get('/feedback/trends/?months=12', token);
const facultyBreakdown = await apiClient.get('/feedback/faculty-breakdown/', token);
```

---

## 🌐 Swagger/OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI:** `http://localhost:8000/api/docs/`
- **ReDoc:** `http://localhost:8000/api/redoc/`

---

## 🚀 Quick Start for Frontend Development

1. **Authentication:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/auth/login/ \
     -H "Content-Type: application/json" \
     -d '{"email": "admin@example.com", "password": "password"}'
   ```

2. **List Surveys:**
   ```bash
   curl http://localhost:8000/api/v1/surveys/ \
     -H "Authorization: Token YOUR_TOKEN"
   ```

3. **Create Survey:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/surveys/ \
     -H "Authorization: Token YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d @survey.json
   ```

4. **Send Survey:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/surveys/1/send/ \
     -H "Authorization: Token YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"student_ids": [1,2,3]}'
   ```

---

## 📋 Complete API Endpoint List

### Survey Management (Authenticated)
- `GET /api/v1/surveys/` - List surveys
- `POST /api/v1/surveys/` - Create survey
- `GET /api/v1/surveys/{id}/` - Get survey details
- `PUT /api/v1/surveys/{id}/` - Update survey (full)
- `PATCH /api/v1/surveys/{id}/` - Update survey (partial)
- `DELETE /api/v1/surveys/{id}/` - Delete survey
- `POST /api/v1/surveys/{id}/publish/` - Publish survey
- `POST /api/v1/surveys/{id}/unpublish/` - Unpublish survey
- `GET /api/v1/surveys/{id}/students/` - Get students list
- `POST /api/v1/surveys/{id}/send/` - Send survey emails

### Survey Submission (Public)
- `GET /api/v1/surveys/submit/{token}/` - Get survey by token
- `POST /api/v1/surveys/submit/{token}/` - Submit survey

### Analytics (Authenticated)
- `GET /api/v1/surveys/{id}/responses/` - Get survey responses
- `GET /api/v1/feedback/trends/` - Get satisfaction trends
- `GET /api/v1/feedback/faculty-breakdown/` - Get faculty breakdown

---

## 💡 Best Practices

1. **Always use HTTPS in production**
2. **Store tokens securely** (localStorage or httpOnly cookies)
3. **Handle errors gracefully** (401, 403, 404, 500)
4. **Implement retry logic** for failed requests
5. **Use pagination** for large datasets
6. **Cache responses** where appropriate
7. **Validate data** on the frontend before sending
8. **Show loading states** during API calls
9. **Implement proper error messages** for users
10. **Use TypeScript** for type safety

---

## 🐛 Common Error Codes

- `400 Bad Request` - Invalid data or validation error
- `401 Unauthorized` - Missing or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

---

## 📞 Support

For API support, contact: support@dishalms.com
