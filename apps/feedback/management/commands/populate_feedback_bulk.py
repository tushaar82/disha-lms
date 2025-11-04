"""
Management command to populate test faculty feedback data with multiple feedbacks per student.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.feedback.models import FacultyFeedback
from apps.faculty.models import Faculty
from apps.students.models import Student
from apps.centers.models import Center
from apps.accounts.models import User
import random
from datetime import timedelta


class Command(BaseCommand):
    help = 'Populate test faculty feedback data with 5-7 feedbacks per student'

    def add_arguments(self, parser):
        parser.add_argument(
            '--per-student',
            type=int,
            default=6,
            help='Number of feedback entries per student (default: 6)'
        )
        parser.add_argument(
            '--complete-ratio',
            type=float,
            default=0.85,
            help='Ratio of completed feedbacks (default: 0.85 = 85%)'
        )

    def handle(self, *args, **options):
        per_student = options['per_student']
        complete_ratio = options['complete_ratio']
        
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS('  FACULTY FEEDBACK BULK POPULATION'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(f'\n📊 Creating {per_student} feedbacks per student')
        self.stdout.write(f'✅ {complete_ratio*100}% will be completed\n')
        
        # Get active faculty and students
        faculty_list = list(Faculty.objects.filter(
            deleted_at__isnull=True,
            is_active=True
        ).select_related('user', 'center'))
        
        students_list = list(Student.objects.filter(
            deleted_at__isnull=True,
            status='active'
        ).select_related('center'))
        
        if not faculty_list:
            self.stdout.write(self.style.ERROR('❌ No active faculty found. Please create faculty first.'))
            return
        
        if not students_list:
            self.stdout.write(self.style.ERROR('❌ No active students found. Please create students first.'))
            return
        
        self.stdout.write(f'👥 Found {len(students_list)} students and {len(faculty_list)} faculty\n')
        
        # Get user for created_by
        master_user = User.objects.filter(role='master_account').first()
        if not master_user:
            master_user = User.objects.filter(role='center_head').first()
        if not master_user:
            master_user = User.objects.filter(is_superuser=True).first()
        
        if not master_user:
            self.stdout.write(self.style.ERROR('❌ No user found for created_by field.'))
            return
        
        created_count = 0
        completed_count = 0
        skipped_count = 0
        
        # Sample comments for realistic feedback
        positive_comments = [
            "Excellent teaching! Very clear explanations and always available for doubts.",
            "Great teacher, always patient and makes learning enjoyable.",
            "Makes complex topics easy to understand with practical examples.",
            "Very knowledgeable and helpful. Best faculty I've had!",
            "Outstanding teaching quality. Highly recommend to everyone!",
            "Explains concepts with real-world examples which helps a lot.",
            "Very engaging and interactive sessions. Never boring!",
            "Always available to help and very supportive.",
            "Perfect balance of theory and practice. Excellent mentor!",
            "Creates a positive learning environment. Great experience!",
        ]
        
        neutral_comments = [
            "Good teacher overall. Sessions are helpful.",
            "Decent teaching quality. Getting better with time.",
            "Satisfactory experience. Could use more examples.",
            "Good knowledge but could improve engagement.",
            "Helpful sessions. Would like more interactive activities.",
        ]
        
        negative_comments = [
            "Could improve explanation clarity and pace.",
            "Sometimes difficult to follow. Need more examples.",
            "Need more practice problems and hands-on work.",
            "Could be more patient with questions and doubts.",
        ]
        
        # Create feedbacks for each student
        for student_idx, student in enumerate(students_list, 1):
            # Get faculty from same center
            center_faculty = [f for f in faculty_list if f.center == student.center]
            if not center_faculty:
                skipped_count += 1
                continue
            
            self.stdout.write(f'\n[{student_idx}/{len(students_list)}] 👤 {student.get_full_name()}')
            
            # Create multiple feedbacks for this student
            for i in range(per_student):
                # Randomly select faculty from same center
                faculty = random.choice(center_faculty)
                
                # Determine if this should be completed
                is_completed = random.random() < complete_ratio
                
                # Create feedback
                feedback = FacultyFeedback.objects.create(
                    faculty=faculty,
                    student=student,
                    center=faculty.center,
                    created_by=master_user,
                    modified_by=master_user
                )
                
                if is_completed:
                    # Generate realistic ratings (skewed towards positive)
                    base_score = random.choice([3, 4, 4, 4, 4, 5, 5, 5])  # More 4s and 5s
                    
                    feedback.teaching_quality = max(1, min(5, base_score + random.randint(-1, 1)))
                    feedback.subject_knowledge = max(1, min(5, base_score + random.randint(-1, 1)))
                    feedback.explanation_clarity = max(1, min(5, base_score + random.randint(-1, 1)))
                    feedback.student_engagement = max(1, min(5, base_score + random.randint(-1, 1)))
                    feedback.doubt_resolution = max(1, min(5, base_score + random.randint(-1, 1)))
                    
                    # Add comments based on average score
                    avg_score = (
                        feedback.teaching_quality +
                        feedback.subject_knowledge +
                        feedback.explanation_clarity +
                        feedback.student_engagement +
                        feedback.doubt_resolution
                    ) / 5
                    
                    if avg_score >= 4.5:
                        feedback.comments = random.choice(positive_comments)
                    elif avg_score >= 3.5:
                        if random.random() > 0.5:
                            feedback.comments = random.choice(positive_comments)
                        else:
                            feedback.comments = random.choice(neutral_comments)
                    elif avg_score >= 2.5:
                        feedback.comments = random.choice(neutral_comments)
                    else:
                        feedback.comments = random.choice(negative_comments)
                    
                    # Set submission timestamps (spread over last 90 days)
                    days_ago = random.randint(1, 90)
                    feedback.submitted_at = timezone.now() - timedelta(days=days_ago)
                    feedback.whatsapp_sent_at = feedback.submitted_at - timedelta(days=random.randint(1, 3))
                    feedback.link_opened_at = feedback.submitted_at - timedelta(hours=random.randint(1, 48))
                    feedback.is_completed = True
                    
                    feedback.save()
                    completed_count += 1
                    status_icon = '✅'
                else:
                    # Pending feedback - just set whatsapp_sent_at
                    days_ago = random.randint(1, 7)
                    feedback.whatsapp_sent_at = timezone.now() - timedelta(days=days_ago)
                    feedback.save()
                    status_icon = '⏳'
                
                created_count += 1
                self.stdout.write(f'  {status_icon} Feedback {i+1}/{per_student}: → {faculty.user.get_full_name()} ({feedback.overall_score if is_completed else "Pending"})')
        
        # Summary
        self.stdout.write(self.style.SUCCESS('\n' + '='*60))
        self.stdout.write(self.style.SUCCESS('  SUMMARY'))
        self.stdout.write(self.style.SUCCESS('='*60))
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully created {created_count} feedback entries'))
        self.stdout.write(self.style.SUCCESS(f'   - Completed: {completed_count} ({completed_count/created_count*100:.1f}%)'))
        self.stdout.write(self.style.SUCCESS(f'   - Pending: {created_count - completed_count} ({(created_count-completed_count)/created_count*100:.1f}%)'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'⚠️  Skipped {skipped_count} students (no faculty in center)'))
        self.stdout.write(self.style.SUCCESS(f'\n🎉 Average: {created_count/len(students_list):.1f} feedbacks per student'))
        self.stdout.write(self.style.SUCCESS('\n📊 View feedback at: /feedback/faculty-feedback/'))
        self.stdout.write(self.style.SUCCESS('📈 View analysis at: /feedback/faculty-feedback/analysis/<faculty_id>/\n'))
