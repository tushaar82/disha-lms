"""
Management command to create a master account user.
"""

from django.core.management.base import BaseCommand
from apps.accounts.models import User


class Command(BaseCommand):
    help = 'Create a master account user for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--email',
            type=str,
            default='master@example.com',
            help='Email for the master account (default: master@example.com)'
        )
        parser.add_argument(
            '--password',
            type=str,
            default='master123',
            help='Password for the master account (default: master123)'
        )
        parser.add_argument(
            '--first-name',
            type=str,
            default='Master',
            help='First name (default: Master)'
        )
        parser.add_argument(
            '--last-name',
            type=str,
            default='Admin',
            help='Last name (default: Admin)'
        )

    def handle(self, *args, **options):
        email = options['email']
        password = options['password']
        first_name = options['first_name']
        last_name = options['last_name']

        # Check if user already exists
        if User.objects.filter(email=email).exists():
            self.stdout.write(
                self.style.WARNING(f'User with email {email} already exists!')
            )
            user = User.objects.get(email=email)
            
            # Update to master account if not already
            if user.role != 'master':
                user.role = 'master'
                user.save()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated {email} to master account role.')
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(f'{email} is already a master account.')
                )
            return

        # Create new master account
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role='master',
            is_active=True
        )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nMaster account created successfully!\n'
                f'Email: {email}\n'
                f'Password: {password}\n'
                f'Name: {first_name} {last_name}\n'
                f'\nYou can now login at: http://127.0.0.1:8000/accounts/login/'
            )
        )
