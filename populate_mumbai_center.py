#!/usr/bin/env python3
"""
Populate Mumbai Learning Center with students, subjects, faculty, and 3 months attendance.
Complete data setup for Mumbai center demonstration.
"""

import os
import sys
import django
import datetime
from datetime import timedelta, time
import random

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from django.utils import timezone
from django.contrib.auth import get_user_model
from apps.centers.models import Center
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
    'Sethi', 'Khanna', 'Arora', 'Saxena', 'Sinha', 'Mishra', 'Pandey'
]

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

def main():
    print("=" * 70)
    print("🏢 Mumbai Learning Center - Complete Data Population")
    print("=" * 70)
    
    # Get or create Mumbai center
    print("\n📍 Finding Mumbai Center...")
    try:
        # Try to find by code first (more specific)
        mumbai_center = Center.objects.get(code='DLMUM01')
        print(f"✅ Found: {mumbai_center.name} ({mumbai_center.code})")
    except Center.DoesNotExist:
        print("❌ Mumbai center (DLMUM01) not found!")
        
        # Check if there are other Mumbai centers
        mumbai_centers = Center.objects.filter(city='Mumbai', is_deleted=False)
        if mumbai_centers.exists():
            print(f"\n⚠️  Found {mumbai_centers.count()} Mumbai center(s):")
            for idx, center in enumerate(mumbai_centers, 1):
                print(f"   {idx}. {center.name} ({center.code})")
            
            print("\nUsing the first one...")
            mumbai_center = mumbai_centers.first()
            print(f"✅ Selected: {mumbai_center.name} ({mumbai_center.code})")
        else:
            print("Creating Mumbai center...")
            
            # Get master user
            master = User.objects.filter(role='master').first()
            if not master:
                print("❌ No master account found. Please run populate_database.sh first.")
                return
            
            mumbai_center = Center.objects.create(
                name='Mumbai Learning Center',
                code='DLMUM01',
                address='123, MG Road, Andheri',
                city='Mumbai',
                state='Maharashtra',
                pincode='400001',
                phone=get_random_phone(),
                email='mumbai@dishalms.com',
                is_active=True,
                created_by=master,
                modified_by=master
            )
            print(f"✅ Created: {mumbai_center.name}")
    
    # Get all subjects
    print("\n📚 Checking Subjects...")
    subjects = list(Subject.objects.filter(is_active=True))
    if not subjects:
        print("❌ No subjects found. Please run populate_database.sh first to create subjects.")
        return
    print(f"✅ Found {len(subjects)} subjects")
    
    # Get or create faculty for Mumbai
    print("\n👨‍🏫 Setting up Faculty...")
    faculty_list = list(Faculty.objects.filter(center=mumbai_center, is_active=True))
    
    if len(faculty_list) < 3:
        print(f"Creating additional faculty (need at least 3)...")
        master = User.objects.filter(role='master').first()
        
        for i in range(3 - len(faculty_list)):
            first_name, last_name = get_random_name()
            email = f'faculty.mumbai.{len(faculty_list) + i + 1}@dishalms.com'
            
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
            
            faculty, _ = Faculty.objects.get_or_create(
                user=user,
                defaults={
                    'center': mumbai_center,
                    'employee_id': f'FAC{mumbai_center.code}{len(faculty_list) + i + 1:03d}',
                    'joining_date': timezone.now().date() - timedelta(days=random.randint(180, 730)),
                    'qualification': random.choice(['B.Tech', 'M.Tech', 'MCA', 'B.Sc CS']),
                    'specialization': random.choice(['Software Development', 'Web Technologies', 'Data Science']),
                    'experience_years': random.randint(2, 10),
                    'is_active': True,
                    'created_by': master,
                    'modified_by': master,
                }
            )
            
            # Assign subjects
            faculty_subjects = random.sample(subjects, random.randint(2, min(4, len(subjects))))
            faculty.subjects.set(faculty_subjects)
            faculty_list.append(faculty)
            print(f"   ✅ Created: {user.get_full_name()} - {len(faculty_subjects)} subjects")
    
    print(f"✅ Total Faculty: {len(faculty_list)}")
    
    # Create students
    print("\n🎓 Creating Students...")
    num_students = 25  # Create 25 students for Mumbai
    students_created = 0
    master = User.objects.filter(role='master').first()
    
    for i in range(num_students):
        first_name, last_name = get_random_name()
        guardian_first, guardian_last = get_random_name()
        
        enrollment_number = f'{mumbai_center.code}STU{i+1:04d}'
        
        student, created = Student.objects.get_or_create(
            enrollment_number=enrollment_number,
            defaults={
                'first_name': first_name,
                'last_name': last_name,
                'email': get_random_email(first_name, last_name),
                'phone': get_random_phone(),
                'date_of_birth': timezone.now().date() - timedelta(days=random.randint(6570, 10950)),
                'center': mumbai_center,
                'enrollment_date': timezone.now().date() - timedelta(days=random.randint(30, 120)),
                'status': 'active',
                'guardian_name': f'{guardian_first} {guardian_last}',
                'guardian_phone': get_random_phone(),
                'guardian_email': get_random_email(guardian_first, guardian_last),
                'address': f'{random.randint(1, 999)}, {random.choice(["Sector", "Block", "Lane"])} {random.randint(1, 50)}',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400001',
                'notes': '',
                'created_by': master,
                'modified_by': master,
            }
        )
        
        if created:
            students_created += 1
    
    print(f"✅ Created {students_created} students")
    
    # Create assignments
    print("\n📝 Creating Subject Assignments...")
    students = Student.objects.filter(center=mumbai_center, status='active')
    assignments_created = 0
    
    for student in students:
        # Each student gets 1-3 subjects
        num_subjects = random.randint(1, 3)
        student_subjects = random.sample(subjects, num_subjects)
        
        for subject in student_subjects:
            # Find faculty who teaches this subject
            available_faculty = [f for f in faculty_list if subject in f.subjects.all()]
            
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
                    'created_by': master,
                    'modified_by': master,
                }
            )
            
            if created:
                assignments_created += 1
    
    print(f"✅ Created {assignments_created} assignments")
    
    # Create backdated attendance
    print("\n📅 Creating 3 Months of Backdated Attendance...")
    today = timezone.now().date()
    start_date = today - timedelta(days=90)
    
    session_times = [
        (time(9, 0), time(11, 0)),
        (time(14, 0), time(16, 0)),
        (time(17, 0), time(19, 0)),
    ]
    
    total_attendance = 0
    assignments = Assignment.objects.filter(
        student__center=mumbai_center,
        is_active=True
    ).select_related('student', 'subject', 'faculty__user')
    
    for assignment in assignments:
        current_date = max(start_date, assignment.start_date)
        
        while current_date < today:
            # 70% attendance rate
            if random.random() < 0.7:
                in_time, out_time = random.choice(session_times)
                duration = (datetime.datetime.combine(current_date, out_time) - 
                           datetime.datetime.combine(current_date, in_time)).seconds // 60
                
                # Check if exists
                if AttendanceRecord.objects.filter(
                    student=assignment.student,
                    assignment=assignment,
                    date=current_date
                ).exists():
                    current_date += timedelta(days=1)
                    continue
                
                try:
                    faculty_user = assignment.faculty.user
                    
                    attendance = AttendanceRecord.objects.create(
                        student=assignment.student,
                        assignment=assignment,
                        date=current_date,
                        in_time=in_time,
                        out_time=out_time,
                        duration_minutes=duration,
                        is_backdated=True,
                        backdated_reason='Initial data population',
                        marked_by=faculty_user,
                        created_by=faculty_user,
                        modified_by=faculty_user,
                        notes=random.choice([
                            'Good progress',
                            'Excellent understanding',
                            'Completed exercises',
                            'Active participation',
                            '',
                        ])
                    )
                    
                    # Add topics
                    subject_topics = list(assignment.subject.topics.filter(is_active=True))
                    if subject_topics:
                        num_topics = random.randint(1, min(3, len(subject_topics)))
                        topics = random.sample(subject_topics, num_topics)
                        attendance.topics_covered.set(topics)
                    
                    total_attendance += 1
                    
                except Exception as e:
                    pass
            
            current_date += timedelta(days=1)
        
        if total_attendance % 100 == 0 and total_attendance > 0:
            print(f"   📝 Created {total_attendance} attendance records...")
    
    print(f"✅ Created {total_attendance} attendance records")
    
    # Summary
    print("\n" + "=" * 70)
    print("✅ MUMBAI CENTER DATA POPULATION COMPLETED!")
    print("=" * 70)
    print(f"📊 Summary:")
    print(f"   • Center: {mumbai_center.name}")
    print(f"   • Faculty: {len(faculty_list)}")
    print(f"   • Students: {students.count()}")
    print(f"   • Assignments: {assignments_created}")
    print(f"   • Attendance Records: {total_attendance}")
    print(f"   • Average records per student: {total_attendance / students.count() if students.count() > 0 else 0:.1f}")
    print(f"\n🎯 Next Steps:")
    print(f"   1. View Mumbai Center Dashboard:")
    print(f"      http://127.0.0.1:8000/centers/dashboard/")
    print(f"   2. View Students:")
    print(f"      http://127.0.0.1:8000/students/")
    print(f"   3. View Student Reports:")
    print(f"      http://127.0.0.1:8000/reports/student/<id>/")
    print(f"   4. View Faculty Dashboard:")
    print(f"      http://127.0.0.1:8000/faculty/dashboard/")
    print("=" * 70)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
