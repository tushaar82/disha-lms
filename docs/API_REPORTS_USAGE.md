# Report API Endpoints - Usage Guide

This guide demonstrates how to use the Report API endpoints (T150-T154) for programmatic access to reporting and analytics data.

---

## Authentication

All report endpoints require authentication. Use token-based authentication:

```bash
# Get your token by logging in
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"email": "your@email.com", "password": "yourpassword"}'

# Response includes token
{
  "token": "abc123...",
  "user": {...}
}

# Use token in subsequent requests
curl -H "Authorization: Token abc123..." \
     http://localhost:8000/api/v1/reports/...
```

---

## Endpoints Overview

| Endpoint | Method | Description | Access |
|----------|--------|-------------|--------|
| `/api/v1/reports/center/<id>/` | GET | Center report with metrics | Master, Center Head |
| `/api/v1/reports/student/<id>/` | GET | Student report with velocities | Master, Center Head, Faculty |
| `/api/v1/reports/faculty/<id>/` | GET | Faculty teaching statistics | Master, Center Head |
| `/api/v1/reports/insights/` | GET | All insights (all centers) | Master |
| `/api/v1/reports/insights/<id>/` | GET | Center-specific insights | Master, Center Head |

---

## 1. Center Report API

**Endpoint**: `GET /api/v1/reports/center/<center_id>/`

**Description**: Get comprehensive metrics for a specific center including students, faculty, subjects, attendance, and insights.

**Access**: Master Account (all centers), Center Head (own center only)

### Example Request

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v1/reports/center/1/
```

### Example Response

```json
{
  "center_id": 1,
  "center_name": "Main Center",
  "center_code": "MC001",
  "center_city": "Mumbai",
  "center_state": "Maharashtra",
  "students": {
    "total": 50,
    "active": 45,
    "inactive": 3,
    "completed": 2
  },
  "faculty": {
    "total": 10,
    "active": 9
  },
  "subjects": {
    "total": 15,
    "active": 14
  },
  "attendance": {
    "total": 1200,
    "this_week": 85,
    "this_month": 340,
    "attendance_rate": 75.5,
    "avg_duration": 45.2
  },
  "insights": {
    "at_risk_count": 5,
    "extended_count": 3,
    "nearing_completion_count": 8
  }
}
```

### Use Cases

- **Dashboard Integration**: Display center metrics in external dashboards
- **Monitoring**: Track center performance over time
- **Alerts**: Trigger alerts when metrics fall below thresholds
- **Reporting**: Generate custom reports combining multiple centers

---

## 2. Student Report API

**Endpoint**: `GET /api/v1/reports/student/<student_id>/?days=30`

**Description**: Get detailed student report including attendance velocity, learning velocity, subject progress, and recent attendance records.

**Access**: Master Account, Center Head (own center), Faculty (all students)

**Query Parameters**:
- `days` (optional, default: 30) - Number of days for velocity calculations

### Example Request

```bash
# Default 30-day period
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v1/reports/student/1/

