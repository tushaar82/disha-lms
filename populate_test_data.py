#!/usr/bin/env python3
"""
Populate test data for Disha LMS - Computer Training Institute
Creates realistic data with Indian names, programming subjects, and 3 months attendance
"""

import os
import sys
import django
from datetime import datetime, timedelta, time
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from apps.centers.models import Center, CenterHead
from apps.students.models import Student
from apps.faculty.models import Faculty
from apps.subjects.models import Subject, Topic, Assignment
from apps.attendance.models import AttendanceRecord

User = get_user_model()

# Indian Names
MALE_FIRST_NAMES = [
    'Aarav', 'Vivaan', 'Aditya', 'Vihaan', 'Arjun', 'Sai', 'Arnav', 'Ayaan',
    'Krishna', 'Ishaan', 'Shaurya', 'Atharv', 'Advait', 'Pranav', 'Dhruv',
    'Aryan', 'Reyansh', 'Kabir', 'Shivansh', 'Rudra', 'Rohan', 'Karthik',
    'Varun', 'Aakash', 'Nikhil', 'Rahul', 'Amit', 'Suresh', 'Rajesh', 'Vijay'
]

FEMALE_FIRST_NAMES = [
    'Aadhya', 'Saanvi', 'Ananya', 'Diya', 'Aaradhya', 'Pari', 'Anika', 'Navya',
    'Angel', 'Myra', 'Sara', 'Prisha', 'Avni', 'Kiara', 'Riya', 'Isha',
    'Anvi', 'Shanaya', 'Siya', 'Pihu', 'Priya', 'Sneha', 'Pooja', 'Kavya',
    'Divya', 'Neha', 'Anjali', 'Meera', 'Lakshmi', 'Radha'
]

LAST_NAMES = [
    'Sharma', 'Verma', 'Patel', 'Kumar', 'Singh', 'Gupta', 'Reddy', 'Rao',
    'Nair', 'Iyer', 'Menon', 'Pillai', 'Desai', 'Joshi', 'Kulkarni', 'Mehta',
    'Shah', 'Agarwal', 'Bansal', 'Chopra', 'Malhotra', 'Kapoor', 'Bhatia',
    'Sethi', 'Khanna', 'Arora', 'Saxena', 'Sinha', 'Mishra', 'Pandey',
    'Tiwari', 'Dubey', 'Jain', 'Agrawal', 'Goyal', 'Mittal', 'Garg'
]

INDIAN_CITIES = [
    ('Mumbai', 'Maharashtra', '400001'),
    ('Delhi', 'Delhi', '110001'),
    ('Bangalore', 'Karnataka', '560001'),
    ('Hyderabad', 'Telangana', '500001'),
    ('Chennai', 'Tamil Nadu', '600001'),
    ('Kolkata', 'West Bengal', '700001'),
    ('Pune', 'Maharashtra', '411001'),
    ('Ahmedabad', 'Gujarat', '380001'),
    ('Jaipur', 'Rajasthan', '302001'),
    ('Lucknow', 'Uttar Pradesh', '226001'),
]

