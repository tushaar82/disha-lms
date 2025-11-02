# Disha LMS API Endpoints

**Base URL**: `http://127.0.0.1:8000/api/v1/`  
**Authentication**: Token-based (use `Authorization: Token <your-token>` header)  
**Documentation**: http://127.0.0.1:8000/api/docs/

---

## Authentication Endpoints

### Login
```
POST /api/v1/auth/login/
```
**Body**:
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```
**Response**:
```json
{
  "token": "abc123...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "center_head",
    ...
  }
}
```

### Logout
```
POST /api/v1/auth/logout/
```
**Headers**: `Authorization: Token <token>`

### Get Current User
```
GET /api/v1/auth/me/
PATCH /api/v1/auth/me/
```

---

## Student Management API (NEW! ✨)

### List Students
```
GET /api/v1/students/
```
**Query Parameters**:
- `page`: Page number
- `page_size`: Items per page

**Response**:
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "full_name": "Rahul Sharma",
      "email": "rahul@example.com",
      "center_name": "Mumbai Learning Center",
      "status": "active",
      ...
    }
  ]
}
```

### Create Student
```
POST /api/v1/students/
```
**Body**:
```json
{
  "first_name": "Rahul",
  "last_name": "Sharma",
  "email": "rahul@example.com",
  "phone": "+91-9876543210",
  "center": 1,
  "enrollment_date": "2024-01-01",
  "status": "active"
}
```

### Get Student Detail
```
GET /api/v1/students/{id}/
```

### Update Student
```
PUT /api/v1/students/{id}/
PATCH /api/v1/students/{id}/
```

### Delete Student
```
DELETE /api/v1/students/{id}/
```

### Get Students Ready for Transfer
```
GET /api/v1/students/ready_for_transfer/
```

---

## Faculty Management API (NEW! ✨)

### List Faculty
```
GET /api/v1/faculty/
```

### Create Faculty
```
POST /api/v1/faculty/
```
**Body**:
```json
{
  "user": 2,
  "center": 1,
  "employee_id": "FAC001",
  "joining_date": "2024-01-01",
  "specialization": "Mathematics",
  "qualification": "M.Sc.",
  "experience_years": 5,
  "is_active": true
}
```

### Get Faculty Detail
```
GET /api/v1/faculty/{id}/
```

### Update Faculty
```
PUT /api/v1/faculty/{id}/
PATCH /api/v1/faculty/{id}/
```

### Delete Faculty
```
DELETE /api/v1/faculty/{id}/
```

---

## Subject Management API (NEW! ✨)

### List Subjects
```
GET /api/v1/subjects/
```

### Create Subject
```
POST /api/v1/subjects/
```
**Body**:
```json
{
  "name": "Mathematics",
  "code": "MATH101",
  "description": "Basic Mathematics",
  "center": 1,
  "is_active": true
}
```

### Get Subject Detail
```
GET /api/v1/subjects/{id}/
```

### Update Subject
```
PUT /api/v1/subjects/{id}/
PATCH /api/v1/subjects/{id}/
```

### Delete Subject
```
DELETE /api/v1/subjects/{id}/
```

### Get Topics for Subject
```
GET /api/v1/subjects/{id}/topics/
```

---

## Assignment Management API (NEW! ✨)

### List Assignments
```
GET /api/v1/assignments/
```

### Create Assignment
```
POST /api/v1/assignments/
```
**Body**:
```json
{
  "student": 1,
  "subject": 1,
  "faculty": 1,
  "start_date": "2024-01-01",
  "is_active": true
}
```

### Get Assignment Detail
```
GET /api/v1/assignments/{id}/
```

### Update Assignment
```
PUT /api/v1/assignments/{id}/
PATCH /api/v1/assignments/{id}/
```

### Delete Assignment
```
DELETE /api/v1/assignments/{id}/
```

### Get Assignments by Student
```
GET /api/v1/assignments/by_student/?student_id=1
```

### Get Assignments by Faculty
```
GET /api/v1/assignments/by_faculty/?faculty_id=1
```

---

## Attendance API (Existing)

### List Attendance
```
GET /api/v1/attendance/
```

### Create Attendance
```
POST /api/v1/attendance/
```

### Get Today's Attendance
```
GET /api/v1/attendance/today/
```

### Bulk Create Attendance
```
POST /api/v1/attendance/bulk/
```

---

## API Features

### Role-Based Access Control ✅
- **Center Heads**: See only their center's data
- **Faculty**: See only their assigned students/subjects
- **Master Accounts**: See all data across centers

### Pagination ✅
All list endpoints support pagination:
```
GET /api/v1/students/?page=2&page_size=20
```

### Filtering ✅
Filter by various parameters:
```
GET /api/v1/students/?status=active
GET /api/v1/attendance/?date=2024-01-01
```

### Nested Data ✅
Responses include related data:
- Student responses include `center_name`, `status_display`
- Faculty responses include `user_name`, `center_name`
- Subject responses include `center_name`, `topic_count`
- Assignment responses include `student_name`, `subject_name`, `faculty_name`

---

## Testing the API

### Using cURL
```bash
# Login
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email":"priya@gmail.com","password":"your_password"}'

# Get students (with token)
curl -X GET http://127.0.0.1:8000/api/v1/students/ \
  -H "Authorization: Token YOUR_TOKEN_HERE"

# Create student
curl -X POST http://127.0.0.1:8000/api/v1/students/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Test",
    "last_name": "Student",
    "email": "test@example.com",
    "center": 1,
    "enrollment_date": "2024-01-01",
    "status": "active"
  }'
```

### Using Python
```python
import requests

# Login
response = requests.post(
    'http://127.0.0.1:8000/api/v1/auth/login/',
    json={'email': 'priya@gmail.com', 'password': 'your_password'}
)
token = response.json()['token']

# Get students
headers = {'Authorization': f'Token {token}'}
response = requests.get(
    'http://127.0.0.1:8000/api/v1/students/',
    headers=headers
)
students = response.json()
```

### Using Swagger UI
Visit: http://127.0.0.1:8000/api/docs/

1. Click "Authorize" button
2. Enter: `Token YOUR_TOKEN_HERE`
3. Try out any endpoint interactively

---

## API Endpoints Summary

### Total Endpoints: 40+

**Authentication** (3):
- POST /auth/login/
- POST /auth/logout/
- GET/PATCH /auth/me/

**Students** (6):
- GET/POST /students/
- GET/PUT/PATCH/DELETE /students/{id}/
- GET /students/ready_for_transfer/

**Faculty** (5):
- GET/POST /faculty/
- GET/PUT/PATCH/DELETE /faculty/{id}/

**Subjects** (6):
- GET/POST /subjects/
- GET/PUT/PATCH/DELETE /subjects/{id}/
- GET /subjects/{id}/topics/

**Assignments** (7):
- GET/POST /assignments/
- GET/PUT/PATCH/DELETE /assignments/{id}/
- GET /assignments/by_student/
- GET /assignments/by_faculty/

**Attendance** (3):
- GET/POST /attendance/
- GET /attendance/today/
- POST /attendance/bulk/

---

## Next Steps

1. **Test the API**: Use Swagger UI or cURL
2. **Build Mobile App**: Use these endpoints
3. **Create Integrations**: Connect with other systems
4. **Add More Endpoints**: Extend as needed

**API Documentation**: Always available at http://127.0.0.1:8000/api/docs/ 🚀