# Custom 60-day period
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v1/reports/student/1/?days=60
```

### Example Response

```json
{
  "student": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "full_name": "John Doe",
    "email": "john@example.com",
    "phone": "+91-9876543210",
    "center": 1,
    "center_name": "Main Center",
    "enrollment_number": "STU001",
    "enrollment_date": "2025-01-15",
    "status": "active"
  },
  "attendance_velocity": {
    "sessions_per_week": 3.5,
    "total_sessions": 15,
    "avg_session_duration": 45.2,
    "total_learning_hours": 11.3
  },
  "learning_velocity": {
    "topics_per_session": 2.8,
    "total_topics_covered": 42,
    "minutes_per_topic": 16.1,
    "total_sessions": 15
  },
  "subject_completion": [
    ["Subject", "Topics Covered", "Total Topics", "Progress %"],
    ["Mathematics", 15, 20, 75],
    ["Physics", 10, 15, 67],
    ["Chemistry", 8, 12, 67]
  ],
  "recent_attendance": [
    {
      "id": 1,
      "date": "2025-11-01",
      "in_time": "10:00:00",
      "out_time": "11:00:00",
      "duration_minutes": 60,
      "student_name": "John Doe",
      "subject_name": "Mathematics",
      "marked_by_name": "Jane Smith",
      "topics_covered": [
        {
          "id": 1,
          "name": "Algebra Basics",
          "subject_name": "Mathematics"
        }
      ],
      "notes": "Good progress on quadratic equations"
    }
  ]
}
```

### Use Cases

- **Student Progress Tracking**: Monitor learning velocity and attendance patterns
- **Parent Portal**: Display student progress to parents
- **Mobile App**: Show student dashboard in mobile applications
- **Intervention Triggers**: Identify students needing additional support
- **Performance Analytics**: Analyze learning patterns across cohorts

---

## 3. Faculty Report API

**Endpoint**: `GET /api/v1/reports/faculty/<faculty_id>/`

**Description**: Get teaching statistics for a faculty member including total sessions, students taught, teaching hours, and top students.

**Access**: Master Account, Center Head (own center only)

### Example Request

```bash
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v1/reports/faculty/1/
```

### Example Response

```json
{
  "faculty": {
    "id": 1,
    "user_name": "Jane Smith",
    "user_email": "jane@example.com",
    "center": 1,
    "center_name": "Main Center",
    "employee_id": "EMP001",
    "joining_date": "2024-01-01",
    "specialization": "Mathematics",
    "qualification": "M.Sc. Mathematics",
    "experience_years": 5,
    "is_active": true
  },
  "stats": {
    "total_sessions": 120,
    "total_students": 25,
    "total_subjects": 3,
    "avg_session_duration": 48.5,
    "total_teaching_hours": 97.0
  },
  "top_students": [
    {
      "id": 1,
      "full_name": "John Doe",
      "session_count": 15,
      "email": "john@example.com",
      "status": "active"
    },
    {
      "id": 2,
      "full_name": "Alice Johnson",
      "session_count": 12,
      "email": "alice@example.com",
      "status": "active"
    }
  ],
  "recent_sessions": [
    {
      "id": 1,
      "date": "2025-11-01",
      "in_time": "10:00:00",
      "out_time": "11:00:00",
      "duration_minutes": 60,
      "student_name": "John Doe",
      "subject_name": "Mathematics",
      "topics_covered": [
        {
          "id": 1,
          "name": "Algebra Basics"
        }
      ]
    }
  ]
}
```

### Use Cases

- **Performance Reviews**: Evaluate faculty teaching load and effectiveness
- **Workload Management**: Balance teaching assignments across faculty
- **Recognition**: Identify top-performing faculty members
- **Capacity Planning**: Determine if additional faculty needed
- **Quality Assurance**: Monitor teaching hours and student engagement

---

## 4. Insights API

**Endpoint**: 
- `GET /api/v1/reports/insights/` (all centers - master only)
- `GET /api/v1/reports/insights/<center_id>/` (specific center)

**Description**: Get actionable insights including at-risk students, extended enrollments, and students nearing completion.

**Access**: Master Account (all centers or specific), Center Head (own center only)

**Query Parameters**:
- `days_threshold` (optional, default: 7) - Days without attendance to be considered at-risk
- `months_threshold` (optional, default: 6) - Months enrolled to be considered extended
- `completion_threshold` (optional, default: 80) - Completion percentage to be considered nearing completion

### Example Requests

```bash
# All centers (master account only)
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v1/reports/insights/

# Specific center with default thresholds
curl -H "Authorization: Token YOUR_TOKEN" \
     http://localhost:8000/api/v1/reports/insights/1/

# Custom thresholds
curl -H "Authorization: Token YOUR_TOKEN" \
     "http://localhost:8000/api/v1/reports/insights/1/?days_threshold=10&months_threshold=8&completion_threshold=90"
```

### Example Response

```json
{
  "at_risk_count": 5,
  "extended_count": 3,
  "nearing_completion_count": 8,
  "at_risk_students": [
    {
      "id": 1,
      "full_name": "John Doe",
      "email": "john@example.com",
      "center_name": "Main Center",
      "enrollment_date": "2025-01-15",
      "status": "active",
      "last_attendance_date": "2025-10-20",
      "days_since_last_attendance": 12
    }
  ],
  "extended_students": [
    {
      "id": 2,
      "full_name": "Jane Smith",
      "email": "jane@example.com",
      "center_name": "Main Center",
      "enrollment_date": "2024-04-01",
      "status": "active",
      "months_enrolled": 7
    }
  ],
  "nearing_completion": [
    {
      "id": 3,
      "full_name": "Bob Johnson",
      "email": "bob@example.com",
      "center_name": "Main Center",
      "enrollment_date": "2024-08-01",
      "status": "active",
      "completion_percentage": 85
    }
  ]
}
```

### Use Cases

- **Early Intervention**: Identify and reach out to at-risk students
- **Completion Planning**: Prepare for students nearing completion (transfer/certification)
- **Enrollment Management**: Review extended students for progress or status change
- **Automated Alerts**: Trigger notifications when students meet criteria
- **Dashboard Widgets**: Display key insights on admin dashboards

---

## Error Responses

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "error": "You do not have permission to view this center."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

---

## Python Client Example

```python
import requests