# Programming Subjects and Topics
SUBJECTS_DATA = {
    'Python Programming': {
        'code': 'PY101',
        'topics': [
            'Introduction to Python and Setup',
            'Variables and Data Types',
            'Control Flow - If/Else Statements',
            'Loops - For and While',
            'Functions and Modules',
            'Lists and Tuples',
            'Dictionaries and Sets',
            'File Handling',
            'Exception Handling',
            'Object-Oriented Programming - Classes',
            'OOP - Inheritance and Polymorphism',
            'Working with Libraries - NumPy',
            'Working with Libraries - Pandas',
            'Web Scraping with BeautifulSoup',
            'Introduction to Django Framework',
        ]
    },
    'Java Programming': {
        'code': 'JAVA101',
        'topics': [
            'Introduction to Java and JDK Setup',
            'Java Basics - Variables and Data Types',
            'Operators and Expressions',
            'Control Statements',
            'Arrays and Strings',
            'Methods and Constructors',
            'Object-Oriented Programming Concepts',
            'Inheritance and Interfaces',
            'Packages and Access Modifiers',
            'Exception Handling',
            'Collections Framework',
            'File I/O Operations',
            'Multithreading Basics',
            'JDBC - Database Connectivity',
            'Introduction to Spring Framework',
        ]
    },
    'C++ Programming': {
        'code': 'CPP101',
        'topics': [
            'Introduction to C++ and Setup',
            'Basic Syntax and Data Types',
            'Operators and Control Structures',
            'Functions and Function Overloading',
            'Arrays and Pointers',
            'Structures and Unions',
            'Classes and Objects',
            'Constructors and Destructors',
            'Inheritance',
            'Polymorphism',
            'Virtual Functions',
            'File Handling',
            'Templates',
            'STL - Standard Template Library',
            'Exception Handling',
        ]
    },
    'Web Development - HTML/CSS': {
        'code': 'WEB101',
        'topics': [
            'Introduction to Web Development',
            'HTML Basics - Tags and Elements',
            'HTML Forms and Input Types',
            'HTML5 Semantic Elements',
            'CSS Basics - Selectors and Properties',
            'CSS Box Model',
            'CSS Flexbox Layout',
            'CSS Grid Layout',
            'Responsive Design with Media Queries',
            'CSS Animations and Transitions',
            'Bootstrap Framework',
            'Building a Complete Website',
        ]
    },
    'JavaScript Programming': {
        'code': 'JS101',
        'topics': [
            'Introduction to JavaScript',
            'Variables and Data Types',
            'Operators and Expressions',
            'Control Flow and Loops',
            'Functions and Scope',
            'Arrays and Array Methods',
            'Objects and JSON',
            'DOM Manipulation',
            'Event Handling',
            'ES6 Features - Arrow Functions, Let/Const',
            'Promises and Async/Await',
            'Fetch API and AJAX',
            'Introduction to React.js',
            'Building Interactive Web Apps',
        ]
    },
    'Database Management - SQL': {
        'code': 'SQL101',
        'topics': [
            'Introduction to Databases',
            'Installing MySQL/PostgreSQL',
            'Creating Databases and Tables',
            'Data Types and Constraints',
            'INSERT, UPDATE, DELETE Operations',
            'SELECT Queries and WHERE Clause',
            'Joins - INNER, LEFT, RIGHT, FULL',
            'Aggregate Functions',
            'GROUP BY and HAVING',
            'Subqueries',
            'Views and Indexes',
            'Stored Procedures',
            'Triggers',
            'Database Normalization',
            'Backup and Recovery',
        ]
    },
    'Data Structures & Algorithms': {
        'code': 'DSA101',
        'topics': [
            'Introduction to Data Structures',
            'Time and Space Complexity',
            'Arrays and Strings',
            'Linked Lists',
            'Stacks',
            'Queues',
            'Trees - Binary Trees',
            'Binary Search Trees',
            'Heaps',
            'Hashing',
            'Graphs - Representation',
            'Graph Traversal - BFS and DFS',
            'Sorting Algorithms',
            'Searching Algorithms',
            'Dynamic Programming Basics',
        ]
    },
    'Android App Development': {
        'code': 'AND101',
        'topics': [
            'Introduction to Android Development',
            'Setting up Android Studio',
            'Android Project Structure',
            'Activities and Intents',
            'Layouts - Linear, Relative, Constraint',
            'UI Components - Buttons, TextViews',
            'RecyclerView and Adapters',
            'Fragments',
            'Navigation Components',
            'SharedPreferences',
            'SQLite Database',
            'Networking with Retrofit',
            'Working with APIs',
            'Firebase Integration',
            'Publishing Apps on Play Store',
        ]
    },
}

def get_random_name(gender='random'):
    """Generate random Indian name"""
    if gender == 'random':
        gender = random.choice(['male', 'female'])
    
    if gender == 'male':
        first_name = random.choice(MALE_FIRST_NAMES)
    else:
        first_name = random.choice(FEMALE_FIRST_NAMES)
    
    last_name = random.choice(LAST_NAMES)
    return first_name, last_name

def get_random_phone():
    """Generate random Indian phone number"""
    return f"+91-{random.randint(70000, 99999)}{random.randint(10000, 99999)}"

