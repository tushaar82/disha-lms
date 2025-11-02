"""
API views for Disha LMS.
"""

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import login, logout

from rest_framework import viewsets
from rest_framework.decorators import action

from .serializers import (
    LoginSerializer, LoginResponseSerializer, UserSerializer,
    AttendanceRecordSerializer, TopicSerializer,
    StudentSerializer, AssignmentSerializer,
    FacultySerializer, SubjectSerializer,
    CenterSerializer, CenterHeadSerializer,
    CenterReportSerializer, StudentReportSerializer,
    FacultyReportSerializer, InsightsSerializer
)


class LoginAPIView(APIView):
    """
    API endpoint for user login.
    Returns authentication token and user details.
    """
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Create or get token
            token, created = Token.objects.get_or_create(user=user)
            
            # Login user (for session-based auth)
            login(request, user)
            
            # Prepare response
            response_data = {
                'token': token.key,
                'user': UserSerializer(user).data
            }
            
            return Response(response_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    """
    API endpoint for user logout.
    Deletes the authentication token.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Delete the user's token
        try:
            request.user.auth_token.delete()
        except:
            pass
        
        # Logout user (for session-based auth)
        logout(request)
        
        return Response(
            {'message': 'Successfully logged out.'},
            status=status.HTTP_200_OK
        )


class MeAPIView(APIView):
    """
    API endpoint to get current user's profile.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def patch(self, request):
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Attendance API Views

class AttendanceViewSet(APIView):
    """
    API endpoint for attendance records.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """List attendance records for the authenticated user."""
        from apps.attendance.models import AttendanceRecord
        
        if request.user.is_faculty_member:
            # Faculty sees their own marked attendance
            queryset = AttendanceRecord.objects.filter(
                marked_by=request.user
            ).select_related('student', 'assignment__subject').prefetch_related('topics_covered')
        else:
            # Other roles see all attendance (admin)
            queryset = AttendanceRecord.objects.all().select_related(
                'student', 'assignment__subject'
            ).prefetch_related('topics_covered')
        
        # Filter by date if provided
        date = request.query_params.get('date')
        if date:
            queryset = queryset.filter(date=date)
        
        queryset = queryset.order_by('-date', '-in_time')[:50]  # Limit to 50 records
        
        serializer = AttendanceRecordSerializer(queryset, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        """Create a new attendance record."""
        serializer = AttendanceRecordSerializer(data=request.data)
        
        if serializer.is_valid():
            # Set marked_by to current user
            serializer.save(marked_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TodayAttendanceAPIView(APIView):
    """
    API endpoint for today's attendance.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get today's attendance for the authenticated user."""
        from apps.attendance.services import get_today_attendance_for_faculty
        from django.utils import timezone
        
        if not request.user.is_faculty_member:
            return Response(
                {'error': 'Only faculty can access this endpoint'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        faculty = request.user.faculty_profile
        attendance_records = get_today_attendance_for_faculty(faculty)
        
        serializer = AttendanceRecordSerializer(attendance_records, many=True)
        return Response({
            'date': timezone.now().date(),
            'count': attendance_records.count(),
            'records': serializer.data
        })


class BulkAttendanceAPIView(APIView):
    """
    API endpoint for bulk attendance marking.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Create multiple attendance records at once."""
        if not isinstance(request.data, list):
            return Response(
                {'error': 'Expected a list of attendance records'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        created_records = []
        errors = []
        
        for i, record_data in enumerate(request.data):
            serializer = AttendanceRecordSerializer(data=record_data)
            
            if serializer.is_valid():
                serializer.save(marked_by=request.user)
                created_records.append(serializer.data)
            else:
                errors.append({
                    'index': i,
                    'errors': serializer.errors
                })
        
        return Response({
            'created': len(created_records),
            'failed': len(errors),
            'records': created_records,
            'errors': errors
        }, status=status.HTTP_201_CREATED if created_records else status.HTTP_400_BAD_REQUEST)


# Student Management API ViewSets (T102)

class StudentViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Student CRUD operations.
    """
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.students.models import Student
        
        # Center heads see only their center's students
        if hasattr(self.request.user, 'center_head_profile'):
            return Student.objects.filter(
                center=self.request.user.center_head_profile.center,
                deleted_at__isnull=True
            ).select_related('center')
        
        # Master accounts see all students
        if self.request.user.is_master_account:
            return Student.objects.filter(
                deleted_at__isnull=True
            ).select_related('center')
        
        # Faculty see students assigned to them
        if hasattr(self.request.user, 'faculty_profile'):
            from apps.subjects.models import Assignment
            student_ids = Assignment.objects.filter(
                faculty=self.request.user.faculty_profile,
                is_active=True
            ).values_list('student_id', flat=True)
            return Student.objects.filter(
                id__in=student_ids,
                deleted_at__isnull=True
            ).select_related('center')
        
        return Student.objects.none()
    
    @action(detail=False, methods=['get'])
    def ready_for_transfer(self, request):
        """Get students ready for transfer (completed status)."""
        queryset = self.get_queryset().filter(status='completed')
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# Faculty Management API ViewSet (T103)

class FacultyViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Faculty CRUD operations.
    """
    serializer_class = FacultySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.faculty.models import Faculty
        
        # Center heads see only their center's faculty
        if hasattr(self.request.user, 'center_head_profile'):
            return Faculty.objects.filter(
                center=self.request.user.center_head_profile.center,
                deleted_at__isnull=True
            ).select_related('user', 'center')
        
        # Master accounts see all faculty
        if self.request.user.is_master_account:
            return Faculty.objects.filter(
                deleted_at__isnull=True
            ).select_related('user', 'center')
        
        return Faculty.objects.none()


# Subject Management API ViewSet (T104)

class SubjectViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Subject CRUD operations.
    """
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.subjects.models import Subject
        from django.db.models import Count
        
        # Center heads see only their center's subjects
        if hasattr(self.request.user, 'center_head_profile'):
            return Subject.objects.filter(
                center=self.request.user.center_head_profile.center,
                deleted_at__isnull=True
            ).select_related('center').annotate(
                topic_count=Count('topics')
            )
        
        # Master accounts see all subjects
        if self.request.user.is_master_account:
            return Subject.objects.filter(
                deleted_at__isnull=True
            ).select_related('center').annotate(
                topic_count=Count('topics')
            )
        
        # Faculty see subjects they teach
        if hasattr(self.request.user, 'faculty_profile'):
            from apps.subjects.models import Assignment
            subject_ids = Assignment.objects.filter(
                faculty=self.request.user.faculty_profile,
                is_active=True
            ).values_list('subject_id', flat=True)
            return Subject.objects.filter(
                id__in=subject_ids,
                deleted_at__isnull=True
            ).select_related('center').annotate(
                topic_count=Count('topics')
            )
        
        return Subject.objects.none()
    
    @action(detail=True, methods=['get'])
    def topics(self, request, pk=None):
        """Get topics for a specific subject."""
        subject = self.get_object()
        from apps.subjects.models import Topic
        topics = Topic.objects.filter(
            subject=subject,
            is_active=True
        ).order_by('sequence_number')
        serializer = TopicSerializer(topics, many=True)
        return Response(serializer.data)


# Assignment API ViewSet (T105)

class AssignmentViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Assignment CRUD operations.
    """
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.subjects.models import Assignment
        
        # Center heads see assignments in their center
        if hasattr(self.request.user, 'center_head_profile'):
            return Assignment.objects.filter(
                student__center=self.request.user.center_head_profile.center
            ).select_related('student', 'subject', 'faculty__user')
        
        # Master accounts see all assignments
        if self.request.user.is_master_account:
            return Assignment.objects.all().select_related(
                'student', 'subject', 'faculty__user'
            )
        
        # Faculty see their own assignments
        if hasattr(self.request.user, 'faculty_profile'):
            return Assignment.objects.filter(
                faculty=self.request.user.faculty_profile
            ).select_related('student', 'subject', 'faculty__user')
        
        return Assignment.objects.none()
    
    @action(detail=False, methods=['get'])
    def by_student(self, request):
        """Get assignments for a specific student."""
        student_id = request.query_params.get('student_id')
        if not student_id:
            return Response(
                {'error': 'student_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(student_id=student_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_faculty(self, request):
        """Get assignments for a specific faculty."""
        faculty_id = request.query_params.get('faculty_id')
        if not faculty_id:
            return Response(
                {'error': 'faculty_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(faculty_id=faculty_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# Multi-Center Management API ViewSets (T129-T130)

class CenterViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for Center CRUD operations.
    Master accounts only.
    """
    serializer_class = CenterSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.centers.models import Center
        from django.db.models import Count, Q
        
        # Only master accounts can access centers API
        if not self.request.user.is_master_account:
            return Center.objects.none()
        
        return Center.objects.filter(
            deleted_at__isnull=True
        ).annotate(
            student_count=Count('students', filter=Q(students__deleted_at__isnull=True)),
            faculty_count=Count('faculty_members', filter=Q(faculty_members__deleted_at__isnull=True)),
            subject_count=Count('subjects', filter=Q(subjects__deleted_at__isnull=True))
        ).order_by('-created_at')
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get detailed statistics for a center."""
        center = self.get_object()
        
        from apps.students.models import Student
        from apps.faculty.models import Faculty
        from apps.subjects.models import Subject
        from apps.attendance.models import AttendanceRecord
        from django.utils import timezone
        from datetime import timedelta
        
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)
        
        stats = {
            'center': CenterSerializer(center).data,
            'students': {
                'total': Student.objects.filter(center=center, deleted_at__isnull=True).count(),
                'active': Student.objects.filter(center=center, status='active', deleted_at__isnull=True).count(),
                'inactive': Student.objects.filter(center=center, status='inactive', deleted_at__isnull=True).count(),
                'completed': Student.objects.filter(center=center, status='completed', deleted_at__isnull=True).count(),
            },
            'faculty': {
                'total': Faculty.objects.filter(center=center, deleted_at__isnull=True).count(),
                'active': Faculty.objects.filter(center=center, is_active=True, deleted_at__isnull=True).count(),
            },
            'subjects': {
                'total': Subject.objects.filter(center=center, deleted_at__isnull=True).count(),
                'active': Subject.objects.filter(center=center, is_active=True, deleted_at__isnull=True).count(),
            },
            'attendance': {
                'this_week': AttendanceRecord.objects.filter(
                    student__center=center,
                    date__gte=week_ago
                ).count(),
                'this_month': AttendanceRecord.objects.filter(
                    student__center=center,
                    date__gte=month_ago
                ).count(),
            }
        }
        
        return Response(stats)


class CenterHeadViewSet(viewsets.ModelViewSet):
    """
    API ViewSet for CenterHead CRUD operations.
    Master accounts only.
    """
    serializer_class = CenterHeadSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        from apps.centers.models import CenterHead
        
        # Only master accounts can access center heads API
        if not self.request.user.is_master_account:
            return CenterHead.objects.none()
        
        return CenterHead.objects.filter(
            deleted_at__isnull=True
        ).select_related('user', 'center').order_by('-created_at')
    
    @action(detail=False, methods=['get'])
    def by_center(self, request):
        """Get center heads for a specific center."""
        center_id = request.query_params.get('center_id')
        if not center_id:
            return Response(
                {'error': 'center_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        queryset = self.get_queryset().filter(center_id=center_id)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


# Report API Views (T150-T153)

class CenterReportAPIView(APIView):
    """
    T150: API endpoint for center report data.
    Returns comprehensive metrics, charts, and insights for a center.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, center_id):
        """Get center report data."""
        from apps.centers.models import Center
        from apps.reports.services import calculate_center_metrics, get_insights_summary
        from django.shortcuts import get_object_or_404
        
        center = get_object_or_404(Center, pk=center_id, deleted_at__isnull=True)
        
        # Check permissions
        if request.user.is_center_head:
            if not hasattr(request.user, 'center_head_profile') or \
               request.user.center_head_profile.center != center:
                return Response(
                    {'error': 'You do not have permission to view this center.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not request.user.is_master_account:
            return Response(
                {'error': 'You do not have permission to access reports.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get center metrics
        metrics = calculate_center_metrics(center)[0]
        
        # Get insights
        insights = get_insights_summary(center)
        metrics['insights'] = insights
        
        serializer = CenterReportSerializer(metrics)
        return Response(serializer.data)


class StudentReportAPIView(APIView):
    """
    T151: API endpoint for student report data.
    Returns attendance velocity, learning velocity, and subject progress.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, student_id):
        """Get student report data."""
        from apps.students.models import Student
        from apps.reports.services import (
            calculate_attendance_velocity,
            calculate_learning_velocity,
            prepare_subject_completion_data
        )
        from apps.attendance.models import AttendanceRecord
        from django.shortcuts import get_object_or_404
        
        student = get_object_or_404(Student, pk=student_id, deleted_at__isnull=True)
        
        # Check permissions
        if request.user.is_center_head:
            if not hasattr(request.user, 'center_head_profile') or \
               request.user.center_head_profile.center != student.center:
                return Response(
                    {'error': 'You do not have permission to view this student.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not (request.user.is_master_account or request.user.is_faculty_member):
            return Response(
                {'error': 'You do not have permission to access reports.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get days parameter (default 30)
        days = int(request.query_params.get('days', 30))
        
        # Calculate velocities
        attendance_velocity = calculate_attendance_velocity(student, days=days)
        learning_velocity = calculate_learning_velocity(student)
        
        # Get subject completion data
        subject_completion = prepare_subject_completion_data(student)
        
        # Get recent attendance records
        recent_attendance = AttendanceRecord.objects.filter(
            student=student
        ).select_related('assignment__subject', 'marked_by').order_by('-date')[:10]
        
        # Prepare response data
        data = {
            'student': StudentSerializer(student).data,
            'attendance_velocity': attendance_velocity,
            'learning_velocity': learning_velocity,
            'subject_completion': subject_completion,
            'recent_attendance': AttendanceRecordSerializer(recent_attendance, many=True).data
        }
        
        serializer = StudentReportSerializer(data)
        return Response(serializer.data)


class FacultyReportAPIView(APIView):
    """
    T152: API endpoint for faculty report data.
    Returns teaching statistics, student performance, and session metrics.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, faculty_id):
        """Get faculty report data."""
        from apps.faculty.models import Faculty
        from apps.attendance.models import AttendanceRecord
        from apps.subjects.models import Assignment
        from apps.students.models import Student
        from django.shortcuts import get_object_or_404
        from django.db.models import Avg, Sum, Count, Q
        
        faculty = get_object_or_404(Faculty, pk=faculty_id, deleted_at__isnull=True)
        
        # Check permissions
        if request.user.is_center_head:
            if not hasattr(request.user, 'center_head_profile') or \
               request.user.center_head_profile.center != faculty.center:
                return Response(
                    {'error': 'You do not have permission to view this faculty.'},
                    status=status.HTTP_403_FORBIDDEN
                )
        elif not request.user.is_master_account:
            return Response(
                {'error': 'You do not have permission to access reports.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get teaching statistics
        records = AttendanceRecord.objects.filter(marked_by=faculty.user)
        
        stats = {
            'total_sessions': records.count(),
            'total_students': records.values('student').distinct().count(),
            'total_subjects': Assignment.objects.filter(
                faculty=faculty,
                deleted_at__isnull=True
            ).values('subject').distinct().count(),
            'avg_session_duration': records.aggregate(avg=Avg('duration_minutes'))['avg'] or 0,
            'total_teaching_hours': (records.aggregate(total=Sum('duration_minutes'))['total'] or 0) / 60,
        }
        
        # Get top students
        top_students = Student.objects.filter(
            id__in=records.values_list('student_id', flat=True).distinct()
        ).annotate(
            session_count=Count('attendancerecord', filter=Q(attendancerecord__marked_by=faculty.user))
        ).order_by('-session_count')[:10]
        
        # Get recent sessions
        recent_sessions = records.select_related('student', 'assignment__subject').order_by('-date')[:10]
        
        # Prepare response data
        data = {
            'faculty': FacultySerializer(faculty).data,
            'stats': stats,
            'top_students': StudentSerializer(top_students, many=True).data,
            'recent_sessions': AttendanceRecordSerializer(recent_sessions, many=True).data
        }
        
        serializer = FacultyReportSerializer(data)
        return Response(serializer.data)


class InsightsAPIView(APIView):
    """
    T153: API endpoint for insights data.
    Returns at-risk students, extended students, and students nearing completion.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, center_id=None):
        """Get insights data."""
        from apps.centers.models import Center
        from apps.reports.services import (
            get_insights_summary,
            get_at_risk_students,
            get_extended_students,
            get_nearing_completion_students
        )
        from django.shortcuts import get_object_or_404
        
        # Determine center
        center = None
        if request.user.is_center_head:
            if hasattr(request.user, 'center_head_profile'):
                center = request.user.center_head_profile.center
        elif request.user.is_master_account:
            if center_id:
                center = get_object_or_404(Center, pk=center_id, deleted_at__isnull=True)
        else:
            return Response(
                {'error': 'You do not have permission to access insights.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get query parameters
        days_threshold = int(request.query_params.get('days_threshold', 7))
        months_threshold = int(request.query_params.get('months_threshold', 6))
        completion_threshold = int(request.query_params.get('completion_threshold', 80))
        
        # Get insights
        insights = get_insights_summary(center)
        at_risk = get_at_risk_students(center, days_threshold=days_threshold)
        extended = get_extended_students(center, months_threshold=months_threshold)
        nearing_completion = get_nearing_completion_students(center, completion_threshold=completion_threshold)
        
        # Prepare response data
        data = {
            'at_risk_count': insights['at_risk_count'],
            'extended_count': insights['extended_count'],
            'nearing_completion_count': insights['nearing_completion_count'],
            'at_risk_students': StudentSerializer(at_risk, many=True).data,
            'extended_students': StudentSerializer(extended, many=True).data,
            'nearing_completion': StudentSerializer(nearing_completion, many=True).data
        }
        
        serializer = InsightsSerializer(data)
        return Response(serializer.data)
