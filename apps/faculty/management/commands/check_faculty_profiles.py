"""
Management command to check and fix faculty profile issues.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import User
from apps.faculty.models import Faculty
from apps.centers.models import Center


class Command(BaseCommand):
    help = 'Check for faculty users without profiles and optionally create them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Automatically create missing faculty profiles',
        )
        parser.add_argument(
            '--center-id',
            type=int,
            help='Center ID to assign to new faculty profiles',
        )

    def handle(self, *args, **options):
        fix = options['fix']
        center_id = options.get('center_id')

        # Find faculty users without profiles
        faculty_users = User.objects.filter(role='faculty')
        missing_profiles = []

        self.stdout.write(self.style.SUCCESS(f'\nChecking {faculty_users.count()} faculty users...'))

        for user in faculty_users:
            if not hasattr(user, 'faculty_profile'):
                missing_profiles.append(user)
                self.stdout.write(
                    self.style.WARNING(
                        f'  ❌ User {user.email} (ID: {user.id}) has faculty role but no Faculty profile'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'  ✅ User {user.email} (ID: {user.id}) has Faculty profile'
                    )
                )

        if not missing_profiles:
            self.stdout.write(self.style.SUCCESS('\n✅ All faculty users have profiles!'))
            return

        self.stdout.write(
            self.style.WARNING(f'\n⚠️  Found {len(missing_profiles)} faculty users without profiles')
        )

        if not fix:
            self.stdout.write(
                self.style.NOTICE(
                    '\nTo automatically create profiles, run:\n'
                    '  python manage.py check_faculty_profiles --fix --center-id=<CENTER_ID>'
                )
            )
            return

        # Fix mode - create missing profiles
        if not center_id:
            # Try to get the first available center
            center = Center.objects.filter(deleted_at__isnull=True, is_active=True).first()
            if not center:
                self.stdout.write(
                    self.style.ERROR(
                        '\n❌ No active centers found. Please create a center first or specify --center-id'
                    )
                )
                return
            center_id = center.id
            self.stdout.write(
                self.style.NOTICE(f'\nUsing default center: {center.name} (ID: {center.id})')
            )
        else:
            try:
                center = Center.objects.get(id=center_id, deleted_at__isnull=True)
            except Center.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'\n❌ Center with ID {center_id} not found')
                )
                return

        self.stdout.write(self.style.NOTICE(f'\nCreating Faculty profiles for {len(missing_profiles)} users...'))

        created_count = 0
        with transaction.atomic():
            for user in missing_profiles:
                try:
                    # Generate employee ID
                    employee_id = f'FAC{user.id:04d}'
                    
                    # Check if employee_id already exists
                    while Faculty.objects.filter(employee_id=employee_id).exists():
                        import random
                        employee_id = f'FAC{user.id:04d}{random.randint(10, 99)}'

                    faculty = Faculty.objects.create(
                        user=user,
                        center=center,
                        employee_id=employee_id,
                        joining_date=user.date_joined.date(),
                        is_active=True,
                        experience_years=0
                    )

                    created_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✅ Created Faculty profile for {user.email} '
                            f'(Employee ID: {employee_id})'
                        )
                    )

                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f'  ❌ Failed to create profile for {user.email}: {str(e)}'
                        )
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\n✅ Successfully created {created_count} Faculty profiles!'
            )
        )
        self.stdout.write(
            self.style.NOTICE(
                '\n💡 Note: You may want to update the faculty details (qualification, '
                'specialization, etc.) in the admin panel.'
            )
        )