def get_random_email(first_name, last_name):
    """Generate email from name"""
    domains = ['gmail.com', 'yahoo.com', 'outlook.com', 'hotmail.com']
    return f"{first_name.lower()}.{last_name.lower()}{random.randint(1, 999)}@{random.choice(domains)}"

def create_master_account():
    """Create master account"""
    print("\n📋 Creating Master Account...")
    
    master, created = User.objects.get_or_create(
        email='master@dishalms.com',
        defaults={
            'first_name': 'Master',
            'last_name': 'Admin',
            'role': 'master',
            'is_staff': True,
            'is_superuser': True,
        }
    )
    if created:
        master.set_password('master123')
        master.save()
        print(f"✅ Created: {master.email} (Password: master123)")
    else:
        print(f"ℹ️  Already exists: {master.email}")
    
    return master

def create_centers(master_user):
    """Create centers in different Indian cities"""
    print("\n🏢 Creating Centers...")
    
    centers = []
    for i, (city, state, pincode) in enumerate(INDIAN_CITIES[:5], 1):  # Create 5 centers
        center, created = Center.objects.get_or_create(
            code=f'DL{city[:3].upper()}{i:02d}',
            defaults={
                'name': f'Disha Learning Center - {city}',
                'address': f'{random.randint(1, 999)}, {random.choice(["MG Road", "Main Street", "Park Avenue", "Station Road"])}',
                'city': city,
                'state': state,
                'pincode': pincode,
                'phone': get_random_phone(),
                'email': f'{city.lower()}@dishalms.com',
                'is_active': True,
                'created_by': master_user,
                'modified_by': master_user,
            }
        )
        centers.append(center)
        if created:
            print(f"✅ Created: {center.name} ({center.code})")
        else:
            print(f"ℹ️  Already exists: {center.name}")
    
    return centers

def create_center_heads(centers, master_user):
    """Create center heads for each center"""
    print("\n👔 Creating Center Heads...")
    
    center_heads = []
    for i, center in enumerate(centers, 1):
        first_name, last_name = get_random_name()
        email = f'head.{center.code.lower()}@dishalms.com'
        
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'role': 'center_head',
                'phone': get_random_phone(),
            }
        )
        if created:
            user.set_password('head123')
            user.save()
            print(f"✅ Created User: {user.email} - {user.get_full_name()}")
        
        # Create CenterHead profile
        center_head, ch_created = CenterHead.objects.get_or_create(
            user=user,
            defaults={
                'center': center,
                'employee_id': f'EMP{center.code}{i:03d}',
                'joining_date': timezone.now().date() - timedelta(days=random.randint(365, 1095)),
                'is_active': True,
                'created_by': master_user,
                'modified_by': master_user,
            }
        )
        
        # Add to center's center_heads
        center.center_heads.add(user)
        
        center_heads.append(center_head)
        if ch_created:
            print(f"   ✅ Center Head Profile: {center.name}")
    
    return center_heads

def create_subjects(master_user):
    """Create programming subjects with topics"""
    print("\n📚 Creating Subjects and Topics...")
    
    subjects = []
    for subject_name, data in SUBJECTS_DATA.items():
        subject, created = Subject.objects.get_or_create(
            code=data['code'],
            defaults={
                'name': subject_name,
                'description': f'Complete course on {subject_name}',
                'is_active': True,
                'created_by': master_user,
                'modified_by': master_user,
            }
        )
        subjects.append(subject)
        
        if created:
            print(f"✅ Created Subject: {subject.name} ({subject.code})")
            
            # Create topics
            for seq, topic_name in enumerate(data['topics'], 1):
                topic = Topic.objects.create(
                    subject=subject,
                    name=topic_name,
                    sequence_number=seq,
                    estimated_duration=random.choice([60, 90, 120]),
                    is_active=True,
                    created_by=master_user,
                    modified_by=master_user,
                )
            print(f"   ✅ Created {len(data['topics'])} topics")
        else:
            print(f"ℹ️  Already exists: {subject.name}")
    
    return subjects