class DishaLMSClient:
    def __init__(self, base_url, token):
        self.base_url = base_url
        self.headers = {'Authorization': f'Token {token}'}
    
    def get_center_report(self, center_id):
        """Get center report."""
        url = f"{self.base_url}/api/v1/reports/center/{center_id}/"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_student_report(self, student_id, days=30):
        """Get student report."""
        url = f"{self.base_url}/api/v1/reports/student/{student_id}/"
        params = {'days': days}
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_faculty_report(self, faculty_id):
        """Get faculty report."""
        url = f"{self.base_url}/api/v1/reports/faculty/{faculty_id}/"
        response = requests.get(url, headers=self.headers)
        response.raise_for_status()
        return response.json()
    
    def get_insights(self, center_id=None, days_threshold=7, 
                     months_threshold=6, completion_threshold=80):
        """Get insights."""
        if center_id:
            url = f"{self.base_url}/api/v1/reports/insights/{center_id}/"
        else:
            url = f"{self.base_url}/api/v1/reports/insights/"
        
        params = {
            'days_threshold': days_threshold,
            'months_threshold': months_threshold,
            'completion_threshold': completion_threshold
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()

# Usage
client = DishaLMSClient('http://localhost:8000', 'your_token_here')

# Get center report
center_data = client.get_center_report(1)
print(f"Center: {center_data['center_name']}")
print(f"Active Students: {center_data['students']['active']}")

# Get student report
student_data = client.get_student_report(1, days=60)
print(f"Student: {student_data['student']['full_name']}")
print(f"Sessions/Week: {student_data['attendance_velocity']['sessions_per_week']}")

# Get insights
insights = client.get_insights(center_id=1, days_threshold=10)
print(f"At-risk students: {insights['at_risk_count']}")
```

---

## JavaScript/TypeScript Client Example

```typescript
class DishaLMSClient {
  private baseUrl: string;
  private token: string;

  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  private async request(endpoint: string, params?: Record<string, any>) {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    if (params) {
      Object.keys(params).forEach(key => 
        url.searchParams.append(key, params[key])
      );
    }

    const response = await fetch(url.toString(), {
      headers: {
        'Authorization': `Token ${this.token}`,
        'Content-Type': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return response.json();
  }

  async getCenterReport(centerId: number) {
    return this.request(`/api/v1/reports/center/${centerId}/`);
  }

  async getStudentReport(studentId: number, days: number = 30) {
    return this.request(`/api/v1/reports/student/${studentId}/`, { days });
  }

  async getFacultyReport(facultyId: number) {
    return this.request(`/api/v1/reports/faculty/${facultyId}/`);
  }

  async getInsights(
    centerId?: number,
    daysThreshold: number = 7,
    monthsThreshold: number = 6,
    completionThreshold: number = 80
  ) {
    const endpoint = centerId 
      ? `/api/v1/reports/insights/${centerId}/`
      : '/api/v1/reports/insights/';
    
    return this.request(endpoint, {
      days_threshold: daysThreshold,
      months_threshold: monthsThreshold,
      completion_threshold: completionThreshold
    });
  }
}

// Usage
const client = new DishaLMSClient('http://localhost:8000', 'your_token_here');

// Get center report
const centerData = await client.getCenterReport(1);
console.log(`Center: ${centerData.center_name}`);
console.log(`Active Students: ${centerData.students.active}`);

// Get student report
const studentData = await client.getStudentReport(1, 60);
console.log(`Student: ${studentData.student.full_name}`);
console.log(`Sessions/Week: ${studentData.attendance_velocity.sessions_per_week}`);
```

---

## Integration Examples

### 1. Dashboard Widget

```javascript
// Fetch and display center metrics
async function updateCenterDashboard(centerId) {
  const data = await client.getCenterReport(centerId);
  
  document.getElementById('total-students').textContent = data.students.total;
  document.getElementById('active-students').textContent = data.students.active;
  document.getElementById('attendance-rate').textContent = 
    `${data.attendance.attendance_rate.toFixed(1)}%`;
  
  // Update chart
  updateChart(data.attendance);
}
```

### 2. Student Progress Monitor

```python
# Check student progress and send alerts
def monitor_student_progress(student_id):
    data = client.get_student_report(student_id, days=30)
    
    # Check if sessions per week is below threshold
    if data['attendance_velocity']['sessions_per_week'] < 2.0:
        send_alert(f"Low attendance: {data['student']['full_name']}")
    
    # Check learning velocity
    if data['learning_velocity']['topics_per_session'] < 2.0:
        send_alert(f"Low learning velocity: {data['student']['full_name']}")
```

### 3. Automated Reporting

```python
# Generate weekly report for all centers
def generate_weekly_report():
    insights = client.get_insights()
    
    report = f"""
    Weekly Report
    =============
    At-risk Students: {insights['at_risk_count']}
    Extended Enrollments: {insights['extended_count']}
    Nearing Completion: {insights['nearing_completion_count']}
    
    Action Required:
    """
    
    for student in insights['at_risk_students']:
        report += f"\n- Contact {student['full_name']} (no attendance for {student['days_since_last_attendance']} days)"
    
    send_email_report(report)
```

---

## Rate Limiting & Best Practices

1. **Cache Results**: Reports are computationally expensive. Cache results when possible.
2. **Use Query Parameters**: Customize thresholds to match your business rules.
3. **Batch Requests**: If fetching multiple reports, consider implementing a batch endpoint.
4. **Error Handling**: Always handle 403/404 errors gracefully.
5. **Pagination**: For large datasets, consider implementing pagination (future enhancement).

---

## OpenAPI Documentation

Interactive API documentation is available at:
- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/

These provide:
- Interactive testing
- Request/response schemas
- Authentication examples
- Error codes

---

## Support

For issues or questions:
1. Check the OpenAPI documentation
2. Review the source code in `apps/api/v1/views.py`
3. Check service functions in `apps/reports/services.py`
4. Contact the development team

---

**Last Updated**: 2025-11-01  
**API Version**: v1  
**Tasks**: T150-T154
