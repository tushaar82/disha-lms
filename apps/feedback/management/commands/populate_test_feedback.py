"""
Management command to populate test faculty feedback data.
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
    help = 'Populate test faculty feedback data'

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
            default=0.8,
            help='Ratio of completed feedbacks (default: 0.8 = 80%)'
        )

    def handle(self, *args, **options):
        per_student = options['per_student']
        complete_ratio = options['complete_ratio']
        
        self.stdout.write('Starting to populate test feedback data...')
        self.stdout.write(f'Creating {per_student} feedbacks per student ({complete_ratio*100}% completed)')
        
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
            self.stdout.write(self.style.ERROR('No active faculty found. Please create faculty first.'))
            return
        
        if not students_list:
            self.stdout.write(self.style.ERROR('No active students found. Please create students first.'))
            return
        
        # Get or create a master account user for created_by
        master_user = User.objects.filter(role='master_account').first()
        if not master_user:
            self.stdout.write(self.style.WARNING('No master account found. Using first center head.'))
            master_user = User.objects.filter(role='center_head').first()
        
        if not master_user:
            self.stdout.write(self.style.WARNING('No center head found. Using first superuser.'))
            master_user = User.objects.filter(is_superuser=True).first()
        
        if not master_user:
            self.stdout.write(self.style.ERROR('No user found for created_by field.'))
            return
        
        created_count = 0
        completed_count = 0
        skipped_count = 0
        
        # Sample comments for realistic feedback
        positive_comments = [
            "Excellent teaching! Very clear explanations.",
            "Great teacher, always patient with doubts.",
            "Makes complex topics easy to understand.",
            "Very knowledgeable and helpful.",
            "Best teacher I've had. Highly recommend!",
            "Explains concepts with real-world examples.",
            "Very engaging and interactive sessions.",
            "Always available to help with doubts.",
        ]
        
        neutral_comments = [
            "Good teacher overall.",
            "Sessions are helpful.",
            "Decent teaching quality.",
            "Satisfactory experience.",
        ]
        
        negative_comments = [
            "Could improve explanation clarity.",
            "Sometimes difficult to follow.",
            "Need more examples and practice.",
            "Could be more patient with questions.",
        ]
        
        # Create feedbacks for each student
        for student in students_list:
            # Get faculty from same center
            center_faculty = [f for f in faculty_list if f.center == student.center]
            if not center_faculty:
                continue
            
            # Determine if this should be completed
            is_completed = i < complete_count
            
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
                base_score = random.choice([3, 4, 4, 4, 5, 5, 5])  # More 4s and 5s
                
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
                
                # Set submission timestamps
                days_ago = random.randint(1, 30)
                feedback.submitted_at = timezone.now() - timedelta(days=days_ago)
                feedback.whatsapp_sent_at = feedback.submitted_at - timedelta(days=random.randint(1, 3))
                feedback.link_opened_at = feedback.submitted_at - timedelta(hours=random.randint(1, 48))
                feedback.is_completed = True
                
                feedback.save()
                completed_count += 1
            else:
                # Pending feedback - just set whatsapp_sent_at
                days_ago = random.randint(1, 7)
                feedback.whatsapp_sent_at = timezone.now() - timedelta(days=days_ago)
                feedback.save()
            
            created_count += 1
            
            self.stdout.write(f'Created feedback {created_count}/{count}: {student.get_full_name()} → {faculty.user.get_full_name()} ({"Completed" if is_completed else "Pending"})')
        
        self.stdout.write(self.style.SUCCESS(f'\nSuccessfully created {created_count} feedback entries:'))
        self.stdout.write(self.style.SUCCESS(f'  - Completed: {completed_count}'))
        self.stdout.write(self.style.SUCCESS(f'  - Pending: {created_count - completed_count}'))
        self.stdout.write(self.style.SUCCESS('\nYou can now view the feedback at /feedback/faculty-feedback/'))