def create_faculty(centers, subjects, master_user):
    """Create faculty members for each center"""
    print("\n👨‍🏫 Creating Faculty Members...")
    
    faculty_list = []
    for center in centers:
        # Create 3-5 faculty per center
        num_faculty = random.randint(3, 5)
        
        for i in range(num_faculty):
            first_name, last_name = get_random_name()
            email = f'faculty.{center.code.lower()}.{i+1}@dishalms.com'
            
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'faculty',
                    'phone': get_random_phone(),
                }
            )
            if created:
                user.set_password('faculty123')
                user.save()
                print(f"✅ Created User: {user.email} - {user.get_full_name()}")
            
            # Create Faculty profile
            faculty, f_created = Faculty.objects.get_or_create(
                user=user,
                defaults={
                    'center': center,
                    'employee_id': f'FAC{center.code}{i+1:03d}',
                    'joining_date': timezone.now().date() - timedelta(days=random.randint(180, 730)),
                    'qualification': random.choice(['B.Tech', 'M.Tech', 'MCA', 'B.Sc CS', 'M.Sc CS']),
                    'specialization': random.choice(['Software Development', 'Web Technologies', 'Data Science', 'Mobile Apps']),
                    'experience_years': random.randint(1, 10),
                    'is_active': True,
                    'created_by': master_user,
                    'modified_by': master_user,
                }
            )
            
            if f_created:
                # Assign 2-4 subjects to each faculty
                faculty_subjects = random.sample(subjects, random.randint(2, min(4, len(subjects))))
                faculty.subjects.set(faculty_subjects)
                print(f"   ✅ Faculty Profile: {center.name} - Subjects: {len(faculty_subjects)}")
            
            faculty_list.append(faculty)
    
    return faculty_list

def create_students(centers, master_user):
    """Create students for each center"""
    print("\n🎓 Creating Students...")
    
    students = []
    for center in centers:
        # Create 15-25 students per center
        num_students = random.randint(15, 25)
        
        for i in range(num_students):
            first_name, last_name = get_random_name()
            guardian_first, guardian_last = get_random_name()
            
            enrollment_number = f'{center.code}STU{len(students)+1:04d}'
            
            student, created = Student.objects.get_or_create(
                enrollment_number=enrollment_number,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'email': get_random_email(first_name, last_name),
                    'phone': get_random_phone(),
                    'date_of_birth': timezone.now().date() - timedelta(days=random.randint(6570, 10950)),  # 18-30 years
                    'center': center,
                    'enrollment_date': timezone.now().date() - timedelta(days=random.randint(30, 180)),
                    'status': 'active',
                    'guardian_name': f'{guardian_first} {guardian_last}',
                    'guardian_phone': get_random_phone(),
                    'guardian_email': get_random_email(guardian_first, guardian_last),
                    'address': f'{random.randint(1, 999)}, {random.choice(["Sector", "Block", "Lane", "Street"])} {random.randint(1, 50)}',
                    'city': center.city,
                    'state': center.state,
                    'pincode': center.pincode,
                    'notes': '',
                    'created_by': master_user,
                    'modified_by': master_user,
                }
            )
            
            if created:
                students.append(student)
        
        print(f"✅ Created {num_students} students for {center.name}")
    
    return students

def create_assignments(students, subjects, faculty_list, master_user):
    """Create assignments linking students to subjects and faculty"""
    print("\n📝 Creating Assignments...")
    
    assignments = []
    for student in students:
        # Each student gets 1-3 subjects
        num_subjects = random.randint(1, 3)
        student_subjects = random.sample(subjects, num_subjects)
        
        for subject in student_subjects:
            # Find faculty from same center who teaches this subject
            available_faculty = [
                f for f in faculty_list 
                if f.center == student.center and subject in f.subjects.all()
            ]
            
            if not available_faculty:
                continue
            
            faculty = random.choice(available_faculty)
            
            assignment, created = Assignment.objects.get_or_create(
                student=student,
                subject=subject,
                faculty=faculty,
                start_date=student.enrollment_date,
                defaults={
                    'end_date': None,
                    'is_active': True,
                    'created_by': master_user,
                    'modified_by': master_user,
                }
            )
            
            if created:
                assignments.append(assignment)
    
    print(f"✅ Created {len(assignments)} assignments")
    return assignments

