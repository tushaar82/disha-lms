# Database Population Script - Disha LMS

## Overview
Automated script to populate the Disha LMS database with realistic test data for a computer training institute.

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run the population script
./populate_database.sh
```

Or run directly:
```bash
python3 populate_test_data.py
```

## What Gets Created

### 1. Master Account
- **Email**: `master@dishalms.com`
- **Password**: `master123`
- **Role**: Master Account (full system access)

### 2. Centers (5 locations)
- Mumbai, Maharashtra (DLMUM01)
- Delhi, Delhi (DLDEL02)
- Bangalore, Karnataka (DLBAN03)
- Hyderabad, Telangana (DLHYD04)
- Chennai, Tamil Nadu (DLCHE05)

### 3. Center Heads (5 users)
- **Email Pattern**: `head.<center_code>@dishalms.com`
- **Example**: `head.dlmum01@dishalms.com`
- **Password**: `head123`
- **Indian Names**: Random first and last names

### 4. Programming Subjects (8 subjects with 100+ topics)
1. **Python Programming** (PY101) - 15 topics
2. **Java Programming** (JAVA101) - 15 topics
3. **C++ Programming** (CPP101) - 15 topics
4. **Web Development - HTML/CSS** (WEB101) - 12 topics
5. **JavaScript Programming** (JS101) - 14 topics
6. **Database Management - SQL** (SQL101) - 15 topics
7. **Data Structures & Algorithms** (DSA101) - 15 topics
8. **Android App Development** (AND101) - 15 topics

### 5. Faculty Members (15-25 total)
- **Email Pattern**: `faculty.<center_code>.<num>@dishalms.com`
- **Example**: `faculty.dlmum01.1@dishalms.com`
- **Password**: `faculty123`
- **Distribution**: 3-5 faculty per center
- **Subjects**: Each faculty teaches 2-4 subjects
- **Qualifications**: B.Tech, M.Tech, MCA, B.Sc CS, M.Sc CS
- **Experience**: 1-10 years

### 6. Students (75-125 total)
- **Distribution**: 15-25 students per center
- **Indian Names**: Comprehensive list of male/female names
- **Enrollment Numbers**: `<CENTER_CODE>STU<NUM>`
- **Example**: `DLMUM01STU0001`
- **Age Range**: 18-30 years
- **Complete Profile**: Contact info, guardian details, address

### 7. Assignments (150-300 total)
- Links students to subjects and faculty
- Each student enrolled in 1-3 subjects
- Faculty from same center who teaches that subject

### 8. Attendance Records (1000-2000 records)
- **Duration**: Last 3 months (90 days)
- **Frequency**: 2-4 sessions per week (60% attendance rate)
- **Session Times**:
  - Morning: 9:00 AM - 11:00 AM
  - Afternoon: 2:00 PM - 4:00 PM
  - Evening: 5:00 PM - 7:00 PM
- **Duration**: 2 hours per session
- **Topics**: 1-3 random topics covered per session
- **Notes**: Random progress notes

## Login Examples

### Master Account
```
URL: http://127.0.0.1:8000/accounts/login/
Email: master@dishalms.com
Password: master123
```

### Center Head (Mumbai)
```
URL: http://127.0.0.1:8000/accounts/login/
Email: head.dlmum01@dishalms.com
Password: head123
```

### Faculty (Mumbai, Faculty #1)
```
URL: http://127.0.0.1:8000/accounts/login/
Email: faculty.dlmum01.1@dishalms.com
Password: faculty123
```

## Indian Names Database

### Male First Names (30)
Aarav, Vivaan, Aditya, Vihaan, Arjun, Sai, Arnav, Ayaan, Krishna, Ishaan, Shaurya, Atharv, Advait, Pranav, Dhruv, Aryan, Reyansh, Kabir, Shivansh, Rudra, Rohan, Karthik, Varun, Aakash, Nikhil, Rahul, Amit, Suresh, Rajesh, Vijay

### Female First Names (30)
Aadhya, Saanvi, Ananya, Diya, Aaradhya, Pari, Anika, Navya, Angel, Myra, Sara, Prisha, Avni, Kiara, Riya, Isha, Anvi, Shanaya, Siya, Pihu, Priya, Sneha, Pooja, Kavya, Divya, Neha, Anjali, Meera, Lakshmi, Radha

### Last Names (37)
Sharma, Verma, Patel, Kumar, Singh, Gupta, Reddy, Rao, Nair, Iyer, Menon, Pillai, Desai, Joshi, Kulkarni, Mehta, Shah, Agarwal, Bansal, Chopra, Malhotra, Kapoor, Bhatia, Sethi, Khanna, Arora, Saxena, Sinha, Mishra, Pandey, Tiwari, Dubey, Jain, Agrawal, Goyal, Mittal, Garg

## Expected Data Counts

| Entity | Count |
|--------|-------|
| Centers | 5 |
| Center Heads | 5 |
| Subjects | 8 |
| Topics | 110+ |
| Faculty | 15-25 |
| Students | 75-125 |
| Assignments | 150-300 |
| Attendance Records | 1000-2000 |

## Features to Test After Population

### Master Account
- View all centers
- Access all dashboards
- View cross-center reports

### Center Head
- View center dashboard with statistics
- Manage students (CRUD operations)
- Manage faculty (CRUD operations)
- View attendance reports
- Access student reports

### Faculty
- View faculty dashboard
- Mark attendance for students
- View batch schedule (Gantt chart)
- See absent students alerts
- View teaching analytics

### Student Reports
- Consistency score (0-100%)
- Learning efficiency (topics/hour)
- Progress vs expected pace
- At-risk status detection
- Subject-wise performance
- Attendance trends (30 days)
- Learning timeline

## Troubleshooting

### Error: "Cannot resolve keyword 'username'"
**Fixed!** The User model uses `email` as the unique identifier, not `username`.

### Virtual Environment Not Activated
```bash
source venv/bin/activate
```

### Django Not Installed
```bash
pip install -r requirements.txt
```

### Permission Denied
```bash
chmod +x populate_test_data.py populate_database.sh
```

## Files Created

1. **populate_test_data.py** - Main Python script (630+ lines)
2. **populate_database.sh** - Bash wrapper with user prompts
3. **POPULATE_DATA_README.md** - This documentation

## Data Characteristics

### Realistic Patterns
- ✅ Indian names (male/female)
- ✅ Indian cities and addresses
- ✅ Phone numbers in +91 format
- ✅ Realistic email addresses
- ✅ Programming subjects relevant to computer training
- ✅ 60% attendance rate (realistic dropout/absence)
- ✅ Random session times (morning/afternoon/evening)
- ✅ Progress notes and topics covered

### Event-Sourced Architecture
- ✅ Immutable attendance records
- ✅ Backdating properly tracked
- ✅ Audit trail maintained
- ✅ No delete operations on attendance

## Next Steps After Population

1. **Start the server**:
   ```bash
   python manage.py runserver
   ```

2. **Login as Master**:
   - Email: `master@dishalms.com`
   - Password: `master123`

3. **Explore Dashboards**:
   - Center Dashboard: `/centers/dashboard/`
   - Faculty Dashboard: `/faculty/dashboard/`
   - Student Reports: `/reports/student/<id>/`

4. **Test Features**:
   - View 3 months of attendance history
   - Check Gantt charts and analytics
   - View at-risk students
   - Test faculty performance metrics
   - Explore student progress reports

5. **API Testing**:
   - API Docs: `/api/docs/`
   - Get token: POST `/api/v1/auth/login/`
   - Test endpoints with Swagger UI

## Support

For issues or questions:
1. Check TROUBLESHOOTING.md
2. Review Django logs
3. Verify database migrations are applied
4. Ensure virtual environment is activated

---

**Created**: 2025-11-01  
**Version**: 1.0  
**Status**: ✅ Ready for use
