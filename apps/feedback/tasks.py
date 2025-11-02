"""
Celery tasks for feedback and survey management.
T169: Create send_survey_email() Celery task
"""

from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.utils import timezone
from .models import FeedbackResponse, FeedbackSurvey


@shared_task(bind=True, max_retries=3)
def send_survey_email(self, response_id):
    """
    Send survey email to a student.
    T169: Celery task for sending survey emails
    
    Args:
        response_id: ID of the FeedbackResponse object
    
    Returns:
        dict: Status information
    """
    try:
        response = FeedbackResponse.objects.select_related(
            'survey', 'student'
        ).get(id=response_id)
        
        # Generate survey link (T172)
        survey_url = f"{settings.SITE_URL}/feedback/survey/{response.token}/"
        
        # Prepare email context
        context = {
            'student_name': response.student.get_full_name(),
            'survey_title': response.survey.title,
            'survey_description': response.survey.description,
            'survey_url': survey_url,
            'valid_until': response.survey.valid_until,
            'center_name': response.student.center.name if response.student.center else 'Disha LMS',
        }
        
        # Render email templates (T171)
        html_message = render_to_string('feedback/emails/survey_invitation.html', context)
        plain_message = strip_tags(html_message)
        
        # Send email
        send_mail(
            subject=f"Your feedback requested: {response.survey.title}",
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[response.student.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        # Update email sent timestamp
        response.email_sent_at = timezone.now()
        response.save(update_fields=['email_sent_at'])
        
        return {
            'status': 'success',
            'response_id': response_id,
            'student_email': response.student.email,
            'sent_at': response.email_sent_at.isoformat()
        }
        
    except FeedbackResponse.DoesNotExist:
        return {
            'status': 'error',
            'response_id': response_id,
            'error': 'FeedbackResponse not found'
        }
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def send_bulk_survey_emails(survey_id, student_ids):
    """
    Send survey emails to multiple students.
    
    Args:
        survey_id: ID of the FeedbackSurvey
        student_ids: List of student IDs
    
    Returns:
        dict: Summary of sent emails
    """
    from apps.students.models import Student
    
    survey = FeedbackSurvey.objects.get(id=survey_id)
    students = Student.objects.filter(id__in=student_ids, deleted_at__isnull=True)
    
    sent_count = 0
    failed_count = 0
    response_ids = []
    
    for student in students:
        # Create or get existing response
        response, created = FeedbackResponse.objects.get_or_create(
            survey=survey,
            student=student,
            defaults={'is_completed': False}
        )
        
        # Send email asynchronously
        try:
            send_survey_email.delay(response.id)
            sent_count += 1
            response_ids.append(response.id)
        except Exception as e:
            failed_count += 1
    
    return {
        'survey_id': survey_id,
        'total_students': len(student_ids),
        'sent_count': sent_count,
        'failed_count': failed_count,
        'response_ids': response_ids
    }


@shared_task
def send_pending_surveys():
    """
    Periodic task to send pending survey emails.
    Runs daily via Celery Beat.
    """
    from django.db.models import Q
    
    # Get responses that haven't been sent yet
    pending_responses = FeedbackResponse.objects.filter(
        email_sent_at__isnull=True,
        is_completed=False,
        survey__is_active=True,
        survey__is_published=True,
        survey__deleted_at__isnull=True
    ).select_related('survey', 'student')
    
    sent_count = 0
    for response in pending_responses:
        # Check if survey is still valid
        if response.survey.is_valid():
            send_survey_email.delay(response.id)
            sent_count += 1
    
    return {
        'task': 'send_pending_surveys',
        'sent_count': sent_count,
        'timestamp': timezone.now().isoformat()
    }


@shared_task
def send_survey_reminders():
    """
    Periodic task to send reminder emails for incomplete surveys.
    Runs daily via Celery Beat.
    """
    from datetime import timedelta
    
    # Get responses sent more than 3 days ago but not completed
    reminder_threshold = timezone.now() - timedelta(days=3)
    
    responses_needing_reminder = FeedbackResponse.objects.filter(
        email_sent_at__lte=reminder_threshold,
        is_completed=False,
        survey__is_active=True,
        survey__is_published=True,
        survey__deleted_at__isnull=True
    ).select_related('survey', 'student')
    
    sent_count = 0
    for response in responses_needing_reminder:
        # Check if survey is still valid
        if response.survey.is_valid():
            # Send reminder (reuse the same task)
            send_survey_email.delay(response.id)
            sent_count += 1
    
    return {
        'task': 'send_survey_reminders',
        'sent_count': sent_count,
        'timestamp': timezone.now().isoformat()
    }


@shared_task
def update_student_satisfaction_scores():
    """
    Update student satisfaction scores based on completed surveys.
    T178: Update student satisfaction_score
    """
    from apps.students.models import Student
    from django.db.models import Avg
    
    students = Student.objects.filter(deleted_at__isnull=True)
    updated_count = 0
    
    for student in students:
        # Calculate average satisfaction score from completed responses
        avg_score = FeedbackResponse.objects.filter(
            student=student,
            is_completed=True,
            satisfaction_score__isnull=False
        ).aggregate(avg=Avg('satisfaction_score'))['avg']
        
        if avg_score is not None:
            student.satisfaction_score = round(avg_score, 2)
            student.save(update_fields=['satisfaction_score'])
            updated_count += 1
    
    return {
        'task': 'update_student_satisfaction_scores',
        'updated_count': updated_count,
        'timestamp': timezone.now().isoformat()
    }