def create_attendance_records(assignments):
    """Create 3 months of attendance records"""
    print("\n📅 Creating Attendance Records (Last 3 Months)...")
    
    today = timezone.now().date()
    start_date = today - timedelta(days=90)
    
    attendance_count = 0
    
    for assignment in assignments:
        # Each student attends 2-4 times per week on average
        sessions_per_week = random.uniform(2, 4)
        total_days = (today - max(start_date, assignment.start_date)).days
        expected_sessions = int((total_days / 7) * sessions_per_week)
        
        # Generate random attendance dates
        attendance_dates = []
        current_date = max(start_date, assignment.start_date)
        
        while current_date < today and len(attendance_dates) < expected_sessions:
            # Skip some days randomly
            if random.random() < 0.6:  # 60% chance of attendance
                attendance_dates.append(current_date)
            current_date += timedelta(days=1)
        
        # Create attendance records
        for date in attendance_dates:
            # Random session time (morning, afternoon, or evening)
            session_times = [
                (time(9, 0), time(11, 0)),   # Morning
                (time(14, 0), time(16, 0)),  # Afternoon
                (time(17, 0), time(19, 0)),  # Evening
            ]
            in_time, out_time = random.choice(session_times)
            
            # Calculate duration
            duration = (datetime.combine(date, out_time) - datetime.combine(date, in_time)).seconds // 60
            
            # Check if backdated
            is_backdated = date < today
            backdated_reason = 'Marked later due to system unavailability' if is_backdated and random.random() < 0.1 else ''
            
            try:
                attendance = AttendanceRecord.objects.create(
                    student=assignment.student,
                    assignment=assignment,
                    date=date,
                    in_time=in_time,
                    out_time=out_time,
                    duration_minutes=duration,
                    is_backdated=is_backdated,
                    backdated_reason=backdated_reason,
                    marked_by=assignment.faculty.user,
                    notes=random.choice([
                        'Good progress',
                        'Needs more practice',
                        'Excellent understanding',
                        'Completed exercises',
                        'Cleared all doubts',
                        '',
                    ])
                )
                
                # Add 1-3 random topics covered
                subject_topics = list(assignment.subject.topics.all())
                if subject_topics:
                    num_topics = random.randint(1, min(3, len(subject_topics)))
                    topics = random.sample(subject_topics, num_topics)
                    attendance.topics_covered.set(topics)
                
                attendance_count += 1
                
            except Exception as e:
                # Skip duplicate entries
                pass
        
        if attendance_count % 100 == 0:
            print(f"   📝 Created {attendance_count} attendance records...")
    
    print(f"✅ Created {attendance_count} attendance records")
    return attendance_count

def main():
    """Main function to populate all data"""
    print("=" * 70)
    print("🚀 DISHA LMS - Test Data Population Script")
    print("   Computer Training Institute - Indian Names & Programming Courses")
    print("=" * 70)
    
    try:
        # Create data in order
        master = create_master_account()
        centers = create_centers(master)
        center_heads = create_center_heads(centers, master)
        subjects = create_subjects(master)
        faculty_list = create_faculty(centers, subjects, master)
        students = create_students(centers, master)
        assignments = create_assignments(students, subjects, faculty_list, master)
        attendance_count = create_attendance_records(assignments)
        
        # Summary
        print("\n" + "=" * 70)
        print("✅ DATA POPULATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print(f"📊 Summary:")
        print(f"   • Centers: {len(centers)}")
        print(f"   • Center Heads: {len(center_heads)}")
        print(f"   • Subjects: {len(subjects)}")
        print(f"   • Faculty: {len(faculty_list)}")
        print(f"   • Students: {len(students)}")
        print(f"   • Assignments: {len(assignments)}")
        print(f"   • Attendance Records: {attendance_count}")
        print("\n🔐 Login Credentials:")
        print(f"   Master Account: email='master@dishalms.com', password='master123'")
        print(f"   Center Heads: email='head.<center_code>@dishalms.com', password='head123'")
        print(f"   Faculty: email='faculty.<center_code>.<num>@dishalms.com', password='faculty123'")
        print("\n🌐 Access the application at: http://127.0.0.1:8000/")
        print("=" * 70)
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
