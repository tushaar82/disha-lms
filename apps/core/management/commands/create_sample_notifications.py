"""
Management command to create sample notifications and tasks for testing.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.core.models import Notification, Task
from apps.accounts.models import User
from apps.centers.models import Center


class Command(BaseCommand):
    help = 'Create sample notifications and tasks for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing notifications and tasks before creating new ones',
        )
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='Number of notifications/tasks to create per user',
        )

    def handle(self, *args, **options):
        clear = options['clear']
        count = options['count']

        if clear:
            self.stdout.write('Clearing existing notifications and tasks...')
            Notification.objects.all().delete()
            Task.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared successfully'))

        # Get users
        master_users = User.objects.filter(role=User.MASTER_ACCOUNT, is_active=True)
        center_heads = User.objects.filter(role=User.CENTER_HEAD, is_active=True)
        
        if not master_users.exists() and not center_heads.exists():
            self.stdout.write(self.style.WARNING('No master or center head users found'))
            return

        # Get centers
        centers = Center.objects.filter(deleted_at__isnull=True, is_active=True)

        notifications_created = 0
        tasks_created = 0

        # Create notifications for master accounts
        for user in master_users:
            notifications_created += self.create_master_notifications(user, count)
            tasks_created += self.create_master_tasks(user, count, centers)

        # Create notifications for center heads
        for user in center_heads:
            try:
                center = user.center_head_profile.center
                notifications_created += self.create_center_head_notifications(user, count, center)
                tasks_created += self.create_center_head_tasks(user, count // 2, center)
            except:
                continue

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created {notifications_created} notifications and {tasks_created} tasks'
        ))

    def create_master_notifications(self, user, count):
        """Create sample notifications for master account."""
        notification_templates = [
            {
                'title': '🚨 Low Attendance Alert',
                'message': 'Mumbai Center has attendance rate below 60% this week.',
                'notification_type': 'warning',
                'action_url': '/reports/center/1/'
            },
            {
                'title': '📊 Weekly Report Ready',
                'message': 'Your weekly performance report is now available.',
                'notification_type': 'info',
                'action_url': '/reports/master/'
            },
            {
                'title': '✅ New Center Added',
                'message': 'Pune Center has been successfully added to the system.',
                'notification_type': 'success',
                'action_url': '/centers/'
            },
            {
                'title': '⚠️ Faculty Shortage',
                'message': 'Delhi Center has high student-to-faculty ratio (25:1).',
                'notification_type': 'warning',
                'action_url': '/reports/center/2/'
            },
            {
                'title': '📈 Excellent Performance',
                'message': 'Bangalore Center achieved 95% attendance rate this month!',
                'notification_type': 'success',
                'action_url': '/reports/center/3/'
            },
            {
                'title': '❌ System Maintenance',
                'message': 'Scheduled maintenance on Sunday 2 AM - 4 AM.',
                'notification_type': 'info',
                'action_url': None
            },
            {
                'title': '👥 New Students Enrolled',
                'message': '15 new students enrolled across all centers this week.',
                'notification_type': 'success',
                'action_url': '/students/'
            },
            {
                'title': '📝 Feedback Survey Results',
                'message': 'Student satisfaction survey results are available.',
                'notification_type': 'info',
                'action_url': '/feedback/'
            },
            {
                'title': '⏰ Pending Approvals',
                'message': 'You have 3 pending faculty leave requests.',
                'notification_type': 'warning',
                'action_url': '/core/tasks/'
            },
            {
                'title': '🎯 Monthly Target Achieved',
                'message': 'Congratulations! All centers met their monthly targets.',
                'notification_type': 'success',
                'action_url': '/reports/master/'
            },
        ]

        created = 0
        for i in range(min(count, len(notification_templates))):
            template = notification_templates[i]
            Notification.objects.create(
                user=user,
                title=template['title'],
                message=template['message'],
                notification_type=template['notification_type'],
                action_url=template['action_url'],
                is_read=(i % 3 == 0),  # Mark some as read
                created_at=timezone.now() - timedelta(hours=i)
            )
            created += 1

        return created

    def create_center_head_notifications(self, user, count, center):
        """Create sample notifications for center head."""
        notification_templates = [
            {
                'title': '👨‍🎓 Student Absent Alert',
                'message': f'5 students have been absent for more than 4 days.',
                'notification_type': 'warning',
                'action_url': f'/centers/dashboard/'
            },
            {
                'title': '📚 New Assignment Created',
                'message': 'Faculty has created new assignments for Mathematics.',
                'notification_type': 'info',
                'action_url': '/subjects/'
            },
            {
                'title': '✨ Student Ready for Transfer',
                'message': 'Rahul Kumar has been marked as ready to transfer.',
                'notification_type': 'info',
                'action_url': '/students/'
            },
            {
                'title': '📊 Weekly Attendance Report',
                'message': f'Your center achieved 85% attendance this week.',
                'notification_type': 'success',
                'action_url': '/centers/dashboard/'
            },
            {
                'title': '⚠️ Faculty Absence',
                'message': 'Dr. Sharma will be on leave tomorrow.',
                'notification_type': 'warning',
                'action_url': '/faculty/'
            },
        ]

        created = 0
        for i in range(min(count, len(notification_templates))):
            template = notification_templates[i]
            Notification.objects.create(
                user=user,
                title=template['title'],
                message=template['message'],
                notification_type=template['notification_type'],
                action_url=template['action_url'],
                is_read=(i % 2 == 0),
                created_at=timezone.now() - timedelta(hours=i)
            )
            created += 1

        return created

    def create_master_tasks(self, user, count, centers):
        """Create sample tasks for master account."""
        task_templates = [
            {
                'title': 'Review Low-Performing Centers',
                'description': 'Analyze and create action plan for centers with attendance < 60%.',
                'task_type': 'review',
                'priority': 'high',
                'due_date': timezone.now().date() + timedelta(days=3)
            },
            {
                'title': 'Approve Faculty Hiring',
                'description': 'Review and approve 3 faculty hiring requests from Mumbai Center.',
                'task_type': 'approval',
                'priority': 'medium',
                'due_date': timezone.now().date() + timedelta(days=5)
            },
            {
                'title': 'Quarterly Performance Review',
                'description': 'Conduct quarterly performance review for all centers.',
                'task_type': 'review',
                'priority': 'critical',
                'due_date': timezone.now().date() + timedelta(days=7)
            },
            {
                'title': 'Budget Allocation Planning',
                'description': 'Plan budget allocation for next quarter.',
                'task_type': 'action',
                'priority': 'high',
                'due_date': timezone.now().date() + timedelta(days=10)
            },
            {
                'title': 'Follow Up on Student Feedback',
                'description': 'Address concerns raised in student satisfaction survey.',
                'task_type': 'follow_up',
                'priority': 'medium',
                'due_date': timezone.now().date() + timedelta(days=5)
            },
        ]

        created = 0
        for i in range(min(count, len(task_templates))):
            template = task_templates[i]
            center = centers[i % centers.count()] if centers.exists() else None
            
            Task.objects.create(
                assigned_to=user,
                title=template['title'],
                description=template['description'],
                task_type=template['task_type'],
                priority=template['priority'],
                status='pending' if i % 3 != 0 else 'in_progress',
                related_center=center,
                due_date=template['due_date'],
                created_by=user
            )
            created += 1

        return created

    def create_center_head_tasks(self, user, count, center):
        """Create sample tasks for center head."""
        task_templates = [
            {
                'title': 'Follow Up with Absent Students',
                'description': 'Contact guardians of students absent for more than 4 days.',
                'task_type': 'follow_up',
                'priority': 'high',
                'due_date': timezone.now().date() + timedelta(days=2)
            },
            {
                'title': 'Review Faculty Performance',
                'description': 'Conduct monthly performance review for all faculty.',
                'task_type': 'review',
                'priority': 'medium',
                'due_date': timezone.now().date() + timedelta(days=7)
            },
            {
                'title': 'Organize Parent-Teacher Meeting',
                'description': 'Schedule and organize monthly parent-teacher meeting.',
                'task_type': 'action',
                'priority': 'medium',
                'due_date': timezone.now().date() + timedelta(days=14)
            },
        ]

        created = 0
        for i in range(min(count, len(task_templates))):
            template = task_templates[i]
            
            Task.objects.create(
                assigned_to=user,
                title=template['title'],
                description=template['description'],
                task_type=template['task_type'],
                priority=template['priority'],
                status='pending',
                related_center=center,
                due_date=template['due_date'],
                created_by=user
            )
            created += 1

        return created
