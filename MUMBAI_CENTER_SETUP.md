# Mumbai Learning Center - Complete Setup

## Quick Start

```bash
# Activate virtual environment
source venv/bin/activate

# Run the setup script
./setup_mumbai.sh
```

## What It Creates

### For Mumbai Learning Center

#### Students (25)
- Indian names (male/female)
- Complete profiles with guardian info
- Mumbai addresses
- Active status
- Enrolled in last 1-4 months

#### Faculty (3-5)
- Qualified instructors
- B.Tech/M.Tech/MCA qualified
- 2-10 years experience
- Teaching 2-4 subjects each
- Email: `faculty.mumbai.1@dishalms.com`
- Password: `faculty123`

#### Subjects
- Uses existing subjects (Python, Java, C++, Web Dev, etc.)
- Each subject has 12-15 topics
- Faculty assigned based on specialization

#### Assignments (40-75)
- Each student: 1-3 subjects
- Matched with qualified faculty
- Active assignments

#### Attendance Records (1,500-2,000)
- Last 3 months (90 days)
- 70% attendance rate (realistic)
- Session times:
  - Morning: 9 AM - 11 AM
  - Afternoon: 2 PM - 4 PM
  - Evening: 5 PM - 7 PM
- 1-3 topics covered per session
- Progress notes included

## Expected Output

```
======================================================================
🏢 Mumbai Learning Center - Complete Data Population
======================================================================

📍 Finding Mumbai Center...
✅ Found: Mumbai Learning Center (DLMUM01)

📚 Checking Subjects...
✅ Found 8 subjects

👨‍🏫 Setting up Faculty...
✅ Total Faculty: 4

🎓 Creating Students...
✅ Created 25 students

📝 Creating Subject Assignments...
✅ Created 52 assignments

📅 Creating 3 Months of Backdated Attendance...
   📝 Created 100 attendance records...
   📝 Created 200 attendance records...
   ...
✅ Created 1,847 attendance records

======================================================================
✅ MUMBAI CENTER DATA POPULATION COMPLETED!
======================================================================
📊 Summary:
   • Center: Mumbai Learning Center
   • Faculty: 4
   • Students: 25
   • Assignments: 52
   • Attendance Records: 1,847
   • Average records per student: 73.9

🎯 Next Steps:
   1. View Mumbai Center Dashboard
   2. View Students
   3. View Student Reports
   4. View Faculty Dashboard
======================================================================
```

## What You'll See

### Mumbai Center Dashboard
- **Total Students**: 25
- **Active Faculty**: 3-5
- **Subjects Offered**: 8
- **Attendance This Month**: ~200-300 records
- **Charts**: 7-day attendance trend
- **Insights**: Students needing attention, top faculty

### Student Dashboards
Each student will have:
- ✅ Attendance Trend Chart (30 days)
- ✅ Subject Completion Chart
- ✅ Learning Timeline (Gantt)
- ✅ Calendar Heatmap
- ✅ Monthly Learning Trend
- ✅ Weekly Pattern Chart
- ✅ Consistency Score (0-100%)
- ✅ Learning Efficiency
- ✅ Progress vs Expected
- ✅ At-Risk Status

### Faculty Dashboards
Each faculty will show:
- ✅ Batch Schedule (Gantt chart)
- ✅ Weekly Activity Trends
- ✅ Student Progress Distribution
- ✅ Subject Performance Charts
- ✅ Teaching Pattern by Hour
- ✅ Absent Students Alerts
- ✅ Teaching Metrics

## Access URLs

### Dashboards
- **Center Dashboard**: http://127.0.0.1:8000/centers/dashboard/
- **Students List**: http://127.0.0.1:8000/students/
- **Faculty List**: http://127.0.0.1:8000/faculty/
- **Attendance History**: http://127.0.0.1:8000/attendance/history/

### Reports
- **Student Report**: http://127.0.0.1:8000/reports/student/<id>/
- **Faculty Report**: http://127.0.0.1:8000/reports/faculty/<id>/
- **Center Report**: http://127.0.0.1:8000/reports/center/<id>/

## Login Credentials

### Master Account
```
Email: master@dishalms.com
Password: master123
Access: All centers, all data
```

### Mumbai Faculty
```
Email: faculty.mumbai.1@dishalms.com
Password: faculty123
Access: Mumbai students only
```

### Mumbai Center Head (if exists)
```
Email: head.dlmum01@dishalms.com
Password: head123
Access: Mumbai center only
```

## Sample Students

After running, you'll have students like:
- Aarav Sharma (DLMUM01STU0001)
- Saanvi Patel (DLMUM01STU0002)
- Aditya Kumar (DLMUM01STU0003)
- Diya Singh (DLMUM01STU0004)
- ... and 21 more

Each with:
- 20-80 attendance sessions
- 1-3 subjects enrolled
- Complete learning analytics
- 3 months of history

## Re-running the Script

Safe to run multiple times:
- ✅ Skips existing students
- ✅ Skips existing faculty
- ✅ Skips duplicate attendance
- ✅ Only adds missing data

## Troubleshooting

### No Subjects Found
```
❌ No subjects found. Please run populate_database.sh first.
```
**Solution**: Run the main population script first to create subjects.

### Mumbai Center Not Found
The script will automatically create the Mumbai center if it doesn't exist.

### Permission Errors
Make sure scripts are executable:
```bash
chmod +x populate_mumbai_center.py setup_mumbai.sh
```

## What Makes This Special

### Realistic Data
- ✅ Indian names and addresses
- ✅ Realistic attendance patterns (70% rate)
- ✅ Varied session times
- ✅ Random topics covered
- ✅ Progress notes
- ✅ Guardian information

### Complete Analytics
- ✅ All charts show data
- ✅ Trends visible
- ✅ Comparisons work
- ✅ At-risk detection active
- ✅ Performance metrics calculated

### Production-Ready
- ✅ Proper audit trails
- ✅ Created_by/modified_by set
- ✅ Backdated flags correct
- ✅ No data corruption
- ✅ Referential integrity maintained

## Files Created

1. **`populate_mumbai_center.py`** - Main population script
2. **`setup_mumbai.sh`** - Bash wrapper
3. **`MUMBAI_CENTER_SETUP.md`** - This documentation

## Integration

### After Running This Script

You can:
1. ✅ View beautiful dashboards with real data
2. ✅ Demo the system to stakeholders
3. ✅ Test all features with realistic data
4. ✅ Train users with actual examples
5. ✅ Generate reports for presentations

### Combine with Other Scripts

```bash
# 1. Create all centers and subjects
./populate_database.sh

# 2. Setup Mumbai specifically
./setup_mumbai.sh

# 3. Add more attendance if needed
./add_attendance.sh
```

---

**Status**: ✅ Ready to use  
**Version**: 1.0  
**Date**: 2025-11-02  
**Tested**: ✅ Production ready
