#!/usr/bin/env python3
"""
Add backdated attendance for all students in Disha LMS.
Creates realistic 3-month attendance history with topics covered.
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
from apps.students.models import Student
from apps.subjects.models import Assignment, Topic
from apps.attendance.models import AttendanceRecord

def add_backdated_attendance():
    """Add 3 months of backdated attendance for all active students."""
    
    print("=" * 70)
    print("🚀 Adding Backdated Attendance for All Students")
    print("=" * 70)
    
    today = timezone.now().date()
    start_date = today - timedelta(days=90)  # 3 months ago
    
    # Get all active students with assignments
    students = Student.objects.filter(
        status='active',
        deleted_at__isnull=True,
        assignments__is_active=True
    ).distinct()
    
    total_students = students.count()
    print(f"\n📊 Found {total_students} active students with assignments")
    
    if total_students == 0:
        print("\n⚠️  No active students with assignments found!")
        print("Please create students and assign them subjects first.")
        return
    
    total_records_created = 0
    total_records_skipped = 0
    
    # Session time slots
    session_times = [
        (time(9, 0), time(11, 0)),   # Morning: 9 AM - 11 AM
        (time(11, 0), time(13, 0)),  # Late Morning: 11 AM - 1 PM
        (time(14, 0), time(16, 0)),  # Afternoon: 2 PM - 4 PM
        (time(16, 0), time(18, 0)),  # Late Afternoon: 4 PM - 6 PM
        (time(17, 0), time(19, 0)),  # Evening: 5 PM - 7 PM
        (time(18, 0), time(20, 0)),  # Late Evening: 6 PM - 8 PM
    ]
    
    for student_num, student in enumerate(students, 1):
        print(f"\n[{student_num}/{total_students}] Processing: {student.get_full_name()} ({student.enrollment_number})")
        
        # Get student's assignments
        assignments = Assignment.objects.filter(
            student=student,
            is_active=True,
            deleted_at__isnull=True
        ).select_related('subject', 'faculty__user')
        
        if not assignments.exists():
            print(f"   ⚠️  No active assignments found")
            continue
        
        print(f"   📚 Subjects: {assignments.count()}")
        
        # Determine attendance frequency (2-4 sessions per week)
        sessions_per_week = random.uniform(2, 4)
        
        # Generate attendance dates
        current_date = max(start_date, student.enrollment_date)
        student_records_created = 0
        
        while current_date < today:
            # Random attendance probability (60-80% attendance rate)
            if random.random() < random.uniform(0.6, 0.8):
                # Pick a random assignment for this session
                assignment = random.choice(list(assignments))
                
                # Pick random session time
                in_time, out_time = random.choice(session_times)
                
                # Calculate duration
                duration = (datetime.datetime.combine(current_date, out_time) - 
                           datetime.datetime.combine(current_date, in_time)).seconds // 60
                
                # Check if attendance already exists
                existing = AttendanceRecord.objects.filter(
                    student=student,
                    assignment=assignment,
                    date=current_date
                ).exists()
                
                if existing:
                    total_records_skipped += 1
                    current_date += timedelta(days=1)
                    continue
                
                # Determine if backdated
                is_backdated = current_date < today
                backdated_reason = ''
                if is_backdated and random.random() < 0.1:  # 10% have reasons
                    backdated_reason = random.choice([
                        'Marked later due to system unavailability',
                        'Attendance recorded after session',
                        'Late entry by faculty',
                        'System maintenance delay'
                    ])
                
                try:
                    # Get the faculty user who will mark the attendance
                    faculty_user = assignment.faculty.user
                    
                    # Create attendance record
                    attendance = AttendanceRecord.objects.create(
                        student=student,
                        assignment=assignment,
                        date=current_date,
                        in_time=in_time,
                        out_time=out_time,
                        duration_minutes=duration,
                        is_backdated=is_backdated,
                        backdated_reason=backdated_reason,
                        marked_by=faculty_user,
                        created_by=faculty_user,
                        modified_by=faculty_user,
                        notes=random.choice([
                            'Good progress today',
                            'Completed all exercises',
                            'Needs more practice',
                            'Excellent understanding',
                            'Cleared all doubts',
                            'Active participation',
                            'Homework completed',
                            '',
                        ])
                    )
                    
                    # Add 1-3 random topics covered
                    subject_topics = list(assignment.subject.topics.filter(is_active=True))
                    if subject_topics:
                        num_topics = random.randint(1, min(3, len(subject_topics)))
                        topics = random.sample(subject_topics, num_topics)
                        attendance.topics_covered.set(topics)
                    
                    student_records_created += 1
                    total_records_created += 1
                    
                except Exception as e:
                    # Skip if duplicate or other error
                    error_msg = str(e)
                    if 'UNIQUE constraint' in error_msg or 'duplicate' in error_msg.lower():
                        # Duplicate - this is expected, skip silently
                        total_records_skipped += 1
                    else:
                        # Other error - show details
                        print(f"   ⚠️  Error on {current_date}: {error_msg[:80]}")
                        total_records_skipped += 1
            
            # Move to next day
            current_date += timedelta(days=1)
        
        print(f"   ✅ Created {student_records_created} attendance records")
        
        # Progress indicator every 10 students
        if student_num % 10 == 0:
            print(f"\n📈 Progress: {student_num}/{total_students} students processed")
            print(f"   Total records created so far: {total_records_created}")
    
    # Final summary
    print("\n" + "=" * 70)
    print("✅ BACKDATED ATTENDANCE COMPLETED!")
    print("=" * 70)
    print(f"📊 Summary:")
    print(f"   • Students processed: {total_students}")
    print(f"   • Attendance records created: {total_records_created}")
    print(f"   • Records skipped (duplicates): {total_records_skipped}")
    print(f"   • Average records per student: {total_records_created / total_students if total_students > 0 else 0:.1f}")
    print(f"\n🎯 Next Steps:")
    print(f"   1. View student dashboards to see charts with data")
    print(f"   2. Check faculty dashboards for teaching analytics")
    print(f"   3. View reports at /reports/student/<id>/")
    print("=" * 70)

if __name__ == '__main__':
    try:
        add_backdated_attendance()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
